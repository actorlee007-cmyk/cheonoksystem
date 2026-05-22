# CHEONOK Failure Learning System

## Purpose
CHEONOK is not only an execution system. It is a learning asset. Every failure, blocked API, wrong assumption, manual burden, and patch must become structured data that can be sold, audited, and improved.

## Core Rule
A failure is not finished when the immediate error disappears. A failure is finished only when all five are complete:

1. Symptom recorded
2. Root cause identified
3. Wrong pattern named
4. Correct pattern converted into a rule
5. Evidence stored in a ledger

## What We Learned From The Recent Execution Attempts

### FAIL-001: Repeating loops without ownership create chaos
Symptom: Old analyzer, terminal, and notepad windows kept appearing.
Root cause: No single-instance lock, stale process purge, or scheduler ownership.
Wrong pattern: Create new loops without stop policy.
Correct pattern: Every loop must have owner, lock, stop route, and proof output.
Rule: Never add a recurring runtime unless it has a kill route and status ledger.

### FAIL-002: Local environment assumptions break execution
Symptom: git pull failed because C:\CHEONOK was not a Git repository.
Root cause: The system assumed a local repo checkout existed.
Wrong pattern: Ask the CEO to manage git/path details.
Correct pattern: One-command bootstrap downloads raw runtime and creates paths automatically.
Rule: Never assume local repository state.

### FAIL-003: Environment files must be verified, not trusted
Symptom: API key was saved but Python reported missing key.
Root cause: PowerShell UTF-8 BOM and environment assignment mismatch.
Wrong pattern: Write .env and assume Python can read it.
Correct pattern: Write BOM-free .env and immediately verify key readback.
Rule: Any secret/config write must include readback validation.

### FAIL-004: External APIs cannot be allowed to stop revenue execution
Symptom: YouTube API returned 403 API_KEY_SERVICE_BLOCKED.
Root cause: YouTube Data API v3 was not enabled or permitted for the key/project.
Wrong pattern: Full pipeline calls before API health check.
Correct pattern: Health check first; if blocked, create fallback revenue assets.
Rule: External API failure must generate blocker evidence and continue with offline revenue output.

### FAIL-005: GitHub patch is not enough if local scheduler runs stale code
Symptom: Old runtime kept running after GitHub patch.
Root cause: Windows scheduled task pointed to stale local file.
Wrong pattern: Patch remote code and assume local scheduled task is updated.
Correct pattern: Force repair removes old task, downloads current runtime, verifies version, reinstalls scheduler.
Rule: Every runtime patch must include local update and scheduler replacement route.

### FAIL-006: PASS must never mean only process completion
Symptom: Console showed PASS while API was blocked.
Root cause: One success flag mixed process completion, API status, and revenue proof.
Wrong pattern: Runtime completed equals success.
Correct pattern: Separate Runtime Status, API Status, Asset Status, Revenue Proof, and Final Veto.
Rule: No PASS without evidence.

### FAIL-007: CEO manual burden is a product defect
Symptom: CEO had to execute mkdir, git, env, and manual path commands.
Root cause: Actions were explained before being packaged.
Wrong pattern: Describe steps.
Correct pattern: Generate one-command installer, repair script, ledger, and output files.
Rule: Any repeated manual step becomes code.

### FAIL-008: Fixes without memory do not compound
Symptom: Problems were patched but not stored as sellable data.
Root cause: No mandatory incident-to-ledger process.
Wrong pattern: Fix and move on.
Correct pattern: Every failure becomes structured data: symptom, cause, wrong pattern, correct pattern, patch, proof, reuse rule, exit value.
Rule: No failure is closed until it is logged.

## Mandatory Data Model
Every runtime and operating incident must write these fields:

- id
- date_kst
- system_area
- symptom
- root_cause
- wrong_pattern
- correct_pattern
- patch_applied
- proof_path_or_url
- current_status
- reuse_rule
- revenue_link
- exit_value

## Operating Behavior From Now On
1. Detect error
2. Stop repeating the same action
3. Classify the error
4. Identify root cause
5. Generate bypass route
6. Create or update patch
7. Write ledger row
8. Produce revenue asset anyway
9. Mark CEO approval items only when needed
10. Feed the learning back into the non-regression rules

## Exit Value
This ledger becomes part of the sellable OS:

- operational reliability history
- non-regression memory
- product improvement trail
- customer-support playbook
- onboarding dataset
- investor diligence evidence
- automation training data

## Final Veto
LIVE_TRADE: BLOCKED
CAPITAL_SCALE: BLOCKED
KIS_ORDER_GATE: BLOCKED
PAPER_ONLY: TRUE
