# ProjectSimpleAmazingHand

本项目是对 [AmazingHand](https://github.com/pollen-robotics/AmazingHand) 项目的复刻和管理。

AmazingHand 是一个由 Pollen Robotics 开发的低成本、开源的机器人手项目。它具有 8 个自由度，重量轻，所有执行器都内置在手部内。该项目旨在提供一个可访问、可定制的平台，用于机器人手的研究和开发。

此 `ProjectSimpleAmazingHand` 仓库用于管理、修改和实验 AmazingHand 的设计及相关软件。

## 项目内容预期

本项目预期将包含以下内容：

*   **Python 脚本**: 用于控制和测试机器人手。
*   **模型文件**: 包括 `.f3d` (Fusion 360) 和 `.step` 格式的 3D 模型文件。
*   **文档**: 详细的项目文档、使用说明等。
*   **会议纪要**: 项目相关的讨论和决策记录。
*   **项目规划**: 项目的发展路线图和任务安排。

## 开发辅助

如果你准备上手这个项目，最好为这个项目配备 AI 助手，具体可以参考 [Qwen Code](https://github.com/QwenLM/qwen-code)。

### 配置 Qwen Code 作为 AI 助手

一种可行的方案是在项目根目录下创建一个 `.env` 文件，内容如下：

```env
OPENAI_API_KEY=ms-key--你自己的key
OPENAI_BASE_URL=https://api-inference.modelscope.cn/v1/
OPENAI_MODEL=Qwen/Qwen3-Coder-480B-A35B-Instruct
```

请将 `你自己的key` 替换为你在 ModelScope 上申请的实际 API Key。

## 文档管理方案

为了有效地组织和管理项目中预期的大量文档（包括设计文档、会议纪要、项目规划等），建议采用结构化的文档管理方案。详细方案请参见 [docs/documentation_management_plan.md](./docs/documentation_management_plan.md)。

## 贡献者 (Contributors)

[<img src="https://github.com/TheTinkerJ.png" width="100px;" alt="TheTinkerJ"/>](https://github.com/TheTinkerJ)

*   [TheTinkerJ](https://github.com/TheTinkerJ) - 项目发起人