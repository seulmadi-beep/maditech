# MadiTech site maintenance

- Preserve the approved English/French/Persian design and original supplied images. Never use the roadmap collage as a website asset.
- Keep all visible interface text in the translation dictionaries, with matching en/fr/fa keys. Persian must set lang=fa and dir=rtl; preserve LTR brand spelling.
- Preserve facial identity. Fix cropping with CSS before considering image generation.
- Run `node scripts/check-site.mjs` before committing. Check the browser preview when changing layout or interactions.
- With empty assets/config.js apiBase, chat remains an explicit demo. A real API companion is prepared under backend/ but is not deployed. Do not claim it is active until live-tested. Never expose credentials in HTML.
- Contact/service dialogs download drafts when the backend is absent. A success message is allowed only after the backend confirms webhook delivery. Never imply drafts were sent.
- Production is the existing Render Static Site on main. No build dependencies are required. Keep Root Directory empty and Publish Directory set to `.`.
