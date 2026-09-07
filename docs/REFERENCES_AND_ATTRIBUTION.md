# References and attribution

This repository is a fork of `lumingya/universal-web-api` and keeps the upstream Git history and AGPL-3.0 license. The current branch focuses on a Codex Desktop / Codex CLI to ChatGPT Web bridge, while continuing to use the upstream browser-automation foundation.

We are grateful to the original Universal Web API contributors for the browser control, site abstraction and OpenAI-compatible API foundation that made this fork possible.

The V2 design also studies several public projects. The goal is to reuse proven ideas and protocol patterns rather than independently rediscover every failure mode. Unless a future commit explicitly says otherwise, the V2 code in this repository is independently implemented and does not copy source files from the projects below.

## `FlameFront-end/chatgpt-gateway`

Repository: https://github.com/FlameFront-end/chatgpt-gateway

License observed during V2 research: MIT.

Ideas studied:

- browser ChatGPT as an OpenAI-compatible gateway;
- explicit tool/function round trips through a web model;
- structured tool-call output plus parser validation;
- few-shot examples to improve web-model tool-call reliability;
- multi-turn tool-result continuation and response-completion detection.

What V2 adopts conceptually:

- a client tool call must be structurally observable; plain text that merely looks like command output is not equivalent to a function call;
- tool-call reliability should be measured by protocol evidence, not by the prose in the final assistant response.

What V2 does differently:

- Codex remains the authoritative local executor and sandbox owner;
- V2 keeps the existing UWA browser/network capture layer;
- V2 begins with a strict required-tool contract and metadata trace before changing the global XML/JSON prompting strategy.

## `lininn/codex-proxy`

Repository: https://github.com/lininn/codex-proxy

License observed during V2 research: MIT.

Ideas studied:

- a dedicated Responses protocol boundary for Codex;
- keeping request translation, response translation and SSE translation as distinct concerns;
- treating Responses compatibility as its own adapter layer instead of mixing it with provider logic.

What V2 adopts conceptually:

- Codex-specific behavior lives in a separate V2 route/guard layer before the generic UWA routes;
- the existing proven bridge remains underneath while compatibility logic becomes easier to isolate and replace.

## `mehdic/codex-proxy`

Repository: https://github.com/mehdic/codex-proxy

License observed during V2 research: MIT.

Ideas studied:

- sticky sessions with bounded TTL/LRU behavior;
- serializing concurrent requests for one logical session;
- SSE keepalive comments that do not fabricate assistant content;
- explicit separation of external caller-dispatched tools and Codex-native tools.

Planned V2 use:

- web-session affinity for one Codex agent loop;
- bounded session lifetime and queueing;
- transport keepalive without fake visible output.

These items are roadmap work and are not claimed as complete in the first V2 batch.

## OpenAI `codex-responses-api-proxy`

Source: https://github.com/openai/codex/tree/main/codex-rs/responses-api-proxy

License observed during V2 research: Apache-2.0 as part of the OpenAI Codex repository.

Ideas studied:

- strict `/v1/responses` protocol boundaries;
- paired request/response dumps for diagnosis;
- correlation IDs / deterministic filenames;
- redaction of authentication and cookie data;
- keeping debugging artifacts outside the source repository.

What V2 adopts conceptually:

- private paired Codex wire traces under `~/.uwa`;
- metadata-only tracing by default;
- explicit opt-in for full local payload capture;
- file and directory permissions intended to prevent accidental sharing.

## License and copying policy

The active repository remains governed by its existing AGPL-3.0 license.

The references above are used as design references. MIT- and Apache-2.0-licensed code can be incorporated only when the relevant license and attribution obligations are preserved. The current V2 batch intentionally implements the described behaviors independently, so there is no third-party source file copied into the branch.

If future work copies or substantially adapts a third-party source fragment, the commit and this document must identify the source file, upstream commit, license and local destination.
