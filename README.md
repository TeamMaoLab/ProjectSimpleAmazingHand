# 项目根目录结构说明

## 主要目录

*   `archive/`: 存放已完成或阶段性工作的归档文件夹。
    *   `DT250823_esp32_web_control_demo/`: ESP32 无线控制舵机的演示项目归档。
    *   `DT250828_mujoco_learning/`: MuJoCo 学习阶段的文件归档。
*   `docs/`: 存放项目相关的文档。
    *   `plans/`: 存放详细的项目计划文档。
*   `firmware/`: 存放与硬件（如舵机）相关的固件代码。

## 根目录重要文件

*   `README.md`: 项目主说明文件。
*   `pyproject.toml`: Python 项目配置文件，定义了项目依赖和元数据。
*   `uv.lock`: 由 `uv` 工具生成的依赖锁定文件，确保依赖版本一致。
*   `.python-version`: 指定项目使用的 Python 版本。
*   `.gitignore`: Git 忽略文件配置。

## MuJoCo 学习归档 (archive/DT250828_mujoco_learning/) 内容概览

此目录包含了 MuJoCo 学习阶段一和阶段二第一项的核心实践文件与笔记。

### 核心实践脚本与模型

*   `hello.xml`: 官方基础入门教程中的第一个示例模型文件。
*   `load_hello_xml.py`: 用于加载并可视化 `hello.xml` 模型的 Python 脚本。
*   `exp_mj_forward.py`: 探索 `mujoco.mj_forward` 函数作用的实验脚本。
*   `integrated_joint_demo.py`: 演示如何在 MJCF 中为刚体添加关节（如 `hinge`）并控制其状态的脚本。
*   `exp_contact_demo.py`: 展示接触检测、访问接触信息及可视化接触点和力的脚本。
*   `exp_actuator_demo.py`: 探索 `position` 和 `velocity` 执行器 (Actuator) 基本用法和参数调优的脚本。

### 学习笔记与指南

*   `mujoco_fundamentals.md`: 阶段一的学习笔记，涵盖了 MuJoCo 核心概念与 MJCF 结构的初步理解。
*   `tutorial_guide.md`: 阶段二第一项（基础入门教程）的详细学习指南和知识沉淀，是核心的学习成果总结。
*   `mj_forward_in_depth.md`: 对 `mj_forward` 函数更深入的探索和理解笔记。
*   `model_compilation.md`: 关于 MuJoCo 模型编译过程的笔记。

### 其他

*   `tmp_*` 目录: 临时文件夹，用于存放实验过程中的临时文件或输出。
*   `tmp-output-*.png`: 实验过程中生成的临时渲染图像。
*   `MUJOCO_LOG.TXT`: MuJoCo 运行时的日志文件。