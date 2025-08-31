#!/usr/bin/env python3
"""
实验：探索 MuJoCo 的接触与碰撞机制。

此脚本基于 `integrated_joint_demo.py` 的思想，创建一个专门用于学习接触和碰撞的场景。
目标：
1. 观察 MuJoCo 如何检测和处理接触。
2. 学会访问和打印接触信息（接触点、法线、涉及几何体）。
3. 学会使用 mjvOption 可视化接触点和接触力。
4. 理解 geom_xpos 更新对于接触检测的重要性。

模型描述：
- 一个固定的平面 (floor)。
- 一个自由关节连接的刚体 (free_body)，上面附着一个盒子 (free_box) 和一个小球 (free_sphere)。
- free_body 初始位置较高，会在重力作用下下落并与 floor 发生碰撞。
"""

import mujoco
import mujoco.viewer # 确保导入 viewer 模块
import numpy as np
import os


def render_and_save_with_contacts(model, data, filename, show_contacts=True):
    """使用 Renderer 渲染当前场景，可选地显示接触信息，并保存为 PNG 图像。"""
    try:
        with mujoco.Renderer(model, height=480, width=640) as renderer:
            if show_contacts:
                # 创建并配置可视化选项
                scene_option = mujoco.MjvOption()
                # 启用接触点可视化 (红色点)
                scene_option.flags[mujoco.mjtVisFlag.mjVIS_CONTACTPOINT] = True
                # 启用接触力可视化 (线段)
                scene_option.flags[mujoco.mjtVisFlag.mjVIS_CONTACTFORCE] = True
                # 可选：调整接触力可视化大小
                # scene_option.contact_force_width = 0.05
                # scene_option.contact_scale = 0.5
                renderer.update_scene(data, scene_option=scene_option)
            else:
                renderer.update_scene(data)
            
            image = renderer.render()
            
            # 保存图像到临时目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            tmp_dir = os.path.join(script_dir, "tmp_renders")
            os.makedirs(tmp_dir, exist_ok=True)
            save_path = os.path.join(tmp_dir, filename)
            
            import matplotlib.pyplot as plt
            plt.imsave(save_path, image)
            print(f"  📷 场景已渲染并保存至: {save_path}")
            
    except ImportError:
        print("  ⚠️  未安装 matplotlib，无法保存图像。请运行 'pip install matplotlib' 安装。")
    except Exception as e:
        print(f"  ❌ 渲染或保存图像失败: {e}")


def print_contact_info(model, data, step_desc=""):
    """打印当前的接触信息。"""
    print(f"    检测到的接触数 (ncon): {data.ncon}")
    print(f"    有效接触约束数 (nefc): {data.nefc}")
    
    if data.ncon > 0:
        print(f"    --- 详细接触信息 ({step_desc}) ---")
        for i in range(data.ncon):
            contact = data.contact[i]
            geom1_id = contact.geom1
            geom2_id = contact.geom2
            geom1_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom1_id)
            geom2_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom2_id)
            
            contact_pos = contact.pos.copy()
            contact_normal = contact.frame[:3].copy() # 法线向量
            
            print(f"      接触 {i+1}: '{geom1_name}' (ID: {geom1_id}) 和 '{geom2_name}' (ID: {geom2_id})")
            print(f"        位置: [{contact_pos[0]:.4f}, {contact_pos[1]:.4f}, {contact_pos[2]:.4f}]")
            print(f"        法线 (从 {geom1_name} 指向 {geom2_name}): [{contact_normal[0]:.4f}, {contact_normal[1]:.4f}, {contact_normal[2]:.4f}]")


def main():
    # --- 定义 MJCF 模型 ---
    xml_model = """
<mujoco model="contact_demo">
  <option gravity="0 0 -9.81" timestep="0.01"/>

  <worldbody>
    <!-- 固定的地面 -->
    <geom name="floor" type="plane" size="5 5 0.1" rgba="0.8 0.9 0.8 1" pos="0 0 -0.5"/>

    <!-- 通过 free 关节连接的刚体 -->
    <body name="free_body" pos="0 0 2"> <!-- 初始位置更高 -->
      <joint name="free_joint" type="free"/>
      <geom name="free_box" type="box" size="0.1 0.1 0.1" rgba="1 0 0 1" mass="1"/>
      <!-- 添加一个小球以可视化旋转 -->
      <geom name="free_sphere" type="sphere" size="0.05" pos="0.1 0 0" rgba="1 1 0 1" mass="0.1"/>
    </body>
  </worldbody>
</mujoco>
"""

    # --- 加载模型 ---
    try:
        model = mujoco.MjModel.from_xml_string(xml_model)
        data = mujoco.MjData(model)
        print("✅ 模型加载成功")
        print(f"自由度数量 (nq): {model.nq}")
        print(f"关节数量: {model.njnt}")
        print(f"几何体数量: {model.ngeom}")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return

    # --- 实验开始 ---
    print("\n--- 实验开始：接触与碰撞机制探索 ---")
    
    # --- 步骤 1: 初始状态检查 ---
    print("\n--- 步骤 1: 初始状态检查 ---")
    mujoco.mj_forward(model, data) # 确保 geom_xpos 是最新的
    print(f"  仿真时间: {data.time:.3f}s")
    print_contact_info(model, data, "初始状态")
    render_and_save_with_contacts(model, data, "contact_step_1_initial.png", show_contacts=True)

    # --- 步骤 2: 执行仿真步进并观察接触 ---
    print("\n--- 步骤 2: 执行仿真步进并观察接触 ---")
    sim_steps = 150
    contact_detected_step = None
    for i in range(sim_steps):
        mujoco.mj_step(model, data)
        
        # 检查是否是关键帧（例如，刚开始、接触发生时、结束前）
        is_keyframe = (i == 0) or (i == sim_steps - 1) or (data.ncon > 0 and contact_detected_step is None)
        
        if is_keyframe:
            if data.ncon > 0 and contact_detected_step is None:
                contact_detected_step = i + 1
                
            print(f"\n  仿真步 {i+1} (时间: {data.time:.3f}s):")
            print_contact_info(model, data, f"仿真步 {i+1}")
            render_and_save_with_contacts(model, data, f"contact_step_{i+1:03d}.png", show_contacts=True)

    if contact_detected_step:
        print(f"\n✅ 首次检测到接触发生在仿真步 {contact_detected_step}。")
    else:
        print(f"\n⚠️  在 {sim_steps} 步仿真中未检测到接触。请检查模型或增加仿真步数。")

    # --- 步骤 3: 探索 geom_xpos 的重要性 (对比实验) ---
    print("\n--- 步骤 3: 探索 geom_xpos 的重要性 (对比实验) ---")
    
    # 重置数据到初始状态
    mujoco.mj_resetData(model, data)
    mujoco.mj_forward(model, data) # 确保初始状态正确
    print("  数据已重置到初始状态。")
    
    # 手动将 free_body 的位置设置到地面下方 (穿透)
    print("  将 free_body 的 Z 坐标手动设置到地面下方 (穿透状态)...")
    data.qpos[2] = -0.6 # Z 坐标 (free_joint 的平移部分)
    # 注意：此时 geom_xpos 还未更新，仍处于旧位置
    
    print(f"  修改后的 qpos (位置部分): {data.qpos[0:3]}")
    print("  ⚠️  注意：此时未调用 mj_forward，geom_xpos 仍是旧值。")
    print("  旧的 free_box 位置:", data.geom('free_box').xpos)
    
    # (错误做法) 不更新 geom_xpos 直接检查接触
    print("\n  [错误做法] 不调用 mj_forward，直接检查接触:")
    print_contact_info(model, data, "未更新 geom_xpos")
    render_and_save_with_contacts(model, data, "contact_step_no_update.png", show_contacts=True)

    # (正确做法) 更新 geom_xpos 后再检查接触
    print("\n  [正确做法] 调用 mj_forward 更新 geom_xpos 后，再检查接触:")
    mujoco.mj_forward(model, data) # 更新 geom_xpos
    print("  更新后的 free_box 位置:", data.geom('free_box').xpos)
    print_contact_info(model, data, "已更新 geom_xpos")
    render_and_save_with_contacts(model, data, "contact_step_after_update.png", show_contacts=True)
    
    print("\n--- 实验结束 ---")
    print("📊 总结:")
    print("  1. 仿真过程中，当物体接触时，`data.ncon` 和 `data.nefc` 会大于 0。")
    print("  2. 可以通过遍历 `data.contact` 数组获取详细的接触信息。")
    print("  3. 使用 `mjvOption` 可以在渲染器中可视化接触点和接触力。")
    print("  4. 在进行依赖于几何体位置的计算（如碰撞检测）前，必须确保 `geom_xpos` 是最新的。")
    print("     这通常通过调用 `mj_forward` 或 `mj_kinematics` 来实现。")
    print("  5. 查看 tmp_renders 目录下的图像，对比有无接触信息的可视化效果。")

    # --- 启动交互式查看器 ---
    print("\n🎮 启动交互式查看器以进行手动探索...")
    print("  - 在查看器 UI (通常在右侧面板) 中，找到 'Visualization' 选项。")
    print("  - 尝试启用/禁用 'Contact Point' 和 'Contact Force' 查看效果。")
    print("  - 使用鼠标拖拽 'free_body' 使其与地面或其他物体接触。")
    print("  - 关闭查看器窗口以结束程序。")
    try:
        mujoco.viewer.launch(model, data)
    except KeyboardInterrupt:
        print("\n🛑 用户中断，退出程序")
    except Exception as e:
        print(f"\n❌ 查看器运行错误: {e}")
    finally:
        print("👋 程序结束")


if __name__ == "__main__":
    main()
