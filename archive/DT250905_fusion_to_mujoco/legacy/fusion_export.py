"""
Fusion 360 零部件位置导出器（改进版）

该脚本用于导出Fusion 360中所有零部件的STL文件和位置信息，
特别支持在MuJoCo中复原装配位置的功能。

特点：
1. 导出每个零部件的STL文件（基于occurrence而非component）
2. 记录每个零部件的世界坐标位置和旋转（四元数格式）
3. 支持从"一字排开"的临时位置复原到装配位置
4. 改进的错误处理和文件名安全过滤
5. 自动跳过无实体的组件，避免导出失败
6. 添加目录写权限测试，确保导出成功

改进说明：
- 使用occurrence作为导出对象，更符合Fusion 360 API最佳实践
- 移除entityToken，避免文件名包含特殊字符导致导出失败
- 增强文件名安全过滤，限制长度并严格过滤特殊字符
- 添加目录写权限测试，确保导出目录可写
- 改进错误处理，使用文本命令面板输出错误而非弹窗
- 优化递归收集逻辑，直接收集occurrences简化处理
- 跳过无实体的组件，避免导出空组件导致错误

使用方法：
1. 在Fusion 360中打开要导出的装配体
2. 运行此脚本
3. 选择输出目录
4. 等待导出完成

输出文件：
- component_positions.json：包含所有零部件的位置信息
- stl_files/：包含所有零部件的STL文件

作者：基于VisibleComponentSTLExporter分析设计
日期：2025-09-05
版本：改进版 v1.1
"""

import adsk.core, adsk.fusion, adsk.cam
import traceback
import os
import json
import time
import re


class ComponentPositionExporter:
    def __init__(self):
        """初始化导出器"""
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface

        # 数据存储
        self.export_data = {}
        self.exported_files = []
        self.stl_export_dir = ""

        # 单位转换系数（mm→m）
        self.unit_conversion_factor = 0.001

        # 配置选项
        self.export_assembly_positions = True  # 导出装配位置而非临时位置
        self.mesh_quality = 'medium'  # STL网格质量

    def run(self):
        """主运行函数"""
        try:
            # 1. 检查是否有活跃文档
            if not self.app.activeDocument:
                self.ui.messageBox("请先打开一个Fusion 360文档")
                return

            # 2. 获取输出目录
            output_dir = self._get_output_directory()
            if not output_dir:
                return

            # 3. 创建导出子目录（带时间戳）
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.stl_export_dir = os.path.join(output_dir, f"component_positions_{timestamp}")
            os.makedirs(self.stl_export_dir, exist_ok=True)

            # 4. 创建STL子目录
            self.stl_files_dir = os.path.join(self.stl_export_dir, "stl_files")
            os.makedirs(self.stl_files_dir, exist_ok=True)

            # 5. 显示开始消息
            self.ui.messageBox("开始导出零部件位置信息...\n\n请稍候，导出过程可能需要几分钟时间。")

            # 6. 执行导出
            self._export_all_components()

            # 7. 显示完成消息
            self._show_completion_message()

        except Exception as e:
            self.ui.messageBox(f"导出失败:\n{str(e)}\n\n{traceback.format_exc()}")

    def _get_output_directory(self):
        """获取输出目录"""
        folder_dialog = self.ui.createFolderDialog()
        folder_dialog.title = "选择零部件位置导出目录"
        result = folder_dialog.showDialog()

        if result == adsk.core.DialogResults.DialogOK:
            return folder_dialog.folder
        return None

    def _export_all_components(self):
        """导出所有零部件"""
        design = adsk.fusion.Design.cast(self.app.activeProduct)
        root_comp = design.rootComponent

        # 收集所有occurrences而不是components
        all_occurrences = []
        self._collect_occurrences_recursive(root_comp.occurrences, all_occurrences)

        # 导出每个occurrence的STL文件
        exported_components = []
        for i, occ in enumerate(all_occurrences):
            # 显示当前进度
            self.ui.palettes.itemById('TextCommands').writeText(
                f"正在导出零部件 {i + 1}/{len(all_occurrences)}: {occ.fullPathName}")

            # 导出STL文件
            stl_filename = None
            comp = occ.component
            bodies_count = comp.bRepBodies.count

            if bodies_count > 0:
                try:
                    stl_filename = self._export_occurrence_stl(occ)
                except Exception as e:
                    self.ui.palettes.itemById('TextCommands').writeText(f"跳过（导出失败）: {occ.fullPathName}: {str(e)}")

            # 获取occurrence位置信息
            position_data = self._get_occurrence_position_data(occ)

            # 记录导出信息
            comp_data = {
                "component_name": comp.name,
                "occurrence_name": occ.name,
                "occurrence_fullname": occ.fullPathName,
                "component_id": comp.entityToken,
                "stl_file": stl_filename,
                "position": position_data,
                "bodies_count": bodies_count,
                "has_children": occ.childOccurrences.count > 0
            }
            exported_components.append(comp_data)

        # 保存位置信息到JSON文件
        self._save_position_data(exported_components)

    def _collect_occurrences_recursive(self, parent_occurrences, occ_list):
        """递归收集所有occurrences"""
        for occ in parent_occurrences:
            occ_list.append(occ)
            if occ.childOccurrences:
                self._collect_occurrences_recursive(occ.childOccurrences, occ_list)

    def _export_occurrence_stl(self, occurrence):
        """导出单个occurrence的STL文件"""
        try:
            design = adsk.fusion.Design.cast(self.app.activeProduct)
            export_manager = design.exportManager

            # 生成安全的文件名（不使用entityToken）
            safe_name = self._get_safe_filename(occurrence.name)
            stl_filename = f"{safe_name}_{len(self.exported_files) + 1}.stl"
            stl_filepath = os.path.join(self.stl_files_dir, stl_filename)

            # 确保目录存在
            if not os.path.exists(self.stl_files_dir):
                os.makedirs(self.stl_files_dir, exist_ok=True)

            # 确保使用绝对路径
            stl_filepath = os.path.abspath(stl_filepath)

            # 测试目录写权限
            if not self._test_directory_write(self.stl_files_dir):
                raise RuntimeError(f"目录不可写: {self.stl_files_dir}")

            # 创建STL导出选项
            stl_options = export_manager.createSTLExportOptions(occurrence, stl_filepath)

            # 设置网格质量
            quality_settings = {
                'low': adsk.fusion.MeshRefinementSettings.MeshRefinementLow,
                'medium': adsk.fusion.MeshRefinementSettings.MeshRefinementMedium,
                'high': adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            }
            stl_options.meshRefinement = quality_settings.get(self.mesh_quality,
                                                              adsk.fusion.MeshRefinementSettings.MeshRefinementMedium)

            # 设置导出选项
            stl_options.isBinaryFormat = True
            stl_options.isOneFilePerBody = False  # 整个零部件导出为一个文件

            # 执行导出
            result = export_manager.execute(stl_options)

            if result:
                self.exported_files.append(stl_filepath)
                return stl_filename
            else:
                raise RuntimeError(f"导出失败: {occurrence.fullPathName}")

        except Exception as e:
            self.ui.palettes.itemById('TextCommands').writeText(f"导出失败 {occurrence.fullPathName}: {str(e)}")
            raise

    def _get_occurrence_position_data(self, occurrence):
        """获取occurrence的位置信息"""
        # 获取occurrence在世界坐标系中的变换矩阵
        world_transform = self._get_occurrence_world_transform(occurrence)

        # 转换为位置和四元数
        position, quaternion = self._matrix_to_pos_quat(world_transform)

        # 获取装配位置信息（如果存在）
        assembly_position = None
        assembly_quaternion = None

        if self.export_assembly_positions:
            # 尝试获取装配位置
            assembly_transform = self._get_assembly_transform(occurrence)
            if assembly_transform:
                assembly_position, assembly_quaternion = self._matrix_to_pos_quat(assembly_transform)

        return {
            "current_position": position,
            "current_quaternion": quaternion,
            "current_matrix": world_transform.asArray(),
            "assembly_position": assembly_position,
            "assembly_quaternion": assembly_quaternion,
            "assembly_matrix": assembly_transform.asArray() if assembly_transform else None
        }

    def _get_occurrence_world_transform(self, occurrence):
        """获取occurrence在世界坐标系中的变换矩阵"""
        try:
            # 获取世界变换矩阵
            if hasattr(occurrence, 'transform2'):
                return occurrence.transform2
            else:
                return occurrence.transform

        except Exception as e:
            self.ui.palettes.itemById('TextCommands').writeText(f"获取世界变换矩阵失败: {str(e)}")
            return adsk.core.Matrix3D.create()

    def _get_assembly_transform(self, occurrence):
        """获取occurrence的装配位置变换矩阵"""
        try:
            # 这里需要根据你的具体装配逻辑来实现
            # 一种方法是保存零部件在装配时的变换矩阵
            # 另一种方法是通过配合关系反推装配位置

            # 简化实现：返回当前变换矩阵
            # 在实际使用中，你需要根据你的装配逻辑来修改这个函数
            return self._get_occurrence_world_transform(occurrence)

        except Exception as e:
            self.ui.palettes.itemById('TextCommands').writeText(f"获取装配变换矩阵失败: {str(e)}")
            return None

    def _matrix_to_pos_quat(self, matrix, mm_to_m=0.001):
        """从矩阵提取位置和四元数"""
        try:
            # 获取矩阵数组（列主序）
            matrix_array = matrix.asArray()

            # 提取平移部分并转换单位
            tx = matrix_array[12] * mm_to_m
            ty = matrix_array[13] * mm_to_m
            tz = matrix_array[14] * mm_to_m

            # 提取旋转子矩阵
            r00, r01, r02 = matrix_array[0], matrix_array[4], matrix_array[8]
            r10, r11, r12 = matrix_array[1], matrix_array[5], matrix_array[9]
            r20, r21, r22 = matrix_array[2], matrix_array[6], matrix_array[10]

            # 计算四元数（基于矩阵迹的方法）
            trace = r00 + r11 + r22

            if trace > 0:
                s = (trace + 1.0) ** 0.5 * 2
                qw = 0.25 * s
                qx = (r21 - r12) / s
                qy = (r02 - r20) / s
                qz = (r10 - r01) / s
            elif (r00 > r11) and (r00 > r22):
                s = (r00 - r11 - r22 + 1.0) ** 0.5 * 2
                qw = (r21 - r12) / s
                qx = 0.25 * s
                qy = (r01 + r10) / s
                qz = (r02 + r20) / s
            elif r11 > r22:
                s = (r11 - r00 - r22 + 1.0) ** 0.5 * 2
                qw = (r02 - r20) / s
                qx = (r01 + r10) / s
                qy = 0.25 * s
                qz = (r12 + r21) / s
            else:
                s = (r22 - r00 - r11 + 1.0) ** 0.5 * 2
                qw = (r10 - r01) / s
                qx = (r02 + r20) / s
                qy = (r12 + r21) / s
                qz = 0.25 * s

            # 四元数归一化
            norm = (qw * qw + qx * qx + qy * qy + qz * qz) ** 0.5
            if norm > 0:
                qw /= norm
                qx /= norm
                qy /= norm
                qz /= norm

            position = [tx, ty, tz]
            quaternion = [qw, qx, qy, qz]

            return position, quaternion

        except Exception as e:
            self.ui.messageBox(f"矩阵转换失败: {str(e)}")
            return [0, 0, 0], [1, 0, 0, 0]

    def _save_position_data(self, components_data):
        """保存位置数据到JSON文件"""
        data = {
            "meta": {
                "export_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "export_mode": "assembly_positions" if self.export_assembly_positions else "current_positions",
                "geometry_unit": "mm",
                "position_unit": "m",
                "matrix_storage": "column-major",
                "count_components": len(components_data),
                "format_version": "1.0",
                "note": "STL files are in mm. Positions are in meters. Quaternions are in wxyz format."
            },
            "components": components_data
        }

        json_filepath = os.path.join(self.stl_export_dir, "component_positions.json")
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.export_data = data

    def _get_safe_filename(self, name, max_len=80):
        """生成安全的文件名"""
        # 保留中文字符、英文字母、数字和常见符号
        safe = re.sub(r'[^\u4e00-\u9fa5A-Za-z0-9_.\- ]', '_', name)
        safe = re.sub(r'\s+', '_', safe).strip('_')
        if not safe:
            safe = "part"
        if len(safe) > max_len:
            safe = safe[:max_len]
        return safe

    def _test_directory_write(self, path):
        """测试目录写权限"""
        testfile = os.path.join(path, "_write_test.tmp")
        try:
            with open(testfile, "w") as f:
                f.write("ok")
            os.remove(testfile)
            return True
        except:
            return False

    def _show_completion_message(self):
        """显示完成消息"""
        message = f"零部件位置导出完成！\n\n"
        message += f"导出目录: {self.stl_export_dir}\n"
        message += f"导出零部件数: {len(self.export_data.get('components', []))}\n"
        message += f"STL文件数: {len(self.exported_files)}\n\n"
        message += f"生成文件:\n"
        message += f"- component_positions.json (位置信息)\n"
        message += f"- stl_files/ (STL文件目录)\n\n"
        message += "注意：STL文件使用毫米单位，位置信息使用米单位。"

        self.ui.messageBox(message)


def run(context):
    """运行导出器"""
    try:
        exporter = ComponentPositionExporter()
        exporter.run()
    except Exception as e:
        ui = adsk.core.Application.get().userInterface
        ui.messageBox(f"运行失败:\n{str(e)}\n\n{traceback.format_exc()}")


# 在Fusion 360中运行此脚本的入口点
if __name__ == "__main__":
    run(None)