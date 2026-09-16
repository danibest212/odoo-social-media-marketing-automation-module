# -*- coding: utf-8 -*-
from odoo import fields, models


class SocialMediaTemplate(models.Model):
    _name = 'social.media.template'
    _description = 'Social Media Post Template'
    _order = 'name'

    name = fields.Char(required=True)
    message = fields.Text(required=True)
    image = fields.Image(max_width=1920, max_height=1920)
    link_url = fields.Char(string='Link')
    hashtag_ids = fields.Many2many('social.media.hashtag', string='Hashtags')
    platform = fields.Selection(
        [
            ('facebook', 'Facebook'),
            ('instagram', 'Instagram'),
            ('twitter', 'X (Twitter)'),
            ('linkedin', 'LinkedIn'),
            ('tiktok', 'TikTok'),
            ('youtube', 'YouTube'),
        ],
        string='Target Platform',
        help='Optional: restrict this template to accounts of a specific platform.',
    )
    active = fields.Boolean(default=True)
