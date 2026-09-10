# H3 agent-turn timeout after browser send repair

Date: 2026-09-10

Status: OPEN / release blocker

## Observed live result

A one-shot H3 agent-turn probe was run after the ChatGPT idle-composer send repair had already passed a direct High browser round trip.

Sanitized result:

```text
branch = codex-web-bridge-v2
working tree = clean
configured provider = uwa
configured model = chatgpt
health before running_count = 0
Codex exec bounded timeout = reached
Codex client events = thread.started, turn.started
new completed metadata wire request files = 0
new completed metadata wire response files = 0
required exec_command detected by completed traces = NO
exec_command function call emitted by completed traces = NO
completed response observed = NO
health immediately after timeout running_count = 1
probe result = FAIL
```

No private prompt body, command output, thread identifier, browser identifier, PID, account data, cookie, token or raw trace is recorded here.

## Interpretation

This does not reopen the already verified direct High browser-send repair. It proves that the fresh Codex agent-turn path can still remain in flight long enough for the bounded client probe to time out.

The absence of completed metadata trace files is expected while an attempt has not finished because the current trace writer persists request/response summaries after the body iterator completes. Therefore `NEW_TRACE_REQUESTS=0` by itself cannot prove that Codex omitted tools.

Static inspection also found a narrower, independently reproducible detector gap: the live probe phrase `You must use the local exec_command tool` contains the qualifier `the local`, while the current strict English required-tool expression expects the tool name immediately after `use/call/invoke`. This phrase therefore bypasses the strict required-tool path even when `exec_command` is declared.

## Immediate repair

`tools/codex_h3_repair_and_verify.py` performs the next step as one bounded local operation:

1. extend required-tool recognition to qualified phrases such as `the local exec_command` and the previously observed imperative client wording;
2. add focused positive and false-positive regression coverage;
3. run static checks and focused pytest when available;
4. restart managed UWA to clear the timed-out request cleanly;
5. rerun the H3 agent-turn probe with a shorter bounded timeout;
6. commit and push the detector repair automatically, so the operator does not perform Git bookkeeping manually.

If the live turn still stalls after required-tool recognition is fixed, the next blocker remains in the browser/tool-turn execution path and must be diagnosed from the newly bounded run rather than inferred from missing completed trace files.
