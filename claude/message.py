from dataclasses import dataclass

CLAUDE_MESSAGE_ROLE_USER = "user"
CLAUDE_MESSAGE_ROLE_ASSISTANT = "assistant"


@dataclass
class Message:
    role: str
    content: str


@dataclass
class TextBlock:
    text: str
    type: str = "text"


@dataclass
class CallRequest:
    model: str
    messages: list[Message]
    stream: bool = False


@dataclass
class CallResponse:
    id: str
    content: list[Message]
    model: str


class MessageManager:
    def __init__(self):
        self.history: list[Message] = []

    def add_user_message(self, content: str):
        self.history.append(Message(role=CLAUDE_MESSAGE_ROLE_USER, content=content))

    def add_assistant_message(self, content: str):
        self.history.append(Message(role=CLAUDE_MESSAGE_ROLE_ASSISTANT, content=content))

    def get_history(self) -> list[Message]:
        return self.history
