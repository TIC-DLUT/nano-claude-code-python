from agent.chat import Agent


def direct_run(agent: Agent, message: str):
    if message == "":
        raise ValueError("message不能为空")

    print(f"开始处理 {message}")

    agent.chat_stream(message, lambda s: print(s, end="", flush=True))
