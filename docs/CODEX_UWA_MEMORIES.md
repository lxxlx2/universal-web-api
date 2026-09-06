# Codex Memories under the UWA bridge

Last updated: 2026-09-06

## Live finding

A foreground Codex Desktop coding task can finish while Codex continues to launch an internal memory-consolidation job in the background. In the current upstream Codex implementation, the preferred memory-consolidation model is `gpt-5.6-terra`.

The observed background Phase 2 flow references Codex memory workspace artifacts such as:

- `phase2_workspace_diff.md`
- `raw_memories.md`
- `MEMORY.md`
- `memory_summary.md`
- `rollout_summaries/`

With `model_provider = "uwa"`, these auxiliary model requests can also be sent through UWA. That produces several undesirable effects before dedicated support exists:

- ChatGPT Web keeps working after the foreground Codex task appears finished;
- the controlled ChatGPT tab can be occupied by background memory work;
- extra ChatGPT sidebar conversations are created;
- long memory prompts can consume latency and web-model usage;
- the memory subtask can hit the same client-tool/runtime continuity edge cases as normal coding turns;
- partially completed memory consolidation is not acceptable because provenance and incremental forgetting rules matter.

## Current support policy

Automatic Codex memory generation is **not part of the supported UWA bridge path yet**.

While UWA mode is active, disable both:

```toml
[memories]
generate_memories = false
use_memories = false
```

This does not delete Codex thread history, project files, Git state, UWA continuation snapshots, or the existing Codex memory files. It only prevents new UWA-mode threads from generating/using Codex automatic memories while this path is unvalidated.

The supported continuity layers remain:

1. Codex Desktop thread history;
2. UWA private Responses continuation (`~/.uwa/codex_responses.sqlite3`);
3. Git-tracked project checkpoints (`README.md`, current-state and acceptance docs, tests and commits).

## Memory guard helper

The repository includes:

```bash
python3 tools/codex_uwa_memory_guard.py status
python3 tools/codex_uwa_memory_guard.py disable
python3 tools/codex_uwa_memory_guard.py restore
```

`disable`:

- backs up `~/.codex/config.toml`;
- saves only the previous boolean settings to `~/.uwa/codex_memories_guard.json`;
- sets `generate_memories = false` and `use_memories = false`;
- never reads or writes memory contents.

`restore` returns those two booleans to their previous state when switching back to the official provider.

The private guard state is local runtime data and must never be committed.

## Live restart procedure

If a Terra Phase 2 job is already running:

1. quit Codex Desktop so the background job stops at the client;
2. stop UWA so any in-flight browser request is cancelled;
3. pull the latest `security-hardening` branch;
4. run the memory guard `disable` action;
5. restart UWA and Codex Desktop;
6. create a new UWA-mode Codex thread for further acceptance testing.

Existing ChatGPT Web conversations created by previous background jobs can be left alone; they are historical UI artifacts and are not required for bridge continuity.

## Future acceptance

Dedicated Codex Memories support is deferred until the foreground bridge passes the normal acceptance stages. A future Memories acceptance must prove at least:

- background-vs-foreground request isolation;
- stable access to the Codex memory workspace through client tools;
- no cross-project contamination;
- provenance-preserving incremental consolidation;
- bounded browser conversation usage;
- restart behavior;
- safe cancellation;
- no private memory contents in public logs or repository artifacts.

Until then, automatic Codex Memories remain disabled in UWA mode by design.
