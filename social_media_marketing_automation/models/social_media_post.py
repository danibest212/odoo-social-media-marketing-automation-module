# -*- coding: utf-8 -*-
import logging

import requests

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

MANAGER_GROUP = 'social_media_marketing_automation.group_social_media_manager'
PARAM_AI_WEBHOOK_URL = 'social_media_marketing_automation.n8n_ai_webhook_url'
PARAM_API_KEY = 'social_media_marketing_automation.api_key'


class SocialMediaPost(models.Model):
    _name = 'social.media.post'
    _description = 'Social Media Post'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, id desc'

    name = fields.Char(
        string='Title', compute='_compute_name', store=True, readonly=False
    )
    message = fields.Text(required=True, tracking=True)
    image = fields.Image(max_width=1920, max_height=1920)
    link_url = fields.Char(string='Link')
    template_id = fields.Many2one(
        'social.media.template', string='Template',
        help='Pick a template to prefill the message, image, link and hashtags below.',
    )
    hashtag_ids = fields.Many2many('social.media.hashtag', string='Hashtags')
    account_id = fields.Many2one(
        'social.media.account', string='Account', required=True, tracking=True,
        ondelete='cascade',
    )
    platform = fields.Selection(related='account_id.platform', store=True, readonly=True)
    char_limit = fields.Integer(related='account_id.char_limit', readonly=True)
    company_id = fields.Many2one(related='account_id.company_id', store=True, readonly=True)
    campaign_id = fields.Many2one('social.media.campaign', string='Campaign', tracking=True)
    scheduled_date = fields.Datetime(string='Scheduled Date', tracking=True)
    published_date = fields.Datetime(string='Published Date', readonly=True)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('pending_approval', 'Pending Approval'),
            ('scheduled', 'Scheduled'),
            ('published', 'Published'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        default='draft',
        tracking=True,
    )
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_date = fields.Datetime(string='Approved Date', readonly=True)
    error_message = fields.Text(readonly=True)

    ai_brief = fields.Text(
        string='AI Brief',
        help='Describe what you want the AI to write about; sent to n8n as the '
             'generation prompt when you click "Generate with AI".',
    )
    ai_content_status = fields.Selection(
        [
            ('none', 'Not Requested'),
            ('requested', 'Requested'),
            ('received', 'Received'),
            ('failed', 'Failed'),
        ],
        string='AI Content Status',
        default='none',
        readonly=True,
        tracking=True,
    )

    message_length = fields.Integer(string='Characters', compute='_compute_message_length')
    over_char_limit = fields.Boolean(string='Over Limit', compute='_compute_message_length')

    like_count = fields.Integer(string='Likes', readonly=True)
    comment_count = fields.Integer(string='Comments', readonly=True)
    share_count = fields.Integer(string='Shares', readonly=True)
    click_count = fields.Integer(string='Clicks', readonly=True)
    engagement_count = fields.Integer(
        string='Total Engagement', compute='_compute_engagement_count', store=True
    )

    @api.depends('message')
    def _compute_name(self):
        for post in self:
            if not post.name and post.message:
                post.name = post.message[:60]

    @api.depends('like_count', 'comment_count', 'share_count', 'click_count')
    def _compute_engagement_count(self):
        for post in self:
            post.engagement_count = (
                post.like_count + post.comment_count + post.share_count + post.click_count
            )

    @api.depends('message', 'account_id.char_limit')
    def _compute_message_length(self):
        for post in self:
            length = len(post.message or '')
            post.message_length = length
            post.over_char_limit = bool(post.account_id.char_limit) and length > post.account_id.char_limit

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            self.message = self.template_id.message
            self.image = self.template_id.image
            self.link_url = self.template_id.link_url
            self.hashtag_ids = self.template_id.hashtag_ids

    def action_insert_hashtags(self):
        for post in self:
            if not post.hashtag_ids:
                continue
            hashtag_text = ' '.join('#%s' % h.name for h in post.hashtag_ids)
            post.message = '%s\n\n%s' % (post.message or '', hashtag_text)

    def _check_scheduled_date(self):
        for post in self:
            if not post.scheduled_date:
                raise UserError(_('Set a scheduled date before scheduling "%s".') % post.name)

    def action_submit_for_approval(self):
        self._check_scheduled_date()
        self.write({'state': 'pending_approval', 'error_message': False})

    def _check_manager(self):
        if not self.env.user.has_group(MANAGER_GROUP):
            raise AccessError(_('Only a Social Marketing Manager can perform this action.'))

    def action_schedule(self):
        """Manager fast-path: schedule immediately, bypassing approval."""
        self._check_manager()
        self._check_scheduled_date()
        self.write({'state': 'scheduled', 'error_message': False})

    def action_approve(self):
        self._check_manager()
        self._check_scheduled_date()
        self.write(
            {
                'state': 'scheduled',
                'approved_by': self.env.user.id,
                'approved_date': fields.Datetime.now(),
                'error_message': False,
            }
        )

    def action_reject(self):
        self._check_manager()
        self.write({'state': 'draft'})
        self.message_post(body=_('Post submission was rejected and reset to draft.'))

    def action_reset_to_draft(self):
        self.write({'state': 'draft', 'error_message': False})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_publish_now(self):
        self._publish()

    def action_request_ai_content(self):
        self.ensure_one()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        webhook_url = get_param(PARAM_AI_WEBHOOK_URL)
        api_key = get_param(PARAM_API_KEY)
        if not webhook_url or not api_key:
            raise UserError(_(
                'Configure the n8n AI webhook URL and shared API key first, under '
                'Social Marketing > Configuration > Automation Settings.'
            ))
        base_url = get_param('web.base.url')
        payload = {
            'post_id': self.id,
            'platform': self.platform,
            'account_handle': self.account_id.handle,
            'brief': self.ai_brief or self.message,
            'callback_url': '%s/social_media/webhook/posts/%s/ai-content' % (base_url, self.id),
            'api_key': api_key,
        }
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise UserError(_('Could not reach the n8n webhook: %s') % exc)
        self.ai_content_status = 'requested'

    def action_duplicate(self):
        self.ensure_one()
        new_post = self.copy()
        return {
            'name': _('Post (copy)'),
            'type': 'ir.actions.act_window',
            'res_model': 'social.media.post',
            'view_mode': 'form',
            'res_id': new_post.id,
        }

    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault('state', 'draft')
        default.setdefault('scheduled_date', False)
        default.setdefault('published_date', False)
        default.setdefault('error_message', False)
        default.setdefault('approved_by', False)
        default.setdefault('approved_date', False)
        default.setdefault('ai_content_status', 'none')
        default.setdefault('like_count', 0)
        default.setdefault('comment_count', 0)
        default.setdefault('share_count', 0)
        default.setdefault('click_count', 0)
        return super().copy(default)

    def _publish(self):
        """Attempt to publish each post via its account's API integration."""
        for post in self:
            if post.state == 'published':
                continue
            try:
                post.account_id._api_publish(post)
            except Exception as exc:  # noqa: BLE001 - surfaced on the record, not swallowed
                _logger.exception('Failed to publish social media post %s', post.id)
                post.write({'state': 'failed', 'error_message': str(exc)})
            else:
                post.write(
                    {
                        'state': 'published',
                        'published_date': fields.Datetime.now(),
                        'error_message': False,
                    }
                )

    @api.model
    def _cron_publish_scheduled_posts(self):
        due_posts = self.search(
            [('state', '=', 'scheduled'), ('scheduled_date', '<=', fields.Datetime.now())]
        )
        due_posts._publish()
