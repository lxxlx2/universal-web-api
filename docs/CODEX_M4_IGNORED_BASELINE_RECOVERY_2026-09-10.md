# M4 ignored-baseline recovery — 2026-09-10

## Result that triggered this repair

The bounded M4 timeout-recovery runner stopped before touching the canonical implementation because its resume precondition treated every pre-existing non-transient ignored file in the checkout as an unexpected M4 path.

Observed safe state:

```text
tracked changed before = app/api/codex_responses_v2.py
standard untracked before = none
staged path count = 0
failure = unexpected_ignored_resume_paths
```

The tracked modification is the expected partial M4 implementation left by the earlier real Codex long-task timeout. No new tracked or standard-untracked path was implicated by this failure.

## Repair

`tools/codex_m4_resume_safe.py` wraps the deterministic recovery runner and keeps strict checks for:

```text
branch = codex-web-bridge-v2
staged paths = none
tracked dirty scope subset = app/api/codex_responses_v2.py
standard untracked dirty scope subset = tests/test_codex_v2_stream_cancellation.py
```

Unrelated pre-existing ignored files are treated as baseline-local state. Their names are not printed. The wrapper prints only a count and whether the expected M4 test path is already ignored.

The underlying recovery remains responsible for rebuilding the canonical cancellation cleanup from tracked base, writing the fixed regression test path, running local validation, performing a bounded read-only Codex/UWA review, verifying route/request-manager state, and staging/committing/pushing only the two expected M4 paths after all gates pass.

## Safety

This change does not broaden the allowed tracked or standard-untracked M4 mutation scope and does not expose ignored local path names in public output.
