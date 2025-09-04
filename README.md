# ProjectSimpleAmazingHand

本项目是对 [AmazingHand](https://github.com/pollen-robotics/AmazingHand) 项目的复刻和管理。

AmazingHand 是一个由 Pollen Robotics 开发的低成本、开源的机器人手项目。它具有 8 个自由度，重量轻，所有执行器都内置在手部内。该项目旨在提供一个可访问、可定制的平台，用于机器人手的研究和开发。

此 `ProjectSimpleAmazingHand` 仓库用于管理、修改和实验 AmazingHand 的设计及相关软件。

## 项目当前推进状态

项目当前推进状态请参见 [docs/plans/overview.md](./docs/plans/overview.md)。

最近完成的项目：
- [使用 micropython 快速实现一个单手指控制的网页demo](./docs/plans/esp32_web_control_demo.md) (已完成 - 2025-08-23)
- [Fusion360导出插件重构完成](./archive/DT250902_fusion360_export_plugin/fusion_export_helper/README.md) (已完成 - 2025-09-02) - 将通用批量导出工具重构为专注于MuJoCo仿真的精准导出插件

进行中的项目：
- [MuJoCo 学习计划](./docs/plans/DT250828_mujoco_learning_plan.md) (进行中)

## 项目内容预期

本项目预期将包含以下内容：

*   **Python 脚本**: 用于控制和测试机器人手。
*   **模型文件**: 包括 `.f3d` (Fusion 360) 和 `.step` 格式的 3D 模型文件。
*   **文档**: 详细的项目文档、使用说明等。
*   **会议纪要**: 项目相关的讨论和决策记录。
*   **项目规划**: 项目的发展路线图和任务安排。
*   **固件**: 项目相关的固件文件存放在 `firmware/` 目录下，该目录不受 Git 版本控制。

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

### 项目文件路径规则

为了确保项目在不同环境下的可移植性和一致性，特别是在使用 Git 进行版本控制时，我们制定了以下文件路径规则：

1.  **相对路径原则**: 所有代码中的文件路径都应使用相对路径，而不是绝对路径。这确保了项目在不同用户的机器上能够正确运行。
2.  **Python 脚本中的相对路径**: 在 Python 脚本中，应使用 `os.path` 或 `pathlib` 模块来构建相对于脚本位置的路径。
3.  **文档中的路径引用**: 在 Markdown 文档中，使用相对路径来引用项目内的其他文件。
4.  **项目结构**: 项目应保持清晰的目录结构，常见的目录包括 `src/`、`data/`、`docs/`、`archive/` 和 `tests/`。
5.  **版本控制**: 所有源代码和文档都应纳入 Git 版本控制，大型二进制文件应考虑使用 Git LFS 管理，生成的文件不应纳入版本控制。

## 贡献者 (Contributors)

[<img src="https://github.com/TheTinkerJ.png" width="100px;" alt="TheTinkerJ"/>](https://github.com/TheTinkerJ)

*   [TheTinkerJ](https://github.com/TheTinkerJ) - 项目发起人