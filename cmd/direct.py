from agent.chat import Agent


def directRun(agent: Agent, message: str):
    if message == "":
        raise ValueError("message不能为空")

    print(f"开始处理 {message}")

    agent.chatStream(message, lambda s: print(s, end="", flush=True))
