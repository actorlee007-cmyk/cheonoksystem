# SAFETY GUARDRAILS — JOS/CHEONOK MASTER SYSTEM

## Non-Negotiable Locks
- LIVE_TRADE: BLOCKED
- CAPITAL_SCALE: BLOCKED
- KIS_ORDER_GATE: BLOCKED
- AUTO_CODE_PATCH: BLOCKED
- CORE_PATCH: BLOCKED
- PAPER_ONLY: TRUE

## Trading Safety
The system may collect, rank, simulate, and report. It must not place live orders, suggest capital scaling, or activate any broker order gate.

## Simulation Rules
- Stop-loss assumption: fixed -2% in simulation.
- PAPER validation is required before any operational expansion.
- Required validation before any future live-trade discussion: at least 20 trading days, simulation score 90+, MDD within 10%, at least 50 paper trades, win rate at least 50%.

## Output Veto
Block outputs that include:
- live order execution
- capital deployment or leverage scaling
- broker API order activation
- sensitive credential exposure
- unverified revenue guarantees
- completion claims without file, URL, log, or report evidence
- manual workload transfer to the CEO

## Patch Governance
- No direct core patch.
- No automatic code patch to production.
- New changes must be proposed as patch candidates.
- Main branch writes should be documentation or safe skeleton only unless explicitly approved.

## Current State
Autonomous learning and PAPER data accumulation only.