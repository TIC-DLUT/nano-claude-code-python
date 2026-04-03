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
