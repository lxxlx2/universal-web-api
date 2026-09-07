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

## Traceback root cause

The local UWA traceback identifies the exact failure at the final success-log line in `app/api/codex_compact.py`:

```text
TypeError: SecureLogger.info() takes 2 positional arguments but 3 were given
```

The route had already completed the backing ChatGPT Web request, sanitized the payload and produced a non-empty assistant `output`. The request then failed only while recording the success log:

```python
logger.info("[CODEX_COMPACT] compacted history into %s assistant item(s)", len(output))
```

UWA's `SecureLogger.info()` accepts one message argument, unlike the stdlib logging interpolation signature. The exception converted an otherwise successful compact call into HTTP 500.

Code inspection also found the same incompatible style on the backing-error branch:

```python
logger.warning("Codex compact backing request failed: %s", exc)
```

That path had not triggered in the live probe, but it would likewise raise instead of returning the intended structured 502.

## Classification

```text
route registration                         PASS
backing compact execution                   PASS in observed live path
assistant replacement output generation     PASS in observed live path
success logging                             FAIL: incompatible SecureLogger call
implementation unit/regression tests        insufficient before repair
GitHub Actions Security hardening #220      PASS on pre-repair tests
direct macOS compact request                FAIL: HTTP 500
P1.1 overall                                NOT PASS until live rerun
P1.2 large-context stress                   BLOCKED
```

## Repair

The narrow repair is:

1. replace stdlib-style multi-argument logger calls with single preformatted messages;
2. cover the full compact route success path using a logger whose `info()` accepts exactly one argument;
3. cover the backing-failure route with a logger whose `warning()` accepts exactly one argument;
4. run CI;
5. rerun the same macOS direct compact probe without changing acceptance criteria.

The post-repair live gate still requires:

```text
COMPACT_ROUTE_REGISTERED=YES
COMPACT_HTTP_CODE=200
JSON_PARSE=PASS
OUTPUT_IS_LIST=YES
OUTPUT_COUNT>=1
MARKER_PRESERVED=YES
TASK_PRESERVED=YES
```

No account data, cookies, browser identifiers, thread identifiers, private source, full logs, or Responses SQLite contents are recorded here.
