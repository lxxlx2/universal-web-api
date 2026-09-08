# P1.2 post-remote recovery duplicate required-tool checkpoint — 2026-09-08

Status: protocol state-machine failure confirmed.

Observed on the same previously remote-compacted Codex thread:

- `COMMAND_1_STATUS='completed'`
- `COMMAND_1_EXIT_CODE=0`
- `COMMAND_1_IS_WORKSPACE_GUARD=YES`
- `COMMAND_2_STATUS='completed'`
- `COMMAND_2_EXIT_CODE=0`
- `COMMAND_2_IS_WORKSPACE_GUARD=YES`
- both command fingerprints were identical
- both outputs were identical
- command 2 did not reference the recovery result path
- command 2 did not contain the conversation-only token
- command 2 was not write-like or read-like
- no private-search behavior was observed
- the result file did not exist

Conclusion:

The recovery failure is no longer attributable to remote compaction, token loss, workspace mismatch, or missing tool exposure. The bridge successfully enforced and executed the first required client `exec_command`, but the required-tool constraint was then re-evaluated as unsatisfied on a later continuation round and forced the same workspace-guard call again.

The next repair is therefore in required-tool continuation state: once a required declared client tool has been satisfied by a real matching tool call within the active request/continuation lifecycle, subsequent continuation rounds must not re-force that same requirement. The fix must remain scoped to observed request-local state and must not weaken fail-closed behavior for genuinely unsatisfied required tools.

Do not rerun the long recovery thread until the state-machine fix has focused regression coverage and CI proof.
