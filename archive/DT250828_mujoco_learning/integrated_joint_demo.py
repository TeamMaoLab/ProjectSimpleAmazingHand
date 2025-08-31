#!/usr/bin/env python3
"""
一体化 MuJoCo 示例，用于学习 MJCF 建模、关节自由度和接触碰撞机制。

此脚本将 MJCF 模型定义直接嵌入在 Python 代码中，并启动一个基本的交互式查看器。
通过修改代码中的 qpos 来观察模型状态变化。
同时演示如何使用 Renderer 导出图像到临时目录 (tmp_renders)。
"""

import mujoco
import mujoco.viewer
import time
import numpy as np
import math
import os


def render_and_save(model, data, filename):
    """使用 Renderer 渲染当前场景并保存为 PNG 图像到临时目录。"""
    try:
        # 创建渲染器，尺寸为 640x480
        renderer = mujoco.Renderer(model, height=480, width=640)
        # 更新场景（必须在 render 之前调用）
        renderer.update_scene(data)
        # 渲染图像
        image = renderer.render()
        
        # 保存图像到临时目录
        # 使用相对于当前脚本的路径，并添加 tmp 前缀以符合项目规则
        import inspect
        import os
        # 获取当前函数所在文件的目录
        current_file = inspect.getfile(inspect.currentframe())
        script_dir = os.path.dirname(os.path.abspath(current_file))
        tmp_dir = os.path.join(script_dir, "tmp_renders")
        os.makedirs(tmp_dir, exist_ok=True)
        save_path = os.path.join(tmp_dir, filename)
        
        # 使用 matplotlib 保存图像 (需要安装 matplotlib: pip install matplotlib)
        import matplotlib.pyplot as plt
        plt.imsave(save_path, image)
        print(f"  📷 场景已渲染并保存至: {save_path}")
        
        # 清理渲染器
        renderer.close()
    except ImportError:
        print("  ⚠️  未安装 matplotlib，无法保存图像。请运行 'pip install matplotlib' 安装。")
    except Exception as e:
        print(f"  ❌ 渲染或保存图像失败: {e}")


def main():
    # --- 直接在代码中定义 MJCF 模型 ---
    # 关键概念说明:
    # 1. <body name="hinge_body" pos="1 0 0">:
    #    这个 pos 属性定义了 hinge_body 这个刚体的原点相对于其父级（这里是 worldbody）的位置。
    #    它将整个 hinge_body 子树（在这个简单例子中就是它自己）在世界坐标系中移动到 (1, 0, 0)。
    # 2. data.qpos 的修改:
    #    修改 data.qpos 并不是在修改“世界”，而是在修改通过关节连接的各个“刚体”的状态。
    #    - 修改 data.qpos[7] (hinge_joint 角度) 改变了 hinge_body 相对于其与世界连接点的旋转。
    #    - 修改 data.qpos[0:7] (free_joint 位置和旋转) 改变了 free_body 在世界坐标系中的位姿。
    xml_model = """
<mujoco model="integrated_joint_demo">
  <option gravity="0 0 -9.81" timestep="0.01"/>

  <worldbody>
    <!-- 固定的地面 -->
    <geom name="floor" type="plane" size="5 5 0.1" rgba="0.8 0.9 0.8 1" pos="0 0 -0.5"/>

    <!-- 通过 free 关节连接的刚体 -->
    <body name="free_body" pos="0 0 1">
      <joint name="free_joint" type="free"/>
      <geom name="free_box" type="box" size="0.1 0.1 0.1" rgba="1 0 0 1"/>
      <!-- 添加一个小球以可视化旋转 -->
      <geom name="free_sphere" type="sphere" size="0.05" pos="0.1 0 0" rgba="1 1 0 1"/>
    </body>

    <!-- 通过 hinge 关节连接的摆臂 -->
    <!-- pos="1 0 0" 将 hinge_body 的原点设置在世界坐标 (1, 0, 0) -->
    <body name="hinge_body" pos="1 0 2">
      <joint name="hinge_joint" type="hinge" axis="0 1 0" pos="0 0 0"/>
      <!-- 摆臂的主体 -->
      <geom name="hinge_arm" type="capsule" fromto="0 0 0 0.5 0 0" size="0.05" rgba="0 0 1 1"/>
      <!-- 摆臂末端的球 -->
      <geom name="hinge_end" type="sphere" pos="0.5 0 0" size="0.07" rgba="0 1 1 1"/>
    </body>
  </worldbody>
  
</mujoco>
"""

    # 从 XML 字符串加载 MuJoCo 模型
    try:
        model = mujoco.MjModel.from_xml_string(xml_model)
        data = mujoco.MjData(model)
        print("✅ 模型加载成功")
        print(f"自由度数量 (nq): {model.nq}")
        print(f"速度维度 (nv): {model.nv}")
        print(f"关节数量: {model.njnt}")
        print(f"几何体数量: {model.ngeom}")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return

    # 打印关节信息
    print("\n📋 关节信息:")
    for i in range(model.njnt):
        joint_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
        joint_type = model.jnt_type[i]
        # qpos 的起始索引和维度
        qpos_adr = model.jnt_qposadr[i]
        qpos_dim = model.jnt_dofadr[i+1] - model.jnt_dofadr[i] if i < model.njnt - 1 else model.nq - model.jnt_qposadr[i]
        print(f"  {joint_name}: 类型={joint_type}, qpos起始索引={qpos_adr}, 维度={qpos_dim}")

    # 仿真参数
    dt = model.opt.timestep
    print(f"\n⏱️ 仿真参数:")
    print(f"  时间步长: {dt}s")
    print(f"  重力: {model.opt.gravity}")

    print("\n🎮 启动交互式查看器...")
    print("  使用鼠标拖拽旋转视角")
    print("  滚轮缩放")
    print("  关闭窗口退出程序")
    
    # --- 简单演示：修改 qpos 并观察变化 ---
    # 关键概念说明:
    # 修改 data.qpos 并不是在修改“世界”，而是在修改通过关节连接的各个“刚体”的状态。
    # - 修改 data.qpos[7] (hinge_joint 角度) 改变了 hinge_body 相对于其与世界连接点的旋转。
    # - 修改 data.qpos[0:7] (free_joint 位置和旋转) 改变了 free_body 在世界坐标系中的位姿。
    print("\n--- 演示 qpos 修改效果 ---")
    
    # 1. 初始状态
    print("1. 初始状态:")
    print(f"   Free body qpos: {data.qpos[0:7]}")
    print(f"   Hinge joint angle: {data.qpos[7]:.3f} rad")
    mujoco.mj_forward(model, data) # 确保 geom_xpos 是最新的
    print(f"   Free box position: {data.geom('free_box').xpos}")
    print(f"   Hinge end position: {data.geom('hinge_end').xpos}")
    # 渲染并保存初始状态
    render_and_save(model, data, "step1_initial.png")
    
    # 2. 修改 Hinge 关节角度
    print("\n2. 修改 Hinge 关节角度 (+0.1 rad):")
    data.qpos[7] += 0.1
    mujoco.mj_forward(model, data) # 更新状态
    print(f"   Hinge joint angle: {data.qpos[7]:.3f} rad")
    print(f"   Hinge end position: {data.geom('hinge_end').xpos}")
    # 渲染并保存修改 Hinge 关节后状态
    render_and_save(model, data, "step2_hinge_rotated.png")
    
    # 3. 修改 Free 关节位置 (Z + 0.4m) 和旋转 (绕Y轴 90度)
    print("\n3. 修改 Free 关节位置和旋转:")
    angle_y = math.radians(90)
    data.qpos[2] += 0.4  # Z 坐标 (索引 2)
    # 设置四元数 [qw, qx, qy, qz] 表示绕Y轴旋转
    data.qpos[3] = math.cos(angle_y / 2)  # qw
    data.qpos[4] = 0                      # qx
    data.qpos[5] = math.sin(angle_y / 2)  # qy
    data.qpos[6] = 0                      # qz
    mujoco.mj_forward(model, data) # 更新状态
    print(f"   Free body qpos (pos & quat): {data.qpos[0:7]}")
    print(f"   Free box position: {data.geom('free_box').xpos}")
    # 渲染并保存最终状态
    render_and_save(model, data, "step3_free_moved_and_rotated.png")
    
    # --- 启动查看器 ---
    try:
        # 启动交互式查看器 (使用最简单的形式)
        mujoco.viewer.launch(model, data)

    except KeyboardInterrupt:
        print("\n🛑 用户中断，退出程序")
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
    finally:
        print("👋 程序结束")


if __name__ == "__main__":
    main()
