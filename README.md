# Social Media Marketing Automation for Odoo

An Odoo module to plan, schedule and automate social media posts across
multiple accounts and platforms (Facebook, Instagram, X/Twitter, LinkedIn,
TikTok, YouTube) from a single place.

## Features

- **Accounts** — register one or more accounts per platform, with a
  connect/disconnect status and a per-account *Test Mode* so you can try
  the whole workflow before wiring up real API credentials.
- **Campaigns** — group related posts together with a responsible user,
  date range and status (Draft / In Progress / Done / Cancelled).
- **Posts** — a message, image and optional link, scheduled for a specific
  date/time on a specific account, with a state machine
  (Draft → Scheduled → Published / Failed / Cancelled) and basic
  engagement tracking (likes, comments, shares, clicks).
- **Compose wizard** — write one message and fan it out as individual
  posts across several accounts at once.
- **Automation** — a scheduled action (`ir.cron`) runs every 15 minutes and
  publishes any post whose scheduled time has arrived, recording the result
  (published, or failed with the error message) on the post.
- **Views** — Kanban pipeline (grouped by status), a content calendar,
  list and form views, with chatter/activity tracking on posts and
  campaigns.

## Installation

1. Copy (or symlink) the `social_media_marketing_automation` directory into
   your Odoo `addons` path.
2. Update the apps list and install **Social Media Marketing Automation**
   from the Apps menu.
3. Go to **Social Marketing → Configuration → Accounts** and add your
   social media accounts.

## Publishing to real platforms

Out of the box, every account is created in **Test Mode**: publishing a
post simulates a successful call instead of contacting the real platform,
so you can exercise scheduling, campaigns and the cron job without any API
keys.

To publish to a real platform:

1. Disable *Test Mode* on the account and set its API access token.
2. Implement the actual API call for that platform by overriding
   `social.media.account._api_publish()` (e.g. from an extension module),
   which currently raises `NotImplementedError` outside of test mode as a
   placeholder for that integration.

## Security

Two groups are provided under the **Social Marketing** category:

- **User** — can create, schedule and publish posts and campaigns.
- **Manager** — full access to accounts, campaigns and posts, including
  API credentials.

## License

GPL-3.0 (see [LICENSE](LICENSE)).
