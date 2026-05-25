# JOS Social Source Access and Analysis Protocol — 2026-05-26

## Purpose
This protocol closes the missing gap in the hourly source intelligence system.
The earlier protocol said platforms may require login or block scraping. That was not enough.
This document defines the platform-by-platform access matrix, safe collection paths, blocked methods, evidence grades, operating-model checks, and JOS absorption route.

## Core Rule
Social and web sources must be analyzed as operating systems, not as content.
However, JOS must not bypass login walls, collect private data, scrape restricted content, or call an unverified source PASS.

Every source must be classified as:

```text
PUBLIC_FIRST
OFFICIAL_API_REQUIRED
USER_PROVIDED_ONLY
LOGIN_REQUIRED_HOLD
PRIVATE_BLOCK
MIXED
```

## Evidence Grades

```text
A_OFFICIAL_API      = official API output, authorized and logged
B_PUBLIC_WEB        = visible public page, URL, screenshot, or public metadata
C_USER_PROVIDED     = CEO/user-provided screenshot, link, exported data, or transcript
D_SECONDARY_SOURCE  = third-party reporting or benchmark tool
HOLD_INSUFFICIENT   = not enough evidence to analyze without guessing
```

## Platform Matrix

### 1. YouTube
Access level: MIXED

Safe source path:
- YouTube Data API for structured public channel/video/search/comment metadata where permitted.
- Public channel/video pages.
- User-provided screenshots/links.
- OAuth is required for private/authenticated user data or write actions.

Allowed analysis:
- channel positioning
- upload cadence
- title and thumbnail formula
- visible metrics
- comments and audience pain points
- CTA/funnel
- affiliate links
- community/product path
- ranking-content engine

Blocked:
- private analytics without authorization
- login bypass
- restricted/private data scraping
- claiming exact revenue without evidence

JOS route:
- EXPOSURE engine
- YouTube ranking-content benchmark
- affiliate/ads model extraction
- paid report/content template

### 2. TikTok
Access level: MIXED

Safe source path:
- official TikTok developer products when app/account access exists
- public URL/profile/video review where visible
- user-provided screenshots/links
- TikTok Creative Center or business-facing public resources where available

Allowed analysis:
- hook pattern
- first 3 seconds
- short-form packaging
- trend format
- creator positioning
- CTA/product seeding
- affiliate/social-commerce path
- repeatable video formula

Blocked:
- bypassing app/login walls
- private account scraping
- unsafe engagement automation
- hidden conversion/revenue assumptions

JOS route:
- short-form EXPOSURE extraction
- YouTube Shorts/Reels translation
- ranking format testing
- affiliate content format adaptation

### 3. Instagram
Access level: MIXED

Safe source path:
- Instagram Platform APIs for owned/professional-account data when authorized
- public profile/post/reel review where visible
- user-provided screenshots/links

Allowed analysis:
- bio CTA
- profile positioning
- reel/post/story format
- link-in-bio funnel
- highlights structure
- offer ladder
- DM/lead mechanism
- visual identity system

Blocked:
- private DMs
- password-in-code automation
- login bypass
- risky mass engagement automation
- owner-only insights without authorization

JOS route:
- EXPOSURE -> LEAD
- Canva/Figma template generation
- diagnostic CTA
- content calendar
- lead attribution

### 4. Threads
Access level: USER_PROVIDED_ONLY until runtime/API access is verified

Safe source path:
- public web-visible posts/profiles
- user-provided screenshots/links
- official platform/API only after verified access

Allowed analysis:
- thought-leadership hooks
- worldview/positioning
- conversation format
- community signal
- cross-posting from Instagram/X
- audience psychology

Blocked:
- private or login-only threads
- personal-data collection
- complete reach assumptions from partial visible replies

JOS route:
- authority-building
- founder narrative
- JOS philosophy posts
- diagnostic lead magnets
- subscriber trust content

### 5. X
Access level: OFFICIAL_API_REQUIRED for programmatic scale, PUBLIC/USER_PROVIDED fallback for manual review

Safe source path:
- X API when developer access/credits exist
- public web pages and user-provided screenshots as fallback evidence

Allowed analysis:
- thread structure
- hook/post thesis
- account positioning
- trend usage
- visible engagement metrics
- link funnel
- product/consulting/subscription path

Blocked:
- API/rate-limit bypass
- restricted page scraping
- private DMs
- paid/API-restricted metrics without API evidence

JOS route:
- EXPOSURE -> LEAD
- founder-led content
- lead magnet threads
- subscription/report positioning

### 6. Website / Landing Page
Access level: PUBLIC_FIRST

Safe source path:
- public pages
- landing/pricing/help docs
- screenshots
- source URLs
- official product documentation
- robots-respecting/manual review

Allowed analysis:
- hero offer
- pain point
- CTA
- pricing
- funnel
- trust proof
- lead magnet
- checkout path
- onboarding
- SEO/content moat
- product packaging

Blocked:
- paywall bypass
- login/private dashboard access
- copyrighted page copying
- backend/revenue claims without proof

JOS route:
- LEAD -> PAYMENT -> SUBSCRIPTION
- cheonoksystem.com landing-page improvement
- offer ladder
- pricing and delivery loop

## Universal Analysis Checklist
For every source, answer:

1. What is visible and evidence-backed?
2. What is inferred and must be marked as inference?
3. What is inaccessible and must be HOLD?
4. Is it direct operation, tool stack, content engine, affiliate/ads, sales network, subscription, or mixed?
5. What customer discomfort does it solve?
6. What is the worldview/philosophy/positioning?
7. How does it produce attention?
8. How does it convert attention into lead/payment/subscription?
9. What can JOS absorb without copying?
10. What must be blocked?

## HOLD / BLOCK Rules

HOLD when:
- login is required
- official API access is missing
- source is unavailable
- account is private
- platform is rate-limited
- data is insufficient
- only partial screenshot exists

BLOCK when:
- private data collection is required
- login/paywall bypass is required
- credential storage in code is required
- scraping restricted content is required
- legal/privacy/security risk is unresolved
- copying copyrighted content is the only path
- claims require unverifiable revenue/private analytics

## Airtable Implementation
Created table:

```text
Platform Access Matrix
```

Records inserted:
- YouTube
- TikTok
- Instagram
- Threads
- X
- Website / Landing Page

This table is now the platform-level gate before source intake analysis.

## Automation Patch Requirement
Hourly source scanning must use this matrix before analyzing new links.
If a source falls into HOLD/BLOCK, it must not be summarized as if analyzed.
It must be recorded with the reason and next safe path.

## Final Canon Line
JOS must not chase platform data blindly. It must inspect each social/web source through a platform access matrix, use only safe evidence paths, classify operating model and sales structure, filter through JOS canon, and absorb only what can be verified without violating privacy, platform rules, or evidence discipline.

Current status: autonomous learning and PAPER data accumulation.
