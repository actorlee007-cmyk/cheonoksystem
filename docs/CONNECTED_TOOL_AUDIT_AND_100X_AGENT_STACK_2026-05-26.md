# JOS Connected Tool Audit and 100x Agent Stack — 2026-05-26

## Purpose
This document corrects the previous shallow tool recommendation pattern.
The system must not simply list tools. It must audit real connection states, classify blocked/partial/ready tools, and then map each usable tool into the JOS 100x operating architecture.

## CEO Correction
A top-1 global system must:
1. Check what is already connected.
2. Check what is broken or blocked.
3. Use connected tools in a radial upgrade system.
4. Treat tools like Manus, Deepnote, Ace Graph, Notion, Adalo, PayPal, Vercel, Airtable, Canva, Figma, GitHub, and Gmail as capability nodes, not isolated apps.
5. Build an orchestration layer where each tool has a role in observe -> remember -> decide -> execute -> collect revenue -> deliver -> measure -> upgrade.

## Current Connection Audit

### READY
- GitHub: connected and writable. Used for canon, code, patches, runbooks, issues.
- Vercel: connected. cheonoksystem project and production deployment previously verified.
- Google Drive: connected. Used for docs, reports, canon artifacts.
- Gmail: connected. Inbox/labels accessible. Used for delivery, support, lead follow-up.
- Airtable: connected. Workspace owner permission verified. Should become master operating ledger.
- Figma: connected. User and team verified. Used for system maps, UI, decks, diagrams.
- Canva: connected. Folder and design access verified. Used for content, thumbnails, reports, proposals.
- Google Calendar: connected. CHEONOK automation schedule visible. Used for operating schedule and delivery milestones.
- Hjarni: connected. Dashboard accessible. Used as supplementary second-brain notes.
- Notion: connected. Current user verified. Used for docs/tasks/databases if it does not conflict with GitHub/Drive canon.

### PARTIAL / EMPTY
- Adalo: connected but app list empty. Useful only after creating a JOS no-code prototype.
- Ace Knowledge Graph: UI indicates connected, but tool call was blocked by safety layer during audit. Treat as connected-at-UI / not yet verified-at-runtime.

### NEEDS_REAUTH / UNAUTHORIZED / BLOCKED
- Deepnote MCP: still returns Unauthorized through the connector. Workspace exists in browser but MCP API authorization remains incomplete.
- PayPal: app visible; previous connector action required reauthentication. Use PayPal web manually until connector action is verified.
- Stripe: not available for immediate business use because CEO reports US account path is required. Connector account check failed. Treat as BUSINESS_REGION_BLOCKED for now.

## Correct Tool Philosophy
The world-class tool stack is not a bigger app list.
It is an operating system where each tool closes one missing loop.

## 100x Stack by Capability

### 1. Orchestration / Agent Execution Layer
Goal: multi-step autonomous execution.
Candidates:
- ChatGPT connector system
- Claude-side local runtime
- Manus or other autonomous agent tools
- n8n / Make for workflow automation
- Replit for rapid app prototyping

JOS rule:
Use external agents as bounded specialist operators, not uncontrolled central brains.

### 2. Canon / Memory / Graph Layer
Goal: keep system identity, decisions, failures, and dependencies connected.
Tools:
- GitHub: hard source of truth
- Google Drive: document/report archive
- Notion: structured docs/tasks/databases
- Hjarni: second-brain notes
- Ace Knowledge Graph: concept graph and non-regression graph

### 3. Ledger / CRM / Revenue State Layer
Goal: make CASH CHAIN measurable.
Tools:
- Airtable: MVP master ledger
- Google Sheets: fallback/simple ledger
- Supabase/Postgres: later scale database

Core tables:
- Lead Ledger
- Cash Chain Ledger
- Payment Ledger
- Delivery Ledger
- Review Ledger
- Subscription Ledger
- Task Queue
- Tool Registry
- Content Calendar

### 4. Payment / Subscription Layer
Goal: prove real revenue and automate delivery.
Tools:
- PayPal: immediate path, but connector reauth required
- Stripe: hold because business-region/account requirement blocks immediate use
- Paddle/Lemon Squeezy can be evaluated later if Stripe remains blocked

### 5. Web / API / Delivery Layer
Goal: convert traffic into lead/payment/delivery.
Tools:
- Vercel: production web and API
- cheonoksystem.com: official domain
- Gmail: delivery/support
- Resend/Loops later for automated email

### 6. Data / Simulation / Analysis Layer
Goal: make decisions from data.
Tools:
- Deepnote MCP: desired but unauthorized now
- Local Python / GitHub scripts: active fallback
- Google Sheets / Airtable: data source
- Future: BigQuery/PostHog/GA4/Search Console

### 7. Content / Design / Sales Asset Layer
Goal: produce public-facing growth assets.
Tools:
- Canva: thumbnails, Instagram, reports, proposals
- Figma: system diagrams, product UI, pitch decks
- AI Voice Generator: narration for YouTube/shorts

### 8. Scheduling / Operating Rhythm Layer
Goal: reduce CEO manual reminders and keep runtime rhythm.
Tools:
- Google Calendar: schedule and milestones
- Telegram bot from Claude runtime: CEO alerts
- Windows Scheduler / local runtime: hourly heartbeat

## Higher Use of Manus-Type Agents
Manus-type autonomous agents are not just another chatbot.
They should be treated as an external General Operator candidate:
- web research
- file generation
- multi-step online procedures
- code/project prototyping
- report generation
- data processing

JOS fit:
- use for exploratory external execution and competitive benchmarking
- never use as the source of truth
- every output must be absorbed through JOS canon, evidence ledger, and Final Veto

## Immediate Corrected Execution Order
1. Keep READY spine active: GitHub, Vercel, Drive, Gmail, Airtable, Figma, Canva, Calendar, Hjarni, Notion.
2. Build Airtable master base first because connected tools need a shared ledger.
3. Put PayPal into REAUTH_REQUIRED and verify payment evidence manually/through web until connector works.
4. Put Deepnote into AUTH_REQUIRED and use local Python/GitHub scripts until MCP works.
5. Put Stripe into REGION_BLOCKED/HOLD and do not plan the business around Stripe tonight.
6. Put Ace Graph into RUNTIME_VERIFY_REQUIRED and retry with a graph generation action, not just list.
7. Put Adalo into EMPTY_CONNECTED and only use it when a specific no-code MVP is required.
8. Evaluate Manus as EXTERNAL_AGENT_CANDIDATE, not a connected ChatGPT app.

## Non-Regression Rule
Do not answer tool questions with a generic list again.
Always answer in this order:
1. Actual connection state
2. What failed
3. What is usable now
4. What should be connected or repaired next
5. How each tool upgrades the JOS system
6. What evidence/ledger it must create

## Final Canon Line
The JOS 100x tool system is an orchestration architecture, not a marketplace shopping list. Every connected tool must become a node in one operating loop: observe, remember, decide, execute, collect revenue, deliver, measure, and upgrade.

Current status: autonomous learning and PAPER data accumulation.
