from __future__ import annotations

import os

import pytest

from security_guard import ensure_safe_defaults, validate_runtime_security


def test_safe_defaults(monkeypatch):
    for key in (
        "APP_HOST",
        "APP_DEBUG",
        "CORS_ENABLED",
        "CMD_ALLOW_UNSAFE_PYTHON_COMMANDS",
        "AUTO_UPDATE_ENABLED",
        "PROXY_ENABLED",
        "PIP_MIRROR_URL",
    ):
        monkeypatch.delenv(key, raising=False)

    ensure_safe_defaults()

    assert os.environ["APP_HOST"] == "127.0.0.1"
    assert os.environ["APP_DEBUG"] == "false"
    assert os.environ["CORS_ENABLED"] == "false"
    assert os.environ["CMD_ALLOW_UNSAFE_PYTHON_COMMANDS"] == "false"
    assert os.environ["AUTO_UPDATE_ENABLED"] == "false"
    assert os.environ["PROXY_ENABLED"] == "false"
    assert os.environ["PIP_MIRROR_URL"] == "https://pypi.org/simple"


def test_loopback_is_allowed_without_auth():
    validate_runtime_security(
        {
            "APP_HOST": "127.0.0.1",
            "AUTH_ENABLED": "false",
            "CORS_ENABLED": "false",
            "CMD_ALLOW_UNSAFE_PYTHON_COMMANDS": "false",
            "AUTO_UPDATE_ENABLED": "false",
        }
    )


def test_unsafe_python_is_rejected_even_locally():
    with pytest.raises(RuntimeError, match="CMD_ALLOW_UNSAFE_PYTHON_COMMANDS"):
        validate_runtime_security(
            {
                "APP_HOST": "127.0.0.1",
                "CMD_ALLOW_UNSAFE_PYTHON_COMMANDS": "true",
                "AUTO_UPDATE_ENABLED": "false",
                "CORS_ENABLED": "false",
            }
        )


def test_wildcard_cors_is_rejected():
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        validate_runtime_security(
            {
                "APP_HOST": "127.0.0.1",
                "CORS_ENABLED": "true",
                "CORS_ORIGINS": "*",
                "CMD_ALLOW_UNSAFE_PYTHON_COMMANDS": "false",
                "AUTO_UPDATE_ENABLED": "false",
            }
        )


def test_remote_without_opt_in_is_rejected():
    with pytest.raises(RuntimeError, match="UWAPI_ALLOW_REMOTE"):
        validate_runtime_security(
            {
                "APP_HOST": "0.0.0.0",
                "AUTH_ENABLED": "false",
                "CORS_ENABLED": "false",
                "CMD_ALLOW_UNSAFE_PYTHON_COMMANDS": "false",
                "AUTO_UPDATE_ENABLED": "false",
            }
        )


def test_remote_hardened_configuration_is_allowed():
    validate_runtime_security(
        {
            "APP_HOST": "0.0.0.0",
            "UWAPI_ALLOW_REMOTE": "true",
            "AUTH_ENABLED": "true",
            "AUTH_TOKEN": "a" * 40,
            "DASHBOARD_AUTH_ENABLED": "true",
            "DASHBOARD_AUTH_TOKEN": "b" * 40,
            "APP_DEBUG": "false",
            "CORS_ENABLED": "false",
            "CMD_ALLOW_UNSAFE_PYTHON_COMMANDS": "false",
            "AUTO_UPDATE_ENABLED": "false",
        }
    )


def test_auto_update_needs_second_opt_in():
    with pytest.raises(RuntimeError, match="UWAPI_ALLOW_UPSTREAM_AUTO_UPDATE"):
        validate_runtime_security(
            {
                "APP_HOST": "127.0.0.1",
                "AUTO_UPDATE_ENABLED": "true",
                "UWAPI_ALLOW_UPSTREAM_AUTO_UPDATE": "false",
                "CMD_ALLOW_UNSAFE_PYTHON_COMMANDS": "false",
                "CORS_ENABLED": "false",
            }
        )
