#!/usr/bin/env python3
"""
交互式 MuJoCo 查看器，用于手动探索接触与碰撞。

此脚本加载与 exp_contact_demo.py 相同的模型，
但不自动运行仿真，而是直接启动 mujoco.viewer，
允许用户手动拖拽物体、观察接触并调整可视化选项。
"""

import mujoco
import mujoco.viewer
import numpy as np


def main():
    # --- 定义相同的 MJCF 模型 ---
    xml_model = """
<mujoco model="contact_demo_viewer">
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
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return

    # --- 启动交互式查看器 ---
    print("\n🎮 交互式查看器已启动")
    print("💡 操作提示:")
    print("  - 使用鼠标左键拖拽 'free_body' (红色盒子)。")
    print("  - 在查看器 UI (通常在右侧面板) 中，找到 'Visualization' 部分。")
    print("  - 尝试勾选/取消勾选 'Contact Point' 和 'Contact Force' 查看接触效果。")
    print("  - 将盒子拖拽到地面或使其自然下落，观察接触点和力的可视化。")
    print("  - 关闭查看器窗口以结束程序。")
    
    try:
        # 启动交互式查看器，无限循环直到窗口关闭
        mujoco.viewer.launch(model, data)
    except KeyboardInterrupt:
        print("\n🛑 用户中断，退出程序")
    except Exception as e:
        print(f"\n❌ 查看器运行错误: {e}")
    finally:
        print("👋 程序结束")


if __name__ == "__main__":
    main()
