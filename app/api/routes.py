"""
app/api/routes.py - API 路由聚合入口

职责：
- 聚合所有子路由模块
- 保持向后兼容（外部仍使用 from app.api.routes import router）
"""

from fastapi import APIRouter

from app.api.codex_compat import router as codex_compat_router
from app.api.codex_responses_v2 import router as codex_responses_v2_router
from app.api.codex_responses import router as codex_responses_router
from app.api.chat import router as chat_router
from app.api.anthropic_routes import router as anthropic_router
from app.api.config_routes import router as config_router
from app.api.system import router as system_router
from app.api.tab_routes import router as tab_router
from app.api.cmd_routes import router as cmd_router
from app.api.browser_routes import router as browser_router
from app.api.provider import router as provider_router
from app.services.codex_required_tool_language_patch import (
    install_codex_required_tool_language_patch,
)
from app.services.codex_workspace_refusal_language_patch import (
    install_codex_workspace_refusal_language_patch,
)
from app.services.codex_v2_runtime_hardening import install_codex_v2_runtime_hardening


install_codex_required_tool_language_patch()
install_codex_workspace_refusal_language_patch()

# Install the transport boundary after the V2 module is imported and before the
# first request can reach its router. Optional tracing/persistence/affinity
# failures must never truncate a Codex Responses HTTP body.
install_codex_v2_runtime_hardening()

router = APIRouter()

# Codex 路由顺序是协议的一部分：
# - codex_compat 负责 Codex 专用模型目录；
# - codex_responses_v2 先执行 V2 观测与“明确要求工具”协议约束；
# - codex_responses 保留已验证的 ChatGPT Web/Responses 实现作为底层；
# - 通用 chat_router 最后兜底其他 OpenAI-compatible 请求。
router.include_router(codex_compat_router)
router.include_router(codex_responses_v2_router)
router.include_router(codex_responses_router)

router.include_router(chat_router)
router.include_router(anthropic_router)
router.include_router(config_router)
router.include_router(system_router)
router.include_router(tab_router)
router.include_router(cmd_router)
router.include_router(browser_router)
router.include_router(provider_router)
