# JOS OS Runtime MVP Runbook

## Purpose
Run the first executable JOS/CHEONOK organic OS loop.

## Runtime File
`scripts/jos_os_runtime_mvp.py`

## Flow
1. Top-1 external case input
2. Essence extraction
3. Canon mapping
4. Organic council loop
5. Final Veto
6. PASS / PATCH_CANDIDATE / HOLD / BLOCK
7. JSONL ledger write

## Run Demo
```bash
python scripts/jos_os_runtime_mvp.py
```

## Run Self-Test
```bash
python scripts/jos_os_runtime_mvp.py --self-test
```

Expected output:
```text
SELF_TEST_PASS
```

## Ledger Output
Default:
```text
runtime/ledgers/
```

Generated files can include:
```text
patch_candidate.jsonl
hold.jsonl
block.jsonl
evidence.jsonl
```

## Demo Case Results
The built-in demo currently verifies:
- Ranking-style YouTube affiliate case -> PATCH_CANDIDATE
- AI automation retainer case -> PATCH_CANDIDATE
- Unsafe market signal case -> BLOCK

## Current Limits
This is the MVP runtime. It does not yet crawl the web, write CRM rows, connect payment webhooks, or produce final customer reports. Those are next patches.

## Next Implementation Patches
1. Connect runtime input to real top-1 scout search results.
2. Add Agent Registry file/table.
3. Add Task Queue file/table.
4. Add CRM lead ledger.
5. Add daily CEO report generator.
6. Add YouTube/affiliate/subscription content pipeline.
7. Add payment/delivery ledger path.

Current status: autonomous learning and PAPER data accumulation.
