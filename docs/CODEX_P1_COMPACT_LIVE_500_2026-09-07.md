# P1 compact live HTTP 500 — 2026-09-07

## Scope

This record captures macOS live acceptance of `POST /v1/responses/compact` on `codex-web-bridge-v2`.

Stage A-F and the aggregate checker remain PASS. The failures recorded here were isolated to P1.1 compact protocol hardening and process-lifecycle freshness.

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

The repaired source line is:

```python
logger.info(f"[CODEX_COMPACT] compacted history into {len(output)} assistant item(s)")
```

## Post-repair rerun exposed stale runtime

The operator pulled the repaired branch, verified the corrected source line, ran the normal stop/start workflow, confirmed service health and route registration, and reran the exact same direct compact probe. The request still returned HTTP 500.

A fresh traceback again showed the old multi-argument-call exception while the displayed source already contained the one-argument f-string call. That contradiction suggested stale loaded bytecode rather than a second compact-protocol defect.

The actual TCP 8199 listener and a fresh venv import were then inspected:

```text
old listener pid = 19974
old listener start time = 2026-09-07 18:00:52 local
old listener cwd = /Users/jerson/universal-web-api
fresh module file = /Users/jerson/universal-web-api/app/api/codex_compact.py
fresh bound logger.info signature = (msg: str)
fresh SecureLogger.info signature = (self, msg: str)
fresh imported source = one-argument f-string logger.info(...)
fresh Python bytecode = CALL 1 for logger.info
```

The listener predated the repair while a fresh interpreter saw the repaired bytecode. Therefore the failed rerun was served by a stale long-lived UWA process. The normal `codex-uwa-stop` / `codex-uwa` workflow had reported a restart without actually replacing the TCP 8199 listener.

## Verified fresh-listener rerun: PASS

The operator then terminated the exact process listening on TCP 8199 after verifying its cwd, confirmed the port was empty, started UWA again, and verified a different listener PID before rerunning the unchanged compact probe.

Observed evidence:

```text
PORT_8199_EMPTY=YES
OLD_PID=19974
NEW_PID=57575
LISTENER_REPLACED=YES
NEW_CWD=/Users/jerson/universal-web-api
service health = healthy
COMPACT_HTTP_CODE=200
JSON_PARSE=PASS
OUTPUT_IS_LIST=YES
OUTPUT_COUNT=1
OUTPUT_0_TYPE=message ROLE=assistant
MARKER_PRESERVED=YES
TASK_PRESERVED=YES
```

The returned compact summary preserved both synthetic durable facts:

```text
Project marker: ALPHA-42.
Current task: verifying the Responses compact protocol.
```

This proves that the repaired compact implementation works in the real macOS runtime once the actual listener is fresh.

## Final P1.1 classification

```text
route registration                         PASS
compact endpoint implementation             PASS
first live 500 root cause                  CONFIRMED: SecureLogger signature
SecureLogger repair                         PASS
route-level regression coverage             PASS
repair CI                                   PASS: #239
stale-runtime diagnosis                     CONFIRMED
fresh listener replacement                  PASS
post-replacement service health             PASS
direct compact HTTP                         PASS: 200
assistant output structure                  PASS
marker preservation                         PASS
task preservation                           PASS
P1.1 compact protocol overall               PASS
```

P1.1 is therefore closed.

## Remaining lifecycle defect

The compact protocol is no longer blocked. A separate operator/runtime defect remains: the normal `codex-uwa-stop` / `codex-uwa` workflow can report success while leaving the real TCP 8199 listener alive. That defect must be repaired before restart-heavy P1.2/P1.3 acceptance so stale processes cannot invalidate future results.

Next sequence:

1. inspect the actual shell/function definitions behind `codex-uwa-stop` and `codex-uwa`;
2. harden stop/start so the real TCP 8199 listener is verified terminated/replaced;
3. add an automated lifecycle regression where practical;
4. run P1.2 synthetic large-context compaction/recovery;
5. continue P1.3 lost-affinity/restart fallback and the mandatory Desktop D1-D5 live gate.

No account data, cookies, browser identifiers, thread identifiers, private source, full logs, or Responses SQLite contents are recorded here.
