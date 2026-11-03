# Automation state

## Active
- GitHub Actions validates source, image paths, anchor links, all EN/FR/FA translations and API behavior on every push or pull request.
- Render's existing frontend auto-deployment continues to publish main.
- Weekly project sync (`.github/workflows/project-sync.yml`): checks only the repositories approved in `projects/approved-projects.json` and opens a review pull request when their public GitHub facts change. No pull request when nothing changed. It does not merge, deploy or change Render.

## Prepared, awaiting a server and credentials
- Real AI chat through the companion service.
- Customer enquiries through an authenticated n8n production webhook.
- Owner-authorized content drafts through the companion service; no public publication.

## n8n workflow to configure after a host is connected
1. Create a production POST Webhook using Header Auth. The header name must be X-MadiTech-Token and its secret must match server-side N8N_WEBHOOK_TOKEN.
2. Validate name/email/service/message/language and enforce consent on the companion API.
3. Store the submission in a private CRM/data store using that service's n8n credential. If using Notion, create/use a private Requests database and grant the runtime integration access to that database only. The ChatGPT Notion connection does not automatically authorize a separate server.
4. Return a 2xx response only after durable storage succeeds. Return an error when storage fails so the site retains the form and offers retry.
5. Do not enable outbound emails, social publishing, or customer outreach without a separate explicit instruction.

No n8n server or production workflow has been installed or activated by this change. No visitor data is stored in GitHub. No secrets belong in this public repository.
