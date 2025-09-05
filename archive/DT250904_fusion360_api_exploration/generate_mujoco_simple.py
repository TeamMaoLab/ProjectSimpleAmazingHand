#!/usr/bin/env python3
"""
Fusion 360 STEP导出数据转换为MuJoCo XML脚本 (简化版)

此脚本读取新格式的STEP导出JSON数据，生成对应的MuJoCo XML文件。
新格式特点：
- 无质心数据
- 直接使用pos_m和quat_wxyz
- STEP文件需要转换为STL
"""

import json
import os
import shutil
from pathlib import Path
import re
import numpy as np
import argparse
import subprocess
import tempfile

try:
    from pypinyin import pinyin, Style
    PINYIN_AVAILABLE = True
except ImportError:
    print("⚠️  警告: 未安装pypinyin，将使用简单替换处理中文")
    PINYIN_AVAILABLE = False

try:
    import cadquery as cq
    CADQUERY_AVAILABLE = True
except ImportError:
    print("⚠️  警告: 未安装cadquery，将使用FreeCAD进行STEP转换")
    CADQUERY_AVAILABLE = False


def chinese_to_pinyin(text):
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


def get_safe_filename(text):
    """生成安全的文件名"""
    # 转换中文为拼音
    safe_name = chinese_to_pinyin(text)
    
    # 清理其他特殊字符
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', safe_name)
    
    # 确保不以数字开头
    if safe_name and safe_name[0].isdigit():
        safe_name = f"part_{safe_name}"
    
    # 避免空文件名
    if not safe_name:
        safe_name = "unnamed_part"
    
    return safe_name


class SimpleMuJoCoGenerator:
    def __init__(self, export_dir, stl_tolerance=0.1, prefer_freecad=False):
        self.export_dir = Path(export_dir)
        self.stl_tolerance = stl_tolerance
        self.prefer_freecad = prefer_freecad
        
        # 查找JSON文件
        json_files = list(self.export_dir.rglob("export_data.json"))
        if not json_files:
            raise FileNotFoundError(f"未找到 export_data.json 文件")
        
        self.json_file = json_files[0]
        self.base_dir = self.json_file.parent
        
        # 设置输出目录
        self.mujoco_dir = self.base_dir / "mujoco"
        self.assets_dir = self.mujoco_dir / "assets"
        self.xml_file = self.mujoco_dir / "model.xml"
        self.viewer_script = self.mujoco_dir / "viewer.py"
        
        # 创建目录
        self.mujoco_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(exist_ok=True)
        
        print(f"📂 导出目录: {self.export_dir}")
        print(f"📄 JSON文件: {self.json_file}")
        print(f"🔧 STL容差: {stl_tolerance}mm")
        print(f"🔧 转换工具: {'FreeCAD' if prefer_freecad else 'CadQuery (优先)'}")
        
    def load_export_data(self):
        """加载导出的JSON数据"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            meta = data.get('meta', {})
            print(f"✅ 成功加载JSON数据")
            print(f"   几何数量: {meta.get('count_geometries', 0)}")
            print(f"   实例数量: {meta.get('count_instances', 0)}")
            print(f"   格式版本: {meta.get('format_version', '未知')}")
            print(f"   包含质心: {meta.get('contains_com', False)}")
            
            return data
        except Exception as e:
            print(f"❌ 加载JSON数据失败: {e}")
            return None
    
    def convert_step_to_stl_cadquery(self, step_path, stl_path, tolerance=0.1):
        """使用CadQuery将STEP转换为STL"""
        if not CADQUERY_AVAILABLE:
            return False
        
        try:
            # 加载STEP文件
            shape = cq.importers.importStep(str(step_path))
            
            # 导出为STL
            cq.exporters.export(shape, str(stl_path), exportType='STL', tolerance=tolerance)
            
            return True
        except Exception as e:
            print(f"    ❌ CadQuery转换失败: {e}")
            return False
    
    def convert_step_to_stl_freecad(self, step_path, stl_path):
        """使用FreeCAD将STEP转换为STL"""
        try:
            # 创建FreeCAD宏脚本
            macro_script = f'''
import FreeCAD
import Part
import Mesh

# 加载STEP文件
shape = Part.Shape()
shape.load("{step_path}")

# 创建网格
mesh = Mesh.Mesh()
mesh.addFacets(shape.tessellate(0.1))

# 保存STL
mesh.write("{stl_path}")
print("STL导出完成")
'''
            
            # 写入临时宏文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(macro_script)
                macro_path = f.name
            
            # 运行FreeCAD
            result = subprocess.run([
                'freecad', '--console', '--hidden', macro_path
            ], capture_output=True, text=True, timeout=30)
            
            # 清理临时文件
            os.unlink(macro_path)
            
            if result.returncode == 0 and stl_path.exists():
                return True
            else:
                print(f"    ❌ FreeCAD转换失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("    ❌ FreeCAD转换超时")
            return False
        except FileNotFoundError:
            print("    ❌ 未找到FreeCAD，请安装或添加到PATH")
            return False
        except Exception as e:
            print(f"    ❌ FreeCAD转换异常: {e}")
            return False
    
    def process_step_files(self, export_data):
        """处理STEP文件，转换为STL"""
        print("🔄 处理STEP文件...")
        
        geometries = export_data.get('geometries', [])
        self.geometry_map = {}
        
        for geom in geometries:
            geom_id = geom['geometry_id']
            comp_name = geom['component_name']
            step_file = geom['file']
            
            # 生成安全的文件名
            safe_name = get_safe_filename(comp_name)
            stl_name = f"{safe_name}.stl"
            
            # 文件路径
            step_path = self.base_dir / step_file
            stl_path = self.assets_dir / stl_name
            
            if not step_path.exists():
                print(f"  ⚠️  STEP文件不存在: {step_file}")
                continue
            
            # 尝试转换STEP到STL
            converted = False
            
            # 根据偏好选择转换工具
            if self.prefer_freecad:
                print(f"  🔧 使用FreeCAD转换: {step_file}")
                converted = self.convert_step_to_stl_freecad(step_path, stl_path)
                if not converted and CADQUERY_AVAILABLE:
                    print(f"  🔧 FreeCAD失败，尝试CadQuery: {step_file}")
                    converted = self.convert_step_to_stl_cadquery(step_path, stl_path, self.stl_tolerance)
            else:
                # 优先使用CadQuery
                if CADQUERY_AVAILABLE:
                    print(f"  🔧 使用CadQuery转换: {step_file}")
                    converted = self.convert_step_to_stl_cadquery(step_path, stl_path, self.stl_tolerance)
                
                # 如果CadQuery失败，尝试FreeCAD
                if not converted:
                    print(f"  🔧 CadQuery失败，尝试FreeCAD: {step_file}")
                    converted = self.convert_step_to_stl_freecad(step_path, stl_path)
            
            if converted:
                print(f"  ✅ {step_file} → {stl_name}")
            else:
                print(f"  ❌ {step_file} 转换失败，复制原始文件")
                # 如果转换失败，复制原始STEP文件
                shutil.copy2(step_path, stl_path.with_suffix('.step'))
                # 修改文件名引用
                stl_name = f"{safe_name}.step"
            
            # 记录映射关系
            self.geometry_map[geom_id] = {
                'component_name': comp_name,
                'mesh_name': safe_name,
                'file': stl_name
            }
    
    def generate_xml(self, export_data):
        """生成MuJoCo XML文件"""
        print("🔧 生成MuJoCo XML文件...")
        
        # XML头部
        xml_lines = []
        xml_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        xml_lines.append('<mujoco model="fusion360_step_export">')
        
        # 基本选项
        xml_lines.append('  <option timestep="0.001">')
        xml_lines.append('    <flag gravity="enable" contact="enable"/>')
        xml_lines.append('  </option>')
        
        # 默认设置
        xml_lines.append('  <default>')
        xml_lines.append('    <geom type="mesh" contype="0" conaffinity="0"/>')
        xml_lines.append('  </default>')
        
        # 资产定义
        xml_lines.append('  <asset>')
        
        # 添加所有mesh
        for geom_id, geom_info in self.geometry_map.items():
            # 注意：STEP文件需要转换为STL，这里假设已经转换
            xml_lines.append(f'    <mesh name="{geom_info["mesh_name"]}" file="assets/{geom_info["file"]}" scale="0.001 0.001 0.001"/>')
        
        xml_lines.append('  </asset>')
        
        # 世界体
        xml_lines.append('  <worldbody>')
        xml_lines.append('    <light name="light" pos="0 -5 3" dir="0 1 -1"/>')
        
        # 添加所有实例
        instances = export_data.get('instances', [])
        for inst in instances:
            self._add_instance_to_xml(xml_lines, inst)
        
        xml_lines.append('  </worldbody>')
        xml_lines.append('</mujoco>')
        
        # 写入XML文件
        xml_content = '\n'.join(xml_lines)
        with open(self.xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"✅ XML文件已生成: {self.xml_file}")
    
    def _add_instance_to_xml(self, xml_lines, instance):
        """添加单个实例到XML"""
        geom_id = instance['geometry_id']
        if geom_id not in self.geometry_map:
            print(f"  ⚠️  跳过未知几何: {geom_id}")
            return
        
        geom_info = self.geometry_map[geom_id]
        
        # 获取位置和旋转
        pos = instance['pos_m']  # 已经是米
        quat = instance['quat_wxyz']  # w,x,y,z 格式
        
        # 生成安全的body名称
        occurrence_path = instance['occurrence_path']
        safe_body_name = get_safe_filename(occurrence_path.replace(':', '_'))
        
        # 添加body
        pos_str = f"{pos[0]:.9f} {pos[1]:.9f} {pos[2]:.9f}"
        quat_str = f"{quat[0]:.9f} {quat[1]:.9f} {quat[2]:.9f} {quat[3]:.9f}"
        
        xml_lines.append(f'    <body name="{safe_body_name}" pos="{pos_str}" quat="{quat_str}">')
        xml_lines.append('      <freejoint/>')
        xml_lines.append(f'      <geom type="mesh" mesh="{geom_info["mesh_name"]}" rgba="0.7 0.7 0.7 1"/>')
        xml_lines.append('    </body>')
    
    def create_viewer_script(self):
        """创建查看器脚本"""
        print("🎮 创建查看器脚本...")
        
        script_content = '''#!/usr/bin/env python3
"""
MuJoCo 查看器启动脚本
用于验证Fusion 360导出的STEP文件位置是否正确
"""

import mujoco
import mujoco.viewer
import os
import json

def main():
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    xml_file = os.path.join(script_dir, "model.xml")
    
    if not os.path.exists(xml_file):
        print(f"❌ 未找到XML文件: {xml_file}")
        return
    
    try:
        # 加载模型
        model = mujoco.MjModel.from_xml_path(xml_file)
        data = mujoco.MjData(model)
        
        print("✅ 模型加载成功")
        print(f"  组件数量: {model.nbody - 1}")  # 减去worldbody
        print(f"  自由度: {model.nv}")
        print(f"  几何体: {model.ngeom}")
        
        # 打印组件位置信息
        print("📋 组件位置信息:")
        print("=" * 80)
        
        for i in range(1, model.nbody):  # 跳过worldbody
            body_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i)
            if body_name:
                body_pos = data.xpos[i]
                body_quat = data.xquat[i]
                
                print(f"🔧 {body_name}")
                print(f"   位置: ({body_pos[0]:.6f}, {body_pos[1]:.6f}, {body_pos[2]:.6f})")
                print(f"   旋转: ({body_quat[0]:.6f}, {body_quat[1]:.6f}, {body_quat[2]:.6f}, {body_quat[3]:.6f})")
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
        print("🚀 开始Fusion 360 STEP到MuJoCo转换流程...")
        
        # 1. 加载导出数据
        export_data = self.load_export_data()
        if not export_data:
            return
        
        # 2. 处理STEP文件
        self.process_step_files(export_data)
        
        # 3. 生成XML文件
        self.generate_xml(export_data)
        
        # 4. 创建查看器脚本
        self.create_viewer_script()
        
        print("\n🎉 转换完成!")
        print(f"📂 MuJoCo项目目录: {self.mujoco_dir}")
        print(f"📄 XML文件: {self.xml_file}")
        print(f"📁 资源文件目录: {self.assets_dir}")
        print(f"🎮 查看器脚本: {self.viewer_script}")
        print("\n📋 使用方法:")
        print(f"  cd {self.mujoco_dir}")
        print("  python3 viewer.py")
        print("\n⚠️  注意事项:")
        print("  - 需要将STEP文件转换为STL格式")
        print("  - 可以使用FreeCAD、Blender等工具进行批量转换")
        print("  - 转换后的STL文件应放在assets目录中")
        print("  - 确保STL文件名与XML中的mesh名称一致")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Fusion 360 STEP导出数据转换为MuJoCo XML (简化版)')
    parser.add_argument('export_dir', help='STEP导出目录路径')
    parser.add_argument('--stl-tolerance', type=float, default=0.1, 
                       help='STL导出容差(mm)，默认0.1')
    parser.add_argument('--prefer-freecad', action='store_true',
                       help='优先使用FreeCAD而非CadQuery进行转换')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.export_dir):
        print(f"❌ 导出目录不存在: {args.export_dir}")
        return
    
    try:
        generator = SimpleMuJoCoGenerator(
            args.export_dir, 
            stl_tolerance=args.stl_tolerance,
            prefer_freecad=args.prefer_freecad
        )
        generator.run()
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()