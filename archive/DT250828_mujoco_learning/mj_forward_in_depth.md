# 深入理解 `mujoco.mj_forward` 及相关概念 (基于 [`exp_mj_forward.py`](./exp_mj_forward.py))

本文档旨在深入探讨 `mujoco.mj_forward` 函数的作用，并结合 [`exp_mj_forward.py`](./exp_mj_forward.py) 实验脚本，详细解释 `free` 关节的广义坐标 (`qpos`) 以及如何通过修改 `qpos` 来直观感受 `mj_forward` 的必要性。

## 1. `mujoco.mj_forward` 函数详解

### 1.1. 核心作用
`mujoco.mj_forward(model, data)` 是 MuJoCo 中一个至关重要的函数。它的核心作用是：
> **根据当前的模型 (`MjModel`) 和基础状态变量 (`MjData` 中的 `qpos` 和 `qvel`)，计算出所有其他依赖于这些状态的物理量（派生量）。**

这些派生量包括但不限于：
*   `data.geom_xpos`: 几何体在世界坐标系中的位置。
*   `data.geom_xmat`: 几何体在世界坐标系中的方向（旋转矩阵）。
*   `data.qacc`: 广义加速度。
*   `data.qfrc_inverse`: 为了达到当前状态所需的广义力。
*   `data.efc_vel`, `data.efc_J`: 约束相关的速度、雅可比矩阵等。

简单来说，`mj_forward` 是一个“状态传播器”或“状态同步器”，它确保 `MjData` 中所有依赖于基础状态 (`qpos`, `qvel`) 的派生量都是最新的、与基础状态一致的。

### 1.2. 为什么需要 `mj_forward`？

MuJoCo 为了性能优化，**不会**在每次修改 `qpos` 或 `qvel` 后自动重新计算所有派生量。例如，当你直接执行 `data.qpos[:] = new_qpos` 时，`data.geom_xpos` 并不会立即更新。只有在需要这些派生量时（如渲染、访问 `data.geom_xpos`、执行 `mj_step` 等），才需要显式调用 `mj_forward` 来触发计算。

### 1.3. `mj_forward` 内部做了什么？

`mj_forward` 会按顺序调用一系列内部计算函数，主要包括：
1.  **运动学 (`mj_kinematics`)**: 计算所有几何体和标记点 (site) 的位置和方向 (`geom_xpos`, `geom_xmat`, `site_xpos` 等)。这是与 `qpos` 最直接相关的部分。
2.  **质心计算 (`mj_comPos`)**: 计算各个刚体和全系统的质心位置。
3.  **惯性矩阵相关 (`mj_crb`, `mj_factorM` 部分)**: 计算复合刚体惯性 (CRB) 和质量矩阵的 Cholesky 分解因子。
4.  **前向动力学核心 (`mj_forwardSkip`)**:
    *   计算广义加速度 `qacc` (假设无外力和约束)。
    *   计算约束力 `qfrc_constraint`。
    *   计算各种力，如重力 `qfrc_grav`、科里奥利力和离心力 `qfrc_coriolis`、被动摩擦力 `qfrc_passive` 等。

这个过程会填充 `MjData` 结构中的大量字段。

### 1.4. 何时调用 `mj_forward`？

*   **渲染前**: 在修改了 `qpos`/`qvel` 后，调用 `mj_forward` 更新 `geom_xpos` 等几何信息，再调用渲染器，确保看到的是修改后的状态。
*   **访问派生量前**: 在读取任何依赖于 `qpos`/`qvel` 的派生量（如 `geom_xpos`, `site_xvel_lin`, `qacc`, `sensor_data` 等）之前，确保它们是最新的。
*   **`mj_step` 内部**: `mj_step` 会自动调用等效于 `mj_forward` 的计算来获取加速度等用于积分的量。通常你不需要在 `mj_step` 循环内额外调用它。

### 1.5. 与 `mj_step` 的关系

*   `mj_step(model, data)`: 是完整的仿真步进函数，它会根据当前状态 (`data.qpos`, `data.qvel`) 和作用力 (`data.qfrc_applied` 等)，计算下一步的新状态。
*   `mj_forward(model, data)`: 是 `mj_step` 内部用于计算当前状态派生量的关键步骤。
*   **关系**: 可以将 `mj_forward` 看作是“根据当前状态计算所有后果”，而 `mj_step` 是“根据当前状态和这些后果（如加速度）来更新状态”。

## 2. 示例：直观感受 `mj_forward` (来自 `exp_mj_forward.py`)

脚本 `archive/DT250828_mujoco_learning/exp_mj_forward.py` 提供了一个非常直观的例子来展示 `mj_forward` 的作用。

### 2.1. 实验设计思路

1.  **创建模型**: 定义一个简单的模型，包含一个 `body`，该 `body` 通过一个 `free` 关节连接到世界，允许其自由移动和旋转。在该 `body` 上附着一个 `box` 和一个 `sphere`。
2.  **场景 A (初始状态)**:
    *   重置模型状态 (`mj_resetData`)。
    *   调用 `mj_forward` 计算初始派生量。
    *   打印并保存初始的 `geom_xpos` 和渲染图 (`tmp-output-scene_A.png`)。
3.  **场景 B (修改 `qpos` 并观察 `mj_forward` 的作用)**:
    *   **直接修改 `qpos`**: 将 `body` 的 `qpos` 设置为一个新的值，例如平移到 `(0.5, 0.3, 0.1)` 并绕Z轴旋转45度 (`data.qpos[:] = [0.5, 0.3, 0.1, qw, 0, 0, qz]`)。
    *   **关键观察 (数据 1)**: **不调用 `mj_forward`**，立即打印 `geom_xpos`。会发现 `geom_xpos` 的值 **没有变化**，仍然与场景 A 中的值相同。
    *   **调用 `mj_forward`**: 显式调用 `mujoco.mj_forward(model, data)`。
    *   **关键观察 (数据 2)**: 再次打印 `geom_xpos`。会发现 `geom_xpos` 的值 **已经更新**，正确反映了 `body` 新的位置和旋转。
    *   **关键观察 (图像)**: 渲染并保存图像 (`tmp-output-scene_B.png`)，图像显示物体已移动和旋转。

### 2.4. 实验核心结论

*   **直接修改 `data.qpos` 不会自动更新 `data.geom_xpos` 等派生量**。这是实验最直观的证明。通过对比修改 `qpos` 后、调用 `mj_forward` 前打印的 `geom_xpos` 值（值未变）与调用 `mj_forward` 后再次打印的 `geom_xpos` 值（值已变），可以清晰地看到这一点。
*   **必须显式调用 `mujoco.mj_forward(model, data)` 来同步状态**。只有调用它之后，所有依赖于 `qpos` 的派生量才会被正确计算和更新。
*   **`mujoco.Renderer` 的工作依赖于最新的派生量**。脚本最后调用 `mj_forward` 后进行渲染，确保了图像反映了 `qpos` 修改后的正确状态。
*   **相关文件**:
    *   实验脚本: [`exp_mj_forward.py`](./exp_mj_forward.py)

## 3. 理解 `free` 关节的广义坐标 `qpos`

在 MuJoCo 中，一个 `free` 关节给予刚体最大的自由度：3个平移自由度 + 3个旋转自由度，总共6个自由度。

`qpos` 是存储系统所有关节广义位置的数组。对于一个 `free` 关节，它在 `qpos` 中占据 **7** 个连续的元素。

### 3.1. `qpos` 的 7 维结构

对于 `body` 的 `free` 关节，其对应的 `qpos` 为一个7维向量：
`[ x, y, z, qw, qx, qy, qz ]`

*   **`x, y, z` (索引 0, 1, 2)**:
    *   这三个值直接定义了该 `body` 的局部坐标系原点在世界坐标系中的 **平移位置**。
    *   例如，`[0.5, 0.3, 0.1]` 表示将 `body` 的原点移动到世界坐标 `(0.5, 0.3, 0.1)`。

*   **`qw, qx, qy, qz` (索引 3, 4, 5, 6)**:
    *   这四个值共同构成一个 **单位四元数 (Unit Quaternion)**，用来描述该 `body` 的局部坐标系相对于世界坐标系的 **旋转**。
    *   **四元数是什么？**：四元数是一种用于表示3D旋转的数学工具，形式为 `q = qw + i*qx + j*qy + k*qz`，其中 `qw` 是实部，`qx, qy, qz` 是虚部。单位四元数满足 `qw^2 + qx^2 + qy^2 + qz^2 = 1`。
    *   **为什么用四元数？**：相比于欧拉角（如 Roll, Pitch, Yaw），四元数没有“万向锁”问题，并且在插值和计算上更高效、稳定。

### 3.2. 示例：绕 Z 轴旋转

假设我们想让 `body` 绕其自身的 **Z 轴** 旋转一个角度 `angle_z`（以弧度为单位）。

*   旋转轴是 `(0, 0, 1)` (Z轴单位向量)。
*   对应的单位四元数计算公式为：
    *   `qw = cos(angle_z / 2)`
    *   `qx = axis_x * sin(angle_z / 2) = 0 * sin(...) = 0`
    *   `qy = axis_y * sin(angle_z / 2) = 0 * sin(...) = 0`
    *   `qz = axis_z * sin(angle_z / 2) = 1 * sin(angle_z / 2) = sin(angle_z / 2)`

*   因此，绕Z轴旋转 `angle_z` 的四元数是 `[cos(angle_z/2), 0, 0, sin(angle_z/2)]`。

*   **在代码中应用**:
    ```python
    import numpy as np
    dx, dy, dz = 0.5, 0.3, 0.1 # 平移
    angle_z = np.pi / 4.0       # 旋转角度 (例如 45度 = pi/4 弧度)
    qw = np.cos(angle_z / 2.0)
    qz = np.sin(angle_z / 2.0)
    # 构造新的 qpos
    new_qpos = np.array([dx, dy, dz, qw, 0.0, 0.0, qz])
    # 应用到数据
    data.qpos[:] = new_qpos
    ```
    这行代码 `data.qpos[:] = new_qpos` 的含义是：
    1.  将 `body` 的原点平移到世界坐标 `(dx, dy, dz)`。
    2.  将 `body` 绕其自身的 Z 轴旋转 `angle_z` 角度。

### 3.3. `mj_forward` 如何处理 `qpos` 中的平移和旋转？

当 `mj_forward` (或其内部的 `mj_kinematics`) 被调用时，它会读取 `body` 的 `qpos`。

1.  **处理平移 (`x, y, z`)**:
    *   `body` 原点的世界坐标位置直接设置为 `[x, y, z]`。

2.  **处理旋转 (`qw, qx, qy, qz`)**:
    *   MuJoCo 内部会使用这个四元数来计算 `body` 局部坐标系相对于世界坐标系的旋转矩阵 (`xmat`)。
    *   对于附着在 `body` 上的每个几何体 (`geom`)，其局部坐标偏移 (`geom.pos`) 会通过这个旋转矩阵变换到世界坐标系中。

3.  **计算 `geom_xpos`**:
    *   最终，每个 `geom` 的世界坐标位置 `geom_xpos` 由以下公式计算得出：
        `geom_world_pos = body_world_pos + rotate(body_world_rot, geom_local_pos)`
        其中 `body_world_pos` 是 `[x, y, z]`，`rotate` 是由四元数 `[qw, qx, qy, qz]` 确定的旋转操作，`geom_local_pos` 是该几何体相对于 `body` 原点的局部坐标 (`geom.pos`)。

通过 [`exp_mj_forward.py`](./exp_mj_forward.py) 实验，我们可以看到，如果不调用 `mj_forward`，即使 `qpos` 改变了，`geom_xpos` 也不会更新，从而导致状态不一致。这清晰地证明了 `mj_forward` 在同步模型状态中的核心作用。