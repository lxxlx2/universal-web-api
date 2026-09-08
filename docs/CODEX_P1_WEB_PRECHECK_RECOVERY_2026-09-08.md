# P1.2 Web precheck recovered after external 403 blocker

Date: 2026-09-08
Branch: codex-web-bridge-v2

A tiny Codex -> UWA -> ChatGPT Web precheck was executed after the previous post-remote recovery attempt was interrupted by an external ChatGPT Web `HTTP 403 Forbidden: Unusual activity has been detected from your device. Try again later.` response.

Observed live evidence:

- `SERVICE=healthy`
- `BROWSER_CONNECTED=True`
- `HEALTH_PASS=YES`
- `WEB_PRECHECK_REPLY_EXACT=YES`
- `WEB_PRECHECK_FAILED=NO`
- `WEB_PRECHECK_403=NO`
- `UWA_WEB_PRECHECK_PASS=YES`

Classification:

- the prior 403 is treated as a transient external blocker, not a product/protocol failure;
- the external blocker is now cleared for a small live request;
- do not rerun the long-context filler/compaction sequence;
- the current next gate is to rerun only the same-thread post-remote recovery against the already-proven remote-compacted thread.

The recovery gate remains CURRENT until the real write/read continuation completes successfully.
