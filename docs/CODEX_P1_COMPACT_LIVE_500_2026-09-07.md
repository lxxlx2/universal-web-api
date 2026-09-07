# P1 compact live HTTP 500 — 2026-09-07

## Scope

This record captures the first macOS post-implementation live acceptance of `POST /v1/responses/compact` on `codex-web-bridge-v2`.

Stage A-F and the aggregate checker remain PASS. This failure is isolated to P1.1 compact protocol hardening.

## Live evidence

After pulling the branch, restarting UWA and confirming `/health` was healthy, the operator observed:

```text
COMPACT_ROUTE_REGISTERED=YES
COMPACT_HTTP_CODE=500
JSON_PARSE=PASS
OUTPUT_IS_LIST=NO
OUTPUT_COUNT=0
MARKER_PRESERVED=NO
TASK_PRESERVED=NO
```

The harmless probe requested compaction of synthetic history containing marker `ALPHA-42` and a compact-protocol task description.

No account data, cookies, browser identifiers, thread identifiers, private source, full logs, or Responses SQLite contents are recorded here.

## Classification

```text
route registration                         PASS
implementation unit/regression tests        PASS
GitHub Actions Security hardening #220      PASS
direct macOS compact request                FAIL: HTTP 500
P1.1 overall                                NOT PASS
P1.2 large-context stress                   BLOCKED
```

The live `500` means the implementation currently has an unhandled runtime path that unit-level helper tests did not exercise.

## Immediate diagnostic boundary

Inspection of `app/api/codex_compact.py` shows that backing web-mode preparation and `_run_chat_completion_final()` are inside an exception boundary that converts exceptions to structured `502` responses. A raw `500` therefore points more strongly to an exception before that boundary or after the backing request, such as request adaptation, payload sanitization, output conversion, or another route-level path.

This is a hypothesis until the local UWA traceback is inspected.

## Next action

1. preserve this failure in Git before repair;
2. extract only the relevant local traceback around the compact request;
3. identify the exact failing line;
4. add a route-level regression reproducing the live shape;
5. implement the narrow repair;
6. require CI green;
7. rerun the same direct macOS probe without changing its acceptance criteria.
