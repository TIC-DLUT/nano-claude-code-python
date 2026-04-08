from collections.abc import Callable
from typing import Any

from agent.prompt import getNowSystemPrompt
from agent.tools.filesystem import newReadFileTool
from claude.call import StreamableChatModel
from claude.call_tool import Tool
from claude.message import CLAUDE_MESSAGE_ROLE_USER


class Agent:
    def __init__(self, api_client: StreamableChatModel, tools: list[Tool] | None = None):
        self.api_client = api_client
        self.tools = tools or []
        self.api_client.tools = self.tools

    def loadTools(self) -> None:
        filesystem_readfile_tool = newReadFileTool()

        try:
            self.tools.append(filesystem_readfile_tool)
            self.api_client.tools = self.tools
        except Exception as e:
            print(f"加载工具失败: {e}")

    def chatStream(self, message: str, callback: Callable[[str], None]):
        last_tool_call_id = ""

        def stream_handler(m: dict[str, Any]) -> bool:
            nonlocal last_tool_call_id

            content = m.get("content", {})
            content_type = content.get("type")

            if content_type == "text":
                callback(content.get("text", ""))
            elif content_type == "tool_use":
                tool_call_id = content.get("id", "")
                if tool_call_id != last_tool_call_id:
                    last_tool_call_id = tool_call_id
                    callback(f"\n[tool_use] {content.get('name', '')}\n")
            return True

        self.api_client.messages = [{"role": CLAUDE_MESSAGE_ROLE_USER, "content": message}]
        self.api_client.system = getNowSystemPrompt()
        tool_result = self.api_client.chat_with_tools(stream_callback=stream_handler)

        # 当前流式实现在触发工具后会直接返回工具结果，这里需要显式透出给上层。
        if isinstance(tool_result, str) and tool_result:
            callback(f"\n{tool_result}\n")


def newAgent(base_url: str, api_key: str, model: str) -> Agent:
    api_client = StreamableChatModel(
        base_url=base_url,
        api_key=api_key,
        model=model,
    )

    new_agent = Agent(
        api_client=api_client,
    )

    new_agent.loadTools()

    return new_agent


if __name__ == "__main__":
    agent = newAgent()
    print(f"Agent加载完成, 已加载工具: {[tool.name for tool in agent.tools]}")
