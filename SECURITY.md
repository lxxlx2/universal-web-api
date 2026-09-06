# Security Policy for UWA Codex Web Bridge

This repository is public. Treat every committed file, issue, pull request, screenshot, workflow log, and artifact as public information.

The repository retains its existing license and Git history. The rules below describe the current Codex Web Bridge security boundary.

## Intended trust boundary

The hardened workflow is designed for a single-user local machine:

```text
Codex Desktop
  -> 127.0.0.1:8199
  -> UWA
  -> controlled Chromium profile
  -> signed-in ChatGPT Web
```

Local coding tools such as shell commands and file operations execute inside the Codex client permission model. The browser page does not receive direct unrestricted filesystem execution.

## Safe defaults

Keep these defaults unless there is a reviewed reason to change them:

- `APP_HOST=127.0.0.1`
- `APP_DEBUG=false`
- `CORS_ENABLED=false`
- `CMD_ALLOW_UNSAFE_PYTHON_COMMANDS=false`
- `AUTO_UPDATE_ENABLED=false`
- `UWAPI_ALLOW_REMOTE=false`
- use a dedicated controlled browser profile
- keep Codex sandbox and approval controls enabled for normal work

The API port is normally `8199`. The Chromium DevTools port is normally `9222`.

### DevTools port

Port `9222` can control the signed-in browser session. Never publish, forward, tunnel, or expose it to the LAN or public internet. Restrict it to loopback.

### Remote API access

The hardened launcher rejects unsafe non-loopback binding unless explicit safeguards are configured. If remote access is ever required, use a private trusted network, strong independent API and dashboard tokens, explicit CORS origins, TLS where appropriate, and host firewall rules. Do not expose this project as an unauthenticated public service.

## Data that must never be committed

Do not commit or upload:

- `.env` files containing credentials or private endpoints
- API keys, bearer tokens, passwords, cookies, session tokens, recovery codes, or OAuth material
- browser profile directories
- browser local storage or exported cookies
- raw Codex/UWA request logs containing source code or prompts
- private chat transcripts
- local request history and command-result stores
- runtime SQLite databases containing Responses state
- screenshots that reveal tokens, account identifiers, private repository content, private chat content, or filesystem secrets
- generated archives or workflow artifacts that contain any of the above

The repository `.gitignore` excludes known local runtime and browser state. Ignore rules are only a guardrail. Review `git status` and the actual diff before every push.

## Private Codex continuation database

The Codex route can persist `previous_response_id` snapshots locally so UWA process restarts do not automatically destroy short-term thread continuity.

Default location:

```text
~/.uwa/codex_responses.sqlite3
```

It may contain:

- prompts
- source-code snippets
- tool arguments
- tool output
- assistant messages

Default policy:

```text
retention            7 days
max entries          4096
max record size      8 MiB
parent permissions   0700 where supported
DB/WAL/SHM mode      0600 where supported
```

The database is private runtime data. Never move it into the repository, attach it to an issue, upload it as a CI artifact, or use it as public debugging evidence.

To remove persisted Codex continuation data, stop UWA first and delete the local database files:

```bash
codex-uwa-stop
rm -f ~/.uwa/codex_responses.sqlite3 \
      ~/.uwa/codex_responses.sqlite3-wal \
      ~/.uwa/codex_responses.sqlite3-shm
```

This removes the SQLite fallback. Process-local in-memory state disappears when UWA is stopped.

## If a secret is exposed

1. Revoke or rotate the credential immediately.
2. Remove the sensitive file or value from the current branch.
3. Remove it from Git history when practical, especially for credentials or session material.
4. Invalidate affected browser sessions when cookies or profile data were exposed.
5. Review GitHub Actions logs and artifacts for copies.
6. Assume public-repository data may already have been copied.

Deleting the latest commit alone does not make an exposed secret safe.

## Browser account isolation

Use a dedicated Chromium profile for UWA. Avoid reusing a daily browser profile that contains unrelated accounts, extensions, saved passwords, or browsing data.

Temporary Chat is requested by the bridge, but current ChatGPT DOM does not expose that state consistently enough to make it a hard dependency. Treat account-level personalization/memory as outside the project state model. Project correctness must come from Codex thread history, local runtime continuation, files, tests, Git, and tracked checkpoint docs.

## Codex local execution safety

The model can propose local commands through client tools. Treat model-generated commands as untrusted proposals until the Codex client applies its sandbox and approval policy.

For routine work, prefer a workspace-scoped sandbox and interactive approval for operations that need broader access. Avoid combining an experimental web-model bridge with unrestricted filesystem access and a never-ask approval policy.

The UWA tool-repair layer only converts a model decision into a client tool request. It does not execute the command itself and must never bypass Codex permission checks.

## Project continuity safety

Long-term project progress must be reconstructable without private chat logs or the local continuation DB. Keep implementation decisions and verified milestones in tracked project files:

- `README.md`
- `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
- `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md`
- `docs/CODEX_WEB_BRIDGE_PROGRESS.md`

These files must contain only public-safe technical state and synthetic examples.

## Updates and supply chain

Automatic self-update is disabled in the hardened workflow. Review dependency and inherited-code changes before merging or upgrading, especially changes that touch browser startup, command execution, updater logic, authentication, network binding, or profile handling.

Use trusted package indexes. Review dependency changes before installation when possible.

## Public bug reports

When reporting a problem, include only the minimum required information. Redact:

- tokens and cookies
- private source code
- private repository names when sensitive
- local usernames and home-directory paths when unnecessary
- chat text unrelated to the bug
- account email addresses and identifiers

Prefer synthetic reproduction files and the generated acceptance workspace over real project data.

## Current project status

The core Codex Desktop read/edit/test tool loop has passed real macOS acceptance, including the Stage A multi-file scenario. Restart continuity and advanced tools remain under active validation. See `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md` for the current milestone and `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md` for the test matrix.
