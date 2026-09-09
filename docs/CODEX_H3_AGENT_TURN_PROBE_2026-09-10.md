# H3 UWA agent-turn one-shot probe

Status: READY FOR LOCAL LIVE RUN

The browser-send/SSE blocker is closed. The immediate H3 question is whether a fresh Codex custom-provider agent turn declares `exec_command`, whether UWA recognizes it as the required tool, whether the Responses output emits a real `function_call`, and whether the request manager returns cleanly to zero.

`tools/codex_h3_agent_turn_probe.py` performs that diagnosis in one bounded local run. It:

- verifies the active branch and records only dirty-file count;
- prints the safe route-audit provider/model/effort fields;
- samples UWA health before and after;
- runs one fresh harmless `codex exec` turn that requires `exec_command` to execute only `pwd` and forbids file edits;
- reads only newly-created metadata-mode wire summaries;
- never prints prompt text, command bodies, tool outputs, thread ids, browser ids, cookies, credentials, raw traces, or private source;
- classifies the result into missing required-tool detection, missing function call, missing terminal completion, orphan request, or client nonzero exit.

Local command:

```bash
cd "$HOME/universal-web-api"
git switch codex-web-bridge-v2
git pull --ff-only
python3 tools/codex_h3_agent_turn_probe.py
```

Acceptance target:

```text
REQUIRED_EXEC_COMMAND_DETECTED=YES
EXEC_COMMAND_FUNCTION_CALL_EMITTED=YES
COMPLETED_RESPONSE_OBSERVED=YES
REQUEST_MANAGER_CLEAN_AFTER=YES
H3_AGENT_TURN_PROBE=PASS
```

A FAIL result is still useful because `FAILURE_CLASS` identifies the narrow repair layer without requiring full/private wire capture.
