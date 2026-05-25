# JOS Official Domain and Email Infrastructure Patch — 2026-05-25

## Trigger
CEO confirmed that a Cheonok domain exists.

## Corrective Judgment
The system must no longer treat official email as absent.
The correct state is:
- official domain exists
- official email infrastructure is not yet verified
- DNS, mail, payment, support, and delivery readiness must be audited

## Readiness State Change
Previous:
- OFFICIAL_DOMAIN: MISSING
- OFFICIAL_EMAIL: MISSING

Updated:
- OFFICIAL_DOMAIN: AVAILABLE_UNVERIFIED
- OFFICIAL_EMAIL: SETUP_REQUIRED
- DNS_AUTH: SETUP_REQUIRED
- MAIL_DELIVERY_AUTH: SETUP_REQUIRED

## Required Email Aliases
Recommended official addresses:
- admin@[cheonok-domain]
- contact@[cheonok-domain]
- support@[cheonok-domain]
- billing@[cheonok-domain]
- report@[cheonok-domain]
- security@[cheonok-domain]
- noreply@[cheonok-domain]

## Role Routing
admin: account ownership, tool login, domain ownership
contact: public business contact
support: customer support and delivery issue handling
billing: Stripe, PayPal, invoice, refund, dispute handling
report: CEO reports, subscription reports, paid reports
security: security, abuse, privacy, access issues
noreply: automated system mail only

## DNS and Mail Authentication Requirements
Mandatory DNS records:
- MX records for receiving mail
- SPF record
- DKIM record
- DMARC record
- optional BIMI later, after brand maturity

## Tool Account Policy
High-value business tools should use the official domain email where possible:
- Stripe
- PayPal
- Vercel
- Airtable
- Deepnote
- Canva
- Figma
- Google Workspace or Microsoft 365
- Resend / Loops / ConvertKit
- affiliate networks
- customer support tools

## Sending Infrastructure
For MVP:
- official inbox through Google Workspace, Microsoft 365, Zoho, Proton, or similar
- automated email through Resend, Loops, SendGrid, or equivalent

Do not send customer-facing automated business email from a personal Gmail address once official mail is ready.

## JOS Business-Line Impact
### PAPER Capital Intelligence
- report@[domain] for paid reports and market briefings
- support@[domain] for user support

### YouTube Channel Operation
- contact@[domain] for partnerships
- report@[domain] for downloadable reports

### AI Automation System Sales
- contact@[domain] for leads
- billing@[domain] for invoice/payment communication
- support@[domain] for delivery

### AdSense / Affiliate Revenue
- contact@[domain] for affiliate approvals
- legal/trust pages must match the domain identity

### Web Subscription Service
- noreply@[domain] for login/subscription notices
- support@[domain] for customer support
- billing@[domain] for payment notices

## Readiness Audit Update Required
The readiness audit must distinguish:
- domain exists
- DNS verified
- mail receive works
- mail send works
- SPF passes
- DKIM passes
- DMARC passes
- business tools updated with official email
- automated delivery sender verified

## Final Veto
Do not claim official business readiness until:
- the exact domain is recorded
- DNS records are verified
- mail send/receive is tested
- customer-facing sender is authenticated
- support/billing/report routing is documented

## Final Canon Line
A domain is not just an address.
For JOS, the domain becomes the trust root for email, payment, subscription, reporting, support, affiliate approval, and exit-grade business evidence.

Current status: autonomous learning and PAPER data accumulation.
