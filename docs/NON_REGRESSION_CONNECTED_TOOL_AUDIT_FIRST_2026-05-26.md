# Non-Regression: Connected Tool Audit First — 2026-05-26

## Trigger
CEO corrected the system: before recommending tools, the assistant must check which tools are already connected, which are partially connected, and which are failing.

## Correct Rule
Do not recommend a generic tool connection list first.
Always perform connection-state audit first when connected-tool execution is relevant.

Required sequence:
1. Inspect available tools/connectors.
2. Test actual connected status where safe.
3. Classify each tool as READY, PARTIAL, NEEDS_REAUTH, UNAUTHORIZED, EMPTY, TIMEOUT, BLOCKED, or NOT_CONNECTED.
4. Only then produce a connection/action plan.
5. Do not treat a tool as usable just because it appears in the app list.
6. Do not treat a tool as disconnected without checking.

## Current Checked State

### READY
- GitHub: profile accessible as actorlee007-cmyk / actorlee007@gmail.com.
- Vercel: team accessible, cheonoksystem project previously verified.
- Google Drive: profile accessible as 천옥시스템 AI업무자동화팀 / actorlee007@gmail.com.
- Gmail: labels accessible; inbox and unread counts returned.
- Airtable: ping returned pong; workspace exists with owner permission.
- Figma: authenticated as 한울채널 / actorlee007@gmail.com; team plan available.
- Canva: root folder/items accessible; existing designs visible.
- Google Calendar: events accessible; CHEONOK automation schedule event visible.
- Hjarni: dashboard accessible; note/container counts returned.

### PARTIAL / EMPTY
- Adalo: authenticated call succeeded but app list is empty.

### NEEDS_REAUTH / UNAUTHORIZED / ERROR
- PayPal: create invoice check returned reauthentication required.
- Deepnote MCP: get_me returned Unauthorized.
- Stripe: get account info returned token refresh already in progress; recheck needed before use.
- Ace Knowledge Graph: list call timed out; recheck needed.
- Notion: user self-check was blocked by safety check; recheck with safer/search-based call before use.

## Operational Consequence
Tonight connection plan must start from failing or partial tools, not a generic priority list.

Suggested order:
1. Fix PayPal reauthentication because payment path is reported active but connector is not usable here.
2. Fix Deepnote authorization because data notebooks are core to PAPER/simulation layer.
3. Recheck Stripe after token refresh; then verify products, prices, links, subscriptions.
4. Recheck Ace Knowledge Graph timeout; if stable, generate JOS graph.
5. Recheck Notion via safe search/fetch route; if still blocked, use Hjarni/GitHub/Drive as memory instead.
6. Keep Airtable as immediate READY operating ledger.
7. Keep GitHub/Vercel/Drive/Gmail/Canva/Figma/Calendar/Hjarni as active connected stack.
8. Treat Adalo as optional because it is connected but empty.

## Memory Rule
When the CEO asks for tools or system acceleration, do not answer from imagination or broad app lists. First inspect the connected tool state and report based on actual status.

## Final Canon Line
A top-1 operating system does not ask which tools might help before checking which tools are already alive, which are broken, and which must be repaired first.

Current status: autonomous learning and PAPER data accumulation.
