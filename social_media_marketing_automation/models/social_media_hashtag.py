# -*- coding: utf-8 -*-
from odoo import fields, models


class SocialMediaHashtag(models.Model):
    _name = 'social.media.hashtag'
    _description = 'Social Media Hashtag'
    _order = 'name'

    name = fields.Char(required=True)
    color = fields.Integer(string='Color Index')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'This hashtag already exists.'),
    ]
