# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


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
    account_id = fields.Many2one(
        'social.media.account', string='Account', required=True, tracking=True,
        ondelete='cascade',
    )
    platform = fields.Selection(related='account_id.platform', store=True, readonly=True)
    company_id = fields.Many2one(related='account_id.company_id', store=True, readonly=True)
    campaign_id = fields.Many2one('social.media.campaign', string='Campaign', tracking=True)
    scheduled_date = fields.Datetime(string='Scheduled Date', tracking=True)
    published_date = fields.Datetime(string='Published Date', readonly=True)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled'),
            ('published', 'Published'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        default='draft',
        tracking=True,
    )
    error_message = fields.Text(readonly=True)

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

    def action_schedule(self):
        for post in self:
            if not post.scheduled_date:
                raise UserError(_('Set a scheduled date before scheduling "%s".') % post.name)
        self.write({'state': 'scheduled', 'error_message': False})

    def action_reset_to_draft(self):
        self.write({'state': 'draft', 'error_message': False})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_publish_now(self):
        self._publish()

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
