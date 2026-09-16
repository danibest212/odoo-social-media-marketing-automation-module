{
    'name': 'Social Media Marketing Automation',
    'version': '17.0.2.0.0',
    'category': 'Marketing',
    'summary': 'Plan, schedule and automate posts across social media accounts',
    'description': """
Social Media Marketing Automation
==================================
Manage social media accounts, plan campaigns and schedule posts across
multiple platforms (Facebook, Instagram, X/Twitter, LinkedIn, TikTok,
YouTube) directly from Odoo.

Features
--------
* Connect and manage multiple social media accounts per platform
* Organize posts into marketing campaigns
* Compose a single message and schedule it across several accounts at once
* Reusable post templates and a hashtag library
* Manager approval workflow before a post gets scheduled
* Per-platform character limit warnings
* Automatic publishing of scheduled posts via a scheduled action (cron)
* Track publishing status and basic engagement metrics per post
* Kanban, calendar, pivot/graph and form views with chatter/activities
""",
    'author': 'ashewainfo',
    'license': 'GPL-3',
    'depends': ['mail', 'web'],
    'data': [
        'security/social_media_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'wizard/social_media_post_compose_views.xml',
        'views/social_media_account_views.xml',
        'views/social_media_campaign_views.xml',
        'views/social_media_hashtag_views.xml',
        'views/social_media_template_views.xml',
        'views/social_media_post_views.xml',
        'views/social_media_menus.xml',
    ],
    'demo': [
        'demo/social_media_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
