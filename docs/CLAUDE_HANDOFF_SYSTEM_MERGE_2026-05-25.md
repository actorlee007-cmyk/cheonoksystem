# CHEONOK / JOS Claude Handoff System Merge — 2026-05-25

## 0. Purpose
This document merges today's Claude-side work into the single JOS/CHEONOK canon without creating a separate or conflicting system.
Claude work is treated as an external execution branch of the same JOS master system.

## 1. Canon Merge Rule
Claude-side work must not become a second source of truth.
The single source of truth remains:
- GitHub repository: actorlee007-cmyk/cheonoksystem
- Vercel project: cheonoksystem
- Official web domain: cheonoksystem.com
- JOS canon documents and runtime scripts

Claude work is merged only after:
1. actual working status check
2. readiness state classification
3. security redaction
4. ledger destination assignment
5. Final Veto check
6. next patch creation

## 2. Confirmed External Infrastructure From Claude Handoff

### AWS Server
Status: EXISTS_UNVERIFIED_IN_THIS_SESSION
Notes:
- Amazon Linux 2023
- Docker environment
- axital directory referenced
- public/internal IPs were provided by CEO but are not stored in this public repo document

Required next verification:
- SSH access check
- Docker container list
- running process list
- systemd/cron status
- environment variable inventory
- no secret exposure check

### Local PC
Status: EXISTS_BY_REPORT
Notes:
- Windows + PowerShell environment
- C:\\CHEONOK\\ folder structure exists by CEO/Claude report

Required next verification:
- local folder tree
- scheduled task list
- script hash/version
- environment variable check

### Vercel / GitHub / Web
Status: VERIFIED_IN_CHATGPT_VERCEL_CONNECTOR
Known:
- Vercel project exists: cheonoksystem
- production deployment is READY
- GitHub repository connected
- official domains attached:
  - cheonoksystem.com
  - www.cheonoksystem.com

Remaining:
- payment success verification
- lead form storage verification
- analytics verification
- environment variable inventory

## 3. Working Components Reported By Claude

### CHEONOK_ONE_CORE.ps1
Status: REPORTED_WORKING / NEEDS_LOCAL_EVIDENCE
Location:
- C:\\CHEONOK\\CHEONOK_ONE_CORE.ps1
Reported behavior:
- runs every hour via Windows Scheduler
- sends Telegram status reports
- tracks CASH CHAIN stage:
  EXPOSURE -> LEAD -> PAYMENT -> DELIVERY -> REVIEW -> SUBSCRIPTION
- uses environment variables instead of hardcoded tokens

Merge route:
- Local Runtime Ledger
- Scheduler Ledger
- Telegram Report Ledger
- Cash Chain Metrics

Required evidence:
- script content or hash
- scheduled task export
- latest Telegram report sample with secrets removed
- execution log

### Telegram Bot
Status: REPORTED_WORKING / SECRET_ROTATION_PARTLY_DONE
Known:
- Telegram bot environment variables exist
- chat id was provided, but should not be treated as public canonical content

Merge route:
- Report Delivery Channel
- CEO Alert Channel

Required next:
- confirm latest bot token stored only in env
- confirm no token in GitHub, Drive, local scripts
- add Telegram sender to readiness audit

### cheonoksystem.com
Status: VERIFIED_DEPLOYED + REPORTED_PAYMENT_FORM_WORKING
Known by previous Vercel check:
- Vercel deployment READY
- official domain attached
Reported by Claude:
- PayPal $69 payment connected
- free diagnostic form works
- Instagram story posted from energy_9999

Required next verification:
- PayPal payment success event record
- lead form storage target
- delivery path after payment
- CRM/ledger write path
- Instagram proof link/screenshot

## 4. Incomplete Components

### BAIV-X Stock System
Status: HOLD / PAPER_ONLY
Known:
- code exists by report
- not verified today
- PAPER_ONLY remains TRUE
- LIVE_TRADE remains BLOCKED

Required next:
- locate code
- run paper-only smoke test
- verify cost model includes fee, tax, spread, slippage, delay, partial-fill assumptions
- verify no execution gate is enabled

### Gemini Agent
Status: SECURITY_ROTATION_REQUIRED + RUNTIME_HOLD
Known:
- API key was exposed in chat; exact value is intentionally not stored here
- AWS run failed due to Python 3.9 compatibility issue
- google-genai installed on local PC PowerShell

Required next:
1. rotate Gemini API key immediately
2. update environment variable only
3. verify no old key exists in code, shell history, GitHub, Drive, Claude notes
4. choose runtime target:
   - local PC Python version path
   - AWS Python upgrade / venv
   - Docker image with compatible Python

### Instagram Automation
Status: CODE_EXISTS_BY_REPORT / EXECUTION_HOLD
Known:
- instagrapi installed
- code file referenced: cheonok_auto.py
- actual scheduled posting not completed

Required next:
- verify account safety
- avoid repeated login risk
- add manual/assisted posting fallback
- add content calendar and post ledger
- do not store password in code

### Google Drive via Claude Desktop
Status: CONNECTED_BUT_SEARCH_ERROR
Required next:
- do not rely on Claude Drive connector as source of truth
- use ChatGPT Google Drive connector or GitHub canon when available
- log Claude Drive connector as HOLD until search succeeds

## 5. Security Merge

### Reported Security Events
- Instagram password exposure: rotated by report
- Telegram bot token exposure: rotated by report
- AWS PEM key exposure: removed from Drive by report
- Gemini API key exposure: NOT ROTATED by report

### Canon Security State
- Gemini API key: ROTATION_REQUIRED_IMMEDIATE
- All exposed credentials: must be treated as compromised until verified rotated
- Public GitHub docs must not store raw secrets, tokens, keys, chat ids, or PEM material

## 6. Operating Principle Merge

Maintained:
- PAPER_ONLY: TRUE
- LIVE_TRADE: BLOCKED
- stop-loss: -2% fixed in simulation assumptions
- KIS rank lookup endpoint rule: FHPST01710000 only, if applicable
- API keys must not be hardcoded
- CEO approval only for final high-risk actions

Correction:
- Do not say ".env use prohibited" globally.
- Correct rule: secrets must not be hardcoded or committed. Environment variables or approved secret managers are required.

## 7. Unified CASH CHAIN State Machine
The reported Claude CASH CHAIN becomes a core JOS revenue-state machine:

EXPOSURE -> LEAD -> PAYMENT -> DELIVERY -> REVIEW -> SUBSCRIPTION

Required ledger fields:
- timestamp
- source
- channel
- lead_id
- product
- payment_status
- delivery_status
- review_status
- subscription_status
- evidence_url_or_file
- next_action

## 8. Immediate Next Actions

Priority 1 — Security
- rotate Gemini API key
- scan repo/local/Drive for old secret references
- confirm Telegram/Instagram/AWS secrets are no longer exposed

Priority 2 — Working Runtime Evidence
- pull C:\\CHEONOK\\CHEONOK_ONE_CORE.ps1 into private evidence review or sanitized GitHub doc
- export Windows Scheduler task
- confirm latest Telegram hourly report

Priority 3 — Revenue Loop Closure
- verify free diagnostic form writes to a ledger
- verify PayPal $69 payment success path
- verify delivery after payment
- create lead/payment/delivery/review/subscription ledger

Priority 4 — BAIV-X PAPER Check
- locate BAIV-X code
- run paper-only smoke test
- add cost model gate
- verify no live execution path is active

Priority 5 — Social/Content Loop
- confirm Instagram story proof
- stabilize content calendar
- hold full automation until account risk is controlled

## 9. Non-Regression Memory
Do not treat Claude work, ChatGPT work, local work, AWS work, and Vercel work as separate systems.
Everything must be merged into one source of truth with readiness states:
- VERIFIED
- REPORTED_WORKING
- EXISTS_BY_REPORT
- SETUP_REQUIRED
- HOLD
- BLOCK
- ROTATION_REQUIRED

## 10. Final Canon Line
Claude built and verified important execution pieces, but JOS must absorb them into one operating spine: GitHub canon, Vercel web, local Windows runtime, AWS runtime, Telegram reporting, PayPal/free-form revenue loop, PAPER-only trading safety, and security rotation gates.

Current status: autonomous learning and PAPER data accumulation.
