#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MuJoCo XML生成脚本
基于Fusion360导出数据，生成MuJoCo+Python项目模板
"""

import json
import os
import shutil
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from pypinyin import lazy_pinyin


class MuJoCoXMLGenerator:
    """MuJoCo XML生成器"""
    
    def __init__(self, source_path: str, target_path: str, exclude_list: List[str] = None):
        self.source_path = Path(source_path)
        self.target_path = Path(target_path)
        self.exclude_list = exclude_list or []
        self.name_mapping = {}
        self.component_data = {}
        
        # 确保目标目录存在
        self.target_path.mkdir(parents=True, exist_ok=True)
        (self.target_path / "assets").mkdir(exist_ok=True)
        
    def load_export_data(self) -> bool:
        """加载导出数据，解析组件和实例信息"""
        stl_dir = self.source_path / "total_stl"
        json_file = self.source_path / "model_positions.json"
        
        if not stl_dir.exists():
            print(f"错误: STL目录不存在: {stl_dir}")
            return False
            
        if not json_file.exists():
            print(f"错误: JSON文件不存在: {json_file}")
            return False
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
                
            # 解析新的JSON数据结构
            self.instances = []
            self.joint_data = []
            self.component_data = all_data
            
            # 遍历所有组件，提取实例信息
            for component_name, component_info in all_data.items():
                if component_info.get('type') == 'component':
                    instances = component_info.get('instances', [])
                    for instance in instances:
                        # 添加组件名称到实例信息中
                        instance['component_name'] = component_name
                        instance['name'] = f"{component_name}_instance"
                        self.instances.append(instance)
                        
            print(f"成功加载 {len(self.instances)} 个实例数据")
            return True
            
        except Exception as e:
            print(f"加载JSON数据失败: {e}")
            return False
    
    def get_stl_files(self) -> List[Path]:
        """获取所有STL文件"""
        stl_dir = self.source_path / "total_stl"
        stl_files = list(stl_dir.glob("*.stl"))
        
        # 应用排除规则
        filtered_files = []
        for stl_file in stl_files:
            should_exclude = False
            for pattern in self.exclude_list:
                if re.search(pattern, stl_file.name, re.IGNORECASE):
                    should_exclude = True
                    break
            
            if not should_exclude:
                filtered_files.append(stl_file)
        
        print(f"找到 {len(stl_files)} 个STL文件，排除后保留 {len(filtered_files)} 个")
        return filtered_files
    
    def convert_to_english_name(self, chinese_name: str, index: int) -> str:
        """将中文文件名转换为英文"""
        if chinese_name in self.name_mapping:
            return self.name_mapping[chinese_name]
        
        # 移除文件扩展名
        base_name = chinese_name.replace('.stl', '')
        
        # 清理特殊字符
        clean_name = re.sub(r'[^\w\s-]', '', base_name)
        clean_name = clean_name.strip()
        
        if not clean_name:
            clean_name = f"component_{index:03d}"
        else:
            # 转换为拼音
            pinyin_parts = lazy_pinyin(clean_name)
            pinyin_name = ''.join(pinyin_parts)
            
            # 确保只包含字母、数字和下划线
            pinyin_name = re.sub(r'[^a-zA-Z0-9_]', '_', pinyin_name)
            
            if not pinyin_name or len(pinyin_name) < 2:
                pinyin_name = f"component_{index:03d}"
            else:
                pinyin_name = f"{pinyin_name}_{index:03d}"
        
        self.name_mapping[chinese_name] = pinyin_name
        return pinyin_name
    
    def copy_stl_files(self, stl_files: List[Path]) -> Dict[str, str]:
        """复制STL文件并返回映射关系"""
        asset_mapping = {}
        
        for i, stl_file in enumerate(stl_files):
            english_name = self.convert_to_english_name(stl_file.stem, i)
            new_filename = f"{english_name}.stl"
            target_file = self.target_path / "assets" / new_filename
            
            try:
                shutil.copy2(stl_file, target_file)
                asset_mapping[stl_file.name] = new_filename
                print(f"复制: {stl_file.name} -> {new_filename}")
            except Exception as e:
                print(f"复制文件失败 {stl_file.name}: {e}")
        
        return asset_mapping
    
    def generate_mujoco_xml(self, asset_mapping: Dict[str, str]) -> str:
        """生成MuJoCo XML，使用实例的全局位置"""
        SCALE_FACTOR = 0.001  # mm到m
        
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<mujoco>',
            '  <compiler coordinate="local" angle="radian"/>',
            '  <option gravity="0 0 -9.81"/>',
            '  <asset>'
        ]
        
        # 添加网格
        for new_name in asset_mapping.values():
            mesh_name = new_name.replace('.stl', '')
            lines.append(f'    <mesh name="{mesh_name}" file="assets/{new_name}" scale="{SCALE_FACTOR} {SCALE_FACTOR} {SCALE_FACTOR}"/>')
        
        lines.extend([
            '  </asset>',
            '  <worldbody>'
        ])
        
        # 使用实例数据
        for instance in self.instances:
            pos = instance.get('position', {})
            
            if pos:
                # 使用全局位置
                x = pos.get('x', 0) * SCALE_FACTOR
                y = pos.get('y', 0) * SCALE_FACTOR
                z = pos.get('z', 0) * SCALE_FACTOR
                
                # 使用实例名称
                safe_name = re.sub(r'[^\w-]', '_', instance.get('name', 'unknown'))
                
                # 查找对应的STL文件
                component_name = instance.get('component_name', '')
                stl_key = None
                
                # 更精确的STL文件匹配
                for orig_name in asset_mapping.keys():
                    # 移除.stl扩展名进行比较
                    orig_name_clean = orig_name.replace('.stl', '')
                    # 检查是否包含组件名称
                    if component_name in orig_name_clean or orig_name_clean in component_name:
                        stl_key = orig_name
                        break
                
                if stl_key and stl_key in asset_mapping:
                    mesh_name = asset_mapping[stl_key].replace('.stl', '')
                    lines.extend([
                        f'    <body name="{safe_name}" pos="{x:.6f} {y:.6f} {z:.6f}">',
                        f'      <geom type="mesh" mesh="{mesh_name}" density="1000"/>',
                        '    </body>'
                    ])
                else:
                    print(f"警告: 未找到组件 {component_name} 对应的STL文件")
        
        lines.extend([
            '  </worldbody>',
            '</mujoco>'
        ])
        
        return '\n'.join(lines)
    
    def generate_simulate_script(self) -> str:
        """生成Python仿真脚本"""
        return """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import mujoco
import mujoco.viewer
import os

def main():
    model_path = os.path.join(os.path.dirname(__file__), 'model.xml')
    model = mujoco.MjModel.from_xml_path(model_path)
    data = mujoco.MjData(model)
    
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            mujoco.mj_step(model, data)
            viewer.sync()

if __name__ == "__main__":
    main()
"""
    
    def generate_config_script(self) -> str:
        """生成配置文件"""
        return """# MuJoCo仿真配置

SIMULATION_CONFIG = {
    'gravity': [0, 0, -9.81],
    'timestep': 0.001,
    'integrator': 'RK4',
}

PHYSICS_CONFIG = {
    'density': 1000.0,
    'friction': [1.0, 0.005, 0.0001],
}
"""
    
    def generate_pyproject_toml(self) -> str:
        """生成UV依赖管理文件"""
        return """[project]
name = "mujoco-simulation"
version = "0.1.0"
description = "MuJoCo仿真项目"
requires-python = ">=3.8"
dependencies = [
    "mujoco>=3.0.0",
    "numpy>=1.20.0",
    "pypinyin>=0.55.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
    
    def generate_project_readme(self) -> str:
        """生成项目README"""
        return """# MuJoCo仿真项目

基于Fusion360导出的3D模型生成的MuJoCo仿真项目。

## 快速开始
```bash
uv sync
uv run python simulate.py
```

## 项目结构
- model.xml: MuJoCo模型文件
- assets/: STL几何文件
- simulate.py: 仿真启动器
- config.py: 配置文件
"""
    
    def save_project_files(self, templates: Dict[str, str]):
        """保存所有项目文件"""
        for filename, content in templates.items():
            file_path = self.target_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            if filename == 'simulate.py':
                os.chmod(file_path, 0o755)
    
    def save_mapping(self):
        """保存文件名映射"""
        mapping_file = self.target_path / "filename_mapping.json"
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(self.name_mapping, f, ensure_ascii=False, indent=2)
    
    def run(self):
        """运行完整的项目模板生成流程"""
        print("=" * 60)
        print("MuJoCo项目模板生成器")
        print("=" * 60)
        
        if not self.load_export_data():
            return False
        
        stl_files = self.get_stl_files()
        if not stl_files:
            print("没有找到需要处理的STL文件")
            return False
        
        asset_mapping = self.copy_stl_files(stl_files)
        
        # 生成所有模板文件
        templates = {
            'model.xml': self.generate_mujoco_xml(asset_mapping),
            'simulate.py': self.generate_simulate_script(),
            'config.py': self.generate_config_script(),
            'pyproject.toml': self.generate_pyproject_toml(),
            'README.md': self.generate_project_readme()
        }
        
        self.save_project_files(templates)
        self.save_mapping()
        
        print(f"项目模板生成完成: {self.target_path}")
        print(f"- 实例数量: {len(self.instances)}")
        print(f"- 组件数量: {len(self.component_data)}")
        print(f"- STL文件: {len(asset_mapping)}")
        print("下一步: cd", self.target_path, "&& uv sync && uv run python simulate.py")
        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='基于Fusion360导出数据生成MuJoCo项目模板')
    parser.add_argument('input_fusion360export_dir', help='Fusion360导出目录路径')
    parser.add_argument('--exclude-components', nargs='*', default=[], 
                       help='要排除的组件名称模式')
    parser.add_argument('--output-mujoco-template', required=True,
                       help='输出的MuJoCo项目模板目录')
    
    args = parser.parse_args()
    
    generator = MuJoCoXMLGenerator(
        args.input_fusion360export_dir,
        args.output_mujoco_template,
        args.exclude_components
    )
    generator.run()


if __name__ == "__main__":
    main()