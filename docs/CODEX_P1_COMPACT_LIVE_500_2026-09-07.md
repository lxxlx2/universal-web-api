# P1 compact live HTTP 500 — 2026-09-07

## Scope

This record captures macOS live acceptance of `POST /v1/responses/compact` on `codex-web-bridge-v2`.

Stage A-F and the aggregate checker remain PASS. The failures recorded here are isolated to P1.1 compact protocol hardening.

## First post-implementation live failure

After the compact endpoint was first implemented, the operator pulled the branch, restarted UWA, confirmed `/health`, and observed:

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

## First traceback root cause

The first local UWA traceback identified the exact failure at the final success-log line in `app/api/codex_compact.py`:

```text
TypeError: SecureLogger.info() takes 2 positional arguments but 3 were given
```

The route had already completed the backing ChatGPT Web request, sanitized the payload and produced a non-empty assistant `output`. The request then failed only while recording the success log:

```python
logger.info("[CODEX_COMPACT] compacted history into %s assistant item(s)", len(output))
```

UWA's `SecureLogger.info()` accepts one message argument, unlike the stdlib logging interpolation signature. Code inspection also found the same incompatible style on the backing-error `logger.warning()` branch.

## First repair

The narrow repair on `codex-web-bridge-v2` changed compact success/error logging to single preformatted message arguments and added route-level success/error regressions using a one-argument logger. Security hardening CI #239 for repair code commit `7c6d7ff` completed with `success`.

The repaired source line is now:

```python
logger.info(f"[CODEX_COMPACT] compacted history into {len(output)} assistant item(s)")
```

## Post-repair live rerun: FAIL

The operator pulled through branch head `b3f37ac`, verified the repaired source line locally, restarted UWA, confirmed service health and route registration, and reran the exact same direct compact probe.

Observed non-sensitive evidence:

```text
HEAD=b3f37ac
COMPACT_ROUTE_REGISTERED=YES
COMPACT_HTTP_CODE=500
JSON_PARSE=PASS
OUTPUT_IS_LIST=NO
OUTPUT_COUNT=0
MARKER_PRESERVED=NO
TASK_PRESERVED=NO
```

## Fresh post-repair traceback

The fresh traceback again reports the same old multi-argument-call exception:

```text
File ".../app/api/codex_compact.py", line 179, in codex_responses_compact
    logger.info(f"[CODEX_COMPACT] compacted history into {len(output)} assistant item(s)")
TypeError: SecureLogger.info() takes 2 positional arguments but 3 were given
```

This combination is internally inconsistent for the same executing bytecode: the displayed source contains exactly one explicit argument, while the exception says two explicit arguments were passed to the bound `SecureLogger.info()` method.

The strongest evidence-based hypothesis is therefore stale runtime bytecode/process state: the 8199 listener may still be executing the pre-repair function object while traceback line rendering reads the already-updated source file from disk. This is not yet treated as proven until the actual listener PID/start time and a fresh interpreter import are inspected.

Do not introduce another compact protocol code change from this traceback alone.

## Current classification

```text
route registration                         PASS
first live 500 root cause                  CONFIRMED: SecureLogger signature
first SecureLogger repair                  DONE
first repair route regressions              DONE
repair CI                                   PASS: #239
post-repair service restart                 reported PASS
post-repair route registration              PASS
post-repair direct compact request          FAIL: HTTP 500
fresh traceback                             SAME OLD SIGNATURE ERROR
current hypothesis                          stale UWA process / stale loaded bytecode
hypothesis confirmation                     NEXT: listener PID + start time + fresh import
P1.1 overall                                NOT PASS
P1.2 large-context stress                   BLOCKED
```

## Immediate next action

1. inspect the exact process listening on TCP 8199 and its start time;
2. inspect its cwd/command line;
3. independently import `app.api.codex_compact` in the repository venv and verify the live source/function signature;
4. if the listener predates the repair restart or otherwise appears stale, fully terminate the actual listener and start a fresh process with a verified new PID;
5. rerun the unchanged compact probe only after the process boundary is proven fresh.

The live acceptance criteria remain:

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
