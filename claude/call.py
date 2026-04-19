import json
from collections.abc import Callable
from typing import Any

from claude.call_tool import Tool, ToolPropertyDetail, new_tool
from claude.client import ClaudeClient
from claude.message import (
    CLAUDE_MESSAGE_ROLE_ASSISTANT,
    CLAUDE_MESSAGE_ROLE_USER,
)
from errors.errors import raise_for_status


def default_stream_handler(m: dict[str, Any]) -> bool:
    if m["content"]["type"] == "text":
        print(m["content"]["text"], flush=True)
    elif m["content"]["type"] == "tool_use":
        print(
            f"正在调用工具: {m['content']['name']}, {m['content']['partial_json']}",
            flush=True,
        )
    return True


class ChatModel(ClaudeClient):
    def __init__(
        self,
        model: str,
        messages: list[dict[str, Any]] | None = None,
        stream: bool = False,
        tools: list[Tool] | None = None,
        system: str = "",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.messages = messages or []
        self.model = model
        self.system = system
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
            # 处理: 当 message["content"] 已经是一个列表如 [{tool_result1}, {tool_result2}]
            elif isinstance(message["content"], list):
                new_content.extend(message["content"])
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
            "system": self.system,
        }
        if self.tools:
            requested_tools = [tool.to_request() for tool in self.tools]
            body["tools"] = requested_tools
        return body

    def _execute_tools(self, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        执行工具调用并收集结果。
        每个 tool_call 必须包含: id, name, input (已解析的参数 dict)
        """
        tool_results = []
        for tool_call in tool_calls:
            tool_id = tool_call["id"]
            tool_name = tool_call["name"]
            tool_input = tool_call["input"]

            target_tool = next((t for t in self.tools if t.name == tool_name), None)

            if target_tool and target_tool.func:
                result = target_tool.func(tool_input)
            else:
                result = f"工具 {tool_name} 未找到"

            tool_results.append(
                {
                    "tool_use_id": tool_id,
                    "type": "tool_result",
                    "content": result,
                }
            )
        return tool_results

    def call(self) -> str:
        """
        向 Claude API 发送聊天消息并返回响应。
        """

        body = self._get_request_body()

        response_body = self._session.post(
            url=f"{self.base_url}/v1/messages",
            json=body,
        )
        # 根据非200状态码返回错误信息
        # 若状态码为2xx，表示成功。成功则不用raise_for_status
        # 避免读取大段的text影响性能
        if not (200 <= response_body.status_code < 300):
            raise_for_status(response_body.status_code, response_body.text)

        response_body_json = response_body.json()
        return response_body_json["content"]

    def chat_with_tools(self):
        """
        向 Claude API 发送聊天消息(包括工具调用)并返回响应。
        工具结果会追加到 messages 中再次发送给模型，直到模型不再调用工具。
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
                return ""

            tool_results = self._execute_tools(tool_calls)

            # 将工具结果追加为 user 消息，继续循环让模型看到结果
            self.messages.append(
                {
                    "role": CLAUDE_MESSAGE_ROLE_USER,
                    "content": tool_results,
                }
            )


class StreamableChatModel(ChatModel):
    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.stream = True

    def _stream_one_round(
        self,
        event_handler: Callable[[dict[str, Any]], bool],
    ) -> list[dict[str, Any]]:
        """
        发送一次流式请求，解析 SSE 事件，返回解析后的 content blocks 列表。
        每个元素形如 {"type": "text", "text": "..."} 或
        {"type": "tool_use", "id": "...", "name": "...", "partial_json": "..."}.
        """
        body = self._get_request_body()
        response_body = self._session.post(
            url=f"{self.base_url}/v1/messages",
            json=body,
            # requests库特性: 只有在设置了 stream=True 后，iter_lines() 才会在接收到每行数据时就返回，而不是等整个响应结束
            stream=True,
        )
        # 根据非200状态码返回错误信息
        # 若状态码为2xx，表示成功。成功则不用raise_for_status
        # 避免读取大段的text影响性能
        if not (200 <= response_body.status_code < 300):
            raise_for_status(response_body.status_code, response_body.text)

        content_blocks: list[dict[str, Any]] = []
        try:
            for line in response_body.iter_lines():
                if not line:
                    continue

                line_str = line.decode("utf-8")

                if line_str.startswith("data:"):
                    data_json = line_str[6:]

                    # 兼容 OpenRouter 的流式接口，OpenRouter在流式结束时会发送一个data: [DONE]的消息
                    if data_json == "[DONE]":
                        break

                    data_dict = json.loads(data_json)
                    event_type = data_dict["type"]

                    if event_type == "content_block_start":
                        content_block = data_dict["content_block"]
                        if content_block["type"] == "text":
                            content_blocks.append({"type": "text", "text": content_block["text"]})
                        elif content_block["type"] == "tool_use":
                            content_blocks.append(
                                {
                                    "id": content_block["id"],
                                    "type": "tool_use",
                                    "name": content_block["name"],
                                    "partial_json": "",
                                }
                            )

                    elif event_type == "content_block_delta":
                        current = content_blocks[-1]
                        continue_flag = True

                        if current["type"] == "text":
                            delta_text = data_dict["delta"]["text"]
                            current["text"] += delta_text
                            continue_flag = event_handler(
                                {
                                    "role": CLAUDE_MESSAGE_ROLE_ASSISTANT,
                                    "content": {"type": "text", "text": delta_text},
                                }
                            )
                        elif current["type"] == "tool_use":
                            delta_json = data_dict["delta"]["partial_json"]
                            current["partial_json"] += delta_json
                            continue_flag = event_handler(
                                {
                                    "role": CLAUDE_MESSAGE_ROLE_ASSISTANT,
                                    "content": {
                                        "type": "tool_use",
                                        "id": current["id"],
                                        "name": current["name"],
                                        "partial_json": delta_json,
                                    },
                                }
                            )

                        if not continue_flag:
                            break
        finally:
            response_body.close()

        return content_blocks

    def chat_with_tools(
        self,
        stream_callback: Callable[[dict[str, Any]], bool] | None = None,
    ):
        """
        向 Claude API 发送聊天消息并以流式方式返回响应。
        工具结果会追加到 messages 中再次发送给模型，直到模型不再调用工具。
        """
        event_handler = stream_callback or default_stream_handler

        while True:
            content_blocks = self._stream_one_round(event_handler)

            tool_use_blocks = [b for b in content_blocks if b["type"] == "tool_use"]

            if not tool_use_blocks:
                return "".join(b["text"] for b in content_blocks if b["type"] == "text")

            # 构造 assistant 消息（将 partial_json 解析为 input）
            assistant_content = []
            for block in content_blocks:
                if block["type"] == "text":
                    assistant_content.append({"type": "text", "text": block["text"]})
                elif block["type"] == "tool_use":
                    assistant_content.append(
                        {
                            "type": "tool_use",
                            "id": block["id"],
                            "name": block["name"],
                            "input": json.loads(block["partial_json"]),
                        }
                    )
            self.messages.append(
                {
                    "role": CLAUDE_MESSAGE_ROLE_ASSISTANT,
                    "content": assistant_content,
                }
            )

            # 复用已解析的 input，构造 _execute_tools 所需格式
            parsed_tool_calls = [item for item in assistant_content if item["type"] == "tool_use"]
            tool_results = self._execute_tools(parsed_tool_calls)

            # 将工具结果追加为 user 消息，继续循环让模型看到结果
            self.messages.append(
                {
                    "role": CLAUDE_MESSAGE_ROLE_USER,
                    "content": tool_results,
                }
            )


def new_test_client() -> ChatModel:
    return ChatModel(
        model="claude-haiku-4-5",
        messages=[{"role": CLAUDE_MESSAGE_ROLE_USER, "content": "你好"}],
        stream=False,
    )


def test_chat_model_with_tools():
    print("正在测试 ChatModelWithTools...")
    get_weather_tool = new_tool(
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
        system="",
    )
    print(f"api_key:{test_client.api_key},base_url:{test_client.base_url}")
    print(test_client.chat_with_tools())


def test_streamable_chat_model_with_tools():
    print("正在测试 StreamableChatModelWithTools...")
    get_weather_tool = new_tool(
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
        system="",
    )
    print(f"api_key:{test_client.api_key},base_url:{test_client.base_url}")
    print(test_client.chat_with_tools())


if __name__ == "__main__":
    test_chat_model_with_tools()
    print("---" * 10)
    test_streamable_chat_model_with_tools()
