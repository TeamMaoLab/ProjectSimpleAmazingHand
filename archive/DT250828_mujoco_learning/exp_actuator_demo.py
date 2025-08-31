#!/usr/bin/env python3
"""
MuJoCo Actuator (Position vs. Velocity) 演示脚本。

此脚本创建两个独立的单摆系统，分别演示位置控制和速度控制执行器。
- 摆臂1 (pendulum1) 配备一个位置伺服执行器 (position actuator)。
- 摆臂2 (pendulum2) 配备一个速度伺服执行器 (velocity actuator)。

通过交互式查看器，你可以：
1.  使用 'pos_ctrl_arm' 滑块设置摆臂1的目标角度，观察位置伺服如何驱动它。
2.  使用 'vel_ctrl_arm' 滑块设置摆臂2的目标速度，观察速度伺服如何驱动它。
"""

import mujoco
import mujoco.viewer


def main():
    # --- 定义 MJCF 模型 ---
    # 两个独立的单摆系统，分别位于 X 轴两侧。
    xml_model = """
<mujoco model="actuator_demo_pos_vs_vel">
  <option gravity="0 0 -9.81" timestep="0.01"/>
  
  <!-- 定义默认属性 -->
  <default>
    <joint type="hinge" axis="0 1 0"/>
    <geom type="capsule" size=".02"/>
  </default>

  <worldbody>
    <!-- 固定的基座 -->
    <geom name="base" type="cylinder" size=".1 .01" rgba="0.5 0.5 0.5 1" pos="0 0 0.01"/>
    
    <!-- --- 第一个摆臂系统 (位置控制) --- -->
    <body name="pendulum1" pos="-0.3 0 0.5"> <!-- 位于基座左侧 -->
      <joint name="joint1" pos="0 0 0"/>
      <geom name="arm1" fromto="0 0 0 0 0 -0.4" rgba="0 0 1 1"/> <!-- 蓝色 -->
    </body>

    <!-- --- 第二个摆臂系统 (速度控制) --- -->
    <body name="pendulum2" pos="0.3 0 0.5"> <!-- 位于基座右侧 -->
      <joint name="joint2" pos="0 0 0"/>
      <geom name="arm2" fromto="0 0 0 0 0 -0.4" rgba="0 1 0 1"/> <!-- 绿色 -->
    </body>
  </worldbody>
  
  <!-- 定义执行器 -->
  <actuator>
    <!-- 为第一个关节添加位置伺服执行器 -->
    <position name="pos_ctrl_arm" joint="joint1" kp="8" kv="4"/>
    
    <!-- 为第二个关节添加速度伺服执行器 -->
    <!-- kv 参数定义了速度控制的阻尼，通常与 kp 一起调整以获得稳定响应 -->
    <velocity name="vel_ctrl_arm" joint="joint2" kv="10"/>
  </actuator>
</mujoco>
"""

    # --- 加载模型 ---
    try:
        model = mujoco.MjModel.from_xml_string(xml_model)
        data = mujoco.MjData(model)
        print("✅ 模型加载成功")
        print(f"  关节数量: {model.njnt}")
        print(f"  执行器数量: {model.nu}")
        print(f"  关节名称: {[mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i) for i in range(model.njnt)]}")
        print(f"  执行器名称: {[mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(model.nu)]}")
        print(f"  Ctrl 维度: {model.nu} (对应 {model.nu} 个执行器)")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return

    # --- 启动交互式查看器 ---
    print("\n🎮 启动交互式查看器...")
    print("💡 操作提示:")
    print("  - 在查看器 UI (通常在左下角) 找到 'Actuation' 面板。")
    print("  - 你会看到两个滑块 (Sliders):")
    print("    1. 'pos_ctrl_arm' (蓝色): 设置左侧蓝色摆臂的目标角度 (弧度, -3.14 到 3.14)。")
    print("    2. 'vel_ctrl_arm' (绿色): 设置右侧绿色摆臂的目标速度 (弧度/秒, -10 到 10)。")
    print("  - 拖动 'pos_ctrl_arm' 滑块，观察蓝色摆臂如何移动到指定角度并停留。")
    print("  - 拖动 'vel_ctrl_arm' 滑块，观察绿色摆臂如何以指定速度旋转。")
    print("  - 尝试将速度控制设为 0，观察绿色摆臂在重力作用下会自然下垂。")
    print("  - 对比两种控制方式的行为差异。")
    print("  - 关闭窗口以结束程序。")
    
    try:
        # 启动交互式查看器。
        mujoco.viewer.launch(model, data)

    except KeyboardInterrupt:
        print("\n🛑 用户中断，退出程序")
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
    finally:
        print("👋 程序结束")


if __name__ == "__main__":
    main()