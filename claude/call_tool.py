from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

from errors.errors import ClaudeClientError


@dataclass
class ToolPropertyDetail:
    type: str
    description: str


@dataclass
class InputSchema:
    type: str
    properties: dict[str, ToolPropertyDetail]
    required: list[str]


@dataclass
class Tool:
    name: str
    description: str

    input_schema: InputSchema
    # func 字段是Tool所需要的, 但不应该被发送到接口
    func: Callable[[dict[str, any]], str] | None = field(default=None, repr=False)

    def to_request(self) -> dict[str, Any]:
        """
        导出接口需要的字段
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": asdict(self.input_schema),
        }


def newTool(
    name: str,
    description: str,
    properties: dict[str, ToolPropertyDetail],
    required: list[str],
    func: Callable[[dict[str, any]], str] | None = None,
) -> Tool:
    if name is None or description is None:
        raise ClaudeClientError("Tool name and description cannot be None")
    return Tool(
        name=name,
        description=description,
        input_schema=InputSchema(
            type="object",
            properties=properties,
            required=required,
        ),
        func=func,
    )
