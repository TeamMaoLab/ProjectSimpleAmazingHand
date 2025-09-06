"""
Fusion 360 零部件位置导出数据转换为MuJoCo XML脚本

此脚本读取Fusion 360导出的JSON数据，生成对应的MuJoCo XML文件，
并使用pypinyin将中文文件名转换为拼音，创建完整的MuJoCo仿真环境。
特别优化了位置信息的提取和使用。

作者：基于Fusion 360导出工具设计
日期：2025-09-05
版本：v1.0
"""

import json
import os
import shutil
from pathlib import Path
import re
import numpy as np
import argparse

try:
    from pypinyin import pinyin, Style
    PINYIN_AVAILABLE = True
except ImportError:
    print("⚠️  警告: 未安装pypinyin，将使用简单替换处理中文")
    PINYIN_AVAILABLE = False

try:
    from stl import mesh
    STL_AVAILABLE = True
except ImportError:
    print("⚠️  警告: 未安装numpy-stl库，无法重置STL位置")
    STL_AVAILABLE = False


def matrix_to_quaternion(R):
    """
    将3x3旋转矩阵转换为四元数 (w, x, y, z)
    MuJoCo使用四元数格式: w x y z
    
    修复版本：正确处理Fusion 360的旋转矩阵，解决旋转方向相反的问题
    """
    # 确保输入是numpy数组
    R = np.array(R, dtype=float)

    # 方法1：使用标准转换公式（修复符号问题）
    # 计算四元数分量
    tr = R[0,0] + R[1,1] + R[2,2]
    
    if tr > 0:
        S = np.sqrt(tr + 1.0) * 2  # S = 4 * qw
        qw = 0.25 * S
        qx = (R[2,1] - R[1,2]) / S
        qy = (R[0,2] - R[2,0]) / S
        qz = (R[1,0] - R[0,1]) / S
    elif (R[0,0] > R[1,1]) and (R[0,0] > R[2,2]):
        S = np.sqrt(1.0 + R[0,0] - R[1,1] - R[2,2]) * 2  # S = 4 * qx
        qw = (R[2,1] - R[1,2]) / S
        qx = 0.25 * S
        qy = (R[0,1] + R[1,0]) / S
        qz = (R[0,2] + R[2,0]) / S
    elif R[1,1] > R[2,2]:
        S = np.sqrt(1.0 + R[1,1] - R[0,0] - R[2,2]) * 2  # S = 4 * qy
        qw = (R[0,2] - R[2,0]) / S
        qx = (R[0,1] + R[1,0]) / S
        qy = 0.25 * S
        qz = (R[1,2] + R[2,1]) / S
    else:
        S = np.sqrt(1.0 + R[2,2] - R[0,0] - R[1,1]) * 2  # S = 4 * qz
        qw = (R[1,0] - R[0,1]) / S
        qx = (R[0,2] + R[2,0]) / S
        qy = (R[1,2] + R[2,1]) / S
        qz = 0.25 * S

    return np.array([qw, qx, qy, qz])


class MuJoCoXMLGenerator:
    def __init__(self, export_dir, reset_stl_position=False):
        self.export_dir = Path(export_dir)
        self.reset_stl_position = reset_stl_position

        # 查找JSON文件（可能在子目录中）
        json_files = list(self.export_dir.rglob("component_positions.json"))
        if json_files:
            self.json_file = json_files[0]
            self.actual_export_dir = self.json_file.parent
        else:
            self.json_file = self.export_dir / "component_positions.json"
            self.actual_export_dir = self.export_dir

        # 查找STL文件（在stl_files子目录中）
        stl_dir = self.actual_export_dir / "stl_files"
        if stl_dir.exists():
            self.stl_files = list(stl_dir.glob("*.stl"))
        else:
            self.stl_files = list(self.actual_export_dir.rglob("*.stl"))

        # 设置输出目录
        self.mujoco_dir = self.actual_export_dir / "mujoco"
        self.assets_dir = self.mujoco_dir / "assets"
        self.xml_file = self.mujoco_dir / "model.xml"
        self.viewer_script = self.mujoco_dir / "viewer.py"

        # 创建目录
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        # 存储文件名映射
        self.filename_mapping = {}

        # 存储STL偏移量（用于位置补偿）
        self.mesh_offsets = {}

        print(f"📂 导出目录: {self.export_dir}")
        print(f"📄 JSON文件: {self.json_file}")
        print(f"📁 实际导出目录: {self.actual_export_dir}")
        print(f"🔍 找到STL文件: {len(self.stl_files)} 个")
        print(f"🔄 重置STL位置: {'是' if self.reset_stl_position else '否'}")

    def chinese_to_pinyin(self, text):
        """将中文转换为拼音"""
        if not PINYIN_AVAILABLE:
            # 简单替换：移除中文字符，保留英文、数字和下划线
            return re.sub(r'[^\u0000-\u007F]+', '_', text)

        try:
            # 获取拼音
            result = pinyin(text, style=Style.NORMAL)
            # 将拼音列表合并为字符串
            pinyin_str = '_'.join([item[0] for item in result])
            # 清理特殊字符
            pinyin_str = re.sub(r'[^a-zA-Z0-9_]', '_', pinyin_str)
            return pinyin_str
        except Exception as e:
            print(f"拼音转换失败: {e}, 使用简单替换")
            return re.sub(r'[^\u0000-\u007F]+', '_', text)

    def get_safe_filename(self, filename):
        """生成安全的文件名"""
        name = Path(filename).stem
        ext = Path(filename).suffix.lower()

        # 转换中文为拼音
        safe_name = self.chinese_to_pinyin(name)

        # 清理其他特殊字符
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', safe_name)

        # 确保不以数字开头
        if safe_name and safe_name[0].isdigit():
            safe_name = f"stl_{safe_name}"

        # 避免空文件名
        if not safe_name:
            safe_name = "unnamed_stl"

        return f"{safe_name}{ext}"

    def reset_stl_to_origin(self, stl_file_path, output_path, mesh_name):
        """将STL文件重置到原点"""
        if not STL_AVAILABLE:
            print(f"⚠️  跳过STL重置: {stl_file_path.name} (numpy-stl未安装)")
            return None

        try:
            # 加载STL文件
            stl_mesh = mesh.Mesh.from_file(str(stl_file_path))

            # 获取所有顶点
            vertices = stl_mesh.vectors.reshape(-1, 3)

            # 计算包围盒中心
            bbox_min = vertices.min(axis=0)
            bbox_max = vertices.max(axis=0)
            bbox_center = (bbox_min + bbox_max) / 2.0

            # 将所有顶点平移到原点
            vertices_centered = vertices - bbox_center

            # 更新STL网格
            stl_mesh.vectors = vertices_centered.reshape(-1, 3, 3)

            # 保存重置后的STL文件
            stl_mesh.save(str(output_path))

            # 存储偏移量
            self.mesh_offsets[mesh_name] = bbox_center

            print(f"  🔄 重置STL位置: {stl_file_path.name} (中心: {bbox_center})")
            return bbox_center

        except Exception as e:
            print(f"❌ STL重置失败: {stl_file_path.name} - {e}")
            return None

    def copy_and_rename_stl_files(self):
        """复制并重命名STL文件到assets目录"""
        print("📁 复制和重命名STL文件...")

        for stl_file in self.stl_files:
            safe_filename = self.get_safe_filename(stl_file.name)
            target_path = self.assets_dir / safe_filename

            if self.reset_stl_position:
                # 重置STL位置到原点
                mesh_name = Path(safe_filename).stem
                offset = self.reset_stl_to_origin(stl_file, target_path, mesh_name)
                if offset is not None:
                    print(f"  ✅ {stl_file.name} → {safe_filename} (已重置位置)")
                else:
                    # 如果重置失败，直接复制
                    shutil.copy2(stl_file, target_path)
                    print(f"  ⚠️  {stl_file.name} → {safe_filename} (重置失败，直接复制)")
            else:
                # 直接复制文件
                shutil.copy2(stl_file, target_path)
                print(f"  📋 {stl_file.name} → {safe_filename} (保持原始位置)")

            # 记录映射关系
            self.filename_mapping[stl_file.name] = safe_filename

    def load_export_data(self):
        """加载导出的JSON数据"""
        if not self.json_file.exists():
            print(f"❌ 未找到JSON数据文件: {self.json_file}")
            return None

        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 打印元数据信息
            meta = data.get('meta', {})
            print(f"✅ 成功加载JSON数据")
            print(f"   - 组件数量: {len(data.get('components', []))}")
            print(f"   - 导出时间: {meta.get('export_time', 'N/A')}")
            print(f"   - 导出模式: {meta.get('export_mode', 'N/A')}")
            print(f"   - 几何单位: {meta.get('geometry_unit', 'N/A')}")
            print(f"   - 位置单位: {meta.get('position_unit', 'N/A')}")
            print(f"   - 矩阵存储: {meta.get('matrix_storage', 'N/A')}")
            print(f"   - 格式版本: {meta.get('format_version', 'N/A')}")

            return data
        except Exception as e:
            print(f"❌ 加载JSON数据失败: {e}")
            return None

    def generate_xml(self, export_data):
        """生成MuJoCo XML文件"""
        print("🔧 生成MuJoCo XML文件...")

        # 打印一些调试信息
        components = export_data.get('components', [])
        print(f"📊 组件数量: {len(components)}")

        # 检查第一个组件的数据结构
        if components:
            first_comp = components[0]
            print(f"🔍 第一个组件示例:")
            print(f"   - 名称: {first_comp.get('component_name', 'N/A')}")
            print(f"   - STL文件: {first_comp.get('stl_file', 'N/A')}")
            print(f"   - Occurrence名称: {first_comp.get('occurrence_name', 'N/A')}")
            print(f"   - 完整路径: {first_comp.get('occurrence_fullname', 'N/A')}")
            if 'position' in first_comp:
                pos_data = first_comp['position']
                print(f"   - 位置数据键: {list(pos_data.keys())}")
                if 'current_position' in pos_data:
                    print(f"   - 当前位置: {pos_data['current_position']}")
                if 'current_quaternion' in pos_data:
                    print(f"   - 当前四元数: {pos_data['current_quaternion']}")

        # 计算所有组件的绝对位置并调整为平铺结构
        print("📊 计算平铺位置（无层级结构）...")
        
        # 首先找到base组件作为参考
        base_component = None
        base_abs_pos = [0, 0, 0]
        
        # 计算所有组件的绝对位置
        component_abs_positions = {}
        for comp in components:
            comp_name = comp.get('component_name', '')
            position_data = comp.get('position', {})
            
            # 使用当前矩阵
            matrix = position_data.get('current_matrix', [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])
            
            # 提取位置（厘米->米）
            if len(matrix) >= 16:
                tx_cm = matrix[3]   # X位置 (厘米)
                ty_cm = matrix[7]   # Y位置 (厘米)
                tz_cm = matrix[11]  # Z位置 (厘米)
                abs_pos = [tx_cm * 0.01, ty_cm * 0.01, tz_cm * 0.01]
            else:
                abs_pos = [0, 0, 0]
            
            component_abs_positions[comp_name] = abs_pos
            
            if comp_name.lower() == 'base':
                base_component = comp
                base_abs_pos = abs_pos
        
        print(f"   Base组件绝对位置: {base_abs_pos}")
        
        # 调整所有组件位置（相对于base的偏移）
        adjusted_positions = {}
        for comp_name, abs_pos in component_abs_positions.items():
            if comp_name.lower() == 'base':
                # base保持在原点
                adjusted_positions[comp_name] = [0, 0, 0]
            else:
                # 其他组件减去base的位置
                adjusted_pos = [abs_pos[i] - base_abs_pos[i] for i in range(3)]
                adjusted_positions[comp_name] = adjusted_pos
            
            print(f"   {comp_name}: {adjusted_positions[comp_name]}")

        # XML头部
        xml_content = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_content.append('<mujoco model="fusion360_export">')

        # 基本选项
        xml_content.append('  <option timestep="0.001">')
        xml_content.append('    <flag gravity="enable" contact="enable"/>')
        xml_content.append('  </option>')

        # 默认设置
        xml_content.append('  <default>')
        xml_content.append('    <geom type="mesh" contype="0" conaffinity="0"/>')
        xml_content.append('    <joint type="free" armature="0.001" damping="0.1"/>')
        xml_content.append('  </default>')

        # 资产定义
        xml_content.append('  <asset>')

        # 添加所有STL文件作为mesh
        for stl_file in self.stl_files:
            safe_filename = self.filename_mapping.get(stl_file.name, stl_file.name)
            mesh_name = Path(safe_filename).stem

            # STL文件使用毫米单位，需要缩放到米
            xml_content.append(f'    <mesh name="{mesh_name}" file="assets/{safe_filename}" scale="0.001 0.001 0.001"/>')

        xml_content.append('  </asset>')

        # 世界体
        xml_content.append('  <worldbody>')

        # 添加光源
        xml_content.append('    <light name="light" pos="0 -5 3" dir="0 1 -1"/>')

        # 平铺添加所有组件（无层级结构）
        for comp in components:
            comp_name = comp.get('component_name', '')
            adjusted_pos = adjusted_positions.get(comp_name, [0, 0, 0])
            
            # 使用平铺方式添加组件
            self._add_component_flat(xml_content, comp, adjusted_pos)

        xml_content.append('  </worldbody>')
        xml_content.append('</mujoco>')

        # 写入XML文件
        xml_string = '\n'.join(xml_content)
        with open(self.xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_string)

        print(f"✅ XML文件已生成: {self.xml_file}")

    def _analyze_hierarchy(self, components):
        """分析组件层级关系"""
        hierarchy = {}

        # 打印所有组件的occurrence信息以便调试
        print("🔍 调试 - 所有组件的occurrence信息:")
        for comp in components:
            print(f"   - {comp.get('component_name', 'Unknown')}: occurrence='{comp.get('occurrence_name', 'N/A')}', fullname='{comp.get('occurrence_fullname', 'N/A')}'")

        # 简化策略：根据组件名称和位置推断层级关系
        # 这里我们假设：
        # 1. base 是根组件
        # 2. connect 连接到 base
        # 3. hang 连接到 connect

        # 找出各个组件
        base_comp = None
        connect_comp = None
        hang_comp = None

        for comp in components:
            comp_name = comp.get('component_name', '').lower()
            if 'base' in comp_name:
                base_comp = comp
            elif 'connect' in comp_name:
                connect_comp = comp
            elif 'hang' in comp_name:
                hang_comp = comp

        # 构建层级关系
        if base_comp:
            hierarchy['root'] = [base_comp]
            if connect_comp:
                hierarchy['base'] = [connect_comp]
                if hang_comp:
                    hierarchy['connect'] = [hang_comp]

        return hierarchy

    def _add_components_hierarchical(self, xml_content, components, hierarchy, parent_path="root", indent=0):
        """按层级添加组件"""
        indent_str = '  ' * indent

        # 获取当前层级的子组件
        children = hierarchy.get(parent_path, [])

        # 添加当前层级的组件
        for comp in children:
            comp_name = comp.get('component_name', 'N/A')
            print(f"📦 处理组件: {comp_name} (父级: {parent_path})")

            # 添加组件到XML
            self._add_component_to_xml_hierarchical(xml_content, comp, indent)

            # 递归添加子组件
            child_path = comp_name.lower()  # 使用小写名称作为下一级的键
            self._add_components_hierarchical(xml_content, components, hierarchy, child_path, indent + 1)

            # 关闭body标签
            xml_content.append(f'{indent_str}</body>')

    def _add_component_to_xml_hierarchical(self, xml_content, component, indent=0):
        """添加单个组件到XML（层级版本）"""
        # 获取STL文件名
        stl_file = component.get('stl_file', '')
        if not stl_file:
            print(f"⚠️  跳过没有STL文件的组件: {component.get('component_name', 'Unknown')}")
            return

        safe_filename = self.filename_mapping.get(stl_file, stl_file)
        mesh_name = Path(safe_filename).stem

        # 获取位置信息
        position_data = component.get('position', {})
        print(f"🔍 组件 {component.get('component_name', 'Unknown')} 位置数据键: {list(position_data.keys())}")

        # 从矩阵中提取位置和旋转
        if hasattr(self, 'export_assembly_positions') and self.export_assembly_positions and position_data.get('assembly_matrix'):
            # 使用装配矩阵
            matrix = position_data.get('assembly_matrix', [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])
            position_type = "assembly"
            print(f"   - 使用装配矩阵")
        else:
            # 使用当前矩阵
            matrix = position_data.get('current_matrix', [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])
            position_type = "current"
            print(f"   - 使用当前矩阵")

        print(f"   - 矩阵数据: {matrix}")

        # 从矩阵中提取位置
        if len(matrix) >= 16:
            # 使用row-major格式(3,7,11)提取位置（基于分析结果）
            tx_cm = matrix[3]   # X位置 (厘米)
            ty_cm = matrix[7]   # Y位置 (厘米)
            tz_cm = matrix[11]  # Z位置 (厘米)
            
            # 转换为米 (厘米->米)
            position = [tx_cm * 0.01, ty_cm * 0.01, tz_cm * 0.01]
            
            print(f"   - 从矩阵提取位置(cm) [row-major(3,7,11)]: ({tx_cm}, {ty_cm}, {tz_cm})")
            print(f"   - 转换为位置(m): {position}")
        else:
            position = [0, 0, 0]
            print(f"   - 警告: 矩阵长度不足，使用默认位置")

        # 从矩阵中提取旋转并转换为四元数
        if len(matrix) >= 16:
            # 提取3x3旋转子矩阵（列主序 - Fusion 360格式）
            # Fusion 360的4x4列主序矩阵格式：
            # [ R00, R10, R20, 0 ]
            # [ R01, R11, R21, 0 ]
            # [ R02, R12, R22, 0 ]
            # [ Tx,  Ty,  Tz,   1 ]
            # 然后转置矩阵以还原Fusion 360中的视觉效果
            R = np.array([
                [matrix[0], matrix[4], matrix[8]],
                [matrix[1], matrix[5], matrix[9]],
                [matrix[2], matrix[6], matrix[10]]
            ]).T  # 转置以还原Fusion 360视觉效果
            quaternion = matrix_to_quaternion(R)
            print(f"   - 旋转矩阵(列主序+转置): {R.tolist()}")
            print(f"   - 转换为四元数: {quaternion.tolist()}")
        else:
            quaternion = np.array([1, 0, 0, 0])
            print(f"   - 警告: 矩阵长度不足，使用默认四元数")

        # 如果重置了STL位置，需要补偿偏移量
        if self.reset_stl_position and mesh_name in self.mesh_offsets:
            # 获取STL的偏移量（单位：mm，因为STL顶点通常是mm）
            delta_mm = self.mesh_offsets[mesh_name]
            # 转换为厘米（与矩阵位置单位一致）
            delta_cm = delta_mm * 0.1
            # 转换为米
            delta_m = delta_cm * 0.01

            # 补偿公式：t' = t - R * delta
            position = np.array(position) - R @ delta_m
            compensation_info = f"STL重置补偿: delta(mm)={delta_mm.tolist()}, delta(cm)={delta_cm.tolist()}"
            print(f"   - STL重置补偿后位置: {position.tolist()}")
        else:
            compensation_info = "无STL重置"

        # 确保四元数是单位四元数（归一化）
        quaternion_norm = np.linalg.norm(quaternion)
        if quaternion_norm > 0:
            quaternion = quaternion / quaternion_norm
        else:
            quaternion = np.array([1, 0, 0, 0])  # 默认单位四元数
            print(f"   - 警告: 四元数为零，使用默认值")

        print(f"   - 最终位置: {position}")
        print(f"   - 最终四元数: {quaternion}")

        # 生成安全的body名称
        component_name = component.get('component_name', 'component')
        occurrence_name = component.get('occurrence_name', '')
        safe_body_name = self.chinese_to_pinyin(f"{component_name}_{occurrence_name}")
        safe_body_name = re.sub(r'[^a-zA-Z0-9_]', '_', safe_body_name)

        # 缩进
        indent_str = '  ' * indent

        # 添加body，包含位置和旋转
        xml_content.append(f'{indent_str}<body name="{safe_body_name}" pos="{position[0]} {position[1]} {position[2]}" quat="{quaternion[0]} {quaternion[1]} {quaternion[2]} {quaternion[3]}">')

        # 添加关节（如果是根组件使用free，否则使用hinge）
        if indent == 0:  # 根组件
            xml_content.append(f'{indent_str}  <joint name="{safe_body_name}_joint" type="free"/>')
        else:  # 子组件
            # 简化：使用hinge关节，实际应该根据装配关系确定关节类型和轴
            xml_content.append(f'{indent_str}  <joint name="{safe_body_name}_joint" type="hinge" axis="0 0 1"/>')

        # 添加geom，使用mesh引用
        xml_content.append(f'{indent_str}  <geom name="{safe_body_name}_geom" type="mesh" mesh="{mesh_name}" rgba="0.7 0.7 0.7 1"/>')

        # 添加调试信息
        xml_content.append(f'{indent_str}  <!-- {compensation_info} -->')
        xml_content.append(f'{indent_str}  <!-- position_type: {position_type} -->')
        xml_content.append(f'{indent_str}  <!-- component: {component_name} -->')
        if occurrence_name:
            xml_content.append(f'{indent_str}  <!-- occurrence: {occurrence_name} -->')
        xml_content.append(f'{indent_str}  <!-- matrix_pos_mm: ({matrix[3] if len(matrix)>=16 else 0}, {matrix[7] if len(matrix)>=16 else 0}, {matrix[11] if len(matrix)>=16 else 0}) -->')

    def _add_component_to_xml(self, xml_content, component):
        """添加单个组件到XML"""
        # 获取STL文件名
        stl_file = component.get('stl_file', '')
        if not stl_file:
            print(f"⚠️  跳过没有STL文件的组件: {component.get('component_name', 'Unknown')}")
            return  # 跳过没有STL文件的组件

        safe_filename = self.filename_mapping.get(stl_file, stl_file)
        mesh_name = Path(safe_filename).stem

        # 获取位置信息
        position_data = component.get('position', {})
        print(f"🔍 组件 {component.get('component_name', 'Unknown')} 位置数据键: {list(position_data.keys())}")

        # 从矩阵中提取位置和旋转
        if hasattr(self, 'export_assembly_positions') and self.export_assembly_positions and position_data.get('assembly_matrix'):
            # 使用装配矩阵
            matrix = position_data.get('assembly_matrix', [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])
            position_type = "assembly"
            print(f"   - 使用装配矩阵")
        else:
            # 使用当前矩阵
            matrix = position_data.get('current_matrix', [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])
            position_type = "current"
            print(f"   - 使用当前矩阵")

        print(f"   - 矩阵数据: {matrix}")

        # 从矩阵中提取位置
        if len(matrix) >= 16:
            # 使用row-major格式(3,7,11)提取位置（基于分析结果）
            tx_cm = matrix[3]   # X位置 (厘米)
            ty_cm = matrix[7]   # Y位置 (厘米)
            tz_cm = matrix[11]  # Z位置 (厘米)
            
            # 转换为米 (厘米->米)
            position = [tx_cm * 0.01, ty_cm * 0.01, tz_cm * 0.01]
            
            print(f"   - 从矩阵提取位置(cm) [row-major(3,7,11)]: ({tx_cm}, {ty_cm}, {tz_cm})")
            print(f"   - 转换为位置(m): {position}")
        else:
            position = [0, 0, 0]
            print(f"   - 警告: 矩阵长度不足，使用默认位置")

        # 从矩阵中提取旋转并转换为四元数
        if len(matrix) >= 16:
            # 提取3x3旋转子矩阵（列主序 - Fusion 360格式）
            # 然后转置矩阵以还原Fusion 360中的视觉效果
            R = np.array([
                [matrix[0], matrix[4], matrix[8]],
                [matrix[1], matrix[5], matrix[9]],
                [matrix[2], matrix[6], matrix[10]]
            ]).T  # 转置以还原Fusion 360视觉效果
            quaternion = matrix_to_quaternion(R)
            print(f"   - 旋转矩阵: {R.tolist()}")
            print(f"   - 转换为四元数: {quaternion.tolist()}")
        else:
            quaternion = np.array([1, 0, 0, 0])
            print(f"   - 警告: 矩阵长度不足，使用默认四元数")

        # 如果重置了STL位置，需要补偿偏移量
        if self.reset_stl_position and mesh_name in self.mesh_offsets:
            # 获取STL的偏移量（单位：mm，因为STL顶点通常是mm）
            delta_mm = self.mesh_offsets[mesh_name]
            # 转换为厘米（与矩阵位置单位一致）
            delta_cm = delta_mm * 0.1
            # 转换为米
            delta_m = delta_cm * 0.01

            # 补偿公式：t' = t - R * delta
            position = np.array(position) - R @ delta_m
            compensation_info = f"STL重置补偿: delta(mm)={delta_mm.tolist()}, delta(cm)={delta_cm.tolist()}"
            print(f"   - STL重置补偿后位置: {position.tolist()}")
        else:
            compensation_info = "无STL重置"

        # 确保四元数是单位四元数（归一化）
        quaternion_norm = np.linalg.norm(quaternion)
        if quaternion_norm > 0:
            quaternion = quaternion / quaternion_norm
        else:
            quaternion = np.array([1, 0, 0, 0])  # 默认单位四元数
            print(f"   - 警告: 四元数为零，使用默认值")

        print(f"   - 最终位置: {position}")
        print(f"   - 最终四元数: {quaternion}")

        # 生成安全的body名称
        component_name = component.get('component_name', 'component')
        occurrence_name = component.get('occurrence_name', '')
        safe_body_name = self.chinese_to_pinyin(f"{component_name}_{occurrence_name}")
        safe_body_name = re.sub(r'[^a-zA-Z0-9_]', '_', safe_body_name)

        # 添加body，包含位置和旋转
        xml_content.append(f'    <body name="{safe_body_name}" pos="{position[0]} {position[1]} {position[2]}" quat="{quaternion[0]} {quaternion[1]} {quaternion[2]} {quaternion[3]}">')

        # 添加free关节
        xml_content.append(f'      <joint name="{safe_body_name}_joint" type="free"/>')

        # 添加geom，使用mesh引用
        xml_content.append(f'      <geom name="{safe_body_name}_geom" type="mesh" mesh="{mesh_name}" rgba="0.7 0.7 0.7 1"/>')

        # 添加调试信息
        xml_content.append(f'      <!-- {compensation_info} -->')
        xml_content.append(f'      <!-- position_type: {position_type} -->')
        xml_content.append(f'      <!-- component: {component_name} -->')
        if occurrence_name:
            xml_content.append(f'      <!-- occurrence: {occurrence_name} -->')
        xml_content.append(f'      <!-- matrix_pos_mm: ({matrix[12] if len(matrix)>=16 else 0}, {matrix[13] if len(matrix)>=16 else 0}, {matrix[14] if len(matrix)>=16 else 0}) -->')

        xml_content.append('    </body>')

    def create_viewer_script(self):
        """创建查看器启动脚本"""
        print("🎮 创建查看器脚本...")

        script_content = '''#!/usr/bin/env python3
"""
MuJoCo 查看器启动脚本
用于验证Fusion 360导出的STL文件位置是否正确
"""

import mujoco
import mujoco.viewer
import os
import json

def load_original_positions():
    """加载原始的JSON位置数据用于对比"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 查找上一级的component_positions.json
    json_path = os.path.join(script_dir, "..", "component_positions.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return None

def main():
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    xml_file = os.path.join(script_dir, "model.xml")
    
    if not os.path.exists(xml_file):
        print(f"❌ 未找到XML文件: {xml_file}")
        return
    
    try:
        # 加载原始位置数据
        original_data = load_original_positions()
        
        # 加载模型
        model = mujoco.MjModel.from_xml_path(xml_file)
        data = mujoco.MjData(model)
        
        print("✅ 模型加载成功")
        print(f"  组件数量: {model.nbody - 1}")  # 减去worldbody
        print(f"  自由度: {model.nv}")
        print(f"  几何体: {model.ngeom}")
        
        # 打印组件位置对比信息
        print("📋 组件位置对比:")
        print("=" * 80)
        
        for i in range(1, model.nbody):  # 跳过worldbody
            body_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i)
            if body_name:
                body_pos = data.xpos[i]
                body_quat = data.xquat[i]
                
                print(f"🔧 {body_name}")
                print(f"   MuJoCo位置: ({body_pos[0]:.6f}, {body_pos[1]:.6f}, {body_pos[2]:.6f})")
                print(f"   MuJoCo旋转: ({body_quat[0]:.6f}, {body_quat[1]:.6f}, {body_quat[2]:.6f}, {body_quat[3]:.6f})")
                
                # 尝试找到原始数据中的位置
                if original_data and 'components' in original_data:
                    for component in original_data['components']:
                        comp_name = component.get('component_name', '')
                        occ_name = component.get('occurrence_name', '')
                        
                        # 检查是否匹配
                        if comp_name in body_name and (not occ_name or occ_name in body_name):
                            position_data = component.get('position', {})
                            original_pos = position_data.get('current_position', [0, 0, 0])
                            original_quat = position_data.get('current_quaternion', [1, 0, 0, 0])
                            
                            print(f"   原始位置:   ({original_pos[0]:.6f}, {original_pos[1]:.6f}, {original_pos[2]:.6f})")
                            print(f"   原始旋转:   ({original_quat[0]:.6f}, {original_quat[1]:.6f}, {original_quat[2]:.6f}, {original_quat[3]:.6f})")
                            
                            # 计算位置差异
                            diff_pos = [abs(body_pos[i] - original_pos[i]) for i in range(3)]
                            max_diff = max(diff_pos)
                            
                            if max_diff < 1e-6:
                                print(f"   ✅ 位置匹配 (差异: {max_diff:.2e})")
                            else:
                                print(f"   ⚠️  位置差异 (最大差异: {max_diff:.6f})")
                                print(f"      X差异: {diff_pos[0]:.6f}")
                                print(f"      Y差异: {diff_pos[1]:.6f}")
                                print(f"      Z差异: {diff_pos[2]:.6f}")
                            
                            break
                else:
                    print(f"   ⚠️  未找到原始位置数据")
                
                print()
        
        print("=" * 80)
        print("🎮 启动交互式查看器...")
        print("💡 操作提示:")
        print("  - 鼠标左键拖拽: 旋转视角")
        print("  - 鼠标右键拖拽: 平移视角")
        print("  - 滚轮: 缩放")
        print("  - 空格键: 暂停/继续仿真")
        print("  - 可以拖拽组件验证位置是否正确")
        print("  - 关闭窗口退出程序")
        
        # 启动查看器
        mujoco.viewer.launch(model, data)
        
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
'''

        with open(self.viewer_script, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # 设置执行权限
        os.chmod(self.viewer_script, 0o755)

        print(f"✅ 查看器脚本已创建: {self.viewer_script}")

    def run(self):
        """运行完整的转换流程"""
        print("🚀 开始Fusion 360到MuJoCo转换流程...")

        # 1. 复制和重命名STL文件
        self.copy_and_rename_stl_files()

        # 2. 加载导出数据
        export_data = self.load_export_data()
        if not export_data:
            return

        # 3. 生成XML文件
        self.generate_xml(export_data)

        # 4. 创建查看器脚本
        self.create_viewer_script()

        print("\n🎉 转换完成!")
        print(f"📂 MuJoCo项目目录: {self.mujoco_dir}")
        print(f"📄 XML文件: {self.xml_file}")
        print(f"📁 STL文件目录: {self.assets_dir}")
        print(f"🎮 查看器脚本: {self.viewer_script}")
        print("\n📋 使用方法:")
        print(f"  cd {self.mujoco_dir}")
        print("  python3 viewer.py")
        print("\n💡 使用提示:")
        print("  - STL文件使用毫米单位，位置信息使用米单位")
        print("  - 使用 --reset-stl-position 启用STL位置重置")
        print("  - 查看器会显示位置和旋转对比信息")
        print("\n🔧 调试信息:")
        print("  - XML注释中包含组件和occurrence信息")
        print("  - 查看器显示位置差异和旋转四元数")

    def _add_component_flat(self, xml_content, component, position):
        """平铺方式添加单个组件到XML（无层级结构）"""
        # 获取STL文件名
        stl_file = component.get('stl_file', '')
        if not stl_file:
            print(f"⚠️  跳过没有STL文件的组件: {component.get('component_name', 'Unknown')}")
            return

        safe_filename = self.filename_mapping.get(stl_file, stl_file)
        mesh_name = Path(safe_filename).stem

        # 获取旋转信息
        position_data = component.get('position', {})
        matrix = position_data.get('current_matrix', [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])
        
        # 从矩阵中提取旋转并转换为四元数
        if len(matrix) >= 16:
            # 提取3x3旋转子矩阵（列主序 - Fusion 360格式）
            # 然后转置矩阵以还原Fusion 360中的视觉效果
            R = np.array([
                [matrix[0], matrix[4], matrix[8]],
                [matrix[1], matrix[5], matrix[9]],
                [matrix[2], matrix[6], matrix[10]]
            ]).T  # 转置以还原Fusion 360视觉效果
            quaternion = matrix_to_quaternion(R)
            print(f"   - 组件 {component.get('component_name', 'Unknown')} 旋转矩阵(列主序+转置): {R.tolist()}")
            print(f"   - 转换为四元数: {quaternion.tolist()}")
        else:
            quaternion = np.array([1, 0, 0, 0])

        # 如果重置了STL位置，需要补偿偏移量
        if self.reset_stl_position and mesh_name in self.mesh_offsets:
            # 获取STL的偏移量（单位：mm，因为STL顶点通常是mm）
            delta_mm = self.mesh_offsets[mesh_name]
            # 转换为厘米（与矩阵位置单位一致）
            delta_cm = delta_mm * 0.1
            # 转换为米
            delta_m = delta_cm * 0.01

            # 补偿公式：t' = t - R * delta
            position = np.array(position) - R @ delta_m
            compensation_info = f"STL重置补偿: delta(mm)={delta_mm.tolist()}, delta(cm)={delta_cm.tolist()}"
        else:
            compensation_info = "无STL重置"

        # 确保四元数是单位四元数（归一化）
        quaternion_norm = np.linalg.norm(quaternion)
        if quaternion_norm > 0:
            quaternion = quaternion / quaternion_norm
        else:
            quaternion = np.array([1, 0, 0, 0])

        # 生成安全的body名称
        component_name = component.get('component_name', 'component')
        occurrence_name = component.get('occurrence_name', '')
        safe_body_name = self.chinese_to_pinyin(f"{component_name}_{occurrence_name}")
        safe_body_name = re.sub(r'[^a-zA-Z0-9_]', '_', safe_body_name)

        # 添加body，包含位置和旋转
        xml_content.append(f'    <body name="{safe_body_name}" pos="{position[0]} {position[1]} {position[2]}" quat="{quaternion[0]} {quaternion[1]} {quaternion[2]} {quaternion[3]}">')

        # 添加free关节（平铺结构所有组件都使用free关节）
        xml_content.append(f'      <joint name="{safe_body_name}_joint" type="free"/>')

        # 添加geom，使用mesh引用
        xml_content.append(f'      <geom name="{safe_body_name}_geom" type="mesh" mesh="{mesh_name}" rgba="0.7 0.7 0.7 1"/>')

        # 添加调试信息
        xml_content.append(f'      <!-- {compensation_info} -->')
        xml_content.append(f'      <!-- component: {component_name} -->')
        if occurrence_name:
            xml_content.append(f'      <!-- occurrence: {occurrence_name} -->')

        xml_content.append('    </body>')


def _add_component_flat(self, xml_content, component, position):
        """平铺方式添加单个组件到XML（无层级结构）"""
        # 获取STL文件名
        stl_file = component.get('stl_file', '')
        if not stl_file:
            print(f"⚠️  跳过没有STL文件的组件: {component.get('component_name', 'Unknown')}")
            return

        safe_filename = self.filename_mapping.get(stl_file, stl_file)
        mesh_name = Path(safe_filename).stem

        # 获取旋转信息
        position_data = component.get('position', {})
        matrix = position_data.get('current_matrix', [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])
        
        # 从矩阵中提取旋转并转换为四元数
        if len(matrix) >= 16:
            # 提取3x3旋转子矩阵（列主序 - Fusion 360格式）
            # 然后转置矩阵以还原Fusion 360中的视觉效果
            R = np.array([
                [matrix[0], matrix[4], matrix[8]],
                [matrix[1], matrix[5], matrix[9]],
                [matrix[2], matrix[6], matrix[10]]
            ]).T  # 转置以还原Fusion 360视觉效果
            quaternion = matrix_to_quaternion(R)
            print(f"   - 组件 {component.get('component_name', 'Unknown')} 旋转矩阵(列主序+转置): {R.tolist()}")
            print(f"   - 转换为四元数: {quaternion.tolist()}")
        else:
            quaternion = np.array([1, 0, 0, 0])

        # 如果重置了STL位置，需要补偿偏移量
        if self.reset_stl_position and mesh_name in self.mesh_offsets:
            # 获取STL的偏移量（单位：mm，因为STL顶点通常是mm）
            delta_mm = self.mesh_offsets[mesh_name]
            # 转换为厘米（与矩阵位置单位一致）
            delta_cm = delta_mm * 0.1
            # 转换为米
            delta_m = delta_cm * 0.01

            # 补偿公式：t' = t - R * delta
            position = np.array(position) - R @ delta_m
            compensation_info = f"STL重置补偿: delta(mm)={delta_mm.tolist()}, delta(cm)={delta_cm.tolist()}"
        else:
            compensation_info = "无STL重置"

        # 确保四元数是单位四元数（归一化）
        quaternion_norm = np.linalg.norm(quaternion)
        if quaternion_norm > 0:
            quaternion = quaternion / quaternion_norm
        else:
            quaternion = np.array([1, 0, 0, 0])

        # 生成安全的body名称
        component_name = component.get('component_name', 'component')
        occurrence_name = component.get('occurrence_name', '')
        safe_body_name = self.chinese_to_pinyin(f"{component_name}_{occurrence_name}")
        safe_body_name = re.sub(r'[^a-zA-Z0-9_]', '_', safe_body_name)

        # 添加body，包含位置和旋转
        xml_content.append(f'    <body name="{safe_body_name}" pos="{position[0]} {position[1]} {position[2]}" quat="{quaternion[0]} {quaternion[1]} {quaternion[2]} {quaternion[3]}">')

        # 添加free关节（平铺结构所有组件都使用free关节）
        xml_content.append(f'      <joint name="{safe_body_name}_joint" type="free"/>')

        # 添加geom，使用mesh引用
        xml_content.append(f'      <geom name="{safe_body_name}_geom" type="mesh" mesh="{mesh_name}" rgba="0.7 0.7 0.7 1"/>')

        # 添加调试信息
        xml_content.append(f'      <!-- {compensation_info} -->')
        xml_content.append(f'      <!-- component: {component_name} -->')
        if occurrence_name:
            xml_content.append(f'      <!-- occurrence: {occurrence_name} -->')

        xml_content.append('    </body>')


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Fusion 360零部件位置导出数据转换为MuJoCo XML')
    parser.add_argument('export_dir', help='Fusion 360导出目录路径')
    parser.add_argument('--reset-stl-position', action='store_true',
                       help='重置STL文件位置到原点（默认不重置）')
    parser.add_argument('--use-assembly-positions', action='store_true',
                       help='使用装配位置而非当前位置（默认使用当前位置）')

    args = parser.parse_args()

    if not os.path.exists(args.export_dir):
        print(f"❌ 导出目录不存在: {args.export_dir}")
        return

    # 创建生成器
    generator = MuJoCoXMLGenerator(args.export_dir, reset_stl_position=args.reset_stl_position)

    # 设置是否使用装配位置
    generator.export_assembly_positions = args.use_assembly_positions

    # 运行转换流程
    generator.run()

def _add_component_flat(self, xml_content, component, position):
    """平铺方式添加单个组件到XML（无层级结构）"""
    # 获取STL文件名
    stl_file = component.get('stl_file', '')
    if not stl_file:
        print(f"⚠️  跳过没有STL文件的组件: {component.get('component_name', 'Unknown')}")
        return

    safe_filename = self.filename_mapping.get(stl_file, stl_file)
    mesh_name = Path(safe_filename).stem

    # 获取旋转信息
    position_data = component.get('position', {})
    matrix = position_data.get('current_matrix', [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])
    
    # 从矩阵中提取旋转并转换为四元数
    if len(matrix) >= 16:
        # 提取3x3旋转子矩阵（列主序 - Fusion 360格式）
        # 然后转置矩阵以还原Fusion 360中的视觉效果
        R = np.array([
            [matrix[0], matrix[4], matrix[8]],
            [matrix[1], matrix[5], matrix[9]],
            [matrix[2], matrix[6], matrix[10]]
        ]).T  # 转置以还原Fusion 360视觉效果
        quaternion = matrix_to_quaternion(R)
    else:
        quaternion = np.array([1, 0, 0, 0])

    # 如果重置了STL位置，需要补偿偏移量
    if self.reset_stl_position and mesh_name in self.mesh_offsets:
        # 获取STL的偏移量（单位：mm，因为STL顶点通常是mm）
        delta_mm = self.mesh_offsets[mesh_name]
        # 转换为厘米（与矩阵位置单位一致）
        delta_cm = delta_mm * 0.1
        # 转换为米
        delta_m = delta_cm * 0.01

        # 补偿公式：t' = t - R * delta
        position = np.array(position) - R @ delta_m
        compensation_info = f"STL重置补偿: delta(mm)={delta_mm.tolist()}, delta(cm)={delta_cm.tolist()}"
    else:
        compensation_info = "无STL重置"

    # 确保四元数是单位四元数（归一化）
    quaternion_norm = np.linalg.norm(quaternion)
    if quaternion_norm > 0:
        quaternion = quaternion / quaternion_norm
    else:
        quaternion = np.array([1, 0, 0, 0])

    # 生成安全的body名称
    component_name = component.get('component_name', 'component')
    occurrence_name = component.get('occurrence_name', '')
    safe_body_name = self.chinese_to_pinyin(f"{component_name}_{occurrence_name}")
    safe_body_name = re.sub(r'[^a-zA-Z0-9_]', '_', safe_body_name)

    # 添加body，包含位置和旋转
    xml_content.append(f'    <body name="{safe_body_name}" pos="{position[0]} {position[1]} {position[2]}" quat="{quaternion[0]} {quaternion[1]} {quaternion[2]} {quaternion[3]}">')

    # 添加free关节（平铺结构所有组件都使用free关节）
    xml_content.append(f'      <joint name="{safe_body_name}_joint" type="free"/>')

    # 添加geom，使用mesh引用
    xml_content.append(f'      <geom name="{safe_body_name}_geom" type="mesh" mesh="{mesh_name}" rgba="0.7 0.7 0.7 1"/>')

    # 添加调试信息
    xml_content.append(f'      <!-- {compensation_info} -->')
    xml_content.append(f'      <!-- component: {component_name} -->')
    if occurrence_name:
        xml_content.append(f'      <!-- occurrence: {occurrence_name} -->')

    xml_content.append('    </body>')


if __name__ == "__main__":
    main()