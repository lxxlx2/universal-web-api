"""
app/api/routes.py - API 路由聚合入口

职责：
- 聚合所有子路由模块
- 保持向后兼容（外部仍使用 from app.api.routes import router）
"""

from fastapi import APIRouter

# 导入子路由
from app.api.codex_compat import router as codex_compat_router
from app.api.codex_responses import router as codex_responses_router
from app.api.chat import router as chat_router
from app.api.anthropic_routes import router as anthropic_router
from app.api.config_routes import router as config_router
from app.api.system import router as system_router
from app.api.tab_routes import router as tab_router
from app.api.cmd_routes import router as cmd_router  # 🆕 命令系统
from app.api.browser_routes import router as browser_router
from app.api.provider import router as provider_router

# 创建主路由器
router = APIRouter()

# Codex 兼容路由必须先于通用 Chat/Responses 路由注册：
# - /v1/models?client_version=... 使用 Codex 专用模型目录
# - /v1/responses 在 chatgpt 路由上先执行网页模型/推理档位校验
router.include_router(codex_compat_router)
router.include_router(codex_responses_router)

# 聚合所有子路由
router.include_router(chat_router)
router.include_router(anthropic_router)
router.include_router(config_router)
router.include_router(system_router)
router.include_router(tab_router)
router.include_router(cmd_router)  # 🆕
router.include_router(browser_router)
router.include_router(provider_router)
