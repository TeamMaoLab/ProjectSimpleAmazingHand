# Author-Justin Nesselrotte
# Description-A convenient way to export all of your designs and projects in the event you suddenly find yourself in need of something like that.
from __future__ import with_statement

import adsk.core, adsk.fusion, adsk.cam, traceback

from logging import Logger, FileHandler, Formatter
from threading import Thread

import time
import os
import re


class TotalExport(object):

    def __init__(self, app):
        self.app = app
        self.ui = self.app.userInterface
        self.data = self.app.data
        self.documents = self.app.documents
        self.log = Logger("Fusion 360 Total Export")
        self.num_issues = 0
        self.was_cancelled = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def run(self, context):
        self.ui.messageBox(
            "Searching for and exporting files will take a while, depending on how many files you have.\n\n" \
            "You won't be able to do anything else. It has to do everything in the main thread and open and close every file.\n\n" \
            "Take an early lunch." \
            "参数流水优化--装配版"
        )

        output_path = self._ask_for_output_path()

        if output_path is None:
            return

        file_handler = FileHandler(os.path.join(output_path, 'output.log'))
        file_handler.setFormatter(Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.log.addHandler(file_handler)

        self.log.info("Starting export!")

        self._export_data(output_path)

        self.log.info("Done exporting!")

        if self.was_cancelled:
            self.ui.messageBox("Cancelled!")
        elif self.num_issues > 0:
            self.ui.messageBox(
                "The exporting process ran into {num_issues} issue{english_plurals}. Please check the log for more information".format(
                    num_issues=self.num_issues,
                    english_plurals="s" if self.num_issues > 1 else ""
                ))
        else:
            self.ui.messageBox("Export finished completely successfully!")

    def _export_data(self, output_path):
        progress_dialog = self.ui.createProgressDialog()
        progress_dialog.show("Exporting data!", "", 0, 1, 1)

        # 获取当前活跃文档
        active_document = self.app.activeDocument
        if not active_document:
            self.log.warning("没有打开的活跃文档")
            self.ui.messageBox("请先打开一个项目")
            return

        # 获取当前文档对应的数据文件
        data_file = active_document.dataFile
        if not data_file:
            self.log.warning("当前文档没有关联的数据文件")
            self.ui.messageBox("当前文档没有关联的项目数据")
            return

        self.log.info("导出当前文档: \"{}\"".format(data_file.name))

        # 只导出当前打开的文档
        files = [data_file]

        progress_dialog.message = "导出文档: {}\n导出进度 %v of %m".format(data_file.name)
        progress_dialog.maximumValue = len(files)
        progress_dialog.reset()

        for file_index in range(len(files)):
            if progress_dialog.wasCancelled:
                self.log.info("导出过程被取消!")
                self.was_cancelled = True
                return

            file: adsk.core.DataFile = files[file_index]
            progress_dialog.progressValue = file_index + 1
            self._write_data_file(output_path, file)

        # 保存JSON数据
        self._save_json_data(output_path)

        self.log.info("当前文档导出完成")

    def _ask_for_output_path(self):
        folder_dialog = self.ui.createFolderDialog()
        folder_dialog.title = "Where should we store this export?"
        dialog_result = folder_dialog.showDialog()
        if dialog_result != adsk.core.DialogResults.DialogOK:
            return None

        output_path = folder_dialog.folder

        return output_path

    def _get_files_for(self, folder):
        files = []
        for file in folder.dataFiles:
            files.append(file)

        for sub_folder in folder.dataFolders:
            files.extend(self._get_files_for(sub_folder))

        return files

    def _write_data_file(self, root_folder, file: adsk.core.DataFile):
        if file.fileExtension != "f3d" and file.fileExtension != "f3z":
            self.log.info("Not exporting file \"{}\"".format(file.name))
            return

        self.log.info("Exporting file \"{}\"".format(file.name))

        # 创建total_stl文件夹
        self.total_stl_path = os.path.join(root_folder, "total_stl")
        os.makedirs(self.total_stl_path, exist_ok=True)

        # 创建JSON数据存储
        self.json_data = {}

        try:
            # 直接使用当前活跃文档，不需要重新打开
            document = self.app.activeDocument
            if document is None:
                raise Exception("No active document found")
        except BaseException as ex:
            self.num_issues += 1
            self.log.exception("Getting active document failed!".format(file.name), exc_info=ex)
            return

        try:
            file_folder = file.parentFolder
            file_folder_path = self._name(file_folder.name)

            while file_folder.parentFolder is not None:
                file_folder = file_folder.parentFolder
                file_folder_path = os.path.join(self._name(file_folder.name), file_folder_path)

            parent_project = file_folder.parentProject
            parent_hub = parent_project.parentHub

            file_folder_path = self._take(
                root_folder,
                "Hub {}".format(self._name(parent_hub.name)),
                "Project {}".format(self._name(parent_project.name)),
                file_folder_path,
                self._name(file.name) + "." + file.fileExtension
            )

            if not os.path.exists(file_folder_path):
                self.num_issues += 1
                self.log.exception("Couldn't make root folder\"{}\"".format(file_folder_path))
                return

            self.log.info("Writing to \"{}\"".format(file_folder_path))

            fusion_document: adsk.fusion.FusionDocument = adsk.fusion.FusionDocument.cast(document)
            design: adsk.fusion.Design = fusion_document.design
            export_manager: adsk.fusion.ExportManager = design.exportManager

            file_export_path = os.path.join(file_folder_path, self._name(file.name))
            # Write f3d/f3z file
            options = export_manager.createFusionArchiveExportOptions(file_export_path)
            export_manager.execute(options)

            self._write_component(file_folder_path, design.rootComponent)

            self.log.info("Finished exporting file \"{}\"".format(file.name))
        except BaseException as ex:
            self.num_issues += 1
            self.log.exception("Failed while working on \"{}\"".format(file.name), exc_info=ex)
            raise
        finally:
            # 不再关闭文档，保持文档打开状态
            pass

    def _write_component(self, component_base_path, component: adsk.fusion.Component):
        self.log.info("Writing component \"{}\" to \"{}\"".format(component.name, component_base_path))
        design = component.parentDesign

        output_path = os.path.join(component_base_path, self._name(component.name))

        self._write_step(output_path, component)
        self._write_stl(output_path, component)
        self._write_iges(output_path, component)

        sketches = component.sketches
        for sketch_index in range(sketches.count):
            sketch = sketches.item(sketch_index)
            self._write_dxf(os.path.join(output_path, sketch.name), sketch)

        occurrences = component.occurrences
        for occurrence_index in range(occurrences.count):
            occurrence = occurrences.item(occurrence_index)
            sub_component = occurrence.component
            sub_path = self._take(component_base_path, self._name(component.name))
            self._write_component(sub_path, sub_component)

    def _write_step(self, output_path, component: adsk.fusion.Component):
        file_path = output_path + ".stp"
        if os.path.exists(file_path):
            self.log.info("Step file \"{}\" already exists".format(file_path))
            return

        self.log.info("Writing step file \"{}\"".format(file_path))
        export_manager = component.parentDesign.exportManager

        options = export_manager.createSTEPExportOptions(output_path, component)
        export_manager.execute(options)

    def _write_stl(self, output_path, component: adsk.fusion.Component):
        file_path = output_path + ".stl"
        if os.path.exists(file_path):
            self.log.info("Stl file \"{}\" already exists".format(file_path))
            return

        # 记录组件位置信息
        position_info = self._get_component_position_info(component)
        self.log.info("Component position info: {}".format(position_info))

        self.log.info("Writing stl file \"{}\"".format(file_path))
        export_manager = component.parentDesign.exportManager

        try:
            options = export_manager.createSTLExportOptions(component, output_path)
            export_manager.execute(options)

            # 不再导出总体STL对象到total_stl文件夹，只导出子组件和实体
            # 获取组件的JSON数据
            component_json = self._get_component_json_data(component)
            if component_json:
                self.json_data[component.name] = component_json
        except BaseException as ex:
            self.log.exception("Failed writing stl file \"{}\"".format(file_path), exc_info=ex)

            if component.occurrences.count + component.bRepBodies.count + component.meshBodies.count > 0:
                self.num_issues += 1

        bRepBodies = component.bRepBodies
        meshBodies = component.meshBodies

        if (bRepBodies.count + meshBodies.count) > 0:
            self._take(output_path)
            for index in range(bRepBodies.count):
                body = bRepBodies.item(index)
                self._write_stl_body(os.path.join(output_path, body.name), body)

            for index in range(meshBodies.count):
                body = meshBodies.item(index)
                self._write_stl_body(os.path.join(output_path, body.name), body)

    def _write_stl_body(self, output_path, body):
        file_path = output_path + ".stl"
        if os.path.exists(file_path):
            self.log.info("Stl body file \"{}\" already exists".format(file_path))
            return

        # 记录实体位置信息（继承自组件）
        position_info = self._get_component_position_info(body.parentComponent)
        position_info = position_info.replace("组件名称:", "实体名称: {} (父组件:".format(body.name)) + ")"
        self.log.info("Body position info: {}".format(position_info))

        self.log.info("Writing stl body file \"{}\"".format(file_path))
        export_manager = body.parentComponent.parentDesign.exportManager

        try:
            options = export_manager.createSTLExportOptions(body, file_path)
            export_manager.execute(options)

            # 导出到total_stl文件夹
            if hasattr(self, 'total_stl_path'):
                # 使用组件名称和实体名称作为文件名，避免路径冲突
                component_name = self._name(body.parentComponent.name)
                body_name = self._name(body.name)
                total_stl_file_path = os.path.join(self.total_stl_path, component_name + "_" + body_name + ".stl")

                # 如果文件已存在，添加序号
                counter = 1
                while os.path.exists(total_stl_file_path):
                    total_stl_file_path = os.path.join(self.total_stl_path,
                                                       component_name + "_" + body_name + "_" + str(counter) + ".stl")
                    counter += 1

                self.log.info("Also writing stl body file to total_stl: \"{}\"".format(total_stl_file_path))
                options_total = export_manager.createSTLExportOptions(body, total_stl_file_path)
                export_manager.execute(options_total)

                # 获取实体的JSON数据
                body_json = self._get_body_json_data(body)
                if body_json:
                    # 使用组件名_实体名作为JSON键
                    json_key = "{}_{}".format(body.parentComponent.name, body.name)
                    self.json_data[json_key] = body_json
        except BaseException:
            # Probably an empty model, ignore it
            pass

    def _write_iges(self, output_path, component: adsk.fusion.Component):
        file_path = output_path + ".igs"
        if os.path.exists(file_path):
            self.log.info("Iges file \"{}\" already exists".format(file_path))
            return

        self.log.info("Writing iges file \"{}\"".format(file_path))

        export_manager = component.parentDesign.exportManager

        options = export_manager.createIGESExportOptions(file_path, component)
        export_manager.execute(options)

    def _write_dxf(self, output_path, sketch: adsk.fusion.Sketch):
        file_path = output_path + ".dxf"
        if os.path.exists(file_path):
            self.log.info("DXF sketch file \"{}\" already exists".format(file_path))
            return

        self.log.info("Writing dxf sketch file \"{}\"".format(file_path))

        sketch.saveAsDXF(file_path)

    def _take(self, *path):
        out_path = os.path.join(*path)
        os.makedirs(out_path, exist_ok=True)
        return out_path

    def _get_component_json_data(self, component):
        """获取组件的JSON格式位置数据"""
        try:
            # 获取所有引用该组件的occurrences
            design = component.parentDesign
            root_comp = design.rootComponent

            # 如果是根组件，位置为原点
            if component == root_comp:
                return {
                    "name": component.name,
                    "type": "root_component",
                    "position": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "transform": [
                        [1.0, 0.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0],
                        [0.0, 0.0, 0.0, 1.0]
                    ],
                    "instances": []
                }

            # 查找所有引用该组件的occurrences
            found_occurrences = []
            self._find_component_occurrences(root_comp, component, found_occurrences)

            instances = []
            for occ in found_occurrences:
                transform = occ.transform
                translation = transform.translation
                matrix_data = transform.asArray()

                # 将4x4矩阵转换为4x4数组
                transform_matrix = []
                for row in range(4):
                    matrix_row = []
                    row_start = row * 4
                    for col in range(4):
                        matrix_row.append(matrix_data[row_start + col])
                    transform_matrix.append(matrix_row)

                instance_data = {
                    "position": {
                        "x": translation.x,
                        "y": translation.y,
                        "z": translation.z
                    },
                    "transform": transform_matrix
                }
                instances.append(instance_data)

            return {
                "name": component.name,
                "type": "component",
                "instances": instances
            }
        except Exception as ex:
            return {
                "name": component.name,
                "type": "component",
                "error": str(ex)
            }

    def _get_body_json_data(self, body):
        """获取实体的JSON格式位置数据"""
        try:
            # 实体使用其父组件的位置信息
            component = body.parentComponent
            component_json = self._get_component_json_data(component)

            return {
                "name": body.name,
                "type": "body",
                "parent_component": component.name,
                "instances": component_json.get("instances", [])
            }
        except Exception as ex:
            return {
                "name": body.name,
                "type": "body",
                "error": str(ex)
            }

    def _save_json_data(self, root_folder):
        """保存JSON数据到文件"""
        try:
            json_file_path = os.path.join(root_folder, "model_positions.json")
            import json
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.json_data, f, ensure_ascii=False, indent=2)
            self.log.info("JSON数据已保存到: {}".format(json_file_path))
        except Exception as ex:
            self.log.exception("保存JSON数据失败: {}".format(str(ex)))

    def _get_component_position_info(self, component):
        """获取组件的位置信息"""
        try:
            # 获取所有引用该组件的occurrences
            design = component.parentDesign
            root_comp = design.rootComponent

            position_info = "组件名称: {}\n".format(component.name)

            # 如果是根组件，位置为原点
            if component == root_comp:
                position_info += "位置 (X, Y, Z): 0.000000, 0.000000, 0.000000\n"
                position_info += "说明: 根组件，无位置变换\n"
                return position_info

            # 查找所有引用该组件的occurrences
            found_occurrences = []
            self._find_component_occurrences(root_comp, component, found_occurrences)

            if not found_occurrences:
                position_info += "未找到该组件的occurrence\n"
                return position_info

            # 为每个occurrence记录位置信息
            for i, occ in enumerate(found_occurrences):
                position_info += "--- 实例 {} ---\n".format(i + 1)

                # 获取occurrence的变换矩阵
                transform = occ.transform

                # 获取位置信息（平移部分）
                translation = transform.translation
                x = translation.x
                y = translation.y
                z = translation.z

                position_info += "位置 (X, Y, Z): {:.6f}, {:.6f}, {:.6f}\n".format(x, y, z)
                position_info += "变换矩阵:\n"

                # 获取变换矩阵的所有元素 - 使用正确的asArray()方法
                matrix_data = transform.asArray()
                for row in range(4):
                    row_start = row * 4
                    position_info += "  [{:.6f}, {:.6f}, {:.6f}, {:.6f}]\n".format(
                        matrix_data[row_start], matrix_data[row_start + 1],
                        matrix_data[row_start + 2], matrix_data[row_start + 3]
                    )

            return position_info
        except Exception as ex:
            return "组件名称: {}\n获取位置信息失败: {}".format(component.name, str(ex))

    def _find_component_occurrences(self, parent_component, target_component, found_occurrences):
        """递归查找所有引用目标组件的occurrences"""
        for occ in parent_component.occurrences:
            if occ.component == target_component:
                found_occurrences.append(occ)

            # 递归检查子组件中的occurrences
            self._find_component_occurrences(occ.component, target_component, found_occurrences)

    def _name(self, name):
        # 保留中文字符、英文字母、数字和常见符号
        name = re.sub('[^\u4e00-\u9fa5a-zA-Z0-9 \n\._-]', '', name).strip()

        if name.endswith('.stp') or name.endswith('.stl') or name.endswith('.igs'):
            name = name[0: -4] + "_" + name[-3:]

        return name


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()

        with TotalExport(app) as total_export:
            total_export.run(context)

    except:
        ui = app.userInterface
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
