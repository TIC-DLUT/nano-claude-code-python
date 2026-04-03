import json
from typing import Any

from claude.call_tool import Tool, ToolPropertyDetail, newTool
from claude.client import ClaudeClient
from claude.message import (
    CLAUDE_MESSAGE_ROLE_ASSISTANT,
    CLAUDE_MESSAGE_ROLE_USER,
    TextBlock,
)
from errors.errors import ClaudeClientError


# TODO:流式响应中需要重构消息这一数据结构
def deal_func(m: dict[str, Any]) -> bool:
    print(m["content"]["text"])
    return True


class ChatModel(ClaudeClient):
    def __init__(
        self,
        model: str,
        messages: list[dict[str, Any]] = None,
        stream: bool = False,
        tools: list[Tool] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.messages = messages or []
        self.model = model
        self.stream = stream
        self.tools = tools or []

    def _get_request_body(self) -> dict:
        body = {
            "model": self.model,
            "messages": self.messages,
            "stream": self.stream,
        }
        if self.tools:
            requested_tools = [tool.to_request() for tool in self.tools]
            body["tools"] = requested_tools
        return body

    def call(self) -> str:
        """
        向 Claude API 发送聊天消息并返回响应。
        """
        body = self._get_request_body()
        response_body = self._session.post(
            url=f"{self.base_url}/v1/messages",
            json=body,
        )
        response_body.raise_for_status()
        response_body_json = response_body.json()
        return response_body_json["content"]

    def chat_with_tools(self):
        """
        向 Claude API 发送聊天消息(包括工具调用)并返回响应。
        """
        while True:
            assistant_content = self.call()
            self.messages.append(
                {"role": CLAUDE_MESSAGE_ROLE_ASSISTANT, "content": assistant_content}
            )

            tool_calls = [item for item in assistant_content if item["type"] == "tool_use"]

            if not tool_calls:
                for item in assistant_content:
                    if item["type"] == "text":
                        return item["text"]
                    elif item["content"]:
                        return item["content"]
                return ""

            tool_use_result = []
            for tool_call in tool_calls:
                tool_id = tool_call["id"]
                tool_name = tool_call["name"]
                tool_input = tool_call["input"]

                target_tool = next((t for t in self.tools if t.name == tool_name), None)

                tool_result = ""
                if target_tool and target_tool.func:
                    print(f"\n正在调用工具: {tool_name}，输入: {tool_input}\n")
                    tool_result = target_tool.func(tool_input)

                tool_use_result.append(
                    {
                        "tool_use_id": tool_id,
                        "type": "tool_result",
                        "content": tool_result,
                    }
                )

            if tool_use_result:
                self.messages.append({"role": CLAUDE_MESSAGE_ROLE_USER, "content": tool_use_result})
            else:
                raise ClaudeClientError("工具调用失败，未找到匹配的工具或工具执行失败。")


class StreamableChatModel(ChatModel):
    def __init__(
        self, model: str, messages: list[dict[str, Any]] = None, stream: bool = True, **kwargs
    ):
        super().__init__(model=model, messages=messages, stream=stream, **kwargs)

    def chat(self):
        """
        向 Claude API 发送聊天消息并以流式方式返回响应。
        """
        response_body = self._session.post(
            url=f"{self.base_url}/v1/messages",
            json=self.body,
        )
        res_message: list[dict[str, Any]] = []
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
                        res_message.append({"role": CLAUDE_MESSAGE_ROLE_ASSISTANT, "content": ""})
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
                                {
                                    "role": CLAUDE_MESSAGE_ROLE_ASSISTANT,
                                    "content": TextBlock(
                                        type="text",
                                        text=data_dict.get("delta").get("text"),
                                    ),
                                }
                            )

                        if not continue_flag:
                            break

        except Exception as e:
            raise ClaudeClientError(f"Error while streaming response: {str(e)}")

        finally:
            response_body.close()


def newTestClient(
    model: str,
    messages: list[dict[str, Any]] = None,
    stream: bool = False,
    tools: list[Tool] = None,
    **kwargs,
) -> ChatModel:

    return ChatModel(
        model="claude-haiku-4-5",
        messages=[{"role": CLAUDE_MESSAGE_ROLE_USER, "content": "你好"}],
        stream=False,
        **kwargs,
    )


if __name__ == "__main__":
    print("正在测试 ChatModelWithTools...")
    get_weather_tool = newTool(
        name="get_weather",
        description="获取一个城市当前的天气",
        properties={"city": ToolPropertyDetail(type="object", description="城市的名字")},
        required=["city"],
        func=lambda args: f"当前{args['city']}的天气是晴天，温度25摄氏度。",
    )
    test_client = ChatModel(
        base_url="https://api.phsharp.com",
        model="claude-haiku-4-5",
        messages=[{"role": "user", "content": "你好！大连的天气怎么样？"}],
        tools=[get_weather_tool],
    )
    print(f"api_key:{test_client.api_key},base_url:{test_client.base_url}")
    print(test_client.chat_with_tools())
