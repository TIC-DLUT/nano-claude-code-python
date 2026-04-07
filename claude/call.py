import json
from typing import Any

from claude.call_tool import Tool, ToolPropertyDetail, newTool
from claude.client import ClaudeClient
from claude.message import (
    CLAUDE_MESSAGE_ROLE_ASSISTANT,
    CLAUDE_MESSAGE_ROLE_USER,
)
from errors.errors import ClaudeClientError


def deal_func(m: dict[str, Any]) -> bool:
    if m["content"]["type"] == "text":
        print(m["content"]["text"])
    elif m["content"]["type"] == "tool_use":
        print(f"正在调用工具: {m['content']['name']}, {m['content']['partial_json']}")
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

    def _merge_same_role_messages(self):
        """合并相同角色的连续消息，避免API请求格式错误"""
        current_role = CLAUDE_MESSAGE_ROLE_USER
        request_messages: list[dict[str, str | list[str]]] = []

        if len(self.messages) > 0:
            current_role = self.messages[0]["role"]
            request_messages.append({"role": current_role, "content": []})

        for message in self.messages:
            if message["role"] != current_role:
                current_role = message["role"]
                request_messages.append({"role": current_role, "content": []})

            new_content = request_messages[-1]["content"]
            if isinstance(message["content"], str):
                new_content = [{"type": "text", "text": message["content"]}]
            else:
                new_content.append(message["content"])

            request_messages[-1]["content"] = new_content
        self.messages = request_messages

    def _get_request_body(self) -> dict:
        """构造请求体"""
        self._merge_same_role_messages()
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
                    return tool_result

                tool_use_result.append(
                    {
                        "tool_use_id": tool_id,
                        "type": "tool_result",
                        "content": tool_result,
                    }
                )

            else:
                raise ClaudeClientError("工具调用失败，未找到匹配的工具或工具执行失败。")


class StreamableChatModel(ChatModel):
    def __init__(
        self, model: str, messages: list[dict[str, Any]] = None, stream: bool = True, **kwargs
    ):
        super().__init__(model=model, messages=messages, stream=stream, **kwargs)

    def chat_with_tools(self):
        """
        向 Claude API 发送聊天消息并以流式方式返回响应。
        """
        body = self._get_request_body()
        response_body = self._session.post(
            url=f"{self.base_url}/v1/messages",
            json=body,
        )
        res_message: list[dict[str, Any]] = []
        try:
            for line in response_body.iter_lines():
                if not line:
                    continue

                line_str = line.decode("utf-8")

                if line_str.startswith("data:"):
                    data_json = line_str[6:]

                    if data_json == "[DONE]":
                        break

                    data_dict = json.loads(data_json)

                    event_type = data_dict["type"]

                    if event_type == "content_block_start":
                        res_message.append({"role": CLAUDE_MESSAGE_ROLE_ASSISTANT, "content": ""})
                        content = {}
                        content_block = data_dict["content_block"]

                        if content_block["type"] == "text":
                            content = {"type": "text", "text": content_block["text"]}
                        elif content_block["type"] == "tool_use":
                            content = {
                                "id": content_block["id"],
                                "type": "tool_use",
                                "name": content_block["name"],
                            }
                        res_message[-1]["content"] = content
                    elif event_type == "content_block_delta":
                        continue_flag = True
                        if res_message[-1]["content"]["type"] == "text":
                            res_message[-1]["content"] = {
                                "type": "text",
                                "text": res_message[-1]["content"]["text"]
                                + data_dict["delta"]["text"],
                            }
                            continue_flag = deal_func(
                                {
                                    "role": CLAUDE_MESSAGE_ROLE_ASSISTANT,
                                    "content": {
                                        "type": "text",
                                        "text": data_dict["delta"]["text"],
                                    },
                                }
                            )
                        elif res_message[-1]["content"]["type"] == "tool_use":
                            current_content = res_message[-1]["content"]
                            old_partial = current_content.get("partial_json", "")
                            new_partial = data_dict["delta"]["partial_json"]

                            current_content["partial_json"] = old_partial + new_partial

                            continue_flag = deal_func(
                                {
                                    "role": CLAUDE_MESSAGE_ROLE_ASSISTANT,
                                    "content": {
                                        "type": "tool_use",
                                        "id": current_content["id"],
                                        "name": current_content["name"],
                                        "partial_json": new_partial,
                                    },
                                }
                            )

                        if not continue_flag:
                            break

            tool_use_blocks = [
                item for item in res_message if item["content"]["type"] == "tool_use"
            ]

            if not tool_use_blocks:
                return "".join(
                    [
                        item["content"]["text"]
                        for item in res_message
                        if item["content"]["type"] == "text"
                    ]
                )

            for tool_use in tool_use_blocks:
                tool_name = tool_use["content"]["name"]
                target_tool = next((t for t in self.tools if t.name == tool_name), None)

                if target_tool:
                    args = json.loads(tool_use["content"]["partial_json"])
                    result = target_tool.func(args)

                    return result

        except Exception as e:
            raise ClaudeClientError(f"Error while streaming response: {str(e)}")

        finally:
            response_body.close()


def newTestClient() -> ChatModel:
    return ChatModel(
        model="claude-haiku-4-5",
        messages=[{"role": CLAUDE_MESSAGE_ROLE_USER, "content": "你好"}],
        stream=False,
    )


def testChatModelWithTools():
    print("正在测试 ChatModelWithTools...")
    get_weather_tool = newTool(
        name="get_weather",
        description="获取一个城市当前的天气",
        properties={"city": ToolPropertyDetail(type="object", description="城市的名字")},
        required=["city"],
        func=lambda args: f"当前{args['city']}的天气是晴天, 温度25摄氏度。",
    )
    test_client = ChatModel(
        base_url="https://api.phsharp.com",
        model="claude-haiku-4-5",
        messages=[{"role": "user", "content": "你好！大连的天气怎么样？"}],
        tools=[get_weather_tool],
    )
    print(f"api_key:{test_client.api_key},base_url:{test_client.base_url}")
    print(test_client.chat_with_tools())


def testStreamableChatModelWithTools():
    print("正在测试 StreamableChatModelWithTools...")
    get_weather_tool = newTool(
        name="get_weather",
        description="获取一个城市当前的天气",
        properties={"city": ToolPropertyDetail(type="object", description="城市的名字")},
        required=["city"],
        func=lambda args: f"当前{args['city']}的天气是晴天, 温度25摄氏度。",
    )
    test_client = StreamableChatModel(
        base_url="https://api.phsharp.com",
        model="claude-haiku-4-5",
        messages=[{"role": "user", "content": "你好! 大连的天气怎么样？"}],
        tools=[get_weather_tool],
    )
    print(f"api_key:{test_client.api_key},base_url:{test_client.base_url}")
    print(test_client.chat_with_tools())


if __name__ == "__main__":
    testChatModelWithTools()
    print("---" * 10)
    testStreamableChatModelWithTools()
