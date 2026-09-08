# P1.2 post-remote-compaction recovery gate — 2026-09-08

## Status

IMPLEMENTED / CI PASS / REAL MACOS LIVE CURRENT.

The native Codex 0.153.4 remote-V2 compaction trigger has already passed on macOS with:

```text
THRESHOLD_CROSSED=YES
PRE_TRIGGER_OVER_HARD_CAP=NO
ROLLOUT_COMPACT_MARKER_DELTA=1
REMOTE_COMPACT_ROUTE_DELTA=1
REMOTE_COMPACT_SUCCESS_DELTA=1
AUTO_COMPACT_MODE=REMOTE
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

The remaining P1.2 gate is same-thread recovery after that exact remote compaction.

## Versioned runner

`tools/codex_remote_compaction_recovery.py` consumes an explicitly supplied private trigger-probe trace directory under `~/.uwa/p1-large-context/` and never prints the thread id, rollout path, prompt, command body, or private trace contents.

The runner requires:

- the supplied trace to contain one unique Codex thread;
- the prior tiny trigger turn to have replied exactly `AUTO_COMPACT_TRIGGER_OK` with zero tool effects;
- the matching private rollout to already contain at least one compact lifecycle marker;
- the synthetic token to remain absent from the acceptance workspace before recovery;
- recovery to resume the same Codex thread;
- three real separate `exec_command` steps: workspace guard, result write, result read-back;
- no command search of Codex/UWA private history stores;
- exact result bytes equal to the conversation-only token plus one newline;
- exact final reply `POST_REMOTE_RECOVERY_PASS`.

Synthetic evidence written to the acceptance workspace never records a live thread id or private trace path.

## CI

Tracked coverage:

- `tests/test_codex_remote_compaction_recovery.py`
- `.github/workflows/security-hardening.yml` compiles the recovery runner on macOS/Ubuntu Python 3.11/3.13.
- the full reproducible regression suite includes the recovery unit tests.

Security hardening #428 / run `34193504953` completed successfully.

## Current live source

The current live recovery must continue the already-proven remote-compaction trace directory printed by the successful macOS probe:

```text
~/.uwa/p1-large-context/20260908T051119Z
```

If this live gate passes, P1.2 is closed and the accelerated release path moves to the minimal P1.3 continuity blocker set.
