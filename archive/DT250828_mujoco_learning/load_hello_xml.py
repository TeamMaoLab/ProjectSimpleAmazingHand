#!/usr/bin/env python3
"""
使用 MuJoCo 的 Python 接口加载并可视化 'hello.xml' 模型。

注意：要在 macOS 上运行带可视化的脚本，需要使用 `mjpython`：
    mjpython load_hello_xml.py

如果没有安装 `mjpython` 或者想在无可视化的情况下运行：
    python load_hello_xml.py
"""

import mujoco
import time
import os
import sys


def main():
    # 获取当前脚本所在的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建相对于脚本位置的 XML 模型文件路径
    # 这确保了在从 GitHub 克隆项目后路径仍然有效
    model_path = os.path.join(script_dir, "hello.xml")

    # 从 XML 文件加载 MuJoCo 模型
    # 对于新版本的 mujoco，使用 MjModel.from_xml_path
    model = mujoco.MjModel.from_xml_path(model_path)

    # 为模型创建数据结构
    data = mujoco.MjData(model)

    # 检查是否使用 mjpython 运行（支持查看器）
    # 在 macOS 上，查看器需要 mjpython 才能正常工作
    if hasattr(mujoco, 'viewer') and 'mjpython' in sys.executable:
        print("启动交互式查看器...")
        # 启动交互式查看器
        with mujoco.viewer.launch_passive(model, data) as viewer:
            # 仿真循环
            while viewer.is_running():
                # 推进仿真一步
                mujoco.mj_step(model, data)
                
                # 将查看器与当前仿真状态同步
                viewer.sync()
                
                # 添加小延迟以控制仿真速度
                time.sleep(0.01)
    else:
        print("在无可视化模式下运行仿真...")
        print("要在 macOS 上查看可视化效果，请使用 `mjpython` 运行此脚本：")
        print("    mjpython load_hello_xml.py")
        print("")
        
        # 运行固定步数的仿真并打印状态
        print("运行 1000 步仿真...")
        for i in range(1000):
            # 推进仿真一步
            mujoco.mj_step(model, data)
            
            # 每 100 步打印一次状态信息
            if i % 100 == 0:
                print(f"第 {i} 步: 箱子位置 = {data.qpos[:3]}")
                
            # 添加小延迟以控制仿真速度
            time.sleep(0.01)
        
        print("仿真完成。")


if __name__ == "__main__":
    main()