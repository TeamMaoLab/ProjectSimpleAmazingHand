#!/usr/bin/env python3
"""
使用 MuJoCo 的 Python 接口加载并可视化 'hello.xml' 模型。

在 macOS 上，可以直接运行此脚本来启动交互式查看器，无需使用 mjpython。
此脚本使用了 mujoco.viewer.launch 方法，该方法在新版本的 mujoco 中可用，
可以避免在 macOS 上使用 mjpython 的需要。
"""

import mujoco
import mujoco.viewer
import time
import os
import sys
import numpy as np


def main():
    # 获取当前脚本所在的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建相对于脚本位置的 XML 模型文件路径
    # 这确保了在从 GitHub 克隆项目后路径仍然有效
    model_path = os.path.join(script_dir, "hello.xml")

    # 从 XML 文件加载 MuJoCo 模型
    # 对于新版本的 mujoco，使用 MjModel.from_xml_path
    try:
        model = mujoco.MjModel.from_xml_path(model_path)
        data = mujoco.MjData(model)
        print("✅ 模型加载成功")
        print(f"自由度数量: {model.nq}")
        print(f"关节数量: {model.njnt}")
        print(f"执行器数量: {model.nu}")
        print(f"传感器数量: {model.nsensor}")
        print(f"刚体数量: {model.nbody}")
        print(f"几何体数量: {model.ngeom}")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return

    # 打印关节信息
    print("\n📋 关节信息:")
    for i in range(model.njnt):
        joint_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
        joint_type = model.jnt_type[i]
        joint_range = model.jnt_range[i] if model.jnt_limited[i] else [-np.inf, np.inf]
        print(f"  {joint_name}: 类型={joint_type}, 范围={joint_range}")

    # 仿真参数
    dt = model.opt.timestep
    print(f"\n⏱️ 仿真参数:")
    print(f"  时间步长: {dt}s")
    print(f"  重力: {model.opt.gravity}")

    print("\n🎮 启动交互式查看器...")
    print("  使用鼠标拖拽旋转视角")
    print("  滚轮缩放")
    print("  关闭窗口退出程序")

    # 使用交互式查看器（不需要 mjpython）
    try:
        # 启动交互式查看器
        mujoco.viewer.launch(model, data, show_left_ui=True, show_right_ui=True)

    except KeyboardInterrupt:
        print("\n🛑 用户中断，退出程序")
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
    finally:
        print("👋 程序结束")


if __name__ == "__main__":
    main()