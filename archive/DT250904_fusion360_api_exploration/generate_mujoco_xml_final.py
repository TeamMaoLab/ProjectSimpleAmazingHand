"""
Fusion 360 STL导出数据转换为MuJoCo XML脚本 (最终版)

此脚本读取STL导出的JSON数据，生成对应的MuJoCo XML文件，
并使用pypinyin将中文文件名转换为拼音，创建完整的MuJoCo仿真环境。
特别优化了位置信息的提取和使用。
"""

import json
import os
import shutil
from pathlib import Path
import re
import numpy as np

try:
    from stl import mesh
    STL_AVAILABLE = True
except ImportError:
    print("⚠️  警告: 未安装numpy-stl库，无法重置STL位置")
    STL_AVAILABLE = False

try:
    from pypinyin import pinyin, Style
    PINYIN_AVAILABLE = True
except ImportError:
    print("⚠️  警告: 未安装pypinyin，将使用简单替换处理中文")
    PINYIN_AVAILABLE = False

def matrix_to_quaternion(R):
    """
    将3x3旋转矩阵转换为四元数 (w, x, y, z)
    MuJoCo使用四元数格式: w x y z
    """
    # 确保输入是numpy数组
    R = np.array(R, dtype=float)
    
    # 计算四元数分量
    qw = np.sqrt(max(0, 1 + R[0,0] + R[1,1] + R[2,2])) / 2
    qx = np.sqrt(max(0, 1 + R[0,0] - R[1,1] - R[2,2])) / 2
    qy = np.sqrt(max(0, 1 - R[0,0] + R[1,1] - R[2,2])) / 2
    qz = np.sqrt(max(0, 1 - R[0,0] - R[1,1] + R[2,2])) / 2
    
    # 确定符号
    qx = np.copysign(qx, R[2,1] - R[1,2])
    qy = np.copysign(qy, R[0,2] - R[2,0])
    qz = np.copysign(qz, R[1,0] - R[0,1])
    
    return np.array([qw, qx, qy, qz])


class MuJoCoXMLGenerator:
    def __init__(self, export_dir, reset_stl_position=False):
        self.export_dir = Path(export_dir)
        self.reset_stl_position = reset_stl_position  # 是否重置STL位置信息
        
        # 查找JSON文件（可能在子目录中）
        json_files = list(self.export_dir.rglob("export_data.json"))
        if json_files:
            self.json_file = json_files[0]
            self.actual_export_dir = self.json_file.parent
        else:
            self.json_file = self.export_dir / "export_data.json"
            self.actual_export_dir = self.export_dir
        
        # 查找STL文件（在JSON文件所在目录及其子目录）
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
        print(f"🔧 调试模式: 已启用基础验证（暂时关闭STL重置）")
        
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
            print(f"✅ 成功加载JSON数据: {len(data.get('components', {}))} 个组件")
            return data
        except Exception as e:
            print(f"❌ 加载JSON数据失败: {e}")
            return None
    
    def generate_xml(self, export_data):
        """生成MuJoCo XML文件"""
        print("🔧 生成MuJoCo XML文件...")
        
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
            
            # 如果重置了STL位置，需要添加缩放参数将毫米转换为米
            if self.reset_stl_position:
                xml_content.append(f'    <mesh name="{mesh_name}" file="assets/{safe_filename}" scale="0.001 0.001 0.001"/>')
            else:
                xml_content.append(f'    <mesh name="{mesh_name}" file="assets/{safe_filename}"/>')
        
        xml_content.append('  </asset>')
        
        # 世界体
        xml_content.append('  <worldbody>')
        
        # 添加地面
        # xml_content.append('    <geom name="ground" type="plane" size="10 10 0.1" rgba="0.5 0.5 0.5 1"/>')
        xml_content.append('    <light name="light" pos="0 -5 3" dir="0 1 -1"/>')
        
        # 添加所有组件
        components = export_data.get('components', {})
        for component_name, instances in components.items():
            for instance in instances:
                self._add_component_to_xml(xml_content, component_name, instance)
        
        xml_content.append('  </worldbody>')
        xml_content.append('</mujoco>')
        
        # 写入XML文件
        xml_string = '\n'.join(xml_content)
        with open(self.xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_string)
        
        print(f"✅ XML文件已生成: {self.xml_file}")
    
    def _add_component_to_xml(self, xml_content, component_name, instance):
        """添加单个组件到XML"""
        # 获取STL文件名
        stl_file = instance.get('stl_file', '')
        safe_filename = self.filename_mapping.get(stl_file, stl_file)
        mesh_name = Path(safe_filename).stem
        
        # 获取变换矩阵
        transform_matrix = instance.get('world_transform_matrix', 
                                    [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]])
        
        # 转换为numpy数组
        M = np.array(transform_matrix, dtype=float)
        
        # 提取平移部分（假设在最后一列，即列主序）
        # 如果发现位置不对，可能需要改为 M[3, 0:3]（行主序）
        t_cm = M[0:3, 3]  # 假设单位是cm
        
        # 提取旋转部分（左上3x3）
        R = M[0:3, 0:3]
        
        # 单位转换：cm -> m
        t_m = t_cm * 0.01
        
        # 如果重置了STL位置，需要补偿偏移量
        if self.reset_stl_position and mesh_name in self.mesh_offsets:
            # 获取STL的偏移量（单位：mm，因为STL顶点通常是mm）
            delta_mm = self.mesh_offsets[mesh_name]
            # 转换为米
            delta_m = delta_mm * 0.001
            # 补偿公式：t' = t - R * delta
            body_pos = t_m - R @ delta_m
            compensation_info = f"delta(mm)={delta_mm.tolist()}"
        else:
            # 不重置STL位置，直接使用变换矩阵的平移
            body_pos = t_m
            compensation_info = "无补偿"
        
        # 将旋转矩阵转换为四元数
        quat = matrix_to_quaternion(R)
        
        # 生成唯一的body名称
        occurrence_name = instance.get('occurrence_name', 'instance')
        safe_body_name = self.chinese_to_pinyin(f"{component_name}_{occurrence_name}")
        safe_body_name = re.sub(r'[^a-zA-Z0-9_]', '_', safe_body_name)
        
        # 添加body，包含位置和旋转
        xml_content.append(f'    <body name="{safe_body_name}" pos="{body_pos[0]} {body_pos[1]} {body_pos[2]}" quat="{quat[0]} {quat[1]} {quat[2]} {quat[3]}">')
        
        # 添加free关节
        xml_content.append(f'      <joint name="{safe_body_name}_joint" type="free"/>')
        
        # 添加geom，使用mesh引用
        if self.reset_stl_position:
            # 重置了STL位置，需要缩放（mm -> m）
            xml_content.append(f'      <geom name="{safe_body_name}_geom" type="mesh" mesh="{mesh_name}" rgba="0.7 0.7 0.7 1"/>')
        else:
            # 保持STL原始位置，不需要缩放
            xml_content.append(f'      <geom name="{safe_body_name}_geom" type="mesh" mesh="{mesh_name}" rgba="0.7 0.7 0.7 1"/>')
        
        # 添加调试信息
        xml_content.append(f'      <!-- t(cm)={t_cm.tolist()} {compensation_info} -->')
        xml_content.append(f'      <!-- R={R.tolist()} -->')
        
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
    # 查找上一级的export_data.json
    json_path = os.path.join(script_dir, "..", "export_data.json")
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
                
                # 尝试找到原始数据中的位置
                original_pos = None
                if original_data and 'components' in original_data:
                    for comp_name, instances in original_data['components'].items():
                        for instance in instances:
                            occurrence_name = instance.get('occurrence_name', '')
                            safe_comp_name = comp_name.replace(' ', '_').replace(':', '_')
                            safe_occ_name = occurrence_name.replace(' ', '_').replace(':', '_')
                            
                            if safe_comp_name in body_name and safe_occ_name in body_name:
                                # 获取质心的世界坐标位置
                                center_of_mass = instance.get('center_of_mass', {})
                                original_pos = center_of_mass.get('world', {})
                                break
                
                print(f"🔧 {body_name}")
                print(f"   MuJoCo位置: ({body_pos[0]:.6f}, {body_pos[1]:.6f}, {body_pos[2]:.6f})")
                
                if original_pos:
                    # 原始数据是厘米，转换为米以便与MuJoCo比较
                    orig_x, orig_y, orig_z = original_pos['x'] * 0.01, original_pos['y'] * 0.01, original_pos['z'] * 0.01
                    print(f"   原始位置:   ({orig_x:.6f}, {orig_y:.6f}, {orig_z:.6f}) [米]")
                    print(f"   原始位置:   ({original_pos['x']:.6f}, {original_pos['y']:.6f}, {original_pos['z']:.6f}) [厘米]")
                    
                    # 计算差异（现在都是米单位）
                    diff_x = abs(body_pos[0] - orig_x)
                    diff_y = abs(body_pos[1] - orig_y)
                    diff_z = abs(body_pos[2] - orig_z)
                    max_diff = max(diff_x, diff_y, diff_z)
                    
                    # 获取旋转信息
                    body_quat = data.xquat[i]
                    print(f"   MuJoCo旋转: ({body_quat[0]:.6f}, {body_quat[1]:.6f}, {body_quat[2]:.6f}, {body_quat[3]:.6f})")
                    
                    if max_diff < 1e-6:
                        print(f"   ✅ 位置匹配 (差异: {max_diff:.2e})")
                    else:
                        print(f"   ⚠️  位置差异 (最大差异: {max_diff:.6f})")
                        print(f"      X差异: {diff_x:.6f}")
                        print(f"      Y差异: {diff_y:.6f}")
                        print(f"      Z差异: {diff_z:.6f}")
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
        print("\n🔍 修复内容:")
        print("  - 修正变换矩阵translation索引（列3 vs 行3）")
        print("  - 添加旋转矩阵到四元数的转换")
        print("  - 修正单位转换（STL mm vs JSON cm）")
        print("  - 去掉使用center_of_mass作为body pos的逻辑")
        print("  - 添加STL重置后的位置补偿计算")
        print("  - 暂时关闭STL重置，验证基础功能")
        print("\n💡 使用提示:")
        print("  - 当前默认不重置STL位置，用于验证基础功能")
        print("  - 使用 --reset-stl-position 启用STL位置重置")
        print("  - 查看器会显示位置和旋转对比信息")
        print("\n🔧 调试信息:")
        print("  - XML注释中包含变换矩阵和补偿信息")
        print("  - 查看器显示位置差异和旋转四元数")
        print("  - 需要安装numpy-stl库: pip install numpy-stl")


def run_in_main():
    """

    :return:
    """
    generator = MuJoCoXMLGenerator("/Users/maoge/Documents/MaoLab/ProjectSimpleAmazingHand/tmp/tc_00/visible_components_stl_20250904_144753")
    generator.run()

def main():
    """主函数"""
    try:
        import argparse

        parser = argparse.ArgumentParser(description='Fusion 360 STL导出数据转换为MuJoCo XML')
        parser.add_argument('export_dir', help='STL导出目录路径')
        parser.add_argument('--reset-stl-position', action='store_true', 
                           help='重置STL文件位置到原点（默认不重置）')

        args = parser.parse_args()

        if not os.path.exists(args.export_dir):
            print(f"❌ 导出目录不存在: {args.export_dir}")
            return

        # 默认不重置STL位置，除非指定了--reset-stl-position
        reset_stl_position = args.reset_stl_position
        generator = MuJoCoXMLGenerator(args.export_dir, reset_stl_position=reset_stl_position)
        generator.run()
    except:
        run_in_main()





if __name__ == "__main__":
    main()