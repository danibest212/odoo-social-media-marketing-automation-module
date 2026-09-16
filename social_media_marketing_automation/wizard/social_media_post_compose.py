# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SocialMediaPostCompose(models.TransientModel):
    _name = 'social.media.post.compose'
    _description = 'Compose Social Media Post'

    message = fields.Text(required=True)
    image = fields.Image(max_width=1920, max_height=1920)
    link_url = fields.Char(string='Link')
    campaign_id = fields.Many2one('social.media.campaign', string='Campaign')
    account_ids = fields.Many2many('social.media.account', string='Accounts', required=True)
    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        help='Leave empty to save the generated posts as drafts instead of scheduling them.',
    )

    def action_create_posts(self):
        self.ensure_one()
        if not self.account_ids:
            raise UserError(_('Select at least one account to post to.'))

        state = 'scheduled' if self.scheduled_date else 'draft'
        posts = self.env['social.media.post']
        for account in self.account_ids:
            posts |= self.env['social.media.post'].create(
                {
                    'message': self.message,
                    'image': self.image,
                    'link_url': self.link_url,
                    'campaign_id': self.campaign_id.id,
                    'account_id': account.id,
                    'scheduled_date': self.scheduled_date,
                    'state': state,
                }
            )

        return {
            'name': _('Posts'),
            'type': 'ir.actions.act_window',
            'res_model': 'social.media.post',
            'view_mode': 'list,form,calendar,kanban',
            'domain': [('id', 'in', posts.ids)],
        }
