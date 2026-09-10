#!/usr/bin/env python3
"""Close M4 from the already-completed bounded review using structural evidence.

The previous structural finalizer required the UWA response-summary trace itself
to contain ``function_call_names=[exec_command]``. The live Codex review did
execute a local command and completed, but that particular summary field was
empty. This wrapper keeps the existing deterministic M4 local validation and
adds two independent metadata-only proof paths before accepting the completed
review:

1. a post-marker Responses request containing ``function_call_output``;
2. a post-marker Codex rollout containing a real command/function-call event.

No prompt, command body, tool output, raw thread id, rollout path, cookie or
credential is printed or persisted by this helper. It does not repeat the Web
review.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
BASE_PATH = REPO / "tools" / "codex_m4_finalize_completed_review.py"
CODEX_ROOT = Path.home() / ".codex"


def _load_base():
    spec = importlib.util.spec_from_file_location(
        "codex_m4_completed_review_base_for_v2",
        BASE_PATH,
    )
    if spec is None or spec.loader is None:
        raise SystemExit("M4_STRUCTURAL_FINALIZER_V2_IMPORT_FAIL")
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


base = _load_base()
module = base.module


def _parse_event_epoch(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        pass
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.timestamp()


def _evidence_key(path: Path, kind: str, value: Any, line_no: int) -> str:
    raw = f"{path}:{kind}:{value}:{line_no}"
    return hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()[:20]


def _rollout_command_evidence_since(epoch: float) -> tuple[int, int, int]:
    """Return metadata-only counts of post-marker Codex command evidence.

    The scanner understands current and legacy rollout shapes. It never emits
    command text or tool output. Event timestamps are required so an old event
    from a recently-modified rollout cannot satisfy the gate.
    """

    if not CODEX_ROOT.is_dir():
        return 0, 0, 0

    unique_calls: set[str] = set()
    candidate_files = 0
    timed_events = 0

    for path in CODEX_ROOT.rglob("*.jsonl"):
        try:
            if path.stat().st_mtime < epoch - 2.0:
                continue
        except OSError:
            continue

        saw_candidate = False
        try:
            handle = path.open("r", encoding="utf-8", errors="replace")
        except OSError:
            continue
        with handle:
            for line_no, raw in enumerate(handle, 1):
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue
                event_epoch = _parse_event_epoch(obj.get("timestamp"))
                if event_epoch is None or event_epoch < epoch:
                    continue
                timed_events += 1

                outer_type = str(obj.get("type") or "").strip().lower()
                payload = obj.get("payload")
                if not isinstance(payload, dict):
                    payload = {}
                payload_type = str(payload.get("type") or "").strip().lower()

                if outer_type == "response_item" and payload_type in {
                    "function_call",
                    "custom_tool_call",
                    "local_shell_call",
                }:
                    name = str(payload.get("name") or "").strip().lower()
                    if name in {"exec_command", "shell_command", "local_shell", "exec", "shell"}:
                        token = payload.get("call_id") or payload.get("id") or f"line-{line_no}"
                        unique_calls.add(_evidence_key(path, "response_item", token, line_no))
                        saw_candidate = True

                if outer_type == "event_msg" and payload_type in {
                    "exec_command_begin",
                    "exec_command_end",
                }:
                    token = payload.get("call_id") or payload.get("id") or f"line-{line_no}"
                    unique_calls.add(_evidence_key(path, "exec_event", token, line_no))
                    saw_candidate = True

                if outer_type == "event_msg" and payload_type in {
                    "item_started",
                    "item_completed",
                }:
                    item = payload.get("item")
                    if isinstance(item, dict):
                        item_type = str(item.get("type") or "").strip().lower()
                        if "command_execution" in item_type or item_type in {
                            "function_call",
                            "local_shell_call",
                        }:
                            token = item.get("id") or item.get("call_id") or f"line-{line_no}"
                            unique_calls.add(_evidence_key(path, "turn_item", token, line_no))
                            saw_candidate = True

        if saw_candidate:
            candidate_files += 1

    return len(unique_calls), candidate_files, timed_events


def _function_call_output_count(requests: list[dict[str, Any]]) -> int:
    total = 0
    for item in requests:
        input_summary = item.get("input")
        if not isinstance(input_summary, dict):
            continue
        value = input_summary.get("function_call_output_count")
        if isinstance(value, int) and value > 0:
            total += value
    return total


def verify_completed_review_from_wire() -> None:
    epoch = base._read_marker_epoch()
    requests, responses = base._trace_summaries_since(epoch)

    route_ok = any(
        str(item.get("model") or "") == "chatgpt"
        and str(item.get("reasoning_effort") or "") == "high"
        for item in requests
    )
    response_exec_calls = sum(
        1
        for item in responses
        if "exec_command" in (item.get("function_call_names") or [])
    )
    function_outputs = _function_call_output_count(requests)
    completed = sum(
        1
        for item in responses
        if str(item.get("response_status") or "") == "completed"
    )
    rollout_calls, rollout_files, rollout_timed_events = _rollout_command_evidence_since(epoch)

    tool_proof_sources: list[str] = []
    if response_exec_calls >= 1:
        tool_proof_sources.append("uwa_response_function_call")
    if function_outputs >= 1:
        tool_proof_sources.append("responses_function_call_output")
    if rollout_calls >= 1:
        tool_proof_sources.append("codex_rollout_command_event")

    print(f"M4_POST_MARKER_AGENT_REQUEST_COUNT={len(requests)}")
    print(f"M4_POST_MARKER_AGENT_RESPONSE_COUNT={len(responses)}")
    print("M4_POST_MARKER_ROUTE_CHATGPT_HIGH=" + ("YES" if route_ok else "NO"))
    print(f"M4_POST_MARKER_EXEC_COMMAND_RESPONSE_COUNT={response_exec_calls}")
    print(f"M4_POST_MARKER_FUNCTION_CALL_OUTPUT_COUNT={function_outputs}")
    print(f"M4_POST_MARKER_CODEX_COMMAND_EVIDENCE_COUNT={rollout_calls}")
    print(f"M4_POST_MARKER_CODEX_COMMAND_EVIDENCE_FILES={rollout_files}")
    print(f"M4_POST_MARKER_CODEX_TIMED_EVENT_COUNT={rollout_timed_events}")
    print(f"M4_POST_MARKER_COMPLETED_RESPONSE_COUNT={completed}")
    print("M4_REAL_CLIENT_TOOL_PROOF_SOURCES=" + (",".join(tool_proof_sources) or "NONE"))

    if not requests:
        raise module.GateError("completed_review_agent_request_missing")
    if not route_ok:
        raise module.GateError("completed_review_route_mismatch")
    if not tool_proof_sources:
        raise module.GateError("completed_review_real_tool_evidence_missing")
    if completed < 1:
        raise module.GateError("completed_review_response_completed_missing")

    audit = module.run(
        [
            sys.executable,
            "tools/codex_route_audit.py",
            "check",
            "--expect-provider",
            "uwa",
            "--expect-model",
            "chatgpt",
            "--expect-effort",
            "high",
        ],
        timeout=60,
    )
    print(f"M4_ROUTE_AUDIT_RC={audit.returncode}")
    route_pass = audit.returncode == 0 and "ROUTE_EXPECTATION_PASS=YES" in audit.stdout
    print("M4_ROUTE_EXPECTATION_PASS=" + ("YES" if route_pass else "NO"))
    if not route_pass:
        raise module.GateError("completed_review_route_audit_failed")


base.verify_completed_review_from_wire = verify_completed_review_from_wire


if __name__ == "__main__":
    raise SystemExit(base.main())
