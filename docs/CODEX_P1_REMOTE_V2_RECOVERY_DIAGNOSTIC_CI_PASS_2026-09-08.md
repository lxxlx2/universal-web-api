# P1.2 recovery partial diagnostic CI PASS (2026-09-08)

## Status

`PASS — safe timeout-stage diagnostics ready for live use`

## CI evidence

Security hardening run #456 completed successfully across all required jobs:

- public repository safety: PASS
- Ubuntu / Python 3.11 security tests: PASS
- Ubuntu / Python 3.13 security tests: PASS
- macOS / Python 3.11 security tests: PASS
- macOS / Python 3.13 security tests: PASS
- upstream reproducible regression: PASS

## Diagnostic behavior

If the bounded same-thread recovery times out again, the versioned recovery runner now parses the private partial Codex JSONL trace and prints only safe metadata needed to locate the stalled stage:

- whether a partial trace exists;
- same-thread status without printing the thread id;
- completed agent-message and command counts;
- per-command semantic booleans for workspace guard, result-path reference, write/read shape, private-store search and conversation-token presence;
- command length and a short SHA-256 fingerprint, never the command text;
- safe error classifications for skill-budget warnings, HTTP 403 and transport failures;
- result-file existence and exactness booleans.

The parser also handles the bytes-literal shape that can be produced by `subprocess.TimeoutExpired.stdout`.

## Next gate

Run the same P1.2 same-thread recovery with the existing 300-second bound. Do not increase the timeout. If it passes, P1.2 closes. If it times out, use the safe partial diagnostic to identify the exact continuation stage before any further protocol change.

## Privacy

No live process identifiers, private thread ids, private trace paths, account details, prompts, command bodies, tool outputs or conversation tokens are recorded here.
