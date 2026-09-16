# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SocialMediaPostCompose(models.TransientModel):
    _name = 'social.media.post.compose'
    _description = 'Compose Social Media Post'

    template_id = fields.Many2one(
        'social.media.template', string='Template',
        help='Pick a template to prefill the message, image, link and hashtags below.',
    )
    message = fields.Text(required=True)
    image = fields.Image(max_width=1920, max_height=1920)
    link_url = fields.Char(string='Link')
    hashtag_ids = fields.Many2many('social.media.hashtag', string='Hashtags')
    campaign_id = fields.Many2one('social.media.campaign', string='Campaign')
    account_ids = fields.Many2many('social.media.account', string='Accounts', required=True)
    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        help='Leave empty to save the generated posts as drafts instead of scheduling them.',
    )

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            self.message = self.template_id.message
            self.image = self.template_id.image
            self.link_url = self.template_id.link_url
            self.hashtag_ids = self.template_id.hashtag_ids

    def action_create_posts(self):
        self.ensure_one()
        if not self.account_ids:
            raise UserError(_('Select at least one account to post to.'))

        if not self.scheduled_date:
            state = 'draft'
        elif self.env.user.has_group('social_media_marketing_automation.group_social_media_manager'):
            state = 'scheduled'
        else:
            state = 'pending_approval'

        posts = self.env['social.media.post']
        for account in self.account_ids:
            posts |= self.env['social.media.post'].create(
                {
                    'template_id': self.template_id.id,
                    'message': self.message,
                    'image': self.image,
                    'link_url': self.link_url,
                    'hashtag_ids': [(6, 0, self.hashtag_ids.ids)],
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
            'view_mode': 'tree,form,calendar,kanban',
            'domain': [('id', 'in', posts.ids)],
        }
