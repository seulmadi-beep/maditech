# MadiTech — single-document experience

The complete frontend is index.html: inline CSS, inline SVG, vanilla JavaScript, embedded original brand images, and English/French/Persian copy. The only external display dependency is the Inter and Playfair Display font stylesheet from Google Fonts. No npm, framework, JS library or build is required.

The full-screen hero includes a hard brush entrance, linked monochrome/colour layers with a soft pointer reveal, diagonal drift, replay controls, mobile layout and reduced-motion handling. Service information, vision, founder and a downloadable project brief open inside the page.

The brief is downloaded locally and is not sent. Backend sources retained in the repository are not invoked by this hero and are not hosted or connected.

Render Static Site: main branch, empty Root Directory, build command `echo "No build required"`, Publish Directory `.`.

Checks: `node scripts/check-site.mjs` and `node --test backend/service.test.mjs`.
