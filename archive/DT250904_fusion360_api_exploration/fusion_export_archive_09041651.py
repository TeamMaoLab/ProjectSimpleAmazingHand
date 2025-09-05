"""
Fusion 360 可见零部件STL导出工具
整合质心提取、可见性检查和STL导出功能
导出当前活跃项目中处于可视状态的零部件的STL文件及其坐标+变换矩阵
"""

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import os
import json
import re
import time
from datetime import datetime


class VisibleComponentSTLExporter:
    def __init__(self):
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface
        self.export_data = {}
        self.exported_files = []
        self.unit_conversion_factor = 0.001  # Fusion 360默认使用毫米，转换为米的系数

    def run(self):
        """主运行函数"""
        try:
            # 检查是否有活跃文档
            if not self.app.activeDocument:
                self.ui.messageBox("请先打开一个Fusion 360文档")
                return

            # 获取输出目录
            output_dir = self._get_output_directory()
            if not output_dir:
                return

            # 创建导出子目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.stl_export_dir = os.path.join(output_dir, f"visible_components_stl_{timestamp}")
            os.makedirs(self.stl_export_dir, exist_ok=True)

            # 显示进度对话框
            progress_dialog = self.ui.createProgressDialog()
            progress_dialog.isCancelButtonShown = True
            progress_dialog.show("导出可见零部件STL", "正在分析装配结构...", 0, 100)

            # 执行导出
            self._export_visible_components(progress_dialog)

            # 保存JSON数据
            self._save_export_data()

            # 显示完成消息
            self._show_completion_message()

        except Exception as e:
            self.ui.messageBox(f"导出失败: {str(e)}\n\n{traceback.format_exc()}")

    def _get_output_directory(self):
        """获取输出目录"""
        folder_dialog = self.ui.createFolderDialog()
        folder_dialog.title = "选择STL导出目录"
        result = folder_dialog.showDialog()

        if result == adsk.core.DialogResults.DialogOK:
            return folder_dialog.folder
        return None

    def _export_visible_components(self, progress_dialog):
        """导出可见零部件"""
        # 获取设计对象
        design = adsk.fusion.Design.cast(self.app.activeProduct)
        if not design:
            raise Exception("当前文档不是Fusion 360设计")

        root = design.rootComponent

        # 重新计算设计（确保所有约束和位置都已更新）
        self._recompute_design(design)

        # 获取所有可见的装配实例
        visible_occurrences = self._get_visible_occurrences(root)

        if not visible_occurrences:
            self.ui.messageBox("没有找到可见的零部件")
            return

        progress_dialog.maximumValue = len(visible_occurrences)
        progress_dialog.progressValue = 0

        # 导出每个可见实例
        for idx, occurrence in enumerate(visible_occurrences):
            if progress_dialog.wasCancelled:
                break

            progress_dialog.message = f"导出 {idx + 1}/{len(visible_occurrences)}: {occurrence.name}"
            progress_dialog.progressValue = idx + 1

            # 获取世界坐标变换矩阵
            world_transform = self._get_world_transform(occurrence)

            # 创建单位转换矩阵（毫米转米）
            unit_scale_matrix = adsk.core.Matrix3D.create()
            scale_factor = self.unit_conversion_factor
            unit_scale_matrix.setWithArray([
                scale_factor, 0, 0, 0,
                0, scale_factor, 0, 0,
                0, 0, scale_factor, 0,
                0, 0, 0, 1
            ])

            # 组合变换：先应用世界变换，再应用单位缩放
            final_world_transform = world_transform.copy()
            final_world_transform.transformBy(unit_scale_matrix)

            # 导出该实例的STL文件
            self._export_occurrence_stl(occurrence, idx + 1, final_world_transform)

    def _recompute_design(self, design):
        """重新计算设计，确保所有约束和位置都已更新"""
        try:
            # 尝试多种方法重新计算设计
            if hasattr(design, 'recompute'):
                design.recompute()
            elif hasattr(design, 'recalculate'):
                design.recalculate()
            elif hasattr(design.rootComponent, 'recompute'):
                design.rootComponent.recompute()

            # 捕获当前位置
            if hasattr(design, 'snapshots') and design.snapshots:
                if design.snapshots.hasPendingSnapshot:
                    design.snapshots.add()

        except Exception as e:
            print(f"重新计算设计失败: {str(e)}")

    def _get_visible_occurrences(self, root):
        """获取所有可见的装配实例"""
        visible_occurrences = []

        # 遍历所有装配实例
        for occurrence in root.allOccurrences:
            try:
                # 检查是否可见
                if occurrence.isLightBulbOn and occurrence.isValid:
                    visible_occurrences.append(occurrence)
            except Exception as e:
                print(f"检查实例 {occurrence.name} 可见性失败: {str(e)}")
                continue

        return visible_occurrences

    def _export_occurrence_stl(self, occurrence, index, world_transform):
        """导出单个装配实例的STL文件"""
        try:
            component = occurrence.component

            # 生成安全的文件名
            safe_name = self._get_safe_filename(occurrence.name)
            component_safe_name = self._get_safe_filename(component.name)

            # 为每个实例创建唯一文件名
            stl_filename = f"{component_safe_name}_{safe_name}_{index:03d}.stl"
            stl_filepath = os.path.join(self.stl_export_dir, stl_filename)

            # 导出STL文件
            self._export_component_stl(component, stl_filepath, world_transform)

            # 获取组件的质心（已转换为米）
            physical = component.physicalProperties
            local_com = physical.centerOfMass

            # 将质心坐标转换为米
            local_com_meters = {
                "x": local_com.x * self.unit_conversion_factor,
                "y": local_com.y * self.unit_conversion_factor,
                "z": local_com.z * self.unit_conversion_factor
            }

            # 将局部质心转换为世界坐标（米）
            world_com = self._transform_point_to_world(local_com, world_transform)
            world_com_meters = {
                "x": world_com.x,
                "y": world_com.y,
                "z": world_com.z
            }

            # 获取世界位置（米）
            world_position = {
                "x": world_transform.translation.x,
                "y": world_transform.translation.y,
                "z": world_transform.translation.z
            }

            # 记录导出数据
            export_info = {
                "stl_file": stl_filename,
                "stl_path": stl_filepath,
                "component_name": component.name,
                "occurrence_name": occurrence.name,
                "occurrence_full_path": occurrence.fullPathName if hasattr(occurrence,
                                                                           'fullPathName') else occurrence.name,
                "is_visible": occurrence.isLightBulbOn,
                "is_valid": occurrence.isValid,
                "world_position": world_position,
                "world_transform_matrix": self._matrix_to_2d_array(world_transform),
                "center_of_mass": {
                    "local": local_com_meters,
                    "world": world_com_meters
                },
                "export_time": datetime.now().isoformat(),
                "units": "meters"
            }

            # 添加到导出数据
            if component.name not in self.export_data:
                self.export_data[component.name] = []
            self.export_data[component.name].append(export_info)

            # 记录导出的文件
            self.exported_files.append(stl_filepath)

        except Exception as e:
            print(f"导出实例 {occurrence.name} 失败: {str(e)}")

    def _get_world_transform(self, occurrence):
        """计算装配实例的世界坐标变换矩阵"""
        try:
            # 创建单位矩阵
            world_matrix = adsk.core.Matrix3D.create()

            # 从当前实例开始，向上遍历装配链
            current_occ = occurrence
            transform_chain = []

            # 收集变换链
            while current_occ is not None:
                try:
                    # 优先使用transform2
                    if hasattr(current_occ, 'transform2'):
                        transform = current_occ.transform2
                    else:
                        transform = current_occ.transform

                    transform_chain.insert(0, transform)

                    # 移动到父级实例
                    if hasattr(current_occ, 'assemblyContext') and current_occ.assemblyContext:
                        current_occ = current_occ.assemblyContext
                    else:
                        current_occ = None

                except Exception as e:
                    print(f"获取实例 {current_occ.name} 变换失败: {str(e)}")
                    break

            # 应用变换链
            for transform in transform_chain:
                world_matrix.transformBy(transform)

            return world_matrix

        except Exception as e:
            print(f"计算世界变换失败: {str(e)}")
            return adsk.core.Matrix3D.create()

    def _export_component_stl(self, component, filepath, world_transform):
        """导出组件的STL文件"""
        try:
            design = component.parentDesign
            export_manager = design.exportManager

            # 创建STL导出选项
            stl_options = export_manager.createSTLExportOptions(component, filepath)

            # 获取组件的质心
            physical = component.physicalProperties
            local_com = physical.centerOfMass

            # 创建平移矩阵，将质心移动到原点（毫米单位）
            com_translation_matrix = adsk.core.Matrix3D.create()
            com_translation_matrix.translation = adsk.core.Vector3D.create(-local_com.x, -local_com.y, -local_com.z)

            # 创建单位转换矩阵（毫米转米）
            unit_scale_matrix = adsk.core.Matrix3D.create()
            scale_factor = self.unit_conversion_factor
            unit_scale_matrix.setWithArray([
                scale_factor, 0, 0, 0,
                0, scale_factor, 0, 0,
                0, 0, scale_factor, 0,
                0, 0, 0, 1
            ])

            # 组合变换：
            # 1. 先应用质心平移（将质心移到原点）
            # 2. 再应用世界变换（保持组件在装配中的位置和姿态）
            # 3. 最后应用单位缩放（毫米转米）
            final_transform = com_translation_matrix.copy()
            final_transform.transformBy(world_transform)
            final_transform.transformBy(unit_scale_matrix)

            # 设置世界坐标系导出
            stl_options.exportAsWorldCoordinates = True
            stl_options.transform = final_transform

            # 执行导出
            export_manager.execute(stl_options)

        except Exception as e:
            print(f"导出STL文件 {filepath} 失败: {str(e)}")
            raise

    def _get_component_center_of_mass(self, component, world_transform):
        """获取组件在世界坐标系中的质心"""
        try:
            # 获取组件的局部质心
            physical = component.physicalProperties
            local_com = physical.centerOfMass

            # 将局部质心转换为世界坐标
            world_com = self._transform_point_to_world(local_com, world_transform)

            return {
                "local": {
                    "x": local_com.x,
                    "y": local_com.y,
                    "z": local_com.z
                },
                "world": {
                    "x": world_com.x,
                    "y": world_com.y,
                    "z": world_com.z
                }
            }

        except Exception as e:
            print(f"获取质心失败: {str(e)}")
            return {
                "local": {"x": 0, "y": 0, "z": 0},
                "world": {"x": 0, "y": 0, "z": 0},
                "error": str(e)
            }

    def _transform_point_to_world(self, point, world_transform):
        """将点从局部坐标转换到世界坐标"""
        try:
            # 获取变换矩阵数组
            matrix_array = world_transform.asArray()

            # 手动计算点变换
            transformed_x = (matrix_array[0] * point.x +
                             matrix_array[1] * point.y +
                             matrix_array[2] * point.z +
                             matrix_array[3])
            transformed_y = (matrix_array[4] * point.x +
                             matrix_array[5] * point.y +
                             matrix_array[6] * point.z +
                             matrix_array[7])
            transformed_z = (matrix_array[8] * point.x +
                             matrix_array[9] * point.y +
                             matrix_array[10] * point.z +
                             matrix_array[11])

            return adsk.core.Point3D.create(transformed_x, transformed_y, transformed_z)

        except Exception as e:
            print(f"坐标变换失败: {str(e)}")
            return adsk.core.Point3D.create(0, 0, 0)

    def _matrix_to_2d_array(self, matrix):
        """将4x4矩阵转换为2D数组格式"""
        try:
            matrix_array = matrix.asArray()
            return [
                [matrix_array[0], matrix_array[4], matrix_array[8], matrix_array[12]],
                [matrix_array[1], matrix_array[5], matrix_array[9], matrix_array[13]],
                [matrix_array[2], matrix_array[6], matrix_array[10], matrix_array[14]],
                [matrix_array[3], matrix_array[7], matrix_array[11], matrix_array[15]]
            ]
        except Exception as e:
            print(f"矩阵转换失败: {str(e)}")
            return [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]

    def _extract_component_transform(self, world_transform):
        """从世界变换中提取组件自身的变换（去除装配层级变换）"""
        try:
            # 创建一个新的变换矩阵，只保留旋转和缩放部分，去除平移部分
            component_transform = adsk.core.Matrix3D.create()

            # 获取世界变换的数组
            matrix_array = world_transform.asArray()

            # 创建只包含旋转和缩放的矩阵（去除平移）
            rotation_scale_matrix = adsk.core.Matrix3D.create()
            rotation_scale_matrix.setWithArray([
                matrix_array[0], matrix_array[1], matrix_array[2], 0,
                matrix_array[4], matrix_array[5], matrix_array[6], 0,
                matrix_array[8], matrix_array[9], matrix_array[10], 0,
                0, 0, 0, 1
            ])

            return rotation_scale_matrix

        except Exception as e:
            print(f"提取组件变换失败: {str(e)}")
            return adsk.core.Matrix3D.create()

    def _get_safe_filename(self, name):
        """生成安全的文件名"""
        # 保留中文字符、英文字母、数字和常见符号
        safe_name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9 \._-]', '_', name).strip()
        return safe_name

    def _save_export_data(self):
        """保存导出数据到JSON文件"""
        try:
            json_filepath = os.path.join(self.stl_export_dir, "export_data.json")
            readme_filepath = os.path.join(self.stl_export_dir, "README.md")

            export_summary = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "total_files": len(self.exported_files),
                    "total_components": len(self.export_data),
                    "export_directory": self.stl_export_dir
                },
                "components": self.export_data,
                "files": self.exported_files
            }

            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(export_summary, f, ensure_ascii=False, indent=2)

            print(f"导出数据已保存到: {json_filepath}")

            # 创建说明文档
            readme_content = """# Fusion 360 STL导出数据说明

## 文件说明

### export_data.json
包含所有导出的STL文件的详细信息和变换数据。

### JSON数据结构

```json
{
  "export_info": {
    "timestamp": "导出时间戳",
    "total_files": "导出的STL文件总数",
    "total_components": "导出的组件总数",
    "export_directory": "导出目录路径"
  },
  "components": {
    "组件名称": [
      {
        "stl_file": "STL文件名",
        "stl_path": "STL文件完整路径",
        "component_name": "组件名称",
        "occurrence_name": "装配实例名称",
        "occurrence_full_path": "装配实例完整路径",
        "is_visible": "是否可见",
        "is_valid": "是否有效",
        "world_position": {
          "x": "世界坐标X位置",
          "y": "世界坐标Y位置",
          "z": "世界坐标Z位置"
        },
        "world_transform_matrix": [
          [1, 0, 0, 0],
          [0, 1, 0, 0],
          [0, 0, 1, 0],
          [0, 0, 0, 1]
        ],
        "center_of_mass": {
          "local": {
            "x": "局部质心X坐标",
            "y": "局部质心Y坐标",
            "z": "局部质心Z坐标"
          },
          "world": {
            "x": "世界质心X坐标",
            "y": "世界质心Y坐标",
            "z": "世界质心Z坐标"
          }
        },
        "export_time": "导出时间"
      }
    ]
  },
  "files": [
    "所有导出的STL文件路径列表"
  ]
}
```

## 字段说明

### 基本信息字段
- `stl_file`: STL文件名
- `stl_path`: STL文件的完整路径
- `component_name`: 组件的名称
- `occurrence_name`: 装配实例的名称
- `occurrence_full_path`: 装配实例的完整路径
- `is_visible`: 布尔值，表示该实例在导出时是否可见
- `is_valid`: 布尔值，表示该实例是否有效
- `export_time`: 导出时间（ISO格式）
- `units`: 单位标识（固定为"meters"）

### 位置和变换字段
- `world_position`: 组件在世界坐标系中的位置（单位：米）
- `world_transform_matrix`: 4x4变换矩阵，用于将组件从局部坐标系转换到世界坐标系（已包含毫米到米的转换）
  - 矩阵格式：[ [m00, m01, m02, m03], [m10, m11, m12, m13], [m20, m21, m22, m23], [m30, m31, m32, m33] ]
  - 其中m00-m22是旋转缩放部分，m03/m13/m23是平移部分

### 质心字段
- `center_of_mass`: 组件的质心信息
  - `local`: 在组件局部坐标系中的质心坐标（单位：米）
  - `world`: 在世界坐标系中的质心坐标（单位：米）

## 使用说明

### 在MuJoCo中使用
1. 将STL文件导入MuJoCo
2. 使用`world_position`字段设置物体的位置
3. 使用`world_transform_matrix`设置物体的姿态（如果需要）
4. 质心信息可用于设置物体的质量分布

### 变换矩阵使用
变换矩阵可以用于将STL模型从局部坐标系转换到世界坐标系：
- 前3列：旋转和缩放
- 第4列：平移
- 最后一行：[0, 0, 0, 1]（齐次坐标）

### 注意事项
- 导出的STL文件已经将质心平移到原点(0,0,0)
- 所有坐标和尺寸数据已统一转换为米（meters）单位
- 如果需要恢复原始位置，请使用`world_position`和`world_transform_matrix`
- 质心信息可用于物理仿真中的质量分布设置
- STL文件本身已经过单位转换，无需额外缩放
"""

            with open(readme_filepath, 'w', encoding='utf-8') as f:
                f.write(readme_content)

            print(f"说明文档已保存到: {readme_filepath}")

        except Exception as e:
            print(f"保存JSON数据失败: {str(e)}")

    def _show_completion_message(self):
        """显示完成消息"""
        message = f"STL导出完成！\n\n"
        message += f"导出目录: {self.stl_export_dir}\n"
        message += f"导出文件数: {len(self.exported_files)}\n"
        message += f"组件数: {len(self.export_data)}\n\n"
        message += f"每个STL文件对应的坐标和变换矩阵信息已保存到 export_data.json"

        self.ui.messageBox(message)


def run(context):
    """脚本入口函数"""
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        exporter = VisibleComponentSTLExporter()
        exporter.run()

    except Exception as e:
        if ui:
            ui.messageBox(f"脚本执行失败: {str(e)}\n\n{traceback.format_exc()}")
        else:
            print(f"脚本执行失败: {str(e)}\n\n{traceback.format_exc()}")


if __name__ == "__main__":
    run(None)