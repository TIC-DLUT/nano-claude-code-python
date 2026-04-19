import time
from pathlib import Path

SYSTEM_PROMPT = """你是claude code，你需要调用工具帮助人们完成工作

当前时间是：{system_time}
当前工作地址是：{work_path}"""


def get_now_system_prompt() -> str:
    system_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    work_path = str(Path.cwd())
    return SYSTEM_PROMPT.replace("{system_time}", system_time).replace("{work_path}", work_path)


if __name__ == "__main__":
    print(get_now_system_prompt())
