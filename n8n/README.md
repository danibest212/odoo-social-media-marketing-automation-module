# n8n Automation for Social Media Marketing Automation

This folder contains [n8n](https://n8n.io) workflow templates that connect to
the `social_media_marketing_automation` Odoo module's webhook API, so you can
automate two things outside of Odoo's own simulated "test mode" publishing:

1. **AI content generation** — a post's message/hashtags get drafted by an
   AI model.
2. **Auto-publish across all platforms** — due posts get pushed to the real
   Facebook, Instagram, X/Twitter, LinkedIn, TikTok and YouTube APIs.

> These JSON files were hand-authored against n8n's workflow export schema
> and are meant as a solid starting point, not a drop-in production
> integration. They have not been imported into a live n8n instance as part
> of building this (none was available in the sandbox this was built in), so
> after importing: open each node, confirm its parameters loaded as expected
> (n8n is generally tolerant of minor parameter-shape differences across
> versions — a node needing attention shows a warning icon rather than
> failing the whole import), and fill in the credentials/environment
> variables described below. Each platform's exact API request shape is a
> best-effort placeholder; verify it against that platform's current API
> docs before going live, since these change over time and require your own
> developer app credentials to test.

## How it fits together

```
                    ┌────────────────────────────┐
  User clicks       │  n8n: ai-content-generation │
  "Generate with    │  Webhook → Claude API →     │
  AI" on a post ───► │  POST result back to Odoo   │
                    └────────────────────────────┘
                                  │
                                  ▼
  Odoo: social.media.post  (message/hashtags updated,
  ai_content_status = received)

                    ┌────────────────────────────┐
  Every 15 min ────► │  n8n: auto-publish          │
                    │  GET due posts from Odoo →  │
                    │  call each platform's API →  │
                    │  POST result back to Odoo    │
                    └────────────────────────────┘
                                  │
                                  ▼
  Odoo: social.media.post (state = published/failed,
  published_date / error_message updated)
```

Odoo never calls out to a platform directly for real publishing — that stays
in n8n, where you manage platform credentials using n8n's own credential
store (OAuth2, header auth, etc.) instead of storing long-lived tokens in
Odoo.

## 1. Configure Odoo

In Odoo, go to **Social Marketing > Configuration > Automation Settings**
(Manager access only) and set:

- **n8n AI Content Webhook URL** — the Production URL of the imported
  `ai-content-generation` workflow's Webhook node.
- **Shared API Key** — a long random secret. This is:
  - sent by Odoo as the `api_key` field when it calls the AI webhook, for
    the workflow to send back on its callback request, and
  - required as the `X-Api-Key` header on every request to Odoo's webhook
    endpoints below (the `auto-publish` workflow's `SOCIAL_MEDIA_API_KEY`
    environment variable must match this exactly).

Treat this key like a password: only use it over HTTPS, and rotate it by
updating both Odoo's setting and n8n's environment variable together.

## 2. Odoo's webhook endpoints

All of these require the `X-Api-Key` header to match the Shared API Key
above, and return `401` otherwise.

| Method | Path | Used by | Purpose |
|---|---|---|---|
| GET | `/social_media/webhook/posts/due` | auto-publish | List posts in state `scheduled` whose `scheduled_date` has passed |
| POST | `/social_media/webhook/posts/<id>/result` | auto-publish | Report a publish attempt: `{success, error?, like_count?, comment_count?, share_count?, click_count?}` |
| POST | `/social_media/webhook/posts/<id>/ai-content` | ai-content-generation | Report generated content: `{success, message?, hashtags?, error?}` |

## 3. Import the workflows into n8n

1. In n8n: **Workflows > Import from File**, pick `ai-content-generation.json`.
2. Add an **HTTP Header Auth** credential (header name `x-api-key`) with your
   Anthropic API key, and attach it to the "Call Claude (Anthropic API)"
   node. (Swap in any other AI provider/node instead if you prefer — only
   the final "Build Result Payload" step needs to keep producing
   `{message, hashtags}`.)
3. Activate the workflow, then copy its Webhook node's **Production URL**
   into Odoo's Automation Settings.
4. Import `auto-publish.json`, set the environment variables listed in its
   Setup Notes sticky (at minimum `ODOO_BASE_URL` and
   `SOCIAL_MEDIA_API_KEY`; add each platform's credentials as you wire up
   real posting), and activate it.
5. **Deactivate Odoo's built-in cron** (Settings > Technical > Automation >
   Scheduled Actions > "Social Media Marketing: Publish Scheduled Posts")
   if you're using the auto-publish workflow, so the two don't race to
   publish the same due post.

## 4. Extending

- **More platforms / better per-platform auth**: the auto-publish workflow
  uses one generic HTTP node driven by a Code node's URL/body mapping, to
  keep the template readable. For production, split it into one branch per
  platform (Switch node on `platform`) so each branch can use n8n's OAuth2
  credential type instead of a long-lived token in an environment variable.
- **Engagement sync**: extend the `.../result` endpoint's payload (already
  accepts `like_count`/`comment_count`/`share_count`/`click_count`) with a
  scheduled workflow that periodically re-fetches stats for already-published
  posts from each platform and reports them back the same way.
