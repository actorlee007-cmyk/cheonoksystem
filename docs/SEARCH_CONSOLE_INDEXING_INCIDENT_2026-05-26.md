# Search Console Indexing Incident — 2026-05-26

## Trigger
Google Search Console reported new non-indexing reasons for cheonoksystem.com:

- Page with redirect
- Duplicate without user-selected canonical

## Initial Diagnosis
This is a SEO/indexing-control issue, not a revenue-funnel completion issue.
It affects the EXPOSURE stage of the CASH CHAIN.

Likely causes found in repository:

1. `vercel.json` rewrites `/` to `/offers.html`, and `/offers` to `/offers.html`.
2. Root, offers, and html-extension URLs may be seen as duplicate entry points.
3. Sitemap previously included only `https://cheonoksystem.com/`.
4. Robots file did not explicitly exclude internal gate/API paths.
5. HTML canonical tags require further verification before PASS.

## Actions Taken

### 1. robots.txt updated
Commit:
- 3944bdae0015a0993a1780a8943462d0fb22f5c6

Rules added:
- Disallow `/api/`
- Disallow `/gate`
- Disallow `/gate.html`
- Keep sitemap reference

### 2. sitemap.xml updated
Commit:
- b28c7bac9a38ec09a53d3ffc31ca867b9a6f00f3

Canonical URLs now listed:
- `https://cheonoksystem.com/`
- `https://cheonoksystem.com/offers`

## Still Not PASS
This is not an indexing PASS yet.
Remaining checks:

1. Verify deployed `robots.txt`.
2. Verify deployed `sitemap.xml`.
3. Verify `/`, `/offers`, `/offers.html`, `/index.html`, `/ebook`, `/gate`, `/gate.html` status/canonical behavior.
4. Decide canonical strategy:
   - `/` = home canonical
   - `/offers` = offer page canonical
   - `/gate` = noindex/internal
   - `/api/*` = blocked/noindex
5. Add or verify canonical tags inside HTML output.
6. In Search Console, inspect affected URLs and request validation only after deployed behavior is confirmed.

## Final Veto
Do not report Search Console issue as fixed until Google/Vercel deployed evidence exists.
Current status: PATCH_APPLIED_RETEST_REQUIRED.

Current status: autonomous learning and PAPER data accumulation.
