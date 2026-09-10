# H3 required-client-tool repair live pass

Date: 2026-09-10

## Result

The qualified-English required-tool detector repair is live-verified on the real Codex CLI -> UWA -> ChatGPT Web -> Codex client-tool loop.

```text
configured provider = uwa
configured model = chatgpt
browser connected before = YES
request manager running before = 0
Codex exec transport = completed
required_tool = exec_command
exec_command declared by Codex request = YES
bounded repair attempt emitted exec_command = YES
client returned function_call_output = YES
final response.completed = YES
request manager running after = 0
H3_AGENT_TURN_PROBE = PASS
```

The first web attempt returned plain assistant text instead of the required client function. The bounded strict-tool repair kept the same web conversation, forced the declared `exec_command` schema on attempt 2, and the web model emitted a real `exec_command` function call. Codex executed it locally and returned a `function_call_output`; the continuation then completed normally.

## Detector defect

The real acceptance phrasing was equivalent to:

```text
You must use the local exec_command tool.
```

The old English regex accepted forms such as `must use exec_command` but did not allow narrow qualifiers such as `the local` between the verb and tool name. The repair allows bounded qualifiers (`the`, `local`, `client`, `client-side`, `declared`) while retaining a narrow tool-name allowlist and avoiding optional/explanatory wording.

## Safety and observability

The live evidence came from metadata-only wire summaries. Public records do not include the prompt body, command body, tool output, thread identifiers, browser identifiers, cookies, credentials, or raw trace data.

The browser-send/SSE blocker is already closed separately. This live pass also confirms that the earlier five-minute transport stall is absent on this agent-tool path.

## Remaining H3 blocker

The required client-tool path is now closed. H3 remains open only for the Codex hidden metadata-helper isolation and the final official -> UWA stateful handoff proof.

The metadata-helper request must be classified before required-tool enforcement and web-session affinity so that title/description generation cannot execute the embedded user task, contaminate the agent conversation, or become authoritative H3 agent evidence.
