# MadiTech — single-document experience

The complete frontend is index.html: inline CSS, inline SVG, vanilla JavaScript, embedded original brand images, and English/French/Persian copy. The only external display dependency is the Inter and Playfair Display font stylesheet from Google Fonts. No npm, framework, JS library or build is required.

The full-screen hero includes a hard brush entrance, linked monochrome/colour layers with a soft pointer reveal, diagonal drift, replay controls, mobile layout and reduced-motion handling. Service information, vision, founder and a downloadable project brief open inside the page.

The brief is downloaded locally and is not sent. Backend sources retained in the repository are not invoked by this hero and are not hosted or connected.

Render Static Site: main branch, empty Root Directory, build command `echo "No build required"`, Publish Directory `.`.

Public GitHub projects appear as cards inside the matching area (AI, Robotics, Studio, Apps). Only repositories listed in `projects/approved-projects.json` are shown; their EN/FR/FA copy is written by hand there. The **Weekly project sync** workflow (manual or Mondays) reads those repositories' public GitHub facts and, only when something changed, opens a pull request from `automation/project-sync`. It never pushes to main or touches Render. For it to open pull requests, enable *Settings → Actions → General → Allow GitHub Actions to create and approve pull requests*.

Checks: `node scripts/check-site.mjs`, `node --test scripts/sync-projects.test.mjs` and `node --test backend/service.test.mjs`.
