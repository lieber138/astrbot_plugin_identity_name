from __future__ import annotations
from typing import Any

# 尝试从 API 导入基类，增强兼容性
try:
    from astrbot.api.plugin import Star
except ImportError:
    class Star: pass

class IdentityNamePlugin(Star):
    """AstrBot 插件：识别用户昵称并注入身份锚点，不带 QQ 号。"""

    def __init__(self, context: Any = None, **kwargs) -> None:
        super().__init__()
        self.context = context

    def _pick_first(self, obj: dict[str, Any], keys: list[str]) -> Any:
        for key in keys:
            if key in obj and obj[key] not in (None, "", "null"):
                return obj[key]
        return None

    def _extract_identity(self, event: Any) -> dict[str, str] | None:
        # 获取事件数据字典
        data = getattr(event, "__dict__", {}) if not isinstance(event, dict) else event
        
        # 1. 核心修改：优先提取昵称/名字字段，避开纯数字 ID
        user_name = self._pick_first(data, ["sender_name", "nickname", "sender", "user_name"])
        
        # 2. 提取必要的 ID 供后台识别（不给 AI 看）
        platform = self._pick_first(data, ["platform", "adapter", "source"])
        user_id = self._pick_first(data, ["user_id", "sender_id", "uid"])
        
        if not user_id: return None

        # 如果实在找不到昵称，才显示 ID 的前 4 位作为代称
        display_name = str(user_name) if user_name else f"用户_{str(user_id)[:4]}"

        return {
            "platform": str(platform or "unknown"),
            "user_id": str(user_id),
            "user_name": display_name # 这个是给 AI 称呼用的名字
        }

    async def before_llm_request(self, session: Any, messages: list[dict[str, str]], event: Any) -> list[dict[str, str]]:
        """在请求 LLM 前自动注入身份锚点。"""
        identity = self._extract_identity(event)
        if not identity:
            return messages

        # 构建 System Prompt，明确告知 AI 对方的名字
        system_prompt = (
            f"【身份环境确认】当前对话方的名字是: {identity['user_name']}。 "
            f"请在回复中称呼对方为 {identity['user_name']}，并基于此身份维持对话逻辑。"
        )

        return [{"role": "system", "content": system_prompt}, *messages]
