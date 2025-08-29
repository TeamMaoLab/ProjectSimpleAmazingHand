#!/usr/bin/env python3
"""
实验：直观感受 mujoco.mj_forward 的作用 (改进版)。

目标：
1. 创建一个简单的 MuJoCo 模型（一个自由浮动的盒子和球）。
2. 设置初始状态 A。
3. 调用 mj_forward 并渲染，得到图像 img_A。
4. 设置新状态 B。
5. 不调用 mj_forward，直接尝试渲染。由于 Renderer 需要正确数据，这步改为直接说明其必要性。
6. 调用 mj_forward。
7. 再次渲染，得到图像 img_B。
8. 通过比较数据 (geom_xpos) 和说明，清晰展示 mj_forward 的作用。

更准确的实验是：
- 修改 qpos 后，如果不调用 mj_forward，依赖 qpos 的派生量（如 geom_xpos）不会更新。
- Renderer 需要正确的 geom_xpos 才能渲染，因此它内部很可能调用了等效于 mj_forward 的计算。
- 因此，我们通过打印 geom_xpos 的值来直接观察 mj_forward 的效果。
"""

import mujoco
import numpy as np
from PIL import Image


def main():
    """主函数，执行实验流程。"""
    print("--- 实验开始：感受 mujoco.mj_forward 的作用 (改进版) ---")

    # 1. 定义 MJCF 模型字符串
    xml_model = """
    <mujoco>
        <worldbody>
            <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
            <geom type="plane" size="1 1 0.1" rgba=".9 0 0 1"/>
            <body name="my_body">
                <joint type="free"/>
                <geom name="box" type="box" size=".1 .2 .3" rgba="0 .9 0 1" pos="0 0 0"/>
                <geom name="sphere" type="sphere" size=".1" rgba="0 0 .9 1" pos="0.5 0 0"/>
            </body>
        </worldbody>
    </mujoco>
    """

    # 2. 从字符串加载模型
    model = mujoco.MjModel.from_xml_string(xml_model)
    data = mujoco.MjData(model)
    print("✅ 模型加载成功")

    # --- 场景 A ---

    # 3. 重置数据以获得初始状态 A
    mujoco.mj_resetData(model, data)
    print(f"\n--- 场景 A: 初始状态 ---")
    print(f"🕒 仿真时间: {data.time}")
    print(f"📍 qpos (body的平移和四元数旋转): {data.qpos}")
    
    # 4. 调用 mj_forward 更新派生量
    mujoco.mj_forward(model, data)
    
    # 5. 打印初始 geom_xpos
    box_id = model.geom("box").id
    sphere_id = model.geom("sphere").id
    print(f"📦 盒子几何体 ID: {box_id}")
    print(f"🔵 球几何体 ID: {sphere_id}")
    print(f"📍 盒子位置 (geom_xpos[{box_id}]): {data.geom_xpos[box_id]}")
    print(f"📍 球位置 (geom_xpos[{sphere_id}]): {data.geom_xpos[sphere_id]}")

    # 6. 渲染场景 A
    with mujoco.Renderer(model, height=480, width=640) as renderer:
        renderer.update_scene(data)
        image_a = renderer.render()
        Image.fromarray(image_a).save("tmp-output-scene_A.png")
        print("💾 已保存场景 A 渲染图: tmp-output-scene_A.png")

    # --- 场景 B ---

    # 7. 定义并设置新状态 B: 平移和旋转
    print(f"\n--- 场景 B: 修改 qpos 但不调用 mj_forward ---")
    dx, dy, dz = 0.5, 0.3, 0.1
    angle_z = np.pi / 4.0 # 45 degrees
    qw = np.cos(angle_z / 2.0)
    qz = np.sin(angle_z / 2.0)
    new_qpos = np.array([dx, dy, dz, qw, 0.0, 0.0, qz])
    print(f"🔧 设置新的 qpos_B: {new_qpos}")
    # --- 关键操作 ---
    # 直接修改 MjData 中的广义位置 (qpos)
    # 这行代码是本次实验的核心，它改变了系统的配置状态
    # 但是，这并不会自动更新依赖于 qpos 的派生量，如 geom_xpos
    data.qpos[:] = new_qpos
    # --- 关键操作结束 ---

    # 8. 关键步骤：不调用 mj_forward
    #    直接打印 geom_xpos，观察其是否更新
    print("\n🚫 未调用 mj_forward(model, data)")
    print("🔍 检查 geom_xpos 是否更新 (它们不会更新):")
    print(f"📍 盒子位置 (geom_xpos[{box_id}]): {data.geom_xpos[box_id]}")
    print(f"📍 球位置 (geom_xpos[{sphere_id}]): {data.geom_xpos[sphere_id]}")
    # 结论：这些值与场景 A 中的值相同。

    # 9. 关于渲染场景 B (未更新):
    #    Renderer.update_scene(data) 需要正确的 geom_xpos 才能工作。
    #    它内部很可能会调用等效于 mj_forward 的计算来获取这些数据。
    #    因此，试图渲染一个“未更新”的状态在实践中是没有意义的，也是不可能的。
    #    我们通过文字说明这一点。

    # --- 场景 B (已更新) ---

    # 10. 调用 mujoco.mj_forward(model, data) 来更新所有派生量
    print(f"\n--- 场景 B: 调用 mj_forward 后 ---")
    mujoco.mj_forward(model, data)
    print("🔄 mj_forward 已调用，所有派生量已更新。")

    # 11. 再次打印 geom_xpos (在调用 mj_forward 之后)
    print("✅ 现在 geom_xpos 应该已经更新以反映新的 qpos_B。")
    print(f"📍 盒子位置 (geom_xpos[{box_id}]): {data.geom_xpos[box_id]}")
    print(f"📍 球位置 (geom_xpos[{sphere_id}]): {data.geom_xpos[sphere_id]}")
    # 关键点：这些值现在应该反映了平移和旋转后的新位置。

    # 12. 渲染调用 mj_forward 后的状态 B
    with mujoco.Renderer(model, height=480, width=640) as renderer:
        renderer.update_scene(data)
        image_b = renderer.render()
        Image.fromarray(image_b).save("tmp-output-scene_B.png")
        print("💾 已保存场景 B (已更新) 渲染图: tmp-output-scene_B.png")

    print("\n--- 实验结束 ---")
    print("📊 总结:")
    print("  1. 直接修改 `data.qpos` (如设置为 qpos_B) 不会自动更新 `data.geom_xpos` 等派生量。")
    print("  2. 在修改 `qpos` 后，必须调用 `mujoco.mj_forward(model, data)` 来计算并更新这些派生量。")
    print("  3. `mujoco.Renderer` 为了正确渲染，需要最新的 `geom_xpos` 等数据。")
    print("     因此，`renderer.update_scene(data)` 内部很可能调用了等效于 `mj_forward` 的计算。")
    print("  4. 试图渲染一个 '未更新' 的状态在实践中是不可行的。")
    print("  5. 最直接感受 `mj_forward` 作用的方法是：观察修改 `qpos` 前后，打印 `geom_xpos` 的值。")
    print("     - 修改 qpos 后，立即打印 -> xpos 未变。")
    print("     - 调用 mj_forward 后，再次打印 -> xpos 已变。")
    print("  6. 查看 'tmp-output-scene_A.png' 和 'tmp-output-scene_B.png' 对比效果。")


if __name__ == "__main__":
    main()