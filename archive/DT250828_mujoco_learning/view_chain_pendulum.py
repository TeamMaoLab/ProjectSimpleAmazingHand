#!/usr/bin/env python3
"""
加载并可视化一个 MuJoCo 链式摆 (Chain Pendulum) 模型的脚本。

此脚本直接在 Python 代码中定义了 MJCF XML 字符串，
然后使用 mujoco 和 mujoco.viewer 来加载模型并启动交互式查看器。
"""

import mujoco
import mujoco.viewer


def main():
    # --- MJCF XML 字符串定义链式摆模型 ---
    xml_string = """
<mujoco>
  <option timestep=".001">
    <flag energy="enable" contact="disable"/>
  </option>

  <default>
    <joint type="hinge" axis="0 -1 0"/>
    <geom type="capsule" size=".02"/>
  </default>

  <worldbody>
    <light pos="0 -.4 1"/>
    <camera name="fixed" pos="0 -1 0" xyaxes="1 0 0 0 0 1"/>
    <body name="0" pos="0 0 .2">
      <joint name="root"/>
      <geom fromto="-.2 0 0 .2 0 0" rgba="1 1 0 1"/>
      <geom fromto="0 0 0 0 0 -.25" rgba="1 1 0 1"/>
      <body name="1" pos="-.2 0 0">
        <joint/>
        <geom fromto="0 0 0 0 0 -.2" rgba="1 0 0 1"/>
      </body>
      <body name="2" pos=".2 0 0">
        <joint/>
        <geom fromto="0 0 0 0 0 -.2" rgba="0 1 0 1"/>
      </body>
      <body name="3" pos="0 0 -.2">
        <joint/>
        <geom fromto="0 0 0 0 0 -.4" rgba="0 0 1 1"/>
      </body>
    </body>
  </worldbody>
</mujoco>
"""

    # --- 加载模型 ---
    try:
        model = mujoco.MjModel.from_xml_string(xml_string)
        data = mujoco.MjData(model)
        print("✅ 链式摆模型加载成功")
        print(f"  关节数量: {model.njnt}")
        print(f"  几何体数量: {model.ngeom}")
        print(f"  仿真时间步长: {model.opt.timestep}s")
        print(f"  接触检测已禁用: {not model.opt.disableflags & (1 << 0)}") # Check contact disable flag
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return

    # --- 启动交互式查看器 ---
    print("\n🎮 链式摆查看器已启动")
    print("💡 操作提示:")
    print("  - 在查看器中，点击并拖拽模型的任意部分。")
    print("  - 观察由于禁用了接触检测，摆臂可以相互穿过。")
    print("  - 关闭查看器窗口以结束程序。")
    
    try:
        # 启动交互式查看器
        mujoco.viewer.launch(model, data)
    except KeyboardInterrupt:
        print("\n🛑 用户中断，退出程序")
    except Exception as e:
        print(f"\n❌ 查看器运行错误: {e}")
    finally:
        print("👋 程序结束")


if __name__ == "__main__":
    main()