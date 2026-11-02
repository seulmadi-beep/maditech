# MadiTech

Approved EN/FR/FA brand website with original artwork, Persian RTL, local chat demo and service enquiry dialogs.

## Frontend deployment
Render Static Site, branch main, empty Root Directory, build command `echo "No build required"`, Publish Directory `.`. The current public website is https://maditech-mahdi.onrender.com.

## Verification
`node scripts/check-site.mjs`
`node --test backend/service.test.mjs`

GitHub Actions runs these checks on pushes and pull requests.

## Connection state
The backend under backend/ is implemented and locally tested, but not hosted or connected. See backend/README.md and automation/README.md. With an empty public apiBase in assets/config.js, chat remains explicitly a demo and requests can only be downloaded as drafts. No keys or secrets are stored in this repository. No roadmap collage is used as a site asset.

Owner-only content generation returns drafts and never publishes them or sends messages to customers. No n8n runtime, CRM connection, provider account or paid subscription is provisioned by this repository.
