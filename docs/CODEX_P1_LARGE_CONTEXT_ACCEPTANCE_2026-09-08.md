# P1.2 native Codex large-context compaction acceptance — 2026-09-08

## Status

IMPLEMENTED / CI PASS / REAL MACOS LIVE PENDING.

P1.2 tests native Codex conversation-context growth and recovery through UWA. It is intentionally different from reading a large local file: the durable fact under test is seeded only in the Codex conversation and must survive substantial same-thread context growth.

## Automated runner

The repository-tracked runner is:

```text
tools/codex_large_context_acceptance.py
```

It automates the complete synthetic protocol:

```text
conversation-only seed token
→ same Codex thread
→ deterministic multi-turn filler
→ Codex JSONL usage/thread evidence
→ bounded scan of newly appended UWA log bytes
→ explicit /v1/responses/compact success evidence
→ one post-compact filler turn
→ final conversation-memory recovery
→ real local tool write/read
→ exact result-byte checker
```

The synthetic token is `ORBIT-5921`. It appears only in the seed prompt until the final local tool write. Filler and final prompts do not repeat it.

## Native Codex thread protocol

The runner uses `codex exec --json` for the first turn and `codex exec --json resume <thread>` for later turns. Prompts are supplied on stdin so large deterministic filler does not depend on macOS command-line argument limits.

Every resumed turn is checked against the same observed Codex thread id. Raw thread identifiers are private runtime evidence and are not written into the public-repository evidence file.

## Large filler

Default parameters:

```text
filler bytes per round: 20000
maximum filler rounds: 24
post-compact filler rounds: 1
per-turn timeout: 900 seconds
```

Each filler body is deterministic synthetic hash-like material derived from round/index. Filler turns instruct the model not to use tools, not to repeat or ask for the memory token, and to return one exact round acknowledgement.

The runner also records Codex `turn.completed` input/output token usage when available.

## Compaction evidence

P1.2 does not infer compaction merely from prompt byte volume.

The runner records the current private `~/.uwa/uwa.log` offset before the run and scans only bytes appended after that boundary for bounded lifecycle markers:

```text
/v1/responses/compact
[CODEX_COMPACT] compacted history into
```

A successful compact lifecycle marker is required for `COMPACTION_EVIDENCE=PASS`.

If conversation recovery succeeds but explicit compact success evidence is absent, the checker classifies the run as:

```text
STRESS_PASS_COMPACTION_UNPROVEN
```

and does not claim P1.2 compaction PASS.

## Token-leak protection

Before the final turn, the runner scans the synthetic acceptance workspace outside `.git` and requires the token to be absent. This prevents a local fixture file from substituting for conversation memory.

The final prompt explicitly prohibits searching Codex/UWA private history sources such as:

```text
~/.codex
~/.uwa
session/rollout history
logs
SQLite state
PROMPTS.md
```

The final turn must use a real client local tool only after validating the marked acceptance workspace, write exactly `ORBIT-5921\n` to `large_context/result.txt`, read the file back, and return exactly `LARGE_CONTEXT_PASS`.

The runner rejects final command evidence that searches prohibited private session/history locations.

## Evidence and privacy

Raw Codex JSONL is retained privately under:

```text
~/.uwa/p1-large-context/<timestamp>/
```

with restrictive permissions. Raw model/tool payloads, live thread ids, browser ids and private UWA logs are not committed.

The acceptance workspace receives only synthetic machine-auditable outputs:

```text
large_context/result.txt
large_context/evidence.json
```

The public evidence JSON contains synthetic counters/booleans and token-free runtime statistics; it does not contain the private trace path or live thread identity.

## Checker classification

Full P1.2 PASS requires all of the following:

- exact seed response;
- deterministic filler acknowledgements;
- zero pre-final local tool effects;
- same Codex thread observed across turns;
- token absent from workspace before final recovery;
- explicit compact success marker from the current run;
- exact final `LARGE_CONTEXT_PASS` response;
- real final local tool usage;
- no prohibited private-session/history search in final commands;
- exact `ORBIT-5921\n` result bytes.

The independent checker prints:

```text
large_context: PASS
COMPACTION_EVIDENCE=PASS
LARGE_CONTEXT_PASS
```

only when all requirements hold.

## Regression and CI

Tracked regression coverage:

```text
tests/test_codex_large_context_acceptance.py
```

Coverage includes prompt token isolation, deterministic filler, Codex JSONL parsing, appended-log compaction evidence, workspace token-leak detection, final-command safety, full PASS classification and stress-without-compaction classification.

Implementation commits:

```text
40873fe  Add automated P1.2 large-context acceptance runner
95150c4  Cover P1.2 large-context acceptance runner
ab5a857  Compile P1.2 runner in CI matrix
```

Security hardening CI #300 (`34151173565`) completed successfully on `ab5a857c353530aced4a907a61e46f74ef8b46b1`, including upstream regression, macOS/Ubuntu security matrices and public-repository-safety.

## Current gate

One real macOS run of the automated P1.2 runner is now required. The UWA bridge/provider/lifecycle are already live-validated, so the P1.2 run should not restart UWA merely because the runner code changed.

After the live run, its result must be synchronized before entering P1.3.
