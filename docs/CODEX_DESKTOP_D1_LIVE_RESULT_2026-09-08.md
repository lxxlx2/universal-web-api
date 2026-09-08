# Codex Desktop D1 live result — 2026-09-08

## Current classification

D1 is at final verification. The Desktop task, fixture checker, Git diff discipline and route proof all passed. One machine-auditable criterion remains to be read from the metadata-only D1 wire trace before D1 is marked fully PASS: at least one real `exec_command` function call in the D1 trace window.

## Observed Desktop result

The actual Codex Desktop UI was used on the marked synthetic workspace `~/uwa-codex-acceptance` in a fresh thread. The task reported that it modified exactly the two expected implementation files and ran the real unittest suite successfully.

Sanitized post-run evidence:

```text
multi_file: PASS
ACCEPTANCE_PASS

git diff --check                         exit 0
tracked multi_file changes:
  multi_file/math_ops.py
  multi_file/summary.py

test files modified                      NO
```

The implementation diff corrected addition, multiplication and the expected summary rendering. Generated Python `__pycache__` directories were present as untracked synthetic-workspace artifacts; they are not test-source modifications and will be removed before the next Desktop scenario.

## Route proof

The post-marker route audit returned:

```text
CONFIGURED_PROVIDER=uwa
CONFIGURED_MODEL=chatgpt
CONFIGURED_EFFORT=high
LATEST_SESSION_PROVIDER=uwa
LATEST_SESSION_MODEL=chatgpt
LATEST_SESSION_EFFORT=high
CONFIG_SESSION_ROUTE=MATCH
UWA_HEALTH=healthy
UWA_BROWSER_CONNECTED=YES
UWA_WIRE_REQUEST_COUNT=4
UWA_WIRE_RESPONSE_COUNT=4
UWA_WIRE_LATEST_MODEL=chatgpt
UWA_WIRE_LATEST_EFFORT=high
UWA_WIRE_LATEST_STATUS=completed
ROUTE_EXPECTATION_PASS=YES
ROUTE_EXPECTATION_FAILURES=NONE
```

Raw session identities, private trace filenames, prompts, command bodies and tool output are intentionally omitted.

## Remaining proof

The D1 gate requires metadata-only evidence that the D1 trace contains a real `exec_command` function call. The trace format already stores `summary.function_call_names` without command bodies, prompts or tool output. Once that field is checked for the D1 marker window, D1 can be classified PASS if `exec_command` is present.

Do not proceed to D2 until this final trace check is recorded.
