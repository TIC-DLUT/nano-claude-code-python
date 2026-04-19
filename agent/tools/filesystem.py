import os
import subprocess
from typing import Any

from claude.call_tool import Tool, ToolPropertyDetail, new_tool


def new_read_file_tool() -> Tool:
    def read_file_logic(args: dict[str, Any]) -> str:
        path = args["path"]

        if not path:
            return "path不能为空"

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                return content
        except Exception as e:
            return f"读取文件失败: {e}"

    return new_tool(
        name="read_file",
        description="读一个文件，返回该文件的全部内容",
        properties={"path": ToolPropertyDetail(type="string", description="文件目录")},
        required=["path"],
        func=read_file_logic,
    )


def new_edit_file_tool() -> Tool:
    def edit_file_logic(args: dict[str, Any]) -> str:
        path = args["path"]
        old_string = args["old_string"]
        new_string = args["new_string"]

        if not path:
            return "path不能为空"

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return f"读取文件失败: {e}"

        count = content.count(old_string)
        if count == 0:
            return f"未找到匹配的文本: {old_string}"
        if count > 1:
            return f"找到 {count} 处匹配，请提供更多上下文以精确定位"

        new_content = content.replace(old_string, new_string, 1)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return f"编辑文件成功: {path}"
        except Exception as e:
            return f"写入文件失败: {e}"

    return new_tool(
        name="edit_file",
        description="通过替换指定文本来编辑文件,old_string必须在文件中唯一匹配",
        properties={
            "path": ToolPropertyDetail(type="string", description="文件路径"),
            "old_string": ToolPropertyDetail(type="string", description="要被替换的原文本"),
            "new_string": ToolPropertyDetail(type="string", description="替换后的新文本"),
        },
        required=["path", "old_string", "new_string"],
        func=edit_file_logic,
    )


def new_write_file_tool() -> Tool:
    def write_file_logic(args: dict[str, Any]) -> str:
        path = args["path"]
        content = args["content"]

        if not path:
            return "path不能为空"

        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"写入文件成功: {path}"
        except Exception as e:
            return f"写入文件失败: {e}"

    return new_tool(
        name="write_file",
        description="将内容写入指定文件,如果文件已经存在则覆盖,如果父目录不存在则自动创建",
        properties={
            "path": ToolPropertyDetail(type="string", description="文件目录"),
            "content": ToolPropertyDetail(type="string", description="要写入的内容"),
        },
        required=["path", "content"],
        func=write_file_logic,
    )


def new_bash_tool() -> Tool:
    def bash_logic(args: dict[str, Any]) -> str:
        command = args["command"]
        timeout = args.get("timeout", 30)

        if not command:
            return "command不能为空"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode == 0:
                return result.stdout if result.stdout else result.stderr
            else:
                return f"Exit code: {result.returncode}\nstderr: {result.stderr}\nstdout: {result.stdout}"
        except subprocess.TimeoutExpired:
            return f"命令执行超时 ({timeout}s): {command}"
        except Exception as e:
            return f"执行命令失败: {e}"

    return new_tool(
        name="bash",
        description="执行命令行命令并返回输出,支持管道、重定向等shell特性",
        properties={
            "command": ToolPropertyDetail(
                type="string", description="要执行的命令行命令"
            ),
            "timeout": ToolPropertyDetail(
                type="number", description="超时秒数,默认30秒"
            ),
        },
        required=["command"],
        func=bash_logic,
    )
