# -*- coding: utf-8 -*-
from odoo import api, fields, models

PARAM_AI_WEBHOOK_URL = 'social_media_marketing_automation.n8n_ai_webhook_url'
PARAM_API_KEY = 'social_media_marketing_automation.api_key'


class SocialMediaAutomationSettings(models.TransientModel):
    _name = 'social.media.automation.settings'
    _description = 'Social Media n8n Automation Settings'

    n8n_ai_webhook_url = fields.Char(
        string='n8n AI Content Webhook URL',
        help='The n8n Webhook node URL that triggers your AI content generation workflow.',
    )
    api_key = fields.Char(
        string='Shared API Key',
        help='Sent as the X-Api-Key header by n8n when calling back into Odoo, and used '
             'by Odoo to authenticate itself when it asks n8n to generate content. Treat '
             'this like a password and only use it over HTTPS.',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res['n8n_ai_webhook_url'] = get_param(PARAM_AI_WEBHOOK_URL, '')
        res['api_key'] = get_param(PARAM_API_KEY, '')
        return res

    def action_save(self):
        self.ensure_one()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param(PARAM_AI_WEBHOOK_URL, self.n8n_ai_webhook_url or '')
        set_param(PARAM_API_KEY, self.api_key or '')
