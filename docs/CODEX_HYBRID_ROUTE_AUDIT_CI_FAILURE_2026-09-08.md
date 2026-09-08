# Hybrid route-audit CI failure — 2026-09-08

## Classification

The first CI run for `tools/codex_route_audit.py` did not expose a product/runtime failure. Five of six Security hardening jobs passed, including route-audit `py_compile` on Ubuntu/macOS Python 3.11/3.13.

The only failing job was `upstream-regression`, during test collection of `tests/test_codex_route_audit.py` on Python 3.13.

## Failure

The test dynamically loaded `tools/codex_route_audit.py` with `importlib.util.module_from_spec()` and `exec_module()` but did not register the module in `sys.modules` first. Python 3.13 `dataclasses` consults `sys.modules[cls.__module__]` while processing the dataclass, so collection failed with an `AttributeError` before any route-audit regression executed.

## Scope

```text
public-repo-safety                 PASS
security Ubuntu 3.11              PASS
security Ubuntu 3.13              PASS
security macOS 3.11               PASS
security macOS 3.13               PASS
route-audit py_compile            PASS
upstream regression               FAIL during test import/collection
```

No Desktop live probe was run and no provider/model route was changed.

## Next action

Register the dynamically loaded test module in `sys.modules` before `exec_module()`, then rerun complete CI. Do not proceed to the Desktop route probe until CI is green.
