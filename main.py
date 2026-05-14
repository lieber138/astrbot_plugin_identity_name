from __future__ import annotations
from typing import Any

# 兼容性导入
try:
    from astrbot.api.plugin import Star
except ImportError:
    class Star: pass

class IdentityNamePlugin(Star):
    """强制身份注入插件：彻底杜绝数字 ID。"""

    def __init__(self, context: Any = None, **kwargs) -> None:
        super().__init__()
        self.context = context

    def _pick_first(self, obj: dict[str, Any], keys: list[str]) -> Any:
        for key in keys:
            if key in obj and obj[key] not in (None, "", "null"):
                return obj[key]
        return None

    async def before_llm_request(self, session: Any, messages: list[dict[str, str]], event: Any) -> list[dict[str, str]]:
        # 获取事件数据
        data = getattr(event, "__dict__", {}) if not isinstance(event, dict) else event
        
        # 1. 强制提取名字
        name = self._pick_first(data, ["sender_name", "nickname", "sender", "user_name"])
        
        # 2. 如果没名字，取 ID 的前 4 位
        if not name:
            uid = self._pick_first(data, ["user_id", "sender_id", "uid"])
            name = f"用户_{str(uid)[:4]}" if uid else "访客"

        # 3. 构造极高权重的身份指令
        # 明确禁止它提到那串 3907 开头的数字
        identity_instr = (
            f"【系统层级约束】当前用户的真实名字是: {name}。\n"
            f"请在对话中称呼对方为 {name}。严禁在回复中出现任何 QQ 号、数字 ID 或“3907203281”字样。"
        )

        # 4. 插入到消息列表的最前端
        messages.insert(0, {"role": "system", "content": identity_instr})

        return messages
