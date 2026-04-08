import json
import os
from pathlib import Path


def bind_env(config: dict):
    """原地修改传入的字典"""
    mapping = {
        "base_url": "llm.base_url",
        "api_key": "llm.api_key",
        "model": "llm.model",
    }

    for config_key, env_suffix in mapping.items():
        env_val = os.getenv(f"NCC_{env_suffix.replace('.', '_').upper()}")
        if env_val:
            config[config_key] = env_val


def load_config():
    config_file = Path.home() / ".nano-claude-code" / "config.json"

    config = {}

    # 读取 JSON 配置文件
    try:
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

        else:
            print(f"Warning: 配置文件不存在 {config_file}")
            # TODO: 文件不存在, 启动创建引导

    except json.JSONDecodeError as e:
        print(f"Error: 解析配置文件失败 {config_file}: {e}")

    # 读取环境变量覆盖配置文件
    bind_env(config)

    return config


if __name__ == "__main__":
    cfg = load_config()
    print(cfg)
