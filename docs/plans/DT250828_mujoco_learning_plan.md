# MuJoCo 学习计划

## 目标

系统性地学习 MuJoCo 物理引擎，掌握其基本概念、建模方法、API 使用及高级功能，最终能够独立使用 MuJoCo 进行机器人仿真和相关研究。

## 步骤

### 阶段一：基础入门（已完成 ✅ 2025-08-30）

1.  **了解 MuJoCo**:
    *   访问 MuJoCo 官方文档，阅读 "Overview" 部分。
    *   了解 MuJoCo 的基本概念、发展历程、应用领域及关键特性。
2.  **安装配置**:
    *   依赖已通过 `uv add mujoco` 安装。
    *   确保能在本地环境中正常启动 MuJoCo 相关程序。
3.  **学习基本语法与数据结构**:
    *   学习 MJCF（XML 格式）语法，了解如何定义物体、关节、材质等元素。参考 [MuJoCo 核心概念与 MJCF 结构](../../archive/DT250828_mujoco_learning/mujoco_fundamentals.md)。
    *   熟悉 `mjModel` 和 `mjData` 数据结构及其用途。参考 [MuJoCo 核心概念与 MJCF 结构](../../archive/DT250828_mujoco_learning/mujoco_fundamentals.md)。
4.  **运行简单示例**:
    *   运行官方文档中的简单示例，如固定平面、光源和浮动盒子模型。
    *   通过修改模型参数和代码，观察仿真结果的变化。
    *   已创建示例模型 `hello.xml` 和对应的 Python 脚本 `load_hello_xml.py` 来加载和运行仿真。
        *   `hello.xml` 定义了一个简单的物理场景，其详细结构解析如下：
            *   `<mujoco>`: 这是 MuJoCo 模型文件的根元素。
            *   `<worldbody>`: 定义了世界坐标系下的物体，所有静态和动态物体都在这个世界体内部定义。
            *   `<light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>`: 定义了一个光源。
                *   `diffuse=".5 .5 .5"`: 设置漫反射光的强度为RGB(0.5, 0.5, 0.5)。
                *   `pos="0 0 3"`: 光源的位置在 (0, 0, 3)。
                *   `dir="0 0 -1"`: 光线方向朝下（沿着负Z轴）。
            *   `<geom type="plane" size="1 1 0.1" rgba=".9 0 0 1"/>`: 定义了一个平面几何体。
                *   `type="plane"`: 几何体类型是平面。
                *   `size="1 1 0.1"`: 平面的尺寸是 1x1，厚度是 0.1。
                *   `rgba=".9 0 0 1"`: 颜色为红色（RGB: 0.9, 0, 0），不透明度为 1。
            *   `<body pos="0 0 1">`: 定义了一个刚体，初始位置在 (0, 0, 1)。
                *   `<joint type="free"/>`: 为这个刚体定义了一个自由关节，允许它在3D空间中自由移动和旋转。
                *   `<geom type="box" size=".1 .2 .3" rgba="0 .9 0 1"/>`: 在这个刚体上附加了一个盒状几何体。
                    *   `type="box"`: 几何体类型是盒子。
                    *   `size=".1 .2 .3"`: 盒子的尺寸是 0.1x0.2x0.3。
                    *   `rgba="0 .9 0 1"`: 颜色为绿色（RGB: 0, 0.9, 0），不透明度为 1。
        *   整体场景描述：一个绿色的盒子悬浮在红色平面上方，可以自由移动和旋转。当你运行 `load_hello_xml.py` 脚本时，你会看到这个场景的可视化效果，并且盒子会在重力作用下落到平面上。
        *   **常见问题解答**:
            *   Q: 为什么平面和盒子会发生碰撞？
            *   A: 这是因为 MuJoCo 物理仿真引擎的默认行为：
                1.  MuJoCo 默认启用了碰撞检测和响应，当两个几何体在空间中接触或重叠时，引擎会自动计算碰撞力并应用到相关物体上。
                2.  引擎有一套默认的碰撞过滤规则，默认情况下，属于不同刚体（body）的几何体会发生碰撞。在 `hello.xml` 中，平面属于 worldbody（可以看作一个隐式的根刚体），而盒子属于另一个刚体（`<body pos="0 0 1">`），所以它们会碰撞。
                3.  平面和盒子都被定义为具有物理属性的几何体（`<geom>`），引擎会根据它们的几何形状和空间位置来判断是否发生接触。
                4.  在仿真中，默认启用了重力（通常是向下的），盒子在重力作用下会向下移动，直到与平面接触并受到平面的支撑力。
    *   在 macOS 系统下，如果使用 uv 管理项目依赖，可以通过以下命令启动带可视化的仿真：
        ```
        uv run python archive/DT250828_mujoco_learning/load_hello_xml.py
        ```
    *   该脚本使用了 `mujoco.viewer.launch` 方法，该方法在新版本的 mujoco 中可用，可以避免在 macOS 上使用 `mjpython` 的需要。


### 阶段二：系统学习官方教程

5.  **学习官方 Colab 教程**:
    *   按照以下顺序完成官方提供的在线 Colab 教程：
        1.  🌐 [基础入门教程](https://colab.research.google.com/github/google-deepmind/mujoco/blob/main/python/tutorial.ipynb)：学习 MuJoCo 基本概念和使用方法 ✅ (2025-08-30)
            *   📓 本地学习记录：[基础入门教程学习指南](../../archive/DT250828_mujoco_learning/tutorial_guide.md)
            *   学习 MjModel 和 MjData 数据结构
                *   理解 mjModel 包含模型描述，即所有不随时间变化的量
                *   理解 mjData 包含状态和依赖于状态的量
                *   掌握 mjModel 和 mjData 的属性访问方法
            *   掌握 MJCF 建模语言基础
                *   学习 XML 根元素 `<mujoco>` 和世界体 `<worldbody>`
                *   理解几何体 `<geom>` 的定义和属性
                *   掌握刚体 `<body>` 和关节 `<joint>` 的使用
                *   学习默认值和命名规则
            *   学习渲染和仿真的基本操作
                *   掌握 Renderer 对象的使用方法
                *   学习 mj_forward 函数传播数据中的值
                *   理解 mj_step 函数执行仿真步进
            *   理解关节和自由度的概念
                *   学习不同关节类型（hinge、free等）的特点
                *   理解 MuJoCo 的拉格朗日表示法（物体默认没有自由度，需要显式添加关节）
                *   掌握广义坐标和广义速度的概念
            *   掌握接触处理机制
                *   学习接触点和接触力的可视化
                *   理解接触力的测量和分析方法
                *   掌握摩擦参数的设置和影响
            *   学习高级渲染功能
                *   掌握透明度、深度渲染、分割渲染等技术
                *   学习相机矩阵的计算和应用
                *   理解场景修改和多帧渲染

            **第一项教程总结 (2025-08-30)**:

            通过深入学习和实践官方基础入门教程，并结合一系列扩展实验，已圆满完成此部分学习目标，核心成果如下：

            *   **核心概念掌握**:
                *   深入理解了 `mjModel` (模型描述) 和 `mjData` (状态和派生量) 的区别与联系。
                *   熟练掌握了 MJCF 语法，包括 `<mujoco>`, `<worldbody>`, `<geom>`, `<body>`, `<joint>`, `<default>`, `<site>`, `<actuator>` 等关键标签。
                *   透彻理解了关节（Joint）作为约束父子刚体相对运动的核心机制，特别是 `free` 关节（7维 `qpos`）和 `hinge` 关节（1个旋转自由度）的特性。
            *   **实践能力提升**:
                *   成功运行并深入分析了基础示例模型 [hello.xml](../../archive/DT250828_mujoco_learning/hello.xml) / [load_hello_xml.py](../../archive/DT250828_mujoco_learning/load_hello_xml.py)，理解了物理交互（重力、碰撞）的底层逻辑。
                *   通过 [exp_mj_forward.py](../../archive/DT250828_mujoco_learning/exp_mj_forward.py) 实验，直观验证了 `mujoco.mj_forward` 函数在同步状态（如 `qpos`）与其派生量（如 `geom_xpos`）中的关键作用。
                *   通过 [integrated_joint_demo.py](../../archive/DT250828_mujoco_learning/integrated_joint_demo.py) 实验，实践了如何在 MJCF 中为刚体添加关节，并通过代码精确控制其状态。
                *   通过 [exp_contact_demo.py](../../archive/DT250828_mujoco_learning/exp_contact_demo.py) 实验，掌握了接触检测、访问接触信息以及可视化接触点和接触力的方法。
                *   通过 [exp_actuator_demo.py](../../archive/DT250828_mujoco_learning/exp_actuator_demo.py) 实验，初步掌握了 `position` 和 `velocity` 两种执行器（Actuator）的基本原理、行为差异及关键参数（`kp`, `kv`）的调优。
            *   **知识体系构建**:
                *   将学习过程中的关键概念、函数、属性和实践经验系统地整理到了 [tutorial_guide.md](../../archive/DT250828_mujoco_learning/tutorial_guide.md) 中，形成了清晰的学习笔记和未来参考手册。
                *   为进入下一阶段（系统学习后续官方教程或深入研究关键功能）奠定了坚实的基础，具备了独立探索和实验的能力.

        2.  🌐 [模型编辑教程](https://colab.research.google.com/github/google-deepmind/mujoco/blob/main/python/model_editing.ipynb)：掌握如何程序化创建和编辑模型
        3.  🌐 [Rollout 教程](https://colab.research.google.com/github/google-deepmind/mujoco/blob/main/python/rollout.ipynb)：学习使用多线程 rollout 模块
        4.  🌐 [LQR 控制器教程](https://colab.research.google.com/github/google-deepmind/mujoco/blob/main/python/lqr.ipynb)：实现人形单腿平衡控制器
        5.  🌐 [最小二乘法教程](https://colab.research.google.com/github/google-deepmind/mujoco/blob/main/python/least_squares.ipynb)：使用 Python 实现非线性最小二乘求解器
        6.  🌐 [MJX 教程](https://colab.research.google.com/github/google-deepmind/mujoco/blob/main/mjx/tutorial.ipynb)：了解基于 JAX 的 MuJoCo XLA 分支
        7.  🌐 [可微分物理教程](https://colab.research.google.com/github/google-deepmind/mujoco/blob/main/python/differentiable_physics.ipynb)：使用自动推导的物理梯度训练运动策略
    *   每个教程完成后，总结学到的关键概念和技能点
    *   尝试修改教程中的代码，观察不同参数对仿真结果的影响
    *   为每个教程创建本地副本，记录学习笔记和实验结果

### 阶段三：深入研究与实践

6.  **掌握关键功能**:
    *   深入研究 MuJoCo 的关键功能：接触动力学、肌腱建模、actuator 建模。
7.  **学习 API 接口**:
    *   学习 MuJoCo 的 Python API 接口，掌握相关函数的使用方法。
8.  **研究模型实例**:
    *   研究 MuJoCo 官方模型库（Model Gallery）中的复杂模型，如 UR5e 机械臂。

### 阶段四：应用实践

9.  **复现相关研究**:
    *   查找并尝试复现使用 MuJoCo 进行研究的论文实验。
10. **结合其他领域**:
    *   结合特定应用领域（如机器人控制、强化学习）与 MuJoCo 进行实践。
    *   学习 DeepMind 的 dm_control 库。
11. **参与项目或竞赛**:
    *   参与基于 MuJoCo 的项目或竞赛，锻炼实际问题解决能力。

### 阶段五：进阶拓展

12. **自定义开发**:
    *   根据需求对 MuJoCo 进行自定义开发，如创建插件或扩展功能。
13. **关注最新动态**:
    *   关注 MuJoCo 官方网站和社区动态，学习最新特性和技巧。

## 状态

进行中

## 完成日期

(未完成)