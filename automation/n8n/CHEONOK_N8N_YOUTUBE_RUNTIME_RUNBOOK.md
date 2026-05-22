# CHEONOK n8n YouTube Runtime Runbook

## Executive Purpose
This runtime converts CHEONOK reference intelligence into daily revenue assets.

It does not store API secrets in GitHub. API keys must be stored only inside n8n Credentials or n8n Variables.

## Current Critical Security Rule
A YouTube API key was pasted into chat. Treat it as exposed.

Required action in Google Cloud Console:
1. Restrict the key to YouTube Data API v3 only.
2. Add application restrictions where possible.
3. Rotate/regenerate if there is any concern of misuse.
4. Do not paste the key into GitHub, public workflow JSON, website code, or Airtable.

## n8n Workspace State
If n8n shows `Reactivating workspace`, wait for the workspace to open. Once the editor appears, the first job is not SNS posting. The first job is YouTube intelligence collection and content queue generation.

## n8n Variables
Create these inside n8n:

- YOUTUBE_API_KEY
- CHEONOK_SITE_URL = https://cheonoksystem.com/cta-5m.html
- CHEONOK_MODE = PAPER_ONLY

## First Workflow
Name: CHEONOK YouTube Intelligence Runtime

Core flow:
1. Schedule Trigger
2. Set Reference Channels
3. Split In Batches
4. HTTP Request to YouTube Data API channels.list
5. HTTP Request to YouTube Data API playlistItems.list
6. Code node to score title/hook/CTA/revenue pattern
7. Store results in Airtable Content Queue or Google Sheet
8. Draft revenue assets: 3 Shorts hooks, 1 long-form outline, 1 CTA post
9. Report: evidence, blocked items, next proof

## CASH CHAIN Mapping
Exposure:
- channel metadata
- top video titles
- shorts hooks

Lead:
- CTA to cheonoksystem.com/cta-5m.html

Payment:
- 300,000 KRW AI Revenue Bottleneck Diagnosis

Delivery:
- Google Drive diagnostic report

Review:
- transformation story request

Subscription:
- monthly AI operator retainer

Exit Ledger:
- channel pattern database
- lead source
- conversion evidence
- content performance history

## Next Proof
PASS only when at least one of these exists:
- successful n8n execution log
- YouTube API response stored
- Content Queue record created
- public post URL
- free diagnosis lead
- payment proof

## Final Veto
LIVE_TRADE: BLOCKED
CAPITAL_SCALE: BLOCKED
KIS_ORDER_GATE: BLOCKED
PAPER_ONLY: TRUE
