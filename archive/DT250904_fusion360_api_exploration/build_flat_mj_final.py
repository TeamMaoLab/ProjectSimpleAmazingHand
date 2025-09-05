#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版 Fusion 360 STEP → MuJoCo XML 转换器
使用world_com_m正确还原装配位置
"""

import json
import os
import re
import numpy as np
from pathlib import Path

try:
    import cadquery as cq
    CADQUERY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  警告: 未安装 CadQuery: {e}")
    CADQUERY_AVAILABLE = False


def safe_name(name):
    """生成安全的XML标识符"""
    base = re.sub(r'[^0-9A-Za-z_]+', '_', name)
    if not base or base[0].isdigit():
        base = "part_" + base
    return base


def export_stl(step_path, stl_path, tolerance=0.1):
    """将STEP文件转换为STL"""
    shape = cq.importers.importStep(str(step_path))
    cq.exporters.export(shape, str(stl_path), exportType='STL', tolerance=tolerance)


def convert_assembly(export_dir):
    """转换装配体到MuJoCo格式"""
    export_dir = Path(export_dir)
    
    # 查找JSON文件
    json_files = list(export_dir.rglob("export_data.json"))
    if not json_files:
        raise FileNotFoundError("未找到 export_data.json")
    
    json_file = json_files[0]
    base_dir = json_file.parent
    
    # 创建输出目录
    mujoco_dir = base_dir / "mujoco"
    assets_dir = mujoco_dir / "assets"
    mujoco_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(exist_ok=True)
    
    # 读取数据
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print("========== 开始转换 ==========")
    
    # 处理几何体 - 转换STEP到STL
    geometry_map = {}
    for geom in data["geometries"]:
        geom_id = geom["geometry_id"]
        comp_name = geom["component_name"]
        step_path = base_dir / geom["file"]
        
        # 生成安全的网格名称
        mesh_name = safe_name(comp_name if comp_name.strip() else geom_id)
        stl_path = assets_dir / f"{mesh_name}.stl"
        
        print(f"转换: {comp_name} -> {stl_path.name}")
        export_stl(step_path, stl_path)
        
        geometry_map[geom_id] = {
            "mesh_name": mesh_name,
            "component_name": comp_name
        }
    
    # 生成MuJoCo XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<mujoco model="fusion_assembly">',
        '  <option timestep="0.001"/>',
        '  <asset>'
    ]
    
    # 添加网格资源
    for geom_id, info in geometry_map.items():
        mesh_scale = 0.001  # mm转m
        xml_lines.append(
            f'    <mesh name="{info["mesh_name"]}" '
            f'file="assets/{info["mesh_name"]}.stl" '
            f'scale="{mesh_scale} {mesh_scale} {mesh_scale}"/>'
        )
    
    xml_lines.extend([
        '  </asset>',
        '  <worldbody>',
        '    <light name="light" pos="0 -3 3"/>'
    ])
    
    # 处理实例 - 使用world_com_m作为装配位置
    for idx, inst in enumerate(data["instances"]):
        geom_id = inst["geometry_id"]
        if geom_id not in geometry_map:
            continue
            
        info = geometry_map[geom_id]
        
        # 使用world_com_m作为装配后的世界坐标位置
        world_pos = np.array(inst["world_com_m"])
        
        # 使用JSON中的四元数
        if "quat_wxyz" in inst:
            quat = np.array(inst["quat_wxyz"])
        else:
            # 如果没有四元数，使用单位四元数（无旋转）
            quat = np.array([1.0, 0.0, 0.0, 0.0])
        
        # 生成body名称
        body_name = safe_name(inst["occurrence_path"].replace(":", "_"))
        
        # 写入XML
        pos_str = " ".join(f"{x:.6f}" for x in world_pos)
        quat_str = " ".join(f"{x:.6f}" for x in quat)
        
        xml_lines.extend([
            f'    <body name="{body_name}" pos="{pos_str}" quat="{quat_str}">',
            f'      <geom type="mesh" mesh="{info["mesh_name"]}" rgba="0.7 0.7 0.7 1"/>',
            f'      <!-- {info["component_name"]} -->',
            '    </body>'
        ])
        
        print(f"添加: {info['component_name']} 装配位置={world_pos}")
    
    xml_lines.extend([
        '  </worldbody>',
        '</mujoco>'
    ])
    
    # 保存XML文件
    xml_path = mujoco_dir / "model.xml"
    xml_path.write_text("\n".join(xml_lines), encoding="utf-8")
    
    # 创建简单的查看器
    create_simple_viewer(mujoco_dir)
    
    print("========== 转换完成 ==========")
    print(f"MuJoCo模型: {xml_path}")
    print(f"资源目录: {assets_dir}")
    print("运行查看器: cd 到mujoco目录，然后 python viewer.py")


def create_simple_viewer(mujoco_dir):
    """创建简单的MuJoCo查看器"""
    viewer_code = '''#!/usr/bin/env python3
import os
import mujoco
import mujoco.viewer

def main():
    # 加载模型
    xml_path = os.path.join(os.path.dirname(__file__), "model.xml")
    if not os.path.exists(xml_path):
        print("找不到 model.xml")
        return
    
    model = mujoco.MjModel.from_xml_path(xml_path)
    data = mujoco.MjData(model)
    
    print(f"加载模型成功: {model.nbody-1} 个物体")
    print("启动查看器...")
    
    # 启动交互式查看器
    mujoco.viewer.launch(model, data)

if __name__ == "__main__":
    main()
'''
    
    viewer_path = mujoco_dir / "viewer.py"
    viewer_path.write_text(viewer_code, encoding="utf-8")
    os.chmod(viewer_path, 0o755)


def main():
    import sys
    if len(sys.argv) != 2:
        print("用法: python convert.py <export_dir>")
        print("export_dir: 包含 export_data.json 的目录")
        return
    
    export_dir = sys.argv[1]
    if not os.path.exists(export_dir):
        print(f"目录不存在: {export_dir}")
        return
    
    if not CADQUERY_AVAILABLE:
        print("需要安装 CadQuery: pip install cadquery")
        return
    
    convert_assembly(export_dir)


if __name__ == "__main__":
    main()
