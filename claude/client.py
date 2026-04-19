import os

import requests

from errors.errors import ClaudeClientError


class ClaudeClient:
    def __init__(self, base_url: str, api_key: str | None = None, version: str = "2023-06-01"):
        self.base_url = base_url.rstrip("/") if base_url else "https://api.anthropic.com"
        self.api_key = api_key if api_key else os.getenv("CLAUDE_API_KEY")
        self.version = version

        self._session = requests.Session()
        self._session.headers.update(
            {
                "x-api-key": self.api_key,
                "anthropic-version": self.version,  # 官方默认 2023-06-01
                "Content-Type": "application/json",
            }
        )

    def __repr__(self) -> str:
        return f"ClaudeClient(base_url={self.base_url}, api_key={self.api_key}, version={self.version})"


def new_claude_client(base_url: str, api_key: str, version: str = "2023-06-01") -> ClaudeClient:
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        raise ClaudeClientError("Invalid URL: URL must start with http:// or https://")

    return ClaudeClient(base_url=base_url, api_key=api_key, version=version)


if __name__ == "__main__":
    client = ClaudeClient(
        base_url="https://api.anthropic.com",
        api_key="your_api_key_here",
    )
    print(client)
