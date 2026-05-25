# JOS Tool Ecosystem Scout Patch — 2026-05-25

## Corrective Judgment
The previous OS design did not sufficiently treat ChatGPT apps, MCP connectors, and external tools as a top-1% operating asset layer.
This was a system gap.

## Corrected Principle
JOS must not only use internal reasoning and GitHub code.
JOS must continuously scout available apps/tools/connectors, classify them, test whether they strengthen the five business lines, and route them through canon absorption.

## Tool Ecosystem Rule
The correct order is:
1. Discover available tools and external apps.
2. Classify each tool by capability.
3. Map it to the five business lines.
4. Check permission, account readiness, and data risk.
5. Route to PASS / TOOL_CANDIDATE / HOLD / BLOCK.
6. Record in Tool Registry and Task Queue.
7. Use the tool only when it creates measurable leverage.

## Why Not Use Every Tool Blindly
Using every app without classification creates tool sprawl.
Tool sprawl increases:
- security risk
- account fragmentation
- unclear data ownership
- repeated manual work
- broken workflows
- false readiness claims

Therefore, top-1% operation is not "use everything".
Top-1% operation is "scout everything, classify everything, then use the right tool at the right workflow point".

## Required Tool Scout Agents
- Tool Scout Agent: finds available apps/tools/connectors.
- Capability Mapper Agent: maps each tool to business functions.
- Canon Fit Agent: maps tools to JOS canon layers.
- Permission Agent: checks whether access is actually available.
- Risk Agent: checks data, payment, legal, privacy, and security risks.
- Workflow Router Agent: decides where the tool enters the pipeline.
- Tool Registry Agent: records the decision.
- Final Veto Agent: blocks unsafe or irrelevant tool use.

## Current Connected Tool Categories
### Source of Truth / Documents
- Google Drive
- GitHub
- Notion

### CRM / Operational Ledger
- Airtable
- Google Sheets through Google Drive

### Payment / Revenue
- Stripe
- PayPal

### Deployment / Web
- Vercel
- GitHub

### Content / Design
- Canva
- Figma
- Google Slides through Google Drive

### Communication / Delivery
- Gmail
- Google Calendar

### App / No-code Build
- Adalo

## Business Line Routing
### PAPER Capital Intelligence
Useful tools:
- GitHub for code and simulation logic
- Google Drive/Sheets for ledgers and reports
- Gmail for report delivery
- Vercel for web reports

### YouTube Channel Operation
Useful tools:
- Canva for thumbnails and social assets
- Figma for design systems and diagrams
- Google Drive for script/archive storage
- Airtable for content calendar

### AI Automation System Sales
Useful tools:
- Airtable for CRM and delivery pipeline
- Gmail for outreach/delivery
- Stripe/PayPal for payments
- Google Drive for proposals/reports
- Vercel for landing pages

### AdSense / Affiliate Revenue
Useful tools:
- Vercel for web pages
- Airtable/Sheets for offer tracking
- Canva for content assets
- Google Drive for asset archive

### Web Subscription Service
Useful tools:
- Stripe for subscription billing
- Vercel for frontend and APIs
- Airtable/Sheets for subscriber ledger
- Gmail for delivery/support
- Google Drive for report archive

## Decision States
PASS: connected, mapped, safe, and immediately useful.
TOOL_CANDIDATE: useful but requires setup or workflow design.
HOLD: unclear fit, missing account, missing permission, or no current workflow.
BLOCK: security/privacy/payment/legal risk or no JOS fit.

## Final Canon Line
JOS must scout all available tools, but must not blindly use all tools.
Every tool must pass capability mapping, canon fit, permission readiness, risk review, and workflow routing before execution.

Current status: autonomous learning and PAPER data accumulation.
