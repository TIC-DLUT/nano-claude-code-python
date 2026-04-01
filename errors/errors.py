class ClaudeClientError(Exception):
    """
    异常的基类
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def test():
    print("准备抛出异常")
    raise ClaudeClientError("测试ClaudeClientError异常")


if __name__ == "__main__":
    print("测试errors.py文件中")
    try:
        test()
    except ClaudeClientError as e:
        print(f"捕捉到了ClaudeClientError异常: {e.message}")
        print("异常处理完成")
