# JOS/CHEONOK Safe Bridge Skeleton

This folder is reserved for the safe bridge controller.

## Purpose
The bridge connects local execution, Google Drive outputs, GitHub code canon, report generation, and PAPER-only market validation.

## Required Contract
Every run must produce:
- run_id
- date_kst
- command
- status: PASS | HOLD | BLOCK
- evidence_url or log_path
- veto_reason when blocked
- next_action

## Forbidden
- live broker order execution
- capital scaling
- hidden credential logging
- direct core patch without approval
- success message without file/log evidence

## Minimal Safe Flow
1. Read command.
2. Apply safety gate.
3. If blocked, write BLOCKED_LOG.
4. If allowed, execute only safe report/data task.
5. Write result to REPORT_LOG or PATCH_COUNCIL.
6. Return concise CEO report.

## Current State
Skeleton only. PAPER data accumulation mode.