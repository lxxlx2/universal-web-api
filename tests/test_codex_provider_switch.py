from pathlib import Path

from tools.codex_provider_switch import (
    official_text,
    switch_to_official,
    top_level_status,
    write_official,
)


def test_official_text_removes_only_top_level_provider_model_pins():
    source = '''model_provider = "uwa"\nmodel = "gpt-5.6-sol"\nmodel_reasoning_effort = "high"\napproval_policy = "on-request"\n\n[model_providers.uwa]\nname = "UWA"\nbase_url = "http://127.0.0.1:8199/v1"\n\n[profiles.keep]\nmodel = "profile-model"\n'''

    updated = official_text(source)

    assert 'model_provider = "uwa"' not in updated
    assert 'model = "gpt-5.6-sol"' not in updated
    assert 'model_reasoning_effort = "high"' not in updated
    assert 'approval_policy = "on-request"' in updated
    assert '[model_providers.uwa]' in updated
    assert 'base_url = "http://127.0.0.1:8199/v1"' in updated
    assert '[profiles.keep]' in updated
    assert 'model = "profile-model"' in updated


def test_write_official_backs_up_before_modifying(tmp_path: Path):
    path = tmp_path / "config.toml"
    source = 'model_provider = "uwa"\nmodel = "gpt-5.6-sol"\n\n[model_providers.uwa]\nname = "UWA"\n'
    path.write_text(source, encoding="utf-8")

    backup, changed = write_official(path)

    assert changed is True
    assert backup is not None
    assert backup.exists()
    assert backup.read_text(encoding="utf-8") == source
    assert top_level_status(path.read_text(encoding="utf-8")) == {}
    assert '[model_providers.uwa]' in path.read_text(encoding="utf-8")


def test_write_official_is_idempotent_when_no_top_level_pins(tmp_path: Path):
    path = tmp_path / "config.toml"
    source = 'approval_policy = "on-request"\n\n[model_providers.uwa]\nname = "UWA"\n'
    path.write_text(source, encoding="utf-8")

    backup, changed = write_official(path)

    assert changed is False
    assert backup is None
    assert path.read_text(encoding="utf-8") == source


def test_switch_to_official_automates_quit_stop_restore_cleanup_and_reopen(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text(
        'model_provider = "uwa"\n'
        'model = "chatgpt"\n'
        'model_reasoning_effort = "high"\n'
        'approval_policy = "on-request"\n\n'
        '[model_providers.uwa]\n'
        'name = "UWA"\n',
        encoding="utf-8",
    )

    events: list[str] = []

    def quit_fn() -> list[str]:
        events.append("quit_desktop")
        return ["ChatGPT"]

    def stop_fn() -> list[int]:
        events.append("stop_uwa")
        return [12345]

    def restore_fn(config_path: Path) -> None:
        assert config_path == path
        events.append("restore_memories")
        text = config_path.read_text(encoding="utf-8")
        config_path.write_text(text + '\n[memories]\nuse_memories = true\n', encoding="utf-8")

    def open_fn() -> str:
        events.append("open_desktop")
        return "ChatGPT"

    backup, changed, stopped_apps, stopped_pids, reopened = switch_to_official(
        path,
        quit_fn=quit_fn,
        stop_fn=stop_fn,
        restore_fn=restore_fn,
        open_fn=open_fn,
    )

    assert events == [
        "quit_desktop",
        "stop_uwa",
        "restore_memories",
        "open_desktop",
    ]
    assert changed is True
    assert backup is not None
    assert stopped_apps == ["ChatGPT"]
    assert stopped_pids == [12345]
    assert reopened == "ChatGPT"

    updated = path.read_text(encoding="utf-8")
    assert top_level_status(updated) == {}
    assert 'approval_policy = "on-request"' in updated
    assert '[model_providers.uwa]' in updated
    assert '[memories]' in updated
    assert 'use_memories = true' in updated


def test_switch_to_official_can_skip_desktop_and_uwa_automation(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text('model_provider = "uwa"\n', encoding="utf-8")

    calls: list[str] = []

    def forbidden_quit() -> list[str]:
        calls.append("quit")
        raise AssertionError("desktop quit should be skipped")

    def forbidden_stop() -> list[int]:
        calls.append("stop")
        raise AssertionError("UWA stop should be skipped")

    def restore_fn(config_path: Path) -> None:
        calls.append("restore")

    def forbidden_open() -> str:
        calls.append("open")
        raise AssertionError("desktop open should be skipped")

    _, changed, stopped_apps, stopped_pids, reopened = switch_to_official(
        path,
        automate_desktop=False,
        automate_uwa_stop=False,
        quit_fn=forbidden_quit,
        stop_fn=forbidden_stop,
        restore_fn=restore_fn,
        open_fn=forbidden_open,
    )

    assert changed is True
    assert calls == ["restore"]
    assert stopped_apps == []
    assert stopped_pids == []
    assert reopened == "SKIPPED"
    assert top_level_status(path.read_text(encoding="utf-8")) == {}
