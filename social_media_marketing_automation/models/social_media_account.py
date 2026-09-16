# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SocialMediaAccount(models.Model):
    _name = 'social.media.account'
    _description = 'Social Media Account'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    platform = fields.Selection(
        [
            ('facebook', 'Facebook'),
            ('instagram', 'Instagram'),
            ('twitter', 'X (Twitter)'),
            ('linkedin', 'LinkedIn'),
            ('tiktok', 'TikTok'),
            ('youtube', 'YouTube'),
        ],
        required=True,
        tracking=True,
    )
    handle = fields.Char(string='Handle / Username')
    profile_url = fields.Char(string='Profile URL')
    access_token = fields.Char(
        string='API Access Token',
        groups='social_media_marketing_automation.group_social_media_manager',
        help='Credential used to authenticate against the platform API. '
             'Only used when Test Mode is disabled.',
    )
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company
    )
    active = fields.Boolean(default=True)
    image = fields.Image(max_width=256, max_height=256)
    color = fields.Integer(string='Color Index')
    test_mode = fields.Boolean(
        string='Test Mode',
        default=True,
        tracking=True,
        help='While enabled, publishing simulates a successful call instead of '
             'reaching out to the real platform API. Disable once real API '
             'credentials are configured.',
    )
    state = fields.Selection(
        [('disconnected', 'Disconnected'), ('connected', 'Connected')],
        default='disconnected',
        tracking=True,
    )
    post_ids = fields.One2many('social.media.post', 'account_id', string='Posts')
    post_count = fields.Integer(compute='_compute_post_count')

    @api.depends('post_ids')
    def _compute_post_count(self):
        counts = self.env['social.media.post']._read_group(
            [('account_id', 'in', self.ids)], ['account_id'], ['__count']
        )
        mapped = {account.id: count for account, count in counts}
        for account in self:
            account.post_count = mapped.get(account.id, 0)

    def action_connect(self):
        """Mark the account as connected. Placeholder for a real OAuth flow."""
        self.write({'state': 'connected'})

    def action_disconnect(self):
        self.write({'state': 'disconnected'})

    def action_view_posts(self):
        self.ensure_one()
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'social.media.post',
            'view_mode': 'list,form,calendar,kanban',
            'domain': [('account_id', '=', self.id)],
            'context': {'default_account_id': self.id},
        }

    def _api_publish(self, post):
        """Publish ``post`` to this account's platform.

        In test mode this simulates success. Outside of test mode this is a
        placeholder integration point: extend/override per platform (e.g. via
        a dedicated module implementing the real API calls) before disabling
        test mode on an account.
        """
        self.ensure_one()
        if self.test_mode:
            _logger.info(
                'Social Media Marketing Automation: simulated publish of post '
                '%s on %s account %s (test mode).', post.id, self.platform, self.name
            )
            return True
        raise NotImplementedError(
            'No live API integration is configured for platform %r. Enable '
            'test mode or implement _api_publish for this platform.' % self.platform
        )
