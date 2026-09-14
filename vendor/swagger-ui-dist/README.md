# swagger-ui-dist (vendored)

Locked from npm `swagger-ui-dist@5.17.14` (unpkg.com/swagger-ui-dist@5.17.14):

- `swagger-ui-bundle.js` — 1.45 MB minified (includes SwaggerUIBundle + standalone preset)
- `swagger-ui.css` — 152 KB (all images are inline `data:` URIs; fonts fall back to `sans-serif`)

These are embedded into the single-file HTML produced by `apidocgen export --html`
and served by `apidocgen serve`. No CDN / network requests are made at runtime.