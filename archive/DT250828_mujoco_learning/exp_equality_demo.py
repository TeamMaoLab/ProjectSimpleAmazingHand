#!/usr/bin/env python3
"""
MuJoCo 平行四边形四铰链机构
经典的四杆机构：固定杆 + 主动杆 + 连杆 + 从动杆
"""

import mujoco
import mujoco.viewer
import numpy as np
import math
import os
import inspect


def render_and_save(model, data, filename):
    """渲染场景并保存为 PNG 图像"""
    try:
        renderer = mujoco.Renderer(model, height=480, width=640)
        renderer.update_scene(data)
        image = renderer.render()

        current_file = inspect.getfile(inspect.currentframe())
        script_dir = os.path.dirname(os.path.abspath(current_file))
        tmp_dir = os.path.join(script_dir, "tmp_parallelogram_4bar")
        os.makedirs(tmp_dir, exist_ok=True)
        save_path = os.path.join(tmp_dir, filename)

        import matplotlib.pyplot as plt
        plt.imsave(save_path, image)
        print(f"📷 图像已保存至: {save_path}")
        renderer.close()
    except ImportError:
        print("⚠️  未安装 matplotlib，请运行 'pip install matplotlib' 以保存图像")
    except Exception as e:
        print(f"❌ 渲染失败: {e}")


def main():
    # --------------------------
    # 平行四边形四铰链机构参数
    # --------------------------
    BASE_WIDTH = 1.0  # 固定杆长度（底边）
    SIDE_LENGTH = 0.6  # 侧边杆长度（左右两边）
    TOP_LENGTH = 0.8  # 顶边杆长度（与底边平行）

    LINK_RADIUS = 0.025  # 连杆半径
    HINGE_RADIUS = 0.04  # 铰链球半径
    BASE_HEIGHT = 0.3  # 基座高度

    xml_model = f"""
<mujoco model="parallelogram_4bar_linkage">
  <!-- 仿真配置 -->
  <option gravity="0 0 -9.81" timestep="0.005" iterations="100" solver="Newton"/>

  <!-- 编译器设置 -->
  <compiler angle="radian"/>

  <!-- 资源定义 -->
  <asset>
    <material name="mat_base" rgba="0.3 0.3 0.3 1"/>      <!-- 固定基座：灰色 -->
    <material name="mat_crank" rgba="1 0.2 0.2 1"/>       <!-- 主动杆：红色 -->
    <material name="mat_coupler" rgba="0.2 0.8 0.2 1"/>   <!-- 连杆：绿色 -->
    <material name="mat_rocker" rgba="0.2 0.2 1 1"/>      <!-- 从动杆：蓝色 -->
    <material name="mat_hinge" rgba="1 0.8 0 1"/>         <!-- 铰链：金色 -->
    <material name="mat_payload" rgba="1 0 1 0.8"/>       <!-- 负载：紫色半透明 -->
  </asset>

  <worldbody>
    <!-- 地面 -->
    <geom name="floor" type="plane" size="2 2 0.1" rgba="0.8 0.8 0.8 1" pos="0 0 -0.1"/>

    <!-- ==================== 固定基座系统 ==================== -->

    <!-- 左侧固定基座（铰链A） -->
    <body name="base_left" pos="{-BASE_WIDTH / 2} 0 {BASE_HEIGHT}">
      <geom name="base_left_geom" type="cylinder" size="0.08 0.15" 
            material="mat_base" pos="0 0 -0.075"/>
      <!-- 铰链A可视化 -->
      <geom name="hinge_A" type="sphere" size="{HINGE_RADIUS}" 
            material="mat_hinge" pos="0 0 0"/>
    </body>

    <!-- 右侧固定基座（铰链B） -->
    <body name="base_right" pos="{BASE_WIDTH / 2} 0 {BASE_HEIGHT}">
      <geom name="base_right_geom" type="cylinder" size="0.08 0.15" 
            material="mat_base" pos="0 0 -0.075"/>
      <!-- 铰链B可视化 -->
      <geom name="hinge_B" type="sphere" size="{HINGE_RADIUS}" 
            material="mat_hinge" pos="0 0 0"/>
    </body>

    <!-- 固定杆（连接两个基座，仅用于可视化） -->
    <body name="fixed_link" pos="0 0 {BASE_HEIGHT - 0.1}">
      <geom name="fixed_link_geom" type="box" 
            size="{BASE_WIDTH / 2 + 0.05} 0.03 0.02" material="mat_base"/>
    </body>

    <!-- ==================== 可动四杆机构 ==================== -->

    <!-- 主动杆（曲柄）：从左基座铰链A出发 -->
    <body name="crank" pos="{-BASE_WIDTH / 2} 0 {BASE_HEIGHT}">
      <!-- 铰链A：主动关节（可控制） -->
      <joint name="joint_A" type="hinge" axis="0 1 0" pos="0 0 0" 
             range="-3.14159 3.14159" damping="0.1"/>

      <!-- 主动杆几何体 -->
      <geom name="crank_geom" type="capsule" 
            fromto="0 0 0 {SIDE_LENGTH * math.cos(math.pi / 6)} 0 {SIDE_LENGTH * math.sin(math.pi / 6)}" 
            size="{LINK_RADIUS}" material="mat_crank"/>

      <!-- 铰链C位置（主动杆末端） -->
      <site name="site_C" pos="{SIDE_LENGTH * math.cos(math.pi / 6)} 0 {SIDE_LENGTH * math.sin(math.pi / 6)}" 
            size="0.02" rgba="1 0 0 1"/>

      <!-- 铰链C可视化 -->
      <geom name="hinge_C_vis" type="sphere" size="{HINGE_RADIUS}" 
            material="mat_hinge" pos="{SIDE_LENGTH * math.cos(math.pi / 6)} 0 {SIDE_LENGTH * math.sin(math.pi / 6)}"/>
    </body>

    <!-- 从动杆（摇杆）：从右基座铰链B出发 -->
    <body name="rocker" pos="{BASE_WIDTH / 2} 0 {BASE_HEIGHT}">
      <!-- 铰链B：从动关节 -->
      <joint name="joint_B" type="hinge" axis="0 1 0" pos="0 0 0" 
             range="-3.14159 3.14159" damping="0.1"/>

      <!-- 从动杆几何体 -->
      <geom name="rocker_geom" type="capsule" 
            fromto="0 0 0 {-SIDE_LENGTH * math.cos(math.pi / 6)} 0 {SIDE_LENGTH * math.sin(math.pi / 6)}" 
            size="{LINK_RADIUS}" material="mat_rocker"/>

      <!-- 铰链D位置（从动杆末端） -->
      <site name="site_D" pos="{-SIDE_LENGTH * math.cos(math.pi / 6)} 0 {SIDE_LENGTH * math.sin(math.pi / 6)}" 
            size="0.02" rgba="0 0 1 1"/>

      <!-- 铰链D可视化 -->
      <geom name="hinge_D_vis" type="sphere" size="{HINGE_RADIUS}" 
            material="mat_hinge" pos="{-SIDE_LENGTH * math.cos(math.pi / 6)} 0 {SIDE_LENGTH * math.sin(math.pi / 6)}"/>
    </body>

    <!-- 连杆（耦合杆）：连接铰链C和D -->
    <body name="coupler" pos="0 0 {BASE_HEIGHT + SIDE_LENGTH * math.sin(math.pi / 6)}">
      <!-- 自由关节（6DOF，通过约束限制） -->
      <joint name="joint_coupler" type="free"/>

      <!-- 连杆几何体 -->
      <geom name="coupler_geom" type="capsule" 
            fromto="{-TOP_LENGTH / 2} 0 0 {TOP_LENGTH / 2} 0 0" 
            size="{LINK_RADIUS}" material="mat_coupler"/>

      <!-- 连杆左端site（对应铰链C） -->
      <site name="site_coupler_left" pos="{-TOP_LENGTH / 2} 0 0" 
            size="0.02" rgba="0 1 0 1"/>

      <!-- 连杆右端site（对应铰链D） -->
      <site name="site_coupler_right" pos="{TOP_LENGTH / 2} 0 0" 
            size="0.02" rgba="0 1 0 1"/>

      <!-- 负载（连杆中心） -->
      <geom name="payload" type="sphere" size="0.06" 
            material="mat_payload" pos="0 0 0"/>
    </body>
  </worldbody>

  <!-- ==================== 铰链约束 ==================== -->
  <equality>
    <!-- 铰链C：主动杆末端 ↔ 连杆左端 -->
    <connect name="hinge_C_constraint" 
             site1="site_C" 
             site2="site_coupler_left"/>

    <!-- 铰链D：从动杆末端 ↔ 连杆右端 -->
    <connect name="hinge_D_constraint" 
             site1="site_D" 
             site2="site_coupler_right"/>
  </equality>

  <!-- ==================== 驱动器 ==================== -->
  <actuator>
    <!-- 主动杆电机（可控制整个机构运动） -->
    <motor name="crank_motor" joint="joint_A" gear="100" ctrllimited="true" 
           ctrlrange="-10 10"/>
  </actuator>

  <!-- ==================== 传感器 ==================== -->
  <sensor>
    <!-- 关节角度传感器 -->
    <jointpos name="sensor_crank_angle" joint="joint_A"/>
    <jointpos name="sensor_rocker_angle" joint="joint_B"/>

    <!-- 关节速度传感器 -->
    <jointvel name="sensor_crank_vel" joint="joint_A"/>
    <jointvel name="sensor_rocker_vel" joint="joint_B"/>
  </sensor>
</mujoco>
"""

    # --------------------------
    # 加载模型并初始化
    # --------------------------
    try:
        model = mujoco.MjModel.from_xml_string(xml_model)
        data = mujoco.MjData(model)
        print("✅ 平行四边形四铰链机构加载成功！")
        print(f"📊 模型信息: 自由度={model.nq}, 关节数={model.njnt}, 约束数={model.neq}")
        print(f"🎛️  控制器数量: {model.nu}")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return

    # 打印机构信息
    print("\n🔗 四铰链机构组成:")
    print("  📍 铰链A: 左基座 - 主动杆（可控制）")
    print("  📍 铰链B: 右基座 - 从动杆（被动跟随）")
    print("  📍 铰链C: 主动杆 - 连杆")
    print("  📍 铰链D: 从动杆 - 连杆")

    print("\n🔗 关节列表:")
    for i in range(model.njnt):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
        if name:
            jtype = ["free", "ball", "hinge", "slide"][model.jnt_type[i]]
            print(f"  - {name}: 类型={jtype}")

    print("\n⚓ 约束列表:")
    for i in range(model.neq):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_EQUALITY, i)
        if name:
            print(f"  - {name}: 铰链约束")

    # --------------------------
    # 演示机构运动
    # --------------------------
    print("\n--- 演示四铰链机构运动 ---")

    # 初始状态
    print("\n1. 初始状态:")
    mujoco.mj_forward(model, data)
    crank_angle = math.degrees(data.qpos[0]) if model.nq > 0 else 0
    rocker_angle = math.degrees(data.qpos[1]) if model.nq > 1 else 0
    print(f"   主动杆角度: {crank_angle:.1f}°")
    print(f"   从动杆角度: {rocker_angle:.1f}°")
    render_and_save(model, data, "1_initial_state.png")

    # 运动序列演示
    angles = [0, 30, 60, 90, 120, 150, 180, -30, -60, -90]

    for i, angle in enumerate(angles):
        print(f"\n{i + 2}. 主动杆转动到 {angle}°:")
        data.qpos[0] = math.radians(angle)  # 设置主动杆角度
        mujoco.mj_forward(model, data)  # 更新机构状态

        crank_angle = math.degrees(data.qpos[0])
        rocker_angle = math.degrees(data.qpos[1])
        print(f"   主动杆角度: {crank_angle:.1f}°")
        print(f"   从动杆角度: {rocker_angle:.1f}°")

        # 获取负载位置
        try:
            payload_pos = data.site_xpos[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "site_coupler_left")]
            print(f"   负载轨迹: {payload_pos.round(3)}")
        except:
            pass

        render_and_save(model, data, f"{i + 2}_angle_{angle}deg.png")

    # --------------------------
    # 动态仿真演示
    # --------------------------
    print("\n--- 启动动态仿真 ---")

    # 重置到初始状态
    mujoco.mj_resetData(model, data)

    # 运行一小段仿真（展示动力学）
    print("🔄 运行3秒动力学仿真...")
    for step in range(600):  # 3秒 @ 0.005s/step
        # 正弦波控制主动杆
        data.ctrl[0] = 5 * math.sin(0.5 * step * model.opt.timestep)
        mujoco.mj_step(model, data)

        if step % 100 == 0:  # 每0.5秒打印一次
            crank_angle = math.degrees(data.qpos[0])
            rocker_angle = math.degrees(data.qpos[1])
            print(f"   t={data.time:.1f}s: 主动杆={crank_angle:.1f}°, 从动杆={rocker_angle:.1f}°")

    render_and_save(model, data, "final_dynamic_state.png")

    # --------------------------
    # 启动交互式查看器
    # --------------------------
    print("\n🎮 启动交互式查看器:")
    print("   - 鼠标拖拽：旋转视角")
    print("   - 滚轮：缩放")
    print("   - 右键拖拽：平移视角")
    print("   - 空格键：暂停/继续仿真")
    print("   - 可以手动拖动主动杆测试机构")
    print("   - 关闭窗口退出")

    # 重置为静态展示
    mujoco.mj_resetData(model, data)
    data.qpos[0] = math.radians(45)  # 设置一个好看的初始角度
    mujoco.mj_forward(model, data)

    try:
        mujoco.viewer.launch(model, data)
    except KeyboardInterrupt:
        print("\n🛑 用户中断程序")
    finally:
        print("👋 程序结束")


if __name__ == "__main__":
    main()
