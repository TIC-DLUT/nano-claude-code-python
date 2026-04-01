# nano-claude-code-python

> 本项目是一个教学导向的开源实践项目。我们将抛弃 LangChain、抛弃 LlamaIndex，甚至抛弃官方 SDK，仅使用 Python 语言标准库（以及少量辅助库），在 7 天内从零开始，一行行写出一个Claude-Code like Coding Agent。

**nano-claude-code-python** 是一个受 Anthropic [Claude Code](https://github.com/anthropics/claude-code) 和 [nano-claude-code](https://github.com/TIC-DLUT/nano-claude-code) 启发，使用 **Python** 从零开始纯手工打造的轻量级 AI 编码智能体（Agent）。

## QuickStart
``` shell
git clone https://github.com/TIC-DLUT/nano-claude-code-python.git
cd .\nano-claude-code-python\
code .
```

``` shell
uv sync
uv run python -m claude.client
```

## 贡献

由于这是一个教学项目，非常欢迎各位初学者参与进来！

如果你在阅读代码时发现了可以优化的地方，或者你想为这个项目添加一个新功能，发现其中的文档有错误或者可以优化的地方，请随时提交 Pull Request。

1. Fork 本项目
2. 提交你的修改
3. 开启一个 Pull Request
4. @nano-claude-code-maintainer 进行审核