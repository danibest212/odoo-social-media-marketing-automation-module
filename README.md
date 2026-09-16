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
  (Draft → Pending Approval → Scheduled → Published / Failed / Cancelled)
  and basic engagement tracking (likes, comments, shares, clicks).
- **Compose wizard** — write one message and fan it out as individual
  posts across several accounts at once.
- **Templates** — save recurring message/image/link/hashtag combinations
  and reuse them from the compose wizard or directly on a post.
- **Hashtag library** — a reusable, colour-tagged set of hashtags you can
  attach to templates or posts and insert into the message with one click.
- **Approval workflow** — regular Users submit a scheduled post for
  approval; a Social Marketing Manager approves (schedules it) or rejects
  it (back to draft) — or a Manager can schedule directly, bypassing
  approval.
- **Character limit warnings** — each post shows a live character count
  and a warning banner if the message exceeds the target platform's
  approximate limit.
- **Duplicate** — clone any post (as a fresh Draft) from its form view.
- **Automation** — a scheduled action (`ir.cron`) runs every 15 minutes and
  publishes any post whose scheduled time has arrived, recording the result
  (published, or failed with the error message) on the post.
- **Views** — Kanban pipeline (grouped by status), a content calendar,
  pivot/graph performance reporting, list and form views, with
  chatter/activity tracking on posts and campaigns.
- **n8n automation** — API-key-secured webhooks so an [n8n](https://n8n.io)
  instance can (1) generate a post's message/hashtags with AI and send them
  back, and (2) auto-publish due posts to the real platform APIs and report
  the result. See [n8n/README.md](n8n/README.md) for the ready-to-import
  workflow templates and full setup.

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

## n8n automation

Two extra automations are available once you configure an
[n8n](https://n8n.io) instance under **Social Marketing → Configuration →
Automation Settings** (Manager only):

- **Generate with AI** — a button on any post that asks n8n (which calls an
  AI provider, e.g. Claude) to draft the message and hashtags, then writes
  the result back onto the post.
- **Auto-publish across all platforms** — an alternative to (or replacement
  for) the built-in cron: n8n polls Odoo for due posts, calls each
  platform's real API, and reports the result back.

Both directions are authenticated with a single shared API key (sent as the
`X-Api-Key` header) rather than an Odoo login — see
[n8n/README.md](n8n/README.md) for the webhook endpoints, the workflow
templates in `n8n/workflows/`, and setup steps. Treat that key like a
password: only expose these endpoints over HTTPS.

## Security

Two groups are provided under the **Social Marketing** category:

- **User** — can create posts and campaigns and submit posts for approval;
  cannot schedule a post directly or approve/reject a submission.
- **Manager** — full access to accounts, campaigns, posts, templates and
  hashtags, including API credentials and the n8n Automation Settings
  (shared API key and webhook URL); can schedule posts directly or
  approve/reject a User's submission.
- The `/social_media/webhook/...` routes are unauthenticated from Odoo's
  point of view and instead rely entirely on the shared API key configured
  in Automation Settings — leave that key blank (the default) to keep the
  endpoints disabled, and only set it once you're ready to use n8n over
  HTTPS.

## License

GPL-3.0 (see [LICENSE](LICENSE)).
