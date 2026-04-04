"""
将数据结构从 `dataclasses.dataclass` 迁移至原生 `dict` 实现。
主要动机在于提升动态属性的扩展性，并消除在高性能数据交换场景下的对象实例化开销。
此变更旨在兼顾开发灵活性与原生序列(JSON)的兼容性。
如有需求后续可重构为更复杂的类结构以支持更丰富的功能，但当前实现已满足基本的消息管理需求。
"""

from dataclasses import dataclass
from typing import Any

CLAUDE_MESSAGE_ROLE_USER = "user"
CLAUDE_MESSAGE_ROLE_ASSISTANT = "assistant"


@dataclass
class TextBlock:
    text: str
    type: str = "text"


@dataclass
class CallResponse:
    id: str
    content: list[dict[str, Any]]
    model: str


class MessageManager:
    def __init__(self):
        self.history: list[dict[str, Any]] = []

    def add_user_message(self, content: str):
        self.history.append({"role": CLAUDE_MESSAGE_ROLE_USER, "content": content})

    def add_assistant_message(self, content: str):
        self.history.append({"role": CLAUDE_MESSAGE_ROLE_ASSISTANT, "content": content})

    def get_history(self) -> list[dict[str, Any]]:
        return self.history
