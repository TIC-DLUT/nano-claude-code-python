import json
from typing import Any

from claude.client import ClaudeClient
from claude.message import (
    CLAUDE_MESSAGE_ROLE_ASSISTANT,
    CallRequest,
    Message,
    TextBlock,
)
from errors.errors import ClaudeClientError


def deal_func(m: Message) -> bool:
    print(m.content.text)
    return True


class ChatModel(ClaudeClient):
    def __init__(self, model: str, messages: list[Message] = None, stream: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.messages = messages or []
        self.model = model
        self.stream = stream
        self.body = CallRequest(
            model=self.model, messages=self.messages, stream=self.stream
        ).__dict__

    def chat(self) -> str:
        """
        向 Claude API 发送聊天消息并返回响应。
        """
        response = self._session.post(
            url=f"{self.base_url}/v1/messages",
            json=self.body,
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]


class StreamableChatModel(ChatModel):
    def __init__(self, model: str, messages: list[Message] = None, stream: bool = True, **kwargs):
        super().__init__(model=model, messages=messages, stream=stream, **kwargs)

    def chat(self):
        """
        向 Claude API 发送聊天消息并以流式方式返回响应。
        """
        response_body = self._session.post(
            url=f"{self.base_url}/v1/messages",
            json=self.body,
        )
        res_message: list[Message] = []
        try:
            for line in response_body.iter_lines():
                if not line:
                    continue

                line_str = line.decode("utf-8")

                if line_str.startswith("data:"):
                    data_json = line_str[6:]
                    data_dict = json.loads(data_json)

                    event_type = data_dict.get("type", "type_not_found")

                    if event_type == "content_block_start":
                        res_message.append(Message(role=CLAUDE_MESSAGE_ROLE_ASSISTANT, content=""))
                        content: Any = None
                        content_block = data_dict.get("content_block", "no_content_block")
                        text_value = content_block.get("text", "no_text")
                        if text_value is not None:
                            content = TextBlock(type="text", text=text_value)

                        res_message[-1].content = content
                    elif event_type == "content_block_delta":
                        continue_flag = True
                        if isinstance(res_message[-1].content, TextBlock):
                            res_message[-1].content = TextBlock(
                                type="text",
                                text=res_message[-1].content.text
                                + data_dict.get("delta", "no_delta").get("text", "no_text"),
                            )
                            continue_flag = deal_func(
                                Message(
                                    role=CLAUDE_MESSAGE_ROLE_ASSISTANT,
                                    content=TextBlock(
                                        type="text",
                                        text=data_dict.get("delta").get("text"),
                                    ),
                                )
                            )

                        if not continue_flag:
                            break

        except Exception as e:
            raise ClaudeClientError(f"Error while streaming response: {str(e)}")

        finally:
            response_body.close()


if __name__ == "__main__":
    print("正在测试 StreamableChatModel...")
    test_client = StreamableChatModel(
        base_url="https://api.phsharp.com",
        model="claude-haiku-4-5",
        messages=[{"role": "user", "content": "你好！"}],
    )
    print(f"api_key:{test_client.api_key},base_url:{test_client.base_url}")
    test_client.chat()
