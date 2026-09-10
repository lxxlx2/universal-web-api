#!/usr/bin/env python3
"""Install and live-verify H3 Codex metadata-helper isolation in one run.

The runner patches only the narrow V2 metadata-helper path, validates syntax/diff,
restarts UWA, sends a synthetic current-Codex title request containing an embedded
client-tool instruction, proves the request is answered locally without browser or
client-tool execution, proves route audit ignores that helper traffic, then commits
and pushes the verified patch.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Tuple


REPO = Path(__file__).resolve().parents[1]
BRANCH = "codex-web-bridge-v2"
API = REPO / "app" / "api" / "codex_responses_v2.py"
ROUTE = REPO / "tools" / "codex_route_audit.py"
TEST = REPO / "tests" / "test_codex_metadata_helper_isolation.py"
TRACE_DIR = Path.home() / ".uwa" / "debug" / "codex-wire"


def run(cmd: List[str], *, timeout: int = 120) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return 124, out, err


def require_clean_branch() -> None:
    rc, out, _ = run(["git", "branch", "--show-current"], timeout=20)
    branch = out.strip()
    print(f"BRANCH={branch}")
    if rc != 0 or branch != BRANCH:
        raise SystemExit("PRECONDITION_FAIL=wrong_branch")
    rc, out, _ = run(["git", "status", "--porcelain"], timeout=20)
    dirty = [line for line in out.splitlines() if line.strip()]
    print(f"WORKTREE_DIRTY_COUNT={len(dirty)}")
    if rc != 0 or dirty:
        raise SystemExit("PRECONDITION_FAIL=dirty_worktree")


def replace_once(path: Path, old_lf: bytes, new_lf: bytes, label: str) -> None:
    raw = path.read_bytes()
    for newline in (b"\r\n", b"\n"):
        old = old_lf.replace(b"\n", newline)
        count = raw.count(old)
        if count == 1:
            new = new_lf.replace(b"\n", newline)
            path.write_bytes(raw.replace(old, new, 1))
            print(f"{label}=YES")
            return
        if count > 1:
            raise SystemExit(f"{label}_TARGET_COUNT={count}")
    raise SystemExit(f"{label}_TARGET_NOT_FOUND")


def patch_api() -> None:
    replace_once(
        API,
        b"from app.services.codex_network_tuning import install_codex_chatgpt_network_tuning\nfrom app.services.codex_web_policy import (\n",
        b"from app.services.codex_network_tuning import install_codex_chatgpt_network_tuning\nfrom app.services.codex_metadata_helper import (\n    build_metadata_json,\n    classify_metadata_helper,\n)\nfrom app.services.codex_web_policy import (\n",
        "API_IMPORT_PATCH",
    )

    replace_once(
        API,
        b'''def _pack_event(event: str, payload: Dict[str, Any]) -> str:\n    return f"event: {event}\\ndata: {json.dumps(payload, ensure_ascii=False)}\\n\\n"\n\n\ndef _required_tool_failed_events(body: ResponsesRequest, required_tool: str) -> List[str]:\n''',
        b'''def _pack_event(event: str, payload: Dict[str, Any]) -> str:\n    return f"event: {event}\\ndata: {json.dumps(payload, ensure_ascii=False)}\\n\\n"\n\n\ndef _summary_with_request_kind(\n    body: ResponsesRequest,\n    *,\n    request_kind: str,\n    required_tool: str = "",\n) -> Dict[str, Any]:\n    summary = summarize_responses_request(body, required_tool or None)\n    summary["request_kind"] = request_kind\n    return summary\n\n\nasync def _metadata_helper_stream(\n    body: ResponsesRequest,\n    trace_id: str,\n) -> AsyncIterator[str]:\n    """Answer known Codex UI metadata requests locally without touching ChatGPT Web."""\n\n    response_id = _new_response_id()\n    created_at = int(time.time())\n    prompt = _latest_user_text(body.input)\n    structured_text = build_metadata_json(prompt, body.text)\n    chat_payload = {\n        "choices": [\n            {\n                "index": 0,\n                "message": {"role": "assistant", "content": structured_text},\n                "finish_reason": "stop",\n            }\n        ],\n        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},\n    }\n    in_progress = _build_responses_object(\n        body,\n        {"choices": [], "usage": {}},\n        response_id=response_id,\n        created_at=created_at,\n        status="in_progress",\n        error=None,\n    )\n    completed = _build_responses_object(\n        body,\n        chat_payload,\n        response_id=response_id,\n        created_at=created_at,\n        status="completed",\n        error=None,\n    )\n\n    chunks: List[str] = []\n    sequence = 1\n    chunks.append(\n        _codex_event(\n            "response.created",\n            sequence_number=sequence,\n            response=in_progress,\n        )\n    )\n    sequence += 1\n\n    output = completed.get("output") if isinstance(completed.get("output"), list) else []\n    for output_index, item in enumerate(output):\n        if not isinstance(item, dict):\n            continue\n        chunks.append(\n            _codex_event(\n                "response.output_item.done",\n                sequence_number=sequence,\n                output_index=output_index,\n                item=_codex_wire_item(item),\n            )\n        )\n        sequence += 1\n\n    chunks.append(\n        _codex_event(\n            "response.completed",\n            sequence_number=sequence,\n            response=completed,\n        )\n    )\n\n    response_summary = summarize_responses_sse(chunks)\n    response_summary["request_kind"] = "metadata_helper"\n    write_trace_attempt(\n        trace_id=trace_id,\n        attempt=1,\n        request_summary=_summary_with_request_kind(\n            body,\n            request_kind="metadata_helper",\n        ),\n        response_summary=response_summary,\n        full_request=body,\n        raw_sse="".join(chunks),\n    )\n    logger.info("[CODEX_RESPONSES_V2] metadata helper served locally")\n    for chunk in chunks:\n        yield chunk\n\n\ndef _required_tool_failed_events(body: ResponsesRequest, required_tool: str) -> List[str]:\n''',
        "API_METADATA_STREAM_PATCH",
    )

    replace_once(
        API,
        b'''    summary = summarize_responses_sse(chunks)\n    write_trace_attempt(\n        trace_id=trace_id,\n        attempt=1,\n        request_summary=summarize_responses_request(body),\n        response_summary=summary,\n        full_request=body,\n        raw_sse="".join(chunks),\n    )\n''',
        b'''    summary = summarize_responses_sse(chunks)\n    summary["request_kind"] = "agent_turn"\n    write_trace_attempt(\n        trace_id=trace_id,\n        attempt=1,\n        request_summary=_summary_with_request_kind(\n            body,\n            request_kind="agent_turn",\n        ),\n        response_summary=summary,\n        full_request=body,\n        raw_sse="".join(chunks),\n    )\n''',
        "API_AGENT_TRACE_PATCH",
    )

    replace_once(
        API,
        b'''        response_summary = summarize_responses_sse(buffered)\n        names = response_summary.get("function_call_names") or []\n''',
        b'''        response_summary = summarize_responses_sse(buffered)\n        response_summary["request_kind"] = "agent_turn"\n        names = response_summary.get("function_call_names") or []\n''',
        "API_STRICT_RESPONSE_KIND_PATCH",
    )

    replace_once(
        API,
        b'''        request_summary = summarize_responses_request(current_body, required_tool)\n        request_summary["previous_response_id_present"] = bool(\n''',
        b'''        request_summary = _summary_with_request_kind(\n            current_body,\n            request_kind="agent_turn",\n            required_tool=required_tool,\n        )\n        request_summary["previous_response_id_present"] = bool(\n''',
        "API_STRICT_REQUEST_KIND_PATCH",
    )

    replace_once(
        API,
        b'''async def codex_responses_v2(\n    request: Request,\n    body: ResponsesRequest,\n    authenticated: bool = Depends(verify_auth),\n):\n    is_codex_web_tool_turn = (\n''',
        b'''async def codex_responses_v2(\n    request: Request,\n    body: ResponsesRequest,\n    authenticated: bool = Depends(verify_auth),\n):\n    prompt = _latest_user_text(body.input)\n    request_kind = classify_metadata_helper(prompt, body.text)\n    if (\n        request_kind == "metadata_helper"\n        and str(body.model or "").strip().lower() == "chatgpt"\n        and web_mode_enabled()\n        and bool(body.stream)\n    ):\n        trace_id = new_trace_id()\n        return StreamingResponse(\n            _metadata_helper_stream(body, trace_id),\n            media_type="text/event-stream",\n            headers=_stream_headers(),\n        )\n\n    is_codex_web_tool_turn = (\n''',
        "API_ROUTER_CLASSIFICATION_PATCH",
    )


def patch_route_audit() -> None:
    replace_once(
        ROUTE,
        b'''        summary = data.get("summary")\n        if not isinstance(summary, dict):\n            continue\n\n        if path.name.endswith("-request.json"):\n''',
        b'''        summary = data.get("summary")\n        if not isinstance(summary, dict):\n            continue\n        if _clean(summary.get("request_kind")) == "metadata_helper":\n            continue\n\n        if path.name.endswith("-request.json"):\n''',
        "ROUTE_IGNORE_METADATA_HELPER_PATCH",
    )


def write_test() -> None:
    content = '''import asyncio\nimport json\n\nfrom fastapi import Request\n\nfrom app.api.chat import ResponsesRequest\nfrom app.api import codex_responses_v2 as v2\nfrom app.services.codex_metadata_helper import (\n    build_metadata_json,\n    classify_metadata_helper,\n)\n\n\ndef _title_prompt(embedded: str) -> str:\n    return (\n        "Generate a concise, single-line task title of at most 36 characters and under five words where possible. "\n        "Start with an imperative verb. Capitalize only the first word unless the user's language, proper nouns, "\n        "acronyms, or code terms require otherwise. Preserve ticket references exactly. Write in the user's language. "\n        "Do not use quotes, markdown, or trailing punctuation. Do not answer the request.\\n\\n"\n        "User prompt:\\n" + embedded\n    )\n\n\ndef _text_schema():\n    return {\n        "format": {\n            "type": "json_schema",\n            "name": "thread_title",\n            "strict": True,\n            "schema": {\n                "type": "object",\n                "properties": {\n                    "title": {"type": "string", "minLength": 1, "maxLength": 36}\n                },\n                "required": ["title"],\n                "additionalProperties": False,\n            },\n        }\n    }\n\n\ndef _body(embedded: str) -> ResponsesRequest:\n    return ResponsesRequest(\n        model="chatgpt",\n        stream=True,\n        input=[\n            {\n                "type": "message",\n                "role": "user",\n                "content": [{"type": "input_text", "text": _title_prompt(embedded)}],\n            }\n        ],\n        tools=[\n            {\n                "type": "function",\n                "name": "exec_command",\n                "description": "client command",\n                "parameters": {"type": "object", "properties": {}},\n            }\n        ],\n        tool_choice="auto",\n        text=_text_schema(),\n    )\n\n\ndef test_current_codex_title_helper_is_classified_before_embedded_tool_text():\n    body = _body("You must use the local exec_command tool. Run exactly pwd.")\n    prompt = v2._latest_user_text(body.input)\n    assert classify_metadata_helper(prompt, body.text) == "metadata_helper"\n    assert v2.required_declared_tool(body) == "exec_command"\n\n\ndef test_plain_user_request_with_title_word_is_not_metadata_helper():\n    assert classify_metadata_helper("Please fix the title parser", _text_schema()) == ""\n\n\ndef test_local_metadata_json_matches_title_schema():\n    raw = build_metadata_json(_title_prompt("Fix parser tests"), _text_schema())\n    payload = json.loads(raw)\n    assert set(payload) == {"title"}\n    assert 1 <= len(payload["title"]) <= 36\n\n\ndef test_router_serves_metadata_helper_without_web_or_required_tool(monkeypatch):\n    body = _body("You must use the local exec_command tool. Run exactly pwd.")\n    monkeypatch.setattr(v2, "web_mode_enabled", lambda: True)\n    monkeypatch.setattr(\n        v2,\n        "prepare_and_verify_codex_web_mode",\n        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("web path used")),\n    )\n    captured = {}\n\n    def fake_trace(**kwargs):\n        captured.update(kwargs)\n\n    monkeypatch.setattr(v2, "write_trace_attempt", fake_trace)\n    request = Request({"type": "http", "method": "POST", "path": "/v1/responses", "headers": []})\n    response = asyncio.run(v2.codex_responses_v2(request, body, authenticated=True))\n\n    async def collect():\n        chunks = []\n        async for chunk in response.body_iterator:\n            chunks.append(chunk.decode() if isinstance(chunk, bytes) else str(chunk))\n        return "".join(chunks)\n\n    wire = asyncio.run(collect())\n    assert "event: response.completed" in wire\n    assert "function_call" not in wire\n    assert "title" in wire\n    assert captured["request_summary"]["request_kind"] == "metadata_helper"\n    assert captured["response_summary"]["request_kind"] == "metadata_helper"\n'''
    TEST.write_text(content, encoding="utf-8", newline="\n")
    print("METADATA_HELPER_TEST_WRITTEN=YES")


def static_checks() -> None:
    targets = [
        API,
        REPO / "app" / "services" / "codex_metadata_helper.py",
        ROUTE,
        TEST,
    ]
    rc, out, err = run([sys.executable, "-m", "py_compile", *[str(p) for p in targets]], timeout=45)
    print(f"PY_COMPILE_RC={rc}")
    if rc != 0:
        print((out + err)[-2500:])
        raise SystemExit("STATIC_CHECK_FAIL=py_compile")
    rc, out, err = run(["git", "diff", "--check"], timeout=30)
    print(f"GIT_DIFF_CHECK_RC={rc}")
    if rc != 0:
        print((out + err)[-2500:])
        raise SystemExit("STATIC_CHECK_FAIL=git_diff_check")
    rc, _, _ = run([sys.executable, "-m", "pytest", "--version"], timeout=30)
    if rc == 0:
        rc, out, err = run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_codex_metadata_helper_isolation.py",
                "tests/test_codex_required_tool_phrasing.py",
                "tests/test_codex_route_audit.py",
                "-q",
            ],
            timeout=180,
        )
        print(f"FOCUSED_PYTEST_RC={rc}")
        if rc != 0:
            print((out + err)[-5000:])
            raise SystemExit("STATIC_CHECK_FAIL=pytest")
    else:
        print("FOCUSED_PYTEST=SKIPPED_PYTEST_UNAVAILABLE")


def restart_uwa() -> None:
    rc, _, _ = run(["codex-uwa-stop"], timeout=45)
    print(f"UWA_STOP_RC={rc}")
    time.sleep(2)
    rc, out, err = run(["codex-uwa"], timeout=90)
    print(f"UWA_START_RC={rc}")
    if rc != 0:
        print((out + err)[-2500:])
        raise SystemExit("UWA_RESTART_FAIL")
    time.sleep(5)


def health_running_count() -> Any:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8199/health", timeout=5) as response:
            payload = json.load(response)
    except Exception:
        return "ERROR"
    manager = payload.get("request_manager") if isinstance(payload, dict) else None
    return manager.get("running_count") if isinstance(manager, dict) else None


def trace_snapshot() -> set[str]:
    if not TRACE_DIR.is_dir():
        return set()
    return {path.name for path in TRACE_DIR.glob("*.json") if path.is_file()}


def synthetic_helper_body() -> Dict[str, Any]:
    prompt = (
        "Generate a concise, single-line task title of at most 36 characters and under five words where possible. "
        "Start with an imperative verb. Capitalize only the first word unless the user's language, proper nouns, "
        "acronyms, or code terms require otherwise. Preserve ticket references exactly. Write in the user's language. "
        "Do not use quotes, markdown, or trailing punctuation. Do not answer the request.\\n\\n"
        "User prompt:\\nYou must use the local exec_command tool. Run exactly pwd."
    )
    return {
        "model": "chatgpt",
        "stream": True,
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}],
            }
        ],
        "tools": [
            {
                "type": "function",
                "name": "exec_command",
                "description": "client command",
                "parameters": {"type": "object", "properties": {}},
            }
        ],
        "tool_choice": "auto",
        "text": {
            "format": {
                "type": "json_schema",
                "name": "thread_title",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {"title": {"type": "string", "minLength": 1, "maxLength": 36}},
                    "required": ["title"],
                    "additionalProperties": False,
                },
            }
        },
    }


def live_probe() -> None:
    before_running = health_running_count()
    before_files = trace_snapshot()
    started = time.time()
    print(f"HEALTH_BEFORE_RUNNING_COUNT={before_running}")

    request = urllib.request.Request(
        "http://127.0.0.1:8199/v1/responses",
        data=json.dumps(synthetic_helper_body()).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            wire = response.read().decode("utf-8", "replace")
    except Exception as exc:
        print(f"HELPER_HTTP_ERROR={type(exc).__name__}")
        raise SystemExit("METADATA_HELPER_LIVE_FAIL=http")

    time.sleep(0.5)
    after_running = health_running_count()
    after_files = trace_snapshot()
    new_names = sorted(after_files - before_files)
    print(f"HELPER_RESPONSE_COMPLETED={'YES' if 'event: response.completed' in wire else 'NO'}")
    print(f"HELPER_FUNCTION_CALL_PRESENT={'YES' if 'function_call' in wire else 'NO'}")
    print(f"HELPER_TITLE_PRESENT={'YES' if 'title' in wire else 'NO'}")
    print(f"HEALTH_AFTER_RUNNING_COUNT={after_running}")
    print(f"NEW_TRACE_FILES={len(new_names)}")

    request_kinds = []
    for name in new_names:
        path = TRACE_DIR / name
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict) or payload.get("mode") != "metadata":
            continue
        summary = payload.get("summary")
        if isinstance(summary, dict):
            request_kinds.append(str(summary.get("request_kind") or ""))
    print("NEW_TRACE_REQUEST_KINDS=" + ",".join(sorted(set(request_kinds))))

    spec = importlib.util.spec_from_file_location("h3_route_audit", ROUTE)
    if spec is None or spec.loader is None:
        raise SystemExit("METADATA_HELPER_LIVE_FAIL=route_import")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    activity = module.scan_wire_activity(TRACE_DIR, since_epoch=started)
    print(f"ROUTE_AGENT_REQUEST_COUNT_AFTER_HELPER={activity.request_count}")
    print(f"ROUTE_AGENT_RESPONSE_COUNT_AFTER_HELPER={activity.response_count}")

    passed = (
        "event: response.completed" in wire
        and "function_call" not in wire
        and "title" in wire
        and before_running in (0, None)
        and after_running in (0, None)
        and "metadata_helper" in request_kinds
        and activity.request_count == 0
        and activity.response_count == 0
    )
    print(f"H3_METADATA_HELPER_ISOLATION={'PASS' if passed else 'FAIL'}")
    if not passed:
        raise SystemExit("METADATA_HELPER_LIVE_FAIL=assertions")


def commit_and_push() -> None:
    expected = [
        "app/api/codex_responses_v2.py",
        "tools/codex_route_audit.py",
        "tests/test_codex_metadata_helper_isolation.py",
    ]
    rc, out, _ = run(["git", "status", "--porcelain"], timeout=20)
    paths = []
    for line in out.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    print("CHANGED_PATHS=" + ",".join(paths))
    unexpected = sorted(set(paths) - set(expected))
    if rc != 0 or unexpected:
        print("UNEXPECTED_PATHS=" + ",".join(unexpected))
        raise SystemExit("GIT_FAIL=unexpected_changes")

    rc, _, err = run(["git", "add", "app/api/codex_responses_v2.py", "tools/codex_route_audit.py"], timeout=30)
    if rc != 0:
        print(err[-1200:])
        raise SystemExit("GIT_FAIL=add")
    rc, _, err = run(["git", "add", "-f", "tests/test_codex_metadata_helper_isolation.py"], timeout=30)
    if rc != 0:
        print(err[-1200:])
        raise SystemExit("GIT_FAIL=add_test")

    rc, out, err = run(["git", "commit", "-m", "Isolate Codex metadata helper turns"], timeout=60)
    print(f"GIT_COMMIT_RC={rc}")
    if rc != 0:
        print((out + err)[-2500:])
        raise SystemExit("GIT_FAIL=commit")
    rc, out, err = run(["git", "push", "origin", BRANCH], timeout=120)
    print(f"GIT_PUSH_RC={rc}")
    if rc != 0:
        print((out + err)[-2500:])
        raise SystemExit("GIT_FAIL=push")
    rc, head, _ = run(["git", "rev-parse", "HEAD"], timeout=20)
    if rc == 0:
        print("PUSHED_HEAD=" + head.strip())


def main() -> int:
    print("H3_METADATA_HELPER_REPAIR_BEGIN")
    require_clean_branch()
    patch_api()
    patch_route_audit()
    write_test()
    static_checks()
    restart_uwa()
    live_probe()
    commit_and_push()
    print("H3_METADATA_HELPER_REPAIR=PASS_LIVE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
