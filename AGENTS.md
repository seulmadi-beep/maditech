# MadiTech site maintenance

- Preserve the approved English/French/Persian design and original supplied images. Never use the roadmap collage as a website asset.
- Keep all visible interface text in the translation dictionaries, with matching en/fr/fa keys. Persian must set lang=fa and dir=rtl; preserve LTR brand spelling.
- Preserve facial identity. Fix cropping with CSS before considering image generation.
- Run `node scripts/check-site.mjs` before committing. Check the browser preview when changing layout or interactions.
- The chat is a local demo, not a live AI API. Never imply otherwise or expose API keys in HTML.
- Contact currently copies a message; do not imply a request has been sent.
- Production is the existing Render Static Site on main. No build dependencies are required. Keep Root Directory empty and Publish Directory set to `.`.
