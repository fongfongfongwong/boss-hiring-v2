"""System settings API routes – read/write LLM configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from dotenv import dotenv_values, set_key
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/settings", tags=["settings"])

ENV_PATH = Path(__file__).parent.parent.parent / ".env"

# Known LLM providers and their models
PROVIDERS = [
    {
        "id": "kimi",
        "name": "Kimi (Moonshot)",
        "base_url": "https://api.moonshot.cn/v1",
        "models": [
            {"id": "moonshot-v1-128k", "name": "Moonshot v1 128K", "context": "128K"},
            {"id": "moonshot-v1-32k", "name": "Moonshot v1 32K", "context": "32K"},
            {"id": "moonshot-v1-8k", "name": "Moonshot v1 8K", "context": "8K"},
        ],
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "models": [
            {"id": "deepseek-chat", "name": "DeepSeek Chat (V3)", "context": "64K"},
            {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner (R1)", "context": "64K"},
        ],
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o", "context": "128K"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context": "128K"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context": "128K"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context": "16K"},
        ],
    },
    {
        "id": "claude",
        "name": "Claude (Anthropic)",
        "base_url": "https://api.anthropic.com/v1",
        "models": [
            {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "context": "200K"},
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "context": "200K"},
            {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "context": "200K"},
        ],
    },
    {
        "id": "qwen",
        "name": "通义千问 (Qwen)",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": [
            {"id": "qwen-max", "name": "Qwen Max", "context": "32K"},
            {"id": "qwen-plus", "name": "Qwen Plus", "context": "128K"},
            {"id": "qwen-turbo", "name": "Qwen Turbo", "context": "128K"},
        ],
    },
    {
        "id": "zhipu",
        "name": "智谱 (GLM)",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": [
            {"id": "glm-4-plus", "name": "GLM-4 Plus", "context": "128K"},
            {"id": "glm-4", "name": "GLM-4", "context": "128K"},
            {"id": "glm-4-flash", "name": "GLM-4 Flash", "context": "128K"},
        ],
    },
    {
        "id": "custom",
        "name": "自定义 (OpenAI 兼容)",
        "base_url": "",
        "models": [],
    },
]


class SettingsUpdate(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


@router.get("")
def get_settings() -> dict[str, Any]:
    """Read current LLM settings from .env file."""
    env = dotenv_values(str(ENV_PATH))

    api_key = env.get("OPENAI_API_KEY", "")
    base_url = env.get("OPENAI_BASE_URL", "")
    model = env.get("OPENAI_MODEL", "")

    # Mask API key for display
    masked_key = ""
    if api_key:
        masked_key = api_key[:6] + "****" + api_key[-4:] if len(api_key) > 10 else "****"

    # Detect current provider from base_url
    current_provider = "custom"
    for p in PROVIDERS:
        if p["base_url"] and base_url and p["base_url"].rstrip("/") == base_url.rstrip("/"):
            current_provider = p["id"]
            break

    # Check Boss Zhipin login status
    profile_dir = Path(__file__).parent.parent.parent / "data" / "chrome_profile_pw"
    boss_logged_in = profile_dir.exists() and any(profile_dir.iterdir()) if profile_dir.exists() else False

    return {
        "api_key_masked": masked_key,
        "has_api_key": bool(api_key),
        "base_url": base_url,
        "model": model,
        "current_provider": current_provider,
        "boss_logged_in": boss_logged_in,
    }


@router.get("/providers")
def get_providers() -> list[dict[str, Any]]:
    """Return the list of supported LLM providers and their models."""
    return PROVIDERS


@router.put("")
def update_settings(req: SettingsUpdate) -> dict[str, str]:
    """Update LLM settings in the .env file."""
    # Ensure .env exists
    if not ENV_PATH.exists():
        ENV_PATH.write_text("")

    if req.api_key is not None and req.api_key.strip():
        set_key(str(ENV_PATH), "OPENAI_API_KEY", req.api_key.strip())

    if req.base_url is not None:
        set_key(str(ENV_PATH), "OPENAI_BASE_URL", req.base_url.strip())

    if req.model is not None:
        set_key(str(ENV_PATH), "OPENAI_MODEL", req.model.strip())

    # Reload the LLM client with new settings
    try:
        import utils.llm_client as llm_module
        from dotenv import load_dotenv
        load_dotenv(str(ENV_PATH), override=True)
        llm_module.llm = llm_module.LLMClient()
    except Exception:
        pass

    return {"status": "saved"}


@router.post("/test")
def test_connection() -> dict[str, Any]:
    """Test the current LLM API connection."""
    try:
        from utils.llm_client import llm
        result = llm.chat("你是一个助手", "请回复：连接成功", temperature=0.1, max_tokens=20)
        return {"success": True, "response": result, "model": llm.model}
    except Exception as e:
        return {"success": False, "error": str(e)}
