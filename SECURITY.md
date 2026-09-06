# Security Policy for the hardened Codex web-bridge fork

This repository is public. Treat every committed file, issue, pull request, screenshot, workflow log, and artifact as public information.

This fork is based on [`lumingya/universal-web-api`](https://github.com/lumingya/universal-web-api). Thanks to the original author and contributors. The additional security rules below cover this fork's local Codex Desktop browser-bridge workflow and do not replace the upstream project's own guidance.

## Intended trust boundary

The hardened workflow is designed for a single-user local machine:

```text
Codex Desktop
  -> 127.0.0.1:8199
  -> Universal Web API
  -> controlled Chromium profile
  -> signed-in web AI page
```

Local coding tools such as shell commands and file operations must execute inside the Codex client permission model. The browser page and UWA must not be given direct unrestricted filesystem execution merely to make tool calling easier.

## Safe defaults

Keep these defaults unless you have a reviewed reason to change them:

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
- `chrome_profile/` or any other browser profile directory
- browser local storage or exported cookies
- raw Codex/UWA request logs containing source code or prompts
- chat transcripts containing private material
- local request history and command-result stores
- runtime SQLite databases containing Responses state
- screenshots that reveal tokens, account identifiers, private repository content, private chat content, or filesystem secrets
- generated archives or workflow artifacts that contain any of the above

The repository `.gitignore` intentionally excludes known local runtime and browser state. Ignore rules are only a guardrail. Review `git status` and the actual diff before every push.

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

A normal signed-in web AI conversation may use the site's account history, personalization, or memory features. Coding-agent traffic may also create visible chat history. A Temporary Chat style workflow is being investigated for stronger isolation. Until it is implemented and tested, users should assume normal account behavior can apply.

## Codex local execution safety

The model can propose local commands through client tools. Treat model-generated commands as untrusted proposals until the Codex client applies its sandbox and approval policy.

For routine work, prefer a workspace-scoped sandbox and interactive approval for operations that need broader access. Avoid combining an experimental web-model bridge with unrestricted filesystem access and a never-ask approval policy.

The UWA tool-repair layer only converts a model decision into a client tool request. It does not execute the command itself and must never bypass Codex permission checks.

## Persistent conversation state

Future Responses-state persistence may contain source code, prompts, tool outputs, and conversation history. If enabled later, it must:

- stay local by default
- use a Git-ignored path
- have bounded retention
- use restrictive filesystem permissions where supported
- avoid storing secrets unnecessarily
- provide a clear deletion path

Persistent state should be treated as sensitive local application data.

## Updates and supply chain

Automatic upstream self-update is disabled in the hardened workflow. Review upstream changes before merging or upgrading, especially changes that touch browser startup, command execution, updater logic, authentication, network binding, or profile handling.

Use trusted package indexes. Review dependency changes before installation when possible.

## Public bug reports

When reporting a problem, include only the minimum required information. Redact:

- tokens and cookies
- private source code
- private repository names when sensitive
- local usernames and home-directory paths when unnecessary
- chat text unrelated to the bug
- account email addresses and identifiers

Prefer synthetic reproduction files such as a small `calc.py` over real project data.

## Current project status

Codex Desktop inference through the browser bridge is experimental. Core local coding tool round-trips are under active compatibility testing. See [`docs/CODEX_WEB_BRIDGE_PROGRESS.md`](./docs/CODEX_WEB_BRIDGE_PROGRESS.md) for the current milestone, verified capabilities, and known gaps.
