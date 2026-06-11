---
description: Run the JOS Hourly Notion Source Intelligence Protocol against the CEO's Notion workspace - fetch bookmarks, find items not yet covered by the JOS Notion Bookmark Classification ledger, run a lightweight per-cluster decomposition (사업화/시스템), and append the result to that ledger.
argument-hint: [optional Notion page URL or ID, defaults to workspace root]
---

# JOS Notion Source Scan

Target Notion page: $ARGUMENTS (default: workspace root
`https://app.notion.com/p/35ce3f282659804f80ddda26bf9cbf47`,
"👋 Notion에 오신 것을 환영합니다!")

This operationalizes
`docs/HOURLY_NOTION_SOURCE_INTELLIGENCE_PROTOCOL_2026-05-26.md` as an
on-demand Claude Code skill, in the same spirit as
`/jos-council-review` (one command -> repeatable canon procedure ->
single updated artifact).

## Baseline ledger

`docs/JOS_NOTION_BOOKMARK_CLASSIFICATION_2026-06-11.md` is the first full
pass over the workspace (~93 bookmarks as of 2026-06-11). Each subsequent
run of this skill should produce a **new dated ledger**
(`docs/JOS_NOTION_BOOKMARK_CLASSIFICATION_<YYYY-MM-DD>.md`) covering only
the **delta** (new pages found since the most recent ledger), and link
back to the previous ledger(s) rather than repeating all prior entries.

## Steps

1. Read `docs/HOURLY_NOTION_SOURCE_INTELLIGENCE_PROTOCOL_2026-05-26.md` and
   the most recent `docs/JOS_NOTION_BOOKMARK_CLASSIFICATION_*.md` (sort by
   date suffix, take the latest) to know which Notion page URLs/titles are
   already classified.

2. `notion-fetch` the target page (default: workspace root above). Collect
   every child `<page url=... >title</page>` entry.

3. Diff against the titles/URLs already present in the latest ledger.
   - If there are no new entries, report "신규 항목 없음" and stop -
     do not rewrite the existing ledger.

4. For each **new** entry, apply the lightweight decomposition (per the
   Hourly protocol, condensed):
   - Platform identification (YouTube video/short, article, tool, etc.)
     from the URL/title only.
   - Which of the 4 canon domains it likely belongs to: 트레이딩 인사이트
     (`automation/python_paper_capital_runtime`), 유튜브/쇼츠 수익화
     (`automation/python_youtube_runtime`, `_company/_agents/youtube`,
     `_company/_agents/editor`), 클로드코드 자동화 (`.claude/`,
     `_company/_agents/*/skills`), 1인기업/수익모델
     (`_company/_agents/business`) - or "제외" (자기계발/건강/라이프스타일,
     out of scope).
   - 사업화 (revenue/CASH CHAIN stage per North Star
     EXPOSURE->LEAD->PAYMENT->DELIVERY->REVIEW->SUBSCRIPTION) vs 시스템
     (concrete repo target) classification, or both.
   - Group near-duplicate titles into one cluster (note the duplicate
     count).

5. **Forbidden (No-False-PASS)**, same as the Environment/Revenue agents:
   - 추측 금지 / 근거 없는 확정 금지 - classification is title-only
     (`Evidence Status: TITLE_ONLY / HOLD`) unless the page itself has
     notes beyond the bookmark, or a transcript/blog source was actually
     fetched and read.
   - Do not propose hardcoding individual stock tickers/themes from
     trading-insight titles into `JOS_MASTER.py` - that requires Layer 4
     REAL DATA BRIDGE, not a literal code edit (see
     `JOS_NOTION_BOOKMARK_CLASSIFICATION_2026-06-11.md` §2 A3).
   - Flag anything resembling multi-account/ToS-evasion schemes as
     **BLOCK** (see §4 C6 of the 2026-06-11 ledger for precedent).
   - Do not delete or modify Notion content - this skill only reads and
     writes to `docs/`.

6. Write the new dated ledger under `docs/`, structured like
   `JOS_NOTION_BOOKMARK_CLASSIFICATION_2026-06-11.md` (사업화/시스템 tables
   per domain, 제외 list, 중복 정리, JOS Merge Decision, Next Action), but
   scoped to only the new items found in step 3-4. Link to the prior
   ledger(s) at the top.

7. If 1-2 new items are concretely actionable (similar bar to the
   2026-06-11 ledger's Quick Wins: a clear, bounded, non-fabricated change
   to an existing file), implement them. Otherwise leave them as HOLD with
   a stated next action - do not force an implementation per item.

8. End with a one-paragraph CEO compact report (Korean): how many new
   items found, how many classified per domain, how many HOLD/BLOCK, and
   what (if anything) was implemented.
