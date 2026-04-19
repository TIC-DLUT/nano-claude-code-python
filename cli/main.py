import argparse

from agent.chat import new_agent
from cli.direct import direct_run
from config.env import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Nano Claude Code Python CLI")
    parser.add_argument("--tui", action="store_true", help="启用TUI界面")
    parser.add_argument("--message", type=str, default="", help="输入消息进行交互")

    return parser.parse_args()


def main():
    args = parse_args()

    try:
        cfg = load_config()
    except Exception as e:
        print(f"加载配置失败: {e}")
        return

    main_agent = new_agent(**cfg)

    if args.tui:
        print("启动 TUI 模式 ...")
        # TODO: TUI(处理命令行参数)
        pass

    else:
        direct_run(main_agent, args.message)


if __name__ == "__main__":
    main()
