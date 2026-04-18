# nano-claude-code-python

> 本项目是一个教学导向的开源实践项目。我们将抛弃 LangChain、抛弃 LlamaIndex，甚至抛弃官方 SDK，仅使用 Python 语言标准库（以及少量辅助库），在 7 天内从零开始，一行行写出一个Claude-Code like Coding Agent。

**nano-claude-code-python** 是一个受 Anthropic [Claude Code](https://github.com/anthropics/claude-code) 和 [nano-claude-code](https://github.com/TIC-DLUT/nano-claude-code) 启发，使用 **Python** 从零开始纯手工打造的轻量级 AI 编码智能体（Agent）。

没有 LangChain，没有复杂笨重的 AI 框架。这里**甚至连调用 Anthropic 接口的 SDK 都是从零手写的**。本项目旨在通过纯粹、清晰的 Python 代码，向你展示如何从最底层的 API 调用开始，一步步构建一个具备自主能力的 AI Agent。

## 为什么要“从零手搓”？

现在的 AI 封装库越来越厚重，当 Agent 陷入死循环、工具调用失败、或者上下文丢失时，新手往往不知所措。

作为教学项目，nano-claude-code-python 将带你亲自趟过这些坑：

- 亲自手写底层 SDK，搞懂 LLM 接口的 JSON Schema 长什么样。
- 亲自解析 SSE 流式响应，体验在终端打印“打字机”效果的快感。
- 亲自写一个 for 循环来实现 Agent 的“观察 -> 思考 -> 行动”（ReAct）闭环。
- 亲自赋予 LLM 读写本地文件和执行 Bash 命令的危险而强大的能力。
- 亲自设计一个TODO架构的Agent。
- 亲自设计subAgents架构。
- 亲自完成skills框架的设计，包括加载，调用。
- 亲自参与压缩流程的设计，完成一个简单的压缩机制。
- 亲自设计一个Tasks系统，深入了解Agent怎么设计task的依赖和规划。
- 亲自实现一个Backgroud Tasks机制。
- 亲自实现多智能体架构。
- 亲自实现记忆机制，对话记录持久化，赋予Agent灵魂。

## QuickStart
``` shell
git clone https://github.com/TIC-DLUT/nano-claude-code-python.git
cd .\nano-claude-code-python\
code .
```

在 `~/.nano-claude-code/config.json` 中创建配置文件：
``` json
{
    "base_url": "your_base_url",
    "api_key": "your_api_key",
    "model": "claude-sonnet-4-6"
}
```

或者用环境变量：
``` shell
export NCC_LLM_BASE_URL="your_base_url"
export NCC_LLM_API_KEY="your_api_key"
export NCC_LLM_MODEL="claude-sonnet-4-6"
```

``` shell
uv sync
uv run python -m cmd.main --message "创建一个 hello.txt 文件，内容写 Hello World"
uv run python -m cmd.main --message "你有哪些可用的工具？分别介绍一下"
```
`Direct` 模式: 非交互界面，接收一条输入直接执行并输出流式结果
`TUI` 模式: 终端 UI 交互模式

## 目录

- [x] day1: 从零实现一个claude sdk
- [x] day2: SimpleAgentLoop

## Other Version

- [nano-claude-code](https://github.com/TIC-DLUT/nano-claude-code)

- [nano-claude-code-typescript](https://github.com/TIC-DLUT/nano-claude-code-typescript)

## 贡献

由于这是一个教学项目，非常欢迎各位参与进来！

[详细贡献指南](./CONTRIBUTING.md)

## License

[MIT](./LICENSE)