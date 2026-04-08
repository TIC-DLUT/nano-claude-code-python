import argparse
from cmd.direct import directRun

from agent.chat import newAgent
from config.env import load_config

TUI_MODE = False
MESSAGE = ""


def parse_args():
    global TUI_MODE, MESSAGE

    parser = argparse.ArgumentParser(description="Nano Claude Code Python CLI")
    parser.add_argument("--tui", action="store_true", help="启用TUI界面")
    parser.add_argument("--message", type=str, default="", help="输入消息进行交互")

    args = parser.parse_args()  # 处理命令行参数
    TUI_MODE = args.tui
    MESSAGE = args.message


def main():
    # 加载配置文件
    parse_args()

    try:
        cfg = load_config()
    except Exception as e:
        print(f"加载配置失败: {e}")

    main_agent = newAgent(**cfg)

    if TUI_MODE:
        print("启动 TUI 模式 ...")
        # TODO: TUI(处理命令行参数)
        pass

    else:
        directRun(main_agent, MESSAGE)


if __name__ == "__main__":
    main()
