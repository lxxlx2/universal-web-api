from pathlib import Path

from tools.codex_provider_switch import official_text, top_level_status, write_official


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
