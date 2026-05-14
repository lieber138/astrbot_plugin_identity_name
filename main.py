from __future__ import annotations
from typing import Any

# 尝试从 API 导入基类，如果失败则使用最基础的 object
try:
    from astrbot.api.plugin import Star
except ImportError:
    class Star: pass

class IdentityNamePlugin(Star):
    """AstrBot 插件：在 LLM 聊天前注入稳定身份锚点。"""

    def __init__(self, context: Any = None, **kwargs) -> None:
        # 移除 super().__init__(context) 中的参数以修复 object.__init__ 错误
        super().__init__()
        self.context = context

    def _pick_first(self, obj: dict[str, Any], keys: list[str]) -> Any:
        for key in keys:
            if key in obj and obj[key] not in (None, ""):
                return obj[key]
        return None

    def _extract_identity(self, event: Any) -> dict[str, str] | None:
        # 自动识别平台、用户ID和会话ID
        data = getattr(event, "__dict__", {}) if not isinstance(event, dict) else event
        platform = self._pick_first(data, ["platform", "adapter", "source"])
        user_id = self._pick_first(data, ["user_id", "sender_id", "uid"])
        
        if not user_id: return None

        return {
            "platform": str(platform or "unknown"),
            "user_id": str(user_id),
            "session_key": f"{platform}:{user_id}"
        }

    async def before_llm_request(self, session: Any, messages: list[dict[str, str]], event: Any) -> list[dict[str, str]]:
        """在请求 LLM 前自动注入身份锚点。"""
        identity = self._extract_identity(event)
        if not identity:
            return messages

        system_prompt = (
            f"【身份锚点注入】当前用户: {identity['user_id']} (平台: {identity['platform']})。 "
            "请严格基于此身份提供回复，确保对话上下文的独立性。"
        )

        return [{"role": "system", "content": system_prompt}, *messages]
