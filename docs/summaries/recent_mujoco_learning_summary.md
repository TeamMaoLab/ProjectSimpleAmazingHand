# 最近 MuJoCo 学习总结 (截至 2025-08-30)

## 🎯 学习目标与计划

根据制定的 [MuJoCo 学习计划](docs/plans/DT250828_mujoco_learning_plan.md)，近期的核心目标是系统性地学习 MuJoCo，并已完成 **阶段一：基础入门** 和 **阶段二：系统学习官方教程** 中的 **第1项：基础入门教程**。

## 🧠 核心概念掌握

通过阅读官方文档、运行示例代码以及深入分析，已经牢固掌握了以下核心概念：

1.  **核心数据结构 (`mjModel` & `mjData`)**:
    *   理解 `mjModel` 是模型的静态描述（如几何体、关节、质量等），不随时间变化。
    *   理解 `mjData` 是模型的动态状态（如位置 `qpos`、速度 `qvel`）及其派生量（如几何体位置 `geom_xpos`、接触力等）。
    *   熟练掌握了如何访问和操作这两个对象的属性。

2.  **MJCF 建模语言**:
    *   熟练使用 MJCF (MuJoCo Configuration Format) XML 语法来定义物理场景。
    *   掌握了关键标签的使用：`<mujoco>`, `<worldbody>`, `<geom>`, `<body>`, `<joint>`, `<default>`, `<site>`, `<actuator>`。
    *   理解了父子层级结构、默认值继承和命名规则。

3.  **关节 (Joint) 与自由度**:
    *   深刻理解了关节是约束父子刚体相对运动的核心机制。
    *   掌握了 `free` 关节（赋予刚体 6 个自由度，其 `qpos` 为 7 维 `[x, y, z, qw, qx, qy, qz]`）和 `hinge` 关节（单轴旋转，1 个自由度）的特性。
    *   理解了 MuJoCo 的拉格朗日表示法，即物体默认没有自由度，必须通过显式添加关节来获得。

4.  **仿真流程与关键函数**:
    *   理解并熟练使用 `mujoco.mj_step(model, data)` 执行仿真步进，更新状态。
    *   深入理解了 `mujoco.mj_forward(model, data)` 的作用：它根据当前的 `qpos` 和 `qvel` 计算所有派生量（如 `geom_xpos`, `qacc` 等），确保 `MjData` 状态一致。这是在手动修改状态后进行渲染或访问派生量前的必要步骤。
    *   掌握了 `mujoco.Renderer` 的基本用法进行可视化。

5.  **接触 (Contact) 处理**:
    *   理解了 MuJoCo 默认启用碰撞检测与响应。
    *   学会了如何访问 `data.contact` 数组来获取接触点详细信息。
    *   掌握了使用 `mjvOption` 开启接触点和接触力的可视化。

6.  **执行器 (Actuator)**:
    *   初步掌握了 `position` 和 `velocity` 执行器的基本工作原理。
    *   理解了 `kp` (位置增益) 和 `kv` (速度增益) 参数对执行器行为的影响。

## 💻 实践能力提升

通过一系列具体的实践脚本和实验，将理论知识转化为动手能力：

1.  **基础场景运行**:
    *   成功运行并深入分析了官方示例模型 [hello.xml](archive/DT250828_mujoco_learning/hello.xml) 及其加载脚本 [load_hello_xml.py](archive/DT250828_mujoco_learning/load_hello_xml.py)，直观理解了重力、碰撞等物理交互的底层逻辑。

2.  **`mj_forward` 探索**:
    *   通过 [exp_mj_forward.py](archive/DT250828_mujoco_learning/exp_mj_forward.py) 实验，清晰地验证了直接修改 `data.qpos` 后，必须调用 `mj_forward` 才能更新 `geom_xpos` 等派生量，否则渲染和逻辑判断会出现错误。

3.  **关节控制实践**:
    *   通过 [integrated_joint_demo.py](archive/DT250828_mujoco_learning/integrated_joint_demo.py) 实验，实践了在 MJCF 中为刚体添加不同类型的关节，并通过代码精确地修改 `data.qpos` 来控制包含多个自由度的复合刚体状态。

4.  **接触检测与可视化**:
    *   通过 [exp_contact_demo.py](archive/DT250828_mujoco_learning/exp_contact_demo.py) 实验，掌握了检测接触、访问 `data.contact` 信息以及使用 `mjvOption` 在渲染器中可视化接触点和接触力的方法。

5.  **执行器初步应用**:
    *   通过 [exp_actuator_demo.py](archive/DT250828_mujoco_learning/exp_actuator_demo.py) 实验，直观地观察了 `motor`, `position`, `velocity` 执行器的行为差异，并学习了如何调整 `kp` 和 `kv` 参数来优化控制效果。

## 📚 知识体系构建

*   将学习过程中的关键概念、函数、属性和实践经验系统地整理到了 [tutorial_guide.md](archive/DT250828_mujoco_learning/tutorial_guide.md) 中，形成了清晰的学习笔记和未来参考手册。
*   为进入下一阶段（系统学习后续官方教程或深入研究关键功能）奠定了坚实的基础，具备了独立探索和实验的能力。

## 🚀 下一步关注点

*   **Actuator 进阶**：探索如何通过代码直接读写 `data.ctrl` 和 `data.actuator_force` 进行更精细的程序化控制与监控。
*   **继续官方教程**：开始学习阶段二的下一个教程，如模型编辑、Rollout 等。