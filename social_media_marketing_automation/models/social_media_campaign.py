# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SocialMediaCampaign(models.Model):
    _name = 'social.media.campaign'
    _description = 'Social Media Campaign'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    name = fields.Char(required=True, tracking=True)
    user_id = fields.Many2one(
        'res.users', string='Responsible', default=lambda self: self.env.user, tracking=True
    )
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company
    )
    date_start = fields.Date(string='Start Date', tracking=True)
    date_end = fields.Date(string='End Date', tracking=True)
    description = fields.Html(string='Description')
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        default='draft',
        tracking=True,
    )
    post_ids = fields.One2many('social.media.post', 'campaign_id', string='Posts')
    post_count = fields.Integer(compute='_compute_post_count')
    active = fields.Boolean(default=True)

    @api.depends('post_ids')
    def _compute_post_count(self):
        counts = self.env['social.media.post']._read_group(
            [('campaign_id', 'in', self.ids)], ['campaign_id'], ['__count']
        )
        mapped = {campaign.id: count for campaign, count in counts}
        for campaign in self:
            campaign.post_count = mapped.get(campaign.id, 0)

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    def action_view_posts(self):
        self.ensure_one()
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'social.media.post',
            'view_mode': 'list,form,calendar,kanban',
            'domain': [('campaign_id', '=', self.id)],
            'context': {'default_campaign_id': self.id},
        }
