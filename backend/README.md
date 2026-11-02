# MadiTech API companion — prepared, not deployed

This is a separate server for the existing Render Static Site. No package installation is needed; use Node.js 22 or later. It does not run inside a Render Static Site.

Start: `node backend/server.mjs`
Tests: `node --test backend/service.test.mjs`

Use a persistent server you control or a separately configured Web Service. Do not change the existing frontend service type. No service or subscription has been purchased or provisioned by this repository change.

## Server-only configuration

| Variable | Purpose |
| --- | --- |
| SITE_ORIGIN | https://maditech-mahdi.onrender.com |
| PORT | Assigned by the host, defaults to 3000 |
| AI_BASE_URL | HTTPS OpenAI-compatible API base, for example https://api.openai.com/v1 |
| AI_API_KEY | Your provider credential; never commit it |
| AI_MODEL | A model available to that provider account |
| AI_DAILY_REQUEST_LIMIT | Default 30 requests per process per UTC day; includes owner drafts |
| ADMIN_TOKEN | Random secret at least 32 characters, for owner content generation only |
| N8N_WEBHOOK_URL | HTTPS production webhook of a configured workflow |
| N8N_WEBHOOK_TOKEN | Header authentication secret for that webhook |

Set these through the host's private environment settings. An existing ChatGPT subscription does not supply an API key or API usage. No provider is assumed to be free. For a zero-spend deployment, use an already available provider or self-hosted compatible endpoint with your own resources.

## Behaviors

- GET /health reports configuration availability, not successful upstream connectivity.
- POST /api/chat accepts message and language (en/fr/fa); no conversation history is stored.
- POST /api/requests accepts name, email, service (ai/robotics/studio/apps/general), message, language and consent=true. It forwards only explicit submissions to n8n with X-MadiTech-Token header auth. Success means the configured webhook accepted delivery, not that a customer email was sent.
- POST /api/content is owner-only with Bearer ADMIN_TOKEN. It accepts topic and language and returns a marketing draft, published=false. Nothing is posted or sent to others.
- Missing credentials and upstream failures return errors rather than fabricated success.

Before deployment, test using provider test credentials and a disposable enquiry. Configure n8n to save a request durably before returning success. Protect the n8n editor with authentication and HTTPS. Keep CRM tokens inside n8n credentials, not frontend configuration.

Rate limiting uses the socket address and an in-memory global daily AI request cap. Behind a proxy this is conservative and can group users; for multiple instances/restarts use a persistent edge limiter and provider billing limits. This is not a guaranteed monetary budget. The service intentionally has no public owner dashboard, no automatic outreach and no publishing actions.

## Activate frontend only after verification

Set only the backend public HTTPS origin in assets/config.js apiBase once the server and required upstream services pass live tests. The frontend supports real chat and enquiry delivery then. Without that address, it keeps the explicitly labelled local chat demo and offers downloadable enquiry drafts without transmitting them.
