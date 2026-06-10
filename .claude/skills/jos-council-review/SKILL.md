---
description: Run the JOS/CHEONOK Five-Agent council review against a target system, file, or feature - one command dispatches four canon agents in parallel plus a Final Veto synthesis, producing a 0-100 canon scorecard and PASS/HOLD/VERIFY_REQUIRED/PATCH_REQUIRED/BLOCK verdict.
argument-hint: [target path or system name]
---

# JOS Council Review

Target: $ARGUMENTS

This is the JOS/CHEONOK "dynamic workflow": one command fans out to the
canon's Five Agents (`docs/JOS_CHEONOK_MASTER_SYSTEM_v1.md`) running in
parallel, then synthesizes their findings into one report.

## Steps

1. If the target is unclear or empty, ask the user which system/file/
   directory to review (e.g. `automation/python_paper_capital_runtime/`,
   `automation/python_youtube_runtime/`, `_company/`, etc.) before
   proceeding.

2. Read `docs/JOS_CHEONOK_MASTER_SYSTEM_v1.md` and
   `docs/JOS_CHATGPT_100_PERCENT_USAGE_OPERATING_CANON_2026-05-26.md` so you
   can pass their key contents (or paths) to each subagent.

3. Dispatch the following four subagents **in parallel** (single message,
   multiple Agent tool calls), each with the same prompt: "Review TARGET
   against the JOS/CHEONOK canon from your domain's perspective. Canon docs:
   docs/JOS_CHEONOK_MASTER_SYSTEM_v1.md and
   docs/JOS_CHATGPT_100_PERCENT_USAGE_OPERATING_CANON_2026-05-26.md. Follow
   your required output format exactly."
   - `jos-strategy-agent`
   - `jos-revenue-agent`
   - `jos-technology-agent`
   - `jos-environment-agent`

4. Once all four have returned, dispatch `jos-validation-agent` with: the
   TARGET, and the full text of all four findings reports. Ask it to
   synthesize per its required output format (3-axis guard, Final Veto,
   consolidated 0-100 canon scorecard, final verdict).

5. Present the validation agent's consolidated report to the user as the
   final result. Do not re-summarize the four individual reports separately
   unless the user asks for the detail - the validation agent's synthesis
   IS the deliverable.

6. End with one sentence: what changed (if anything was fixed as a result)
   and what the recommended next action is.
