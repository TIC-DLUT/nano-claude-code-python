import json

class ClaudeClientError(Exception):
    """
    异常的基类
    """

    status_code: int | None = None
    default_message = "Claude Client Error"

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)
        self.message = message or self.default_message


class BadRequestError(ClaudeClientError):
    status_code = 400
    default_message = "Bad Request Error"


class UnauthorizedError(ClaudeClientError):
    status_code = 401
    default_message = "Unauthorized Error"


class ForbiddenError(ClaudeClientError):
    status_code = 403
    default_message = "Forbidden Error"


class NotFoundError(ClaudeClientError):
    status_code = 404
    default_message = "Not Found Error"


class TooManyRequestsError(ClaudeClientError):
    status_code = 429
    default_message = "Too Many Requests Error"


class InternalServerError(ClaudeClientError):
    status_code = 500
    default_message = "Internal Server Error"


class ServiceUnavailableError(ClaudeClientError):
    status_code = 503
    default_message = "Service Unavailable Error"

# 常见状态码和对应错误的映射表
ERROR_MAP = {
    400: BadRequestError,
    401: UnauthorizedError,
    403: ForbiddenError,
    404: NotFoundError,
    429: TooManyRequestsError,
    500: InternalServerError,
    503: ServiceUnavailableError,
}


def raise_for_status(status_code: int, text: str | None):
    """
    根据状态码提供错误信息
    
    状态码在[200, 300)之间视为通过
    """

    # 状态码在[200, 300)之间视为通过
    if 200<= status_code < 300:
        return
    
    """
    判断text是否为合法json字符串
    如果是则判断是否有error.message, 有的话就提取出来
    """
    message = text
    if text:
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                error_data = data.get("error")
                if isinstance(error_data, dict):
                    message = error_data.get("message", text)
                elif error_data is not None:
                    message = str(error_data)
        except json.JSONDecodeError:
            pass

    error = ERROR_MAP.get(status_code, ClaudeClientError)
    raise error(f"状态码: {status_code}. 错误信息: {message}" or f"请求失败，status_code={status_code}")


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
