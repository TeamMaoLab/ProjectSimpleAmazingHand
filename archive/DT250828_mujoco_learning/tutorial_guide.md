# MuJoCo 基础入门教程学习指南

## 教程概览

本教程是 MuJoCo Python API 的入门指南，通过实际代码示例介绍 MuJoCo 的核心概念和基本使用方法。教程涵盖了从模型创建、仿真执行到结果可视化的完整流程。

## 你应该熟练掌握的内容（重点技能）

### 1. 核心数据结构操作
- **MjModel 和 MjData 的创建与使用**
  - 熟练使用 `mujoco.MjModel.from_xml_string()` 从 XML 字符串创建模型
  - 熟练创建 `mujoco.MjData` 实例
  - 熟练访问和修改模型及数据的属性
  
  相关代码示例：
  ```python
  xml = """
  <mujoco>
    <worldbody>
      <geom name="red_box" type="box" size=".2 .2 .2" rgba="1 0 0 1"/>
      <geom name="green_sphere" pos=".2 .2 .2" size=".1" rgba="0 1 0 1"/>
    </worldbody>
  </mujoco>
  """
  model = mujoco.MjModel.from_xml_string(xml)
  data = mujoco.MjData(model)
  ```

### 2. 基本仿真流程
- **仿真循环的实现**
  - 熟练使用 `mujoco.mj_step(model, data)` 执行仿真步进
  - 熟练使用 `mujoco.mj_forward(model, data)` 传播数据值
    - **理解 `mj_forward`**: `mj_forward` 函数根据当前的模型 (`MjModel`) 和基础状态变量 (`MjData` 中的 `qpos` 和 `qvel`)，计算出所有其他依赖于这些状态的物理量（如几何体位置 `geom_xpos`、广义加速度 `qacc` 等）。它是一个“状态传播器”，确保 `MjData` 中的派生量是最新的。在修改了 `qpos`/`qvel` 后进行渲染或访问派生量前，通常需要调用此函数。
      - **为什么需要 `mj_forward`？** 为了性能，MuJoCo 并不总是实时计算所有派生量（如 `geom_xpos`, `site_xvel_lin` 等）。这些量依赖于基础状态 `qpos` 和 `qvel`。直接修改 `qpos`/`qvel` 或在 `mj_step` 之外，这些派生量不会自动更新。`mj_forward` 就是用来显式触发这些计算的。
      - **`mj_forward` 内部做了什么？** 它会按顺序调用一系列内部函数，计算运动学（`mj_kinematics`：更新 `geom_xpos` 等）、质心（`mj_comPos`）、惯性矩阵（`mj_crb`, `mj_factorM` 部分）、以及最重要的前向动力学核心（`mj_forwardSkip`：计算 `qacc`、约束力 `qfrc_constraint` 以及各种力如重力、科里奥利力）。这个过程填充了 `MjData` 中大量字段。
      - **何时调用 `mj_forward`？**
        1.  **渲染前**：修改 `qpos`/`qvel` 后，调用 `mj_forward` 更新 `geom_xpos` 等，再调用渲染器，确保看到的是修改后的状态。
        2.  **访问派生量前**：在读取 `geom_xpos`, `qacc`, `sensor_data` 等之前，确保它们是最新的。
        3.  **`mj_step` 内部**：`mj_step` 会自动调用等效于 `mj_forward` 的计算来获取加速度等用于积分的量。通常你不需要在 `mj_step` 循环内额外调用它。
      - **与 `mj_step` 的关系**：`mj_step` 是完整的仿真步进函数，包含了状态更新。`mj_forward` 是 `mj_step` 内部用于计算当前状态派生量的关键步骤。可以将 `mj_forward` 看作是“根据状态计算所有后果”，而 `mj_step` 是“根据状态和后果来更新状态”。
      - **示例：直观感受 `mj_forward` (来自 `exp_mj_forward.py`)**: 通过一个具体例子可以更直观地理解。创建一个包含 `free` 关节的 `body`，其 `qpos` 为7维向量 `[x, y, z, qw, qx, qy, qz]`。直接修改 `data.qpos[:] = [dx, dy, dz, qw, qx, qy, qz]` 改变了 `body` 的位置和旋转状态，但此时 `data.geom_xpos`（各几何体的世界坐标）并未更新。打印 `geom_xpos` 会发现其值仍是旧的。只有在调用 `mujoco.mj_forward(model, data)` 之后，`geom_xpos` 才会根据新的 `qpos` 计算并更新，此时再打印 `geom_xpos` 会得到反映新状态的坐标值。这证明了 `mj_forward` 是同步状态的关键。
  - 熟练控制仿真时间和步长
  
  相关代码示例：
  ```python
  # 重置数据和时间
  mujoco.mj_resetData(model, data)
  
  # 仿真步进
  while data.time < duration:
      mujoco.mj_step(model, data)
  ```

### 3. 渲染技术
- **可视化基础**
  - 熟练使用 `mujoco.Renderer` 进行场景渲染
  - 熟练调用 `renderer.update_scene(data)` 更新场景
    - **理解 `update_scene`**: 此方法根据传入的 `MjData` 对象，更新渲染器内部的场景表示。它会读取 `data` 中的最新状态（如 `geom_xpos`, `geom_rgba` 等），为最终生成图像做准备。
  - 熟练使用 `renderer.render()` 生成图像
    - **理解 `render`**: 此方法是实际的“绘图”操作。它根据 `update_scene` 设置好的场景状态，生成一张代表当前视角下画面的图像（通常是一个 NumPy 数组）。可以将其视为对当前场景的“快照”。
  
  相关代码示例：
  ```python
  with mujoco.Renderer(model) as renderer:
      mujoco.mj_forward(model, data) # 确保 geom_xpos 等是新的
      renderer.update_scene(data)    # 告诉渲染器用新状态更新场景
      media.show_image(renderer.render()) # 生成并显示图像快照
  ```

### 4. 命名访问机制
- **通过名称访问模型元素**
  - 熟练使用 `model.geom('name')`、`model.body('name')` 等访问器
  - 熟练获取和设置元素属性，如 `model.geom('sphere').rgba`
  
  相关代码示例：
  ```python
  # 获取几何体属性
  model.geom('green_sphere').rgba
  
  # 设置几何体属性
  model.geom('red_box').rgba[:3] = np.random.rand(3)
  ```

## 你应该深入理解的内容（核心概念）

### 1. 物理仿真基础概念
- **广义坐标与广义速度**
  - 理解 `data.qpos`（广义位置）和 `data.qvel`（广义速度）的含义
  - 理解不同关节类型的自由度数量（如自由关节6个自由度，铰链关节1个自由度）
  - **深入理解 `free` 关节的 `qpos` (来自 `exp_mj_forward.py`)**: `free` 关节的 `qpos` 是一个7维向量 `[x, y, z, qw, qx, qy, qz]`。
    - 前3个元素 (`x, y, z`) 直接表示刚体原点在世界坐标系中的平移位置。
    - 后4个元素 (`qw, qx, qy, qz`) 是一个单位四元数，表示刚体相对于世界坐标系的旋转。
      - **四元数示例 (绕Z轴旋转)**: 若想让刚体绕其Z轴（也是世界Z轴）旋转 `angle_z`  角度，对应的四元数为 `[qw, qx, qy, qz] = [cos(angle_z/2), 0, 0, sin(angle_z/2)]`。在代码中设置 `data.qpos[:] = [dx, dy, dz, np.cos(angle_z/2), 0, 0, np.sin(angle_z/2)]` 即可实现先平移到 `(dx, dy, dz)` 再绕Z轴旋转 `angle_z`。
  - **深入理解 `hinge` 关节的自由度与作用 (来自对链式摆模型的分析)**:
    - **自由度**: `hinge` 关节只提供 **1** 个自由度，即绕其指定轴的旋转角度。
    - **直觉理解**: 可以将 `hinge` 关节的作用形象地理解为“**一个固定连接点 + 一个固定旋转轴**”。子物体被“钉”在父物体上的一个点，并且只能绕穿过该点的一个固定轴旋转。
  - **深入理解 `data.qpos` 的结构**:
    - `data.qpos` 是一个一维数组，它按顺序存储了模型中**所有关节**的广义位置。
    - 这些信息是按照关节在模型中定义的顺序（或内部ID顺序）依次排列的。
    - 不同类型的关节具有不同数量的自由度，因此在 `qpos` 数组中占用的元素数量也不同：
      - `free` 关节: 有 **7** 个自由度。这对应 `qpos` 中连续的 7 个元素：前 3 个表示笛卡尔坐标 (x, y, z)；后 4 个表示单位四元数 (qw, qx, qy, qz) 来描述旋转。
      - `hinge` 关节: 有 **1** 个自由度。这对应 `qpos` 中的 1 个元素，表示绕其轴的旋转角度（以弧度为单位）。
      - `slide` 关节: 有 **1** 个自由度，表示平移距离。
      - `ball` 关节: 有 **3** 个自由度，用四元数表示旋转。
    - 通过索引访问 `data.qpos` 数组，您可以精确地读取或修改任何一个关节的状态。例如，在一个包含一个 `free` 关节和一个 `hinge` 关节的模型中，`data.qpos[0:7]` 对应 `free` 关节的 7 个广义位置，`data.qpos[7]` 对应 `hinge` 关节的 1 个广义位置（角度）。
    - **核心理解**: `data.qpos` 中存储的值，本质上是每个关节对其连接的父子刚体之间相对运动的描述。理解关节如何约束运动是解读 `qpos` 内容的关键。

### 2. 模型与数据的关系
- **MjModel 与 MjData 的区别与联系**
  - 理解 MjModel 包含不随时间变化的量（模型描述）
  - 理解 MjData 包含随时间变化的量（状态和函数）
  - 理解为什么需要调用 `mj_forward` 来计算派生量
  
  相关代码示例：
  ```python
  # 访问模型属性（不随时间变化）
  model.ngeom
  model.geom_rgba
  
  # 访问数据属性（随时间变化）
  data.geom_xpos  # 需要调用 mj_kinematics 或 mj_forward 来更新
  ```

### 3. MJCF 建模语言核心元素
- **基本标签的作用**
  - 理解 `<mujoco>`、`<worldbody>`、`<geom>`、`<body>`、`<joint>` 的作用
  - 理解默认值机制（如未指定位置默认为 0 0 0，未指定几何体类型默认为 sphere）
  
  相关代码示例：
  ```xml
  <mujoco>
    <worldbody>
      <!-- 未指定位置，默认在原点 -->
      <!-- 未指定类型，默认为 sphere -->
      <geom name="red_box" type="box" size=".2 .2 .2" rgba="1 0 0 1"/>
      <geom name="green_sphere" pos=".2 .2 .2" size=".1" rgba="0 1 0 1"/>
    </worldbody>
  </mujoco>
  ```

### 4. 关节与自由度概念
- **拉格朗日表示法**
  - 理解 MuJoCo 中物体默认没有自由度，需要通过关节显式添加
  - 理解不同关节类型的特点和应用场景
  - **核心概念：关节是连接父子刚体的约束 (来自对 hinge 关节作用范围的深入理解)**:
    - **首要原则**: 关节（Joint）的核心作用是**约束**它所连接的两个物体（父物体和子物体）之间的相对运动。这是理解所有关节类型的基石。
    - **位置**: 每个关节都定义在**子物体** (`body`) 的标签内部。
    - **连接点**: 关节隐式地定义了子物体的**原点**（由子物体的 `pos` 属性相对于其父物体定义）与其父物体上一个固定点的连接。
    - **自由度**: 不同类型的关节通过施加不同形式的约束，将子物体相对于父物体的 6 个自由度（3 平移 + 3 旋转）减少到特定的数量。
      - `free`: 0 个约束，6 个自由度。
      - `hinge`: 5 个约束（固定连接点 + 固定旋转轴），1 个自由度（绕轴旋转角度）。
      - `slide`: 5 个约束（固定连接点 + 固定平移轴），1 个自由度（沿轴平移距离）。
      - `ball`: 3 个约束（固定连接点），3 个自由度（绕任意轴旋转，通常用四元数表示）。
  - **关节约束与层级关系 (来自 `integrated_joint_demo.py`)**: 
    - **Q: 在 `integrated_joint_demo.py` 中，为什么摆臂 (`hinge_body`) 自身不会自然下落？**
    - **A:** 在 `integrated_joint_demo.py` 的 MuJoCo 模型中，摆臂 (`hinge_body`) 没有自然下落的原因在于**关节的约束设置和模型的层级关系**，具体分析如下：
      1.  **摆臂的关节约束了其运动自由度**：摆臂的 `hinge_joint` 是一个**铰链关节**（类型为 `hinge`），其 `axis="0 1 0"` 定义了关节的旋转轴为Y轴（垂直于地面平面）。
          *   铰链关节的特性是：只允许绕指定轴旋转，限制了其他5个自由度（3个平移+2个旋转）。
          *   在这个模型中，`hinge_joint` 的 `pos="0 0 0"` 表示关节原点与 `hinge_body` 的原点重合，而 `hinge_body` 的 `pos="1 0 0"` 是其在世界坐标系中的初始位置。
          *   因此，摆臂被约束为**只能绕Y轴旋转**，但关节本身没有被“固定”在某个父物体上——这会导致摆臂的运动看似“异常”，但核心原因是下面的层级关系问题。
      2.  **摆臂是顶级body，没有父物体约束**：在 MuJoCo 的 `worldbody` 中，直接定义的 `body`（如 `free_body` 和 `hinge_body`）都是**顶级body**，它们的父物体是世界坐标系（默认固定），但关节的作用对象取决于层级关系：
          *   对于顶级body，其关节（如 `hinge_joint`）的作用是**约束该body自身相对于世界坐标系的运动**。
          *   但 `hinge_joint` 仅限制了摆臂的旋转轴，但不限制其**平移自由度**（因为铰链关节不限制平移）。
          *   然而，在你的模型中，摆臂没有下落的真正原因是：**MuJoCo中，顶级body如果没有被关节约束到固定物体上，且关节类型不限制平移，理论上会受重力影响平移下落，但你的模型中摆臂的几何结构和关节参数可能导致了“视觉上的静止”**。
          *   更可能的细节是：摆臂的初始位置 `pos="1 0 0"` 的Z坐标为0，而地面 `floor` 的Z坐标为-0.5，摆臂的最低处（`hinge_arm` 的capsule几何）初始时可能已经与地面接触，被地面的碰撞约束“托住”，因此没有明显下落。
          *   若调整摆臂的初始Z坐标（如 `pos="1 0 2"`），使其远离地面，重新运行仿真会发现：摆臂会在重力作用下向下平移，同时绕Y轴旋转（因为铰链关节不限制Z方向的平移）。
      3.  **总结**：摆臂没有“自然下落”是因为：
          *   初始位置可能与地面接触，被地面的碰撞约束阻止了下落；
          *   铰链关节仅限制旋转轴，但不限制平移，若初始位置远离地面，摆臂会同时下落并旋转。
      4.  **如何实现“单摆”效果**：若想让摆臂像“单摆”一样绕固定点旋转（仅旋转、不下落），需要将其设置为**子body**，并将关节连接到一个固定的父body上（如地面的子body）。
  - **深入理解 `hinge` 关节的作用范围 (来自对链式摆模型的分析)**:
    - **核心概念**: `hinge` 关节（以及其他所有关节类型）的作用是**约束**它所连接的两个物体（父物体和子物体）之间的相对运动。
    - **自由度**: 一个 `hinge` 关节只提供 **1** 个自由度，即绕其指定轴的旋转角度。
    - **作用范围**:
      1.  **连接点**: 关节总是定义在**子物体** (`body`) 的标签内。这个关节隐式地定义了子物体的**原点**（由子物体的 `pos` 属性相对于其父物体定义）与其父物体上一个固定点的连接。这个连接点可以直观地理解为“质心连接点”。
      2.  **约束运动**: `hinge` 关节将子物体的 6 个自由度（3平移 + 3旋转）**约束**到只剩下 1 个自由度——即绕关节轴的旋转。
      3.  **活动轴**: `hinge` 的 `axis` 参数指定了这个唯一的旋转轴。该轴的方向是在**父物体**的坐标系中定义的。
    - **直觉理解**: 可以将 `hinge` 关节的作用形象地理解为“**一个固定连接点 + 一个固定旋转轴**”。子物体被“钉”在父物体上的一个点，并且只能绕穿过该点的一个固定轴旋转。
  
  相关代码示例：
  ```xml
  <body name="box_and_sphere" euler="0 0 -30">
    <!-- 添加铰链关节 -->
    <joint name="swing" type="hinge" axis="1 -1 0" pos="-.2 -.2 -.2"/>
    <geom name="red_box" type="box" size=".2 .2 .2" rgba="1 0 0 1"/>
    <geom name="green_sphere" pos=".2 .2 .2" size=".1" rgba="0 1 0 1"/>
  </body>
  ```

### 5. 接触与碰撞机制
- **物理交互基础**
  - 理解为什么需要调用特定函数来计算接触力和几何体位置
  - 理解碰撞检测的基本原理
  - **深入理解接触信息的获取与可视化 (来自 `exp_contact_demo.py`)**: 通过 `exp_contact_demo.py` 实验，可以深入理解如何检测、访问和可视化接触信息。
    - **接触检测的触发**: MuJoCo 的物理引擎在 `mj_step` 或 `mj_forward` (更具体是 `mj_fwdPosition` 内部调用的 `mj_collision`) 过程中自动进行碰撞检测。当两个几何体发生重叠或接触时，相关信息会被计算并存储。
    - **访问接触数据**: 仿真或前向计算后，可以通过 `data.ncon` (当前存储的接触数量) 和 `data.nefc` (有效接触约束数量) 来判断是否有接触发生。详细的接触信息存储在 `data.contact` 数组中。遍历此数组可以获取每个接触点的具体信息，如：
      - `contact.geom1`, `contact.geom2`: 参与接触的两个几何体的 ID。
      - `contact.pos`: 接触点在世界坐标系中的位置。
      - `contact.frame[:3]`: 接触点的法线向量（从 `geom1` 指向 `geom2`）。
    - **`geom_xpos` 的关键作用**: 碰撞检测依赖于准确的几何体位置。如果直接修改了 `qpos` 而没有调用 `mj_forward` 或 `mj_kinematics` 来更新 `geom_xpos`，碰撞检测将基于过时的位置信息进行，可能导致无法正确检测到接触，如 `exp_contact_demo.py` 的对比实验所示。
    - **可视化接触**: 使用 `mujoco.Renderer` 时，可以通过配置 `mujoco.MjvOption` 对象来开启接触点和接触力的可视化。
      - `scene_option.flags[mujoco.mjtVisFlag.mjVIS_CONTACTPOINT] = True`: 显示接触点（通常为红色小球）。
      - `scene_option.flags[mujoco.mjtVisFlag.mjVIS_CONTACTFORCE] = True`: 显示接触力（通常为从接触点出发的线段，长度和方向表示力的大小和方向）。
  
  相关代码示例：
  ```python
  # 需要调用 mj_kinematics 来计算几何体的全局位置
  mujoco.mj_kinematics(model, data)
  print('geom positions:', data.geom_xpos)
  
  # --- 来自 exp_contact_demo.py 的示例 ---
  # 在 mj_step 或 mj_forward 之后检查接触
  if data.ncon > 0:
      for i in range(data.ncon):
          contact = data.contact[i]
          geom1_id = contact.geom1
          geom2_id = contact.geom2
          geom1_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom1_id)
          geom2_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom2_id)
          contact_pos = contact.pos
          contact_normal = contact.frame[:3]
          print(f"Contact between {geom1_name} and {geom2_name} at {contact_pos}, normal {contact_normal}")

  # --- 来自 exp_contact_demo.py 的可视化示例 ---
  with mujoco.Renderer(model) as renderer:
      scene_option = mujoco.MjvOption()
      scene_option.flags[mujoco.mjtVisFlag.mjVIS_CONTACTPOINT] = True
      scene_option.flags[mujoco.mjtVisFlag.mjVIS_CONTACTFORCE] = True
      renderer.update_scene(data, scene_option=scene_option)
      image = renderer.render()
  ```

## 你应该了解的内容（扩展知识）

### 1. 高级可视化选项
- **渲染增强功能**
  - 了解透明度、关节可视化、接触点可视化等选项
  - 了解深度渲染和分割渲染的概念
  - 了解相机控制和场景修改方法
  
  相关代码示例：
  ```python
  # 启用关节可视化
  scene_option = mujoco.MjvOption()
  scene_option.flags[mujoco.mjtVisFlag.mjVIS_JOINT] = True
  ```

### 2. 模型复杂性
- **高级建模元素**
  - 了解肌腱、执行器、传感器等概念
  - 了解关键帧(keyframe)的使用
  - 了解资产(assets)如纹理和材质的定义
  
  相关代码示例：
  ```xml
  <keyframe>
    <key name="spinning" qpos="0 0 0.02 1 0 0 0" qvel="0 0 0 0 1 200" />
  </keyframe>
  ```

### 3. 仿真控制
- **高级仿真参数**
  - 了解时间步长(timestep)对仿真精度的影响
    - **默认时间步长**: MuJoCo 仿真中的每个 `step` 推进的仿真时间长度由 `mjModel` 的 `opt.timestep` 参数定义。如果在模型文件 (MJCF 或 URDF) 中未显式指定，`opt.timestep` 的默认值通常为 **0.002 秒**。
    - **仿真时间 vs. 实际计算时间**: `opt.timestep` 定义的是仿真世界前进的时间量。而执行 `mj_step` 所需的真实计算机时间（CPU 时间）是不固定的，取决于模型复杂度、计算机性能等因素。选择合适的 `timestep` 需要在仿真精度和计算效率之间进行权衡。较小的步长通常能提供更高的精度，但也需要更多的计算资源。
  - 了解不同积分器(如RK4)的特点
  - 了解仿真稳定性和发散的概念
  
  相关代码示例：
  ```xml
  <!-- 在 MJCF 文件中设置 timestep -->
  <mujoco model="my_model">
    <option timestep="0.001" integrator="RK4"/>
    <!-- 模型内容 -->
  </mujoco>
  ```
  ```python
  # 在 Python 中访问或修改 timestep
  # 假设 model 是已加载的 mujoco.MjModel 实例
  print(f"当前仿真时间步长: {model.opt.timestep} 秒")
  # model.opt.timestep = 0.001 # 可以修改，但通常在加载模型后立即设置
  ```

### 4. 性能考量
- **效率优化**
  - 了解渲染与仿真的性能差异
  - 了解批量仿真的概念
  - 了解多线程处理的可能性

### 5. 深入学习资源
- **详细解析文档**
  - [mj_forward_in_depth.md](./mj_forward_in_depth.md): 一份专门深入探讨 `mujoco.mj_forward` 函数、`free` 关节 `qpos` 结构以及如何通过实验 (`exp_mj_forward.py`) 直观理解这些概念的详细文档.
    - **内容概要**: 
      - `mujoco.mj_forward` 的核心作用、内部机制、调用时机及与 `mj_step` 的关系。
      - 通过 `exp_mj_forward.py` 实验脚本，直观展示修改 `qpos` 后调用/不调用 `mj_forward` 对 `geom_xpos` 等派生量的影响。
      - 详细解释 `free` 关节 7 维 `qpos` 向量 (`[x, y, z, qw, qx, qy, qz]`) 中平移和四元数旋转的含义及应用示例。
  - Actuator 学习资源 (来自 `exp_actuator_demo.py`):
    - **核心概念**:
      - `Actuator` 是为模型添加主动驱动力的方式，使模型能从外部控制信号 (`data.ctrl`) 驱动。
      - 它将模型从被动修改 `qpos`/`qvel` 转变为主动驱动的动态系统，更接近真实世界的物理交互。
    - **关键类型与区别**:
      - `<motor>`: 直接指定施加的力/力矩。用户需要自行处理稳定性和轨迹跟踪。
      - `<position>`: 指定目标角度。内部有控制器逻辑（如 PID），自动计算力矩使关节到达并保持目标角度。稳定性受 `kp` (比例增益) 和 `kv` (微分/阻尼增益) 参数影响。
      - `<velocity>`: 指定目标速度。内部控制器自动计算力矩使关节维持指定速度。
    - **实践理解**:
      - 通过 [`exp_actuator_demo.py`](./exp_actuator_demo.py) 示例，直观体验了 `motor`, `position`, `velocity` 三种执行器的行为差异。
      - 学会了通过 `kp` 和 `kv` 调整 `<position>` 执行器的响应，以平衡响应速度和稳定性，消除“抖动”现象。
      - ~~理解了 `data.ctrl` 是用户设置的控制输入，而 `data.actuator_force` 是执行器实际施加到关节上的力，两者可能因物理限制（如速度、加速度极限）而不同。~~
    - **关键属性**:
      - `model.nu`: 执行器数量。
      - `data.ctrl`: 一维数组，存储用户为每个执行器提供的控制信号。
      - `data.actuator_force`: 一维数组，存储每个执行器实际产生的广义力。

## 学习重点提示

1.  **动手实践最重要**：每个概念都要通过实际代码运行来验证理解
2.  **关注命名访问**：这是 MuJoCo Python API 的重要特性，能让你的代码更具可读性
3.  **理解数据流**：掌握从模型创建到仿真执行再到可视化显示的完整流程
4.  **注意细节差异**：如位置(qpos)和速度(qvel)维度可能不同的情况（特别是涉及四元数时）
5.  **实践总结**：
    -   首先，通过 [`exp_mj_forward.py`](./exp_mj_forward.py) 示例，可以直观地理解 `mujoco.mj_forward` 函数的作用，特别是对于 `free` 关节的 7 维 `qpos` 向量（`[x, y, z, qw, qx, qy, qz]`）以及修改 `qpos` 后调用 `mj_forward` 对同步派生量（如 `geom_xpos`）的必要性。
    -   然后，通过 [`integrated_joint_demo.py`](./integrated_joint_demo.py) 示例，可以深入理解 `data.qpos` 的整体结构（包含所有关节的广义位置）以及如何通过修改 `qpos` 来精确控制不同关节（如 `hinge` 和 `free`）连接的刚体状态。该示例还演示了如何在 MJCF 模型中为 `body` 添加 `joint`，并使用 `mujoco.Renderer` 可视化修改后的结果。
    -   最后，通过 [`exp_contact_demo.py`](./exp_contact_demo.py) 示例，可以学习如何检测、访问和可视化物体间的接触与碰撞信息，理解 `geom_xpos` 更新对接触计算的重要性，并掌握使用 `mjvOption` 在渲染器中开启接触点和接触力可视化的方法。
6.  **核心概念强化**:
    -   **Joint关节即约束**: 牢记关节的核心作用是约束子 `body` 相对于其父 `body` 的运动。这是理解 MuJoCo 动力学建模的基石。
7.  **扩展探索起点**:
    -   **Actuator 进阶**:
        -   已通过 `exp_actuator_demo.py` 直观理解 `motor`, `position`, `velocity` 执行器的基本行为和参数 (`kp`, `kv`) 调优。
        -   **待探索**: 如何通过代码直接读写 `data.ctrl` 和 `data.actuator_force` 进行程序化控制与监控。

## 关键函数和概念总结

### 核心函数
- `mujoco.MjModel.from_xml_string()`: 从 XML 字符串创建模型
- `mujoco.MjData()`: 创建数据实例
- `mujoco.mj_step()`: 执行仿真步进
- `mujoco.mj_forward()`: 传播数据值
- `mujoco.Renderer`: 渲染器类

### 重要属性
- `model.nv`: 模型的自由度数量
- `model.ngeom`: 几何体数量
- `data.qpos`: 广义位置
- `data.qvel`: 广义速度
- `data.geom_xpos`: 几何体位置（需要更新）
- `data.ncon`: 当前检测到的接触数量（来自 `exp_contact_demo.py`）
- `data.nefc`: 当前有效的接触约束数量（来自 `exp_contact_demo.py`）
- `data.contact`: 存储接触点详细信息的数组（来自 `exp_contact_demo.py`）

### 可视化选项
- `mujoco.MjvOption`: 可视化选项类
- `mjVIS_JOINT`: 关节可视化标志
- `mjVIS_CONTACTPOINT`: 接触点可视化标志（来自 `exp_contact_demo.py`）
- `mjVIS_CONTACTFORCE`: 接触力可视化标志（来自 `exp_contact_demo.py`）