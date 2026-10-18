# Redesigned public site (futurecity.andyyaro.com)

A complete redesign of the public pages in `site/www/`, built from the HIG Native design system
(an unofficial web interpretation of Apple's Human Interface Guidelines). It is a separate site:
`site/www/` and everything it is served from are unchanged.

Live at https://futurecity.andyyaro.com (noindex). See any page at every device size at
https://futurecity.andyyaro.com/devices.html.

## Layout

| Path | What it is |
|---|---|
| `www/` | The static site: flat HTML pages, no build step, no frameworks, no web fonts |
| `www/css/tokens.css` | Generated from the design system's `tokens.json` (four themes: light, dark and both increased-contrast variants) |
| `www/css/base.css`, `www/css/hig.css`, `www/js/icons.js` | Copied from the design system (foundations, component styles, icon glyphs) |
| `www/css/site.css`, `www/js/app.js`, `www/js/theme.js` | The shell: navigation, footer, data loading, shared controls, system theme mapping |
| `www/css/pages/`, `www/js/pages/` | One stylesheet and script per page |
| `www/data/sites.json` | The only figures the site shows: outputs from the published Tableau sheets (`dashboard/tableau/build/sheets/`) and `site/platform/contract/v1/`. No inputs (DEC-016) |
| `tools/` | `gen_tokens.py`, `qa.py` (static checks), `matrix.py` (every page at 16 viewports in Chromium and WebKit, light and dark), `deploy.sh` |

## Information architecture

Results: Overview, Sites (split view, deep links like `sites.html#FFX004`), Compare, Outlook,
Explore Data (Tableau views, loaded only on request). Approach: Method, Standards. Project:
Assistant (links to the existing assistant, which needs sign-in), About, Privacy. Phones get a
floating tab bar with a More page; widths of 1024px and up get a floating sidebar.

## Hosting

| Resource | Name |
|---|---|
| S3 bucket | `future-city-redesign` (private, OAC only) |
| CloudFront | `E3RNYDDSMJAZUR`, PriceClass_100, response headers policy `fcf-redesign-noindex` (strict CSP, noindex) |
| Certificate | `futurecity.andyyaro.com`, ACM us-east-1 |
| DNS | A and AAAA aliases plus the ACM validation CNAME in the `andyyaro.com` zone (`cerfodes-dns` profile) |

## Checks and deploy

```bash
python3 site/redesign/tools/qa.py site/redesign/www
(cd site/redesign/www && python3 -m http.server 8765) &
python3 site/redesign/tools/matrix.py http://localhost:8765 /tmp/matrix-shots --shots
site/redesign/tools/deploy.sh site/redesign/www
```

`matrix.py` flags links under 24px. Rows in the design system's lists stretch their link over the
whole row with a pseudo-element, so those flags are expected; tap targets were confirmed by hit
testing.
