# S1 dependency audit result — 2026-09-10

## Status

S1 is `CURRENT` with the first repository-wide dependency/runtime pass green. The verified product baseline on `main` remains untouched.

Source baseline:

```text
main:a140002e65a02a3323abcde3e1fdb8674710c996
```

Audit branch:

```text
codex-standalone-s1
```

## Green first-pass evidence

The dedicated `S1 dependency audit` workflow completed successfully after the parser was made UTF-8-BOM aware.

```text
repository Python files                         292 at first green audit
bridge seed files                               23
reachable parse errors                          0
static reachable files                          143
classified bridge core                         25
provisional upstream runtime                    116
provisional support                             2
runtime import smoke                            PASS
runtime-loaded local files                      165
runtime import errors                           0
public-repository safety                        PASS
```

The detailed machine manifest is generated under private `~/.uwa/s1-audit` state. CI publishes only a sanitized path/category manifest with no prompts, cookies, browser/session identifiers, local absolute paths or tool payloads.

## Important interpretation

The 116-file `required_upstream_runtime` set is deliberately provisional. It describes the current integration tree, not the final standalone keep-set.

Two current package boundaries inflate the observed closure:

1. `app/api/__init__.py` imports the broad `app.api.routes` aggregator at package import time. That aggregator imports Codex routes together with generic chat, Anthropic, configuration, system, tab, command, browser and provider routers.
2. `app/core/parsers/__init__.py` imports and registers every built-in provider parser at package import time. Runtime smoke therefore loads many provider parsers even when the Codex/ChatGPT path did not semantically request them.

These are extraction-coupling findings. They are not regressions in the verified integrated product.

## Current S1 classification

The first-pass core contains the Codex Responses/compact adapters, ChatGPT Web mode preparation, client-tool policy, continuation/affinity/state, stream/runtime hardening, wire observability, tool-calling bridge, provider/lifecycle helpers and public-repository safety tooling.

The audit currently identifies three groups that need refinement before S1 can close:

```text
current semantic/core candidates                keep
upstream runtime reached by real bridge code    keep until disproven
import-time package/registry side effects        decouple/retest
unreachable generic Python surface               exclusion candidate
```

The sanitized manifest currently identifies dozens of Python files that are outside both the static bridge closure and runtime import smoke. These remain candidates only until non-Python assets/configuration and validation dependencies are cross-checked.

## Standalone design consequence

The standalone tree should not copy the broad integration shell unchanged merely because importing the current package triggers it. S2 should provide narrow package/router entry points and retain only the browser/workflow/config/runtime pieces demonstrated necessary by the bridge.

`app/api/chat.py` is also a major coupling point because the Codex routes reuse its Responses models/converters and Web execution worker. S1 now performs a symbol-level slice of only the chat symbols imported by the Codex routes before any shared runtime is extracted.

## Remaining S1 closure work

S1 closes only after all of the following are concrete:

```text
symbol-level shared chat runtime slice          pending final evidence
package side-effect/runtime-only classification pending final evidence
standalone validation/test keep-set             pending final evidence
external dependency keep/drop classification    pending final evidence
non-Python runtime/config asset keep-set         pending final evidence
license/provenance carry-forward set             pending final evidence
exact S2 extraction manifest                     pending
```

No file is deleted from `main` during S1.
