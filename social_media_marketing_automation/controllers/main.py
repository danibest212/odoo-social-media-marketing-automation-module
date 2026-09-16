# -*- coding: utf-8 -*-
"""Webhook API for external automation (e.g. n8n) to drive social media posts.

Every route here is unauthenticated from Odoo's point of view (``auth='none'``)
and instead relies on a shared secret (the ``X-Api-Key`` header) configured by
a Social Marketing Manager under Social Marketing > Configuration >
Automation Settings. All ORM access is done via ``sudo()`` since there is no
logged-in Odoo user on these requests.
"""
import hmac
import json
import logging

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)

CONFIG_PARAM_API_KEY = 'social_media_marketing_automation.api_key'


class SocialMediaWebhookController(http.Controller):

    # -- helpers ---------------------------------------------------------
    def _check_api_key(self):
        configured_key = request.env['ir.config_parameter'].sudo().get_param(CONFIG_PARAM_API_KEY)
        if not configured_key:
            return False
        provided_key = request.httprequest.headers.get('X-Api-Key', '')
        return hmac.compare_digest(configured_key, provided_key)

    def _json_response(self, data, status=200):
        return request.make_json_response(data, status=status)

    def _get_json_body(self):
        try:
            return json.loads(request.httprequest.data or b'{}')
        except ValueError:
            return {}

    def _serialize_post(self, post):
        return {
            'id': post.id,
            'message': post.message,
            'link_url': post.link_url or '',
            'hashtags': post.hashtag_ids.mapped('name'),
            'platform': post.platform,
            'account_id': post.account_id.id,
            'account_handle': post.account_id.handle or '',
            'campaign_id': post.campaign_id.id,
            'scheduled_date': post.scheduled_date.isoformat() if post.scheduled_date else False,
        }

    # -- routes ------------------------------------------------------------
    @http.route('/social_media/webhook/posts/due', type='http', auth='none', csrf=False, methods=['GET'])
    def posts_due(self, **kwargs):
        """Posts an n8n auto-publish workflow should attempt to publish now."""
        if not self._check_api_key():
            return self._json_response({'error': 'unauthorized'}, status=401)
        due_posts = request.env['social.media.post'].sudo().search([
            ('state', '=', 'scheduled'),
            ('scheduled_date', '<=', fields.Datetime.now()),
        ])
        return self._json_response({'posts': [self._serialize_post(p) for p in due_posts]})

    @http.route(
        '/social_media/webhook/posts/<int:post_id>/result', type='http', auth='none', csrf=False,
        methods=['POST'],
    )
    def publish_result(self, post_id, **kwargs):
        """Callback for an n8n auto-publish workflow to report a publish attempt."""
        if not self._check_api_key():
            return self._json_response({'error': 'unauthorized'}, status=401)
        post = request.env['social.media.post'].sudo().browse(post_id)
        if not post.exists():
            return self._json_response({'error': 'not_found'}, status=404)

        payload = self._get_json_body()
        if payload.get('success'):
            vals = {
                'state': 'published',
                'published_date': fields.Datetime.now(),
                'error_message': False,
            }
            for key in ('like_count', 'comment_count', 'share_count', 'click_count'):
                if key in payload:
                    vals[key] = int(payload[key] or 0)
            post.write(vals)
        else:
            post.write({
                'state': 'failed',
                'error_message': payload.get('error') or 'n8n reported a publish failure.',
            })
        return self._json_response({'ok': True})

    @http.route(
        '/social_media/webhook/posts/<int:post_id>/ai-content', type='http', auth='none', csrf=False,
        methods=['POST'],
    )
    def ai_content_result(self, post_id, **kwargs):
        """Callback for the n8n AI content generation workflow."""
        if not self._check_api_key():
            return self._json_response({'error': 'unauthorized'}, status=401)
        post = request.env['social.media.post'].sudo().browse(post_id)
        if not post.exists():
            return self._json_response({'error': 'not_found'}, status=404)

        payload = self._get_json_body()
        if payload.get('success'):
            vals = {'ai_content_status': 'received'}
            if payload.get('message'):
                vals['message'] = payload['message']
            hashtag_names = payload.get('hashtags') or []
            if hashtag_names:
                Hashtag = request.env['social.media.hashtag'].sudo()
                hashtags = Hashtag.browse()
                for name in hashtag_names:
                    name = (name or '').lstrip('#').strip()
                    if not name:
                        continue
                    hashtag = Hashtag.search([('name', '=', name)], limit=1)
                    hashtags |= hashtag or Hashtag.create({'name': name})
                vals['hashtag_ids'] = [(6, 0, hashtags.ids)]
            post.write(vals)
        else:
            post.write({
                'ai_content_status': 'failed',
                'error_message': payload.get('error') or 'AI content generation failed.',
            })
        return self._json_response({'ok': True})
