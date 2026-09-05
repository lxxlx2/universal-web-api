# Security hardening for lxxlx2/universal-web-api

This fork keeps the upstream browser bridge and API compatibility intact while
placing a security gate in front of the upstream launcher.

## What changed

- The original upstream `start.py` is preserved verbatim as `start_upstream.py`.
- The fork's `start.py` validates security settings first and then delegates to
  the upstream launcher.
- Local binding defaults to `127.0.0.1:8199`.
- CORS, debug mode, proxying, scheduled restart, profile cleanup, and upstream
  auto-update default to disabled.
- `CMD_ALLOW_UNSAFE_PYTHON_COMMANDS=true` is rejected.
- Dependency fallback uses official PyPI.
- The controlled browser uses the project-local `chrome_profile` by default.
- Non-loopback binding is rejected unless remote access is explicitly enabled
  and both API and dashboard authentication use strong, separate tokens.
- Wildcard CORS is rejected whenever CORS is enabled.

## Recommended local mode

For Codex CLI on the same Mac, keep the defaults:

```env
APP_HOST=127.0.0.1
APP_PORT=8199
AUTH_ENABLED=false
CORS_ENABLED=false
CMD_ALLOW_UNSAFE_PYTHON_COMMANDS=false
AUTO_UPDATE_ENABLED=false
```

Start with:

```bash
python3 start.py
```

The API base URL remains:

```text
http://127.0.0.1:8199/v1
```

This preserves upstream `/v1/chat/completions`, `/v1/responses`,
`/v1/messages`, streaming, routing, browser automation, and tool-calling logic.

## Controlled remote mode

Use this only for a trusted private network such as Tailscale. The launcher will
refuse non-loopback binding unless all required controls are present.

```env
APP_HOST=0.0.0.0
UWAPI_ALLOW_REMOTE=true

AUTH_ENABLED=true
AUTH_TOKEN=<at least 32 random characters>

DASHBOARD_AUTH_ENABLED=true
DASHBOARD_AUTH_TOKEN=<different token, at least 32 random characters>

APP_DEBUG=false
CORS_ENABLED=false
CMD_ALLOW_UNSAFE_PYTHON_COMMANDS=false
```

Do not expose Chromium DevTools port `9222`, browser profile files, cookies, or
logs through port forwarding or a public tunnel.

## Upstream updates

Automatic upstream updates are disabled by default because an updater can
replace executable code. Prefer reviewing and manually syncing upstream changes.

If you intentionally enable the upstream updater, both flags are required:

```env
AUTO_UPDATE_ENABLED=true
UWAPI_ALLOW_UPSTREAM_AUTO_UPDATE=true
```

After any upstream sync, verify that `start.py` is still the hardened wrapper
and that the upstream launcher remains in `start_upstream.py`.
