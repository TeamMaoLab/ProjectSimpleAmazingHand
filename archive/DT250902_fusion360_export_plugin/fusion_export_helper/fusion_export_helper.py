# Author-Justin Nesselrotte
# Description-A convenient way to export all of your designs and projects in the event you suddenly find yourself in need of something like that.
from __future__ import with_statement

import adsk.core, adsk.fusion, adsk.cam, traceback

import logging
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
        
        # 修复：正确配置日志系统
        self.log = Logger("Fusion 360 Total Export")
        self.log.setLevel(10)  # 设置为DEBUG级别，确保所有日志都能输出
        
        self.num_issues = 0
        self.was_cancelled = False
        self.json_data = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def run(self, context):
        self.ui.messageBox(
            "Searching for and exporting files will take a while, depending on how many files you have.\n\n" \
            "You won't be able to do anything else. It has to do everything in the main thread and open and close every file.\n\n" \
            "Take an early lunch."
        )

        output_path = self._ask_for_output_path()

        if output_path is None:
            return

        # 修复：增强日志配置，确保所有级别日志都能输出
        log_file_path = os.path.join(output_path, 'output.log')
        file_handler = FileHandler(log_file_path, mode='w', encoding='utf-8')
        file_handler.setLevel(10)  # DEBUG级别
        
        # 创建更详细的格式化器
        formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
        file_handler.setFormatter(formatter)
        
        # 添加控制台处理器，便于实时查看
        console_handler = logging.StreamHandler()
        console_handler.setLevel(10)  # DEBUG级别
        console_handler.setFormatter(formatter)
        
        # 清除已有的处理器（避免重复）
        self.log.handlers.clear()
        
        # 添加处理器
        self.log.addHandler(file_handler)
        self.log.addHandler(console_handler)
        
        # 确保日志级别设置正确
        self.log.setLevel(10)
        
        # 测试日志输出
        self.log.info("日志系统初始化完成")
        self.log.debug("DEBUG级别日志已启用")
        self.log.info(f"日志文件路径: {log_file_path}")

        self.log.info("=== 开始导出流程 ===")
        self.log.info(f"Fusion 360版本: {self.app.version}")
        self.log.info(f"活跃文档: {self.app.activeDocument.name if self.app.activeDocument else 'None'}")

        try:
            self._export_data(output_path)
            self.log.info("=== 导出流程完成 ===")
        except Exception as ex:
            self.log.error(f"导出流程发生异常: {str(ex)}", exc_info=True)
            self.num_issues += 1

        self.log.info(f"导出统计: 问题数={self.num_issues}, 取消={self.was_cancelled}")
        self.log.info(f"JSON数据条目: {len(self.json_data)}")

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
            
        # 确保所有日志都被刷新到文件
        file_handler.flush()
        console_handler.flush()

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

        # -------------------------- 修复：基于示例代码的正确API访问方式 --------------------------
        try:
            self.log.debug("开始获取活跃产品...")
            # 基于示例代码：使用app.activeProduct而不是app.activeDocument
            product = self.app.activeProduct
            if product is None:
                raise Exception("No active product found")
            
            self.log.debug(f"成功获取产品: {product.name}")
            
            # 基于示例代码：正确的类型转换方式
            design: adsk.fusion.Design = adsk.fusion.Design.cast(product)
            if design is None:
                raise Exception("无法转换为Design对象")
            
            self.log.debug(f"成功获取Design对象，根组件: {design.rootComponent.name}")
            
            # 强制更新设计（关键：确保所有装配约束、拖拽位置都已计算生效）
            self.log.debug("开始重新计算设计...")
            recompute_success = False
            try:
                # 尝试多种方法来重新计算设计
                if hasattr(design, 'recompute'):
                    design.recompute()
                    self.log.debug("使用 design.recompute() 重新计算完成")
                    recompute_success = True
                elif hasattr(design, 'recalculate'):
                    design.recalculate()
                    self.log.debug("使用 design.recalculate() 重新计算完成")
                    recompute_success = True
                else:
                    # 使用其他方法强制更新
                    if hasattr(design.rootComponent, 'recompute'):
                        design.rootComponent.recompute()
                        self.log.debug("使用 rootComponent.recompute() 重新计算完成")
                        recompute_success = True
                    else:
                        self.log.debug("跳过重新计算步骤")
            except Exception as recompute_ex:
                self.log.warning(f"重新计算设计失败: {str(recompute_ex)}")
                # 继续执行，但记录警告
                self.log.debug("跳过重新计算步骤，继续捕获位置")
            
            if not recompute_success:
                self.log.info("设计重新计算未执行，继续导出流程")
            
            # 捕获当前位置（处理未保存的装配变化）
            try:
                if hasattr(design, 'snapshots') and design.snapshots is not None:
                    self.log.debug(f"检查待处理快照: {design.snapshots.hasPendingSnapshot}")
                    if design.snapshots.hasPendingSnapshot:
                        design.snapshots.add()
                        self.log.info("已捕获当前装配位置和约束状态")
                    else:
                        design.snapshots.add()
                        self.log.info("强制捕获当前装配位置（确保无遗漏）")
                else:
                    self.log.warning("Design对象没有snapshots属性，跳过位置捕获")
                    # 尝试其他方法捕获位置
                    if hasattr(design, 'capturePosition'):
                        design.capturePosition()
                        self.log.info("使用 capturePosition() 捕获位置")
                    else:
                        self.log.info("无法捕获位置，继续导出")
            except Exception as snapshot_ex:
                self.log.warning(f"捕获位置失败: {str(snapshot_ex)}")
                self.log.debug("跳过位置捕获，继续导出")
                
            # 基于示例代码，我们也需要document用于导出
            document = self.app.activeDocument
            if document is None:
                raise Exception("No active document found")
                
        except Exception as ex:
            self.num_issues += 1
            self.log.error(f"初始化设计对象失败: {str(ex)}", exc_info=True)
            self.log.error(f"异常类型: {type(ex).__name__}")
            return
        # -------------------------------------------------------------------------------------

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

            # 导出到total_stl文件夹（关键：将实体与其实例绑定）
            if hasattr(self, 'total_stl_path'):
                design = body.parentComponent.parentDesign
                root_comp = design.rootComponent
                
                # 找到当前实体所属组件的所有实例
                found_occs = []
                self._find_component_occurrences(root_comp, body.parentComponent, found_occs)

                # 为每个实例导出STL并记录位置
                for occ_idx, occ in enumerate(found_occs):
                    # 验证实例有效性
                    if not occ.isValid:
                        self.log.warning(f"实例 {occ.fullPathName} 已失效，跳过STL导出")
                        continue
                    
                    # 计算该实例的世界坐标系位置
                    world_matrix = self._world_transform(occ)
                    translation = world_matrix.translation

                    # 生成唯一的STL文件名（包含实例路径，避免重复）
                    occ_path_safe = occ.fullPathName.replace(":", "_").replace("+", "_") if hasattr(occ, 'fullPathName') else f"instance_{occ_idx}"
                    component_name = self._name(body.parentComponent.name)
                    body_name = self._name(body.name)
                    total_stl_file_path = os.path.join(
                        self.total_stl_path,
                        f"{component_name}_{body_name}_实例{occ_idx+1}_{occ_path_safe}.stl"
                    )

                    # 如果文件已存在，添加序号
                    counter = 1
                    base_path = total_stl_file_path
                    while os.path.exists(total_stl_file_path):
                        total_stl_file_path = base_path.replace(".stl", f"_{counter}.stl")
                        counter += 1

                    self.log.info("Also writing stl body file to total_stl: \"{}\"".format(total_stl_file_path))
                    
                    # -------------------------- 修复：启用世界坐标系 --------------------------
                    options_total = export_manager.createSTLExportOptions(body, total_stl_file_path)
                    options_total.exportAsWorldCoordinates = True  # 关键：强制使用世界坐标系
                    options_total.transform = world_matrix  # 此时矩阵才会生效
                    export_manager.execute(options_total)
                    # -------------------------------------------------------------------------

                    # 记录位置到JSON（关联实例路径和世界坐标）
                    body_json = {
                        "name": body.name,
                        "parent_component": body.parentComponent.name,
                        "occurrence_full_path": occ.fullPathName if hasattr(occ, 'fullPathName') else occ_path_safe,
                        "world_position": {
                            "x": translation.x,
                            "y": translation.y,
                            "z": translation.z
                        },
                        "world_transform_matrix": [world_matrix.asArray()[i:i+4] for i in range(0, 16, 4)],
                        "is_valid": occ.isValid,
                        "instance_index": occ_idx + 1
                    }
                    
                    # 添加配置信息（如果有）
                    if hasattr(occ, 'isConfiguration') and occ.isConfiguration:
                        body_json["is_configuration"] = True
                        if hasattr(occ, 'configurationRow'):
                            body_json["configuration_row"] = occ.configurationRow
                    
                    # 使用组件名_实体名_实例索引作为JSON键
                    json_key = f"{body.parentComponent.name}_{body.name}_实例{occ_idx+1}"
                    self.json_data[json_key] = body_json
                    
        except BaseException as ex:
            self.log.exception(f"导出实体 {body.name} 的STL失败: {str(ex)}")
            # 不再忽略所有异常，只处理空模型情况
            if "empty" not in str(ex).lower():
                self.num_issues += 1

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

    def _world_transform(self, occ):
        """基于官方API示例的正确方式计算Occurrence在世界坐标系中的变换"""
        try:
            # 安全地获取实例名称
            try:
                occ_name = occ.fullPathName if hasattr(occ, 'fullPathName') else occ.name
            except:
                occ_name = "未知实例"
                
            self.log.debug(f"开始计算实例 {occ_name} 的世界变换")
            
            # 基于官方API模式：使用正确的装配链遍历
            # 创建单位矩阵作为起始
            world_matrix = adsk.core.Matrix3D.create()
            
            # 从当前实例开始，向上遍历装配链
            current_occ = occ
            transform_chain = []
            
            # 收集从当前实例到根实例的所有变换
            while current_occ is not None:
                # 记录当前实例的变换
                try:
                    # 优先使用transform2，如果没有则使用transform
                    if hasattr(current_occ, 'transform2'):
                        transform = current_occ.transform2
                        transform_type = "transform2"
                    elif hasattr(current_occ, 'transform'):
                        transform = current_occ.transform
                        transform_type = "transform"
                    else:
                        self.log.warning(f"实例 {current_occ.name} 没有可用的变换属性")
                        break
                    
                    # 将变换添加到链的头部（因为我们是从下往上遍历）
                    transform_chain.insert(0, transform)
                    self.log.debug(f"  收集变换: {current_occ.name} (使用{transform_type})")
                    
                except Exception as transform_ex:
                    self.log.warning(f"获取实例 {current_occ.name} 的变换失败: {str(transform_ex)}")
                    break
                
                # 移动到父级实例
                try:
                    if hasattr(current_occ, 'assemblyContext') and current_occ.assemblyContext:
                        current_occ = current_occ.assemblyContext
                    else:
                        # 没有父级，到达根实例
                        current_occ = None
                except Exception as parent_ex:
                    self.log.warning(f"获取父级实例失败: {str(parent_ex)}")
                    current_occ = None
            
            # 应用变换链（从根到当前实例的顺序）
            self.log.debug(f"应用变换链，长度: {len(transform_chain)}")
            for i, transform in enumerate(transform_chain):
                try:
                    world_matrix.transformBy(transform)
                    self.log.debug(f"  应用第 {i+1}/{len(transform_chain)} 个变换")
                except Exception as apply_ex:
                    self.log.error(f"应用变换矩阵失败: {str(apply_ex)}")
                    continue
            
            # 记录最终结果
            try:
                translation = world_matrix.translation
                self.log.debug(f"世界变换计算完成: 位置=({translation.x:.6f}, {translation.y:.6f}, {translation.z:.6f})")
            except:
                self.log.debug("世界变换计算完成，但无法获取位置信息")
            
            return world_matrix

        except Exception as ex:
            self.log.error(f"计算世界变换失败: {str(ex)}", exc_info=True)
            self.log.error(f"异常类型: {type(ex).__name__}")
            # 返回单位矩阵作为降级处理
            return adsk.core.Matrix3D.create()

    def _get_component_json_data(self, component):
        """获取组件的JSON格式位置数据（使用正确的世界坐标系计算）"""
        try:
            design = component.parentDesign
            root = design.rootComponent

            # 如果是根组件，位置为原点
            if component == root:
                return {
                    "name": component.name,
                    "type": "root_component",
                    "instances": [{
                        "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                        "transform": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
                        "occurrence_path": component.name,
                        "full_path_name": component.name,
                        "is_valid": True
                    }]
                }

            # 查找所有引用该组件的occurrences
            found_occurrences = []
            self._find_component_occurrences(root, component, found_occurrences)

            instances = []
            for occ in found_occurrences:
                # 验证实例有效性
                if not occ.isValid:
                    self.log.warning(f"实例 {occ.fullPathName} 已失效，跳过")
                    continue
                
                # 使用修复后的世界变换计算
                world_transform = self._world_transform(occ)
                translation = world_transform.translation
                matrix_data = world_transform.asArray()  # 列优先数组：[m00, m10, m20, m30, m01, m11, ..., m33]

                # -------------------------- 修复：按列优先格式拆分矩阵 --------------------------
                # 正确的4x4矩阵格式（列优先）：
                # [m00, m01, m02, m03]  （第0列：m00,m10,m20,m30 → 转置后为第0行）
                # [m10, m11, m12, m13]
                # [m20, m21, m22, m23]
                # [m30, m31, m32, m33]
                transform_matrix = [
                    [matrix_data[0], matrix_data[4], matrix_data[8],  matrix_data[12]],  # 第0行（原第0列）
                    [matrix_data[1], matrix_data[5], matrix_data[9],  matrix_data[13]],  # 第1行（原第1列）
                    [matrix_data[2], matrix_data[6], matrix_data[10], matrix_data[14]],  # 第2行（原第2列）
                    [matrix_data[3], matrix_data[7], matrix_data[11], matrix_data[15]]   # 第3行（原第3列）
                ]
                # -------------------------------------------------------------------------

                # 获取完整的装配路径信息
                full_path_name = occ.fullPathName if hasattr(occ, 'fullPathName') else self._get_occurrence_path(occ)
                
                instance_data = {
                    "position": {
                        "x": translation.x,
                        "y": translation.y,
                        "z": translation.z
                    },
                    "transform": transform_matrix,
                    "occurrence_path": self._get_occurrence_path(occ),
                    "full_path_name": full_path_name,
                    "is_valid": occ.isValid,
                    "component_name": component.name
                }
                
                # 添加配置信息（如果有）
                if hasattr(occ, 'isConfiguration') and occ.isConfiguration:
                    instance_data["is_configuration"] = True
                    if hasattr(occ, 'configurationRow'):
                        instance_data["configuration_row"] = occ.configurationRow
                
                instances.append(instance_data)

            return {
                "name": component.name,
                "type": "component",
                "instances": instances
            }
        except Exception as ex:
            self.log.exception(f"获取组件 {component.name} 的JSON数据失败: {str(ex)}")
            return {
                "name": component.name,
                "type": "component",
                "error": str(ex),
                "instances": []
            }

    def _get_occurrence_path(self, occurrence):
        """获取occurrence的完整路径，用于调试"""
        try:
            path_parts = [occurrence.component.name]
            parent = occurrence.assemblyContext
            while parent:
                path_parts.insert(0, parent.component.name)
                parent = parent.assemblyContext
            return " > ".join(path_parts)
        except:
            return occurrence.component.name

    def _get_body_json_data(self, body):
        """获取实体的JSON格式位置数据（使用世界坐标系）"""
        try:
            # 实体使用其父组件的位置信息
            component = body.parentComponent
            component_json = self._get_component_json_data(component)

            return {
                "name": body.name,
                "type": "body",
                "parent_component": component.name,
                "instances": component_json.get("instances", []),
                "world_coordinates": True
            }
        except Exception as ex:
            return {
                "name": body.name,
                "type": "body",
                "error": str(ex),
                "world_coordinates": False
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
        """获取组件的位置信息（世界坐标系）- 基于官方API修复版本"""
        try:
            design = component.parentDesign
            root_comp = design.rootComponent

            position_info = "组件名称: {}\n".format(component.name)

            # 如果是根组件，位置为原点
            if component == root_comp:
                position_info += "位置 (世界坐标系): X=0.000000, Y=0.000000, Z=0.000000\n"
                position_info += "说明: 根组件，世界坐标系基准\n"
                return position_info

            # 查找所有引用该组件的occurrences
            found_occurrences = []
            self._find_component_occurrences(root_comp, component, found_occurrences)

            if not found_occurrences:
                position_info += "说明: 未在装配体中找到该组件的实例\n"
                return position_info

            # 为每个实例提取世界坐标系位置
            for idx, occ in enumerate(found_occurrences, 1):
                # 验证实例有效性
                if not occ.isValid:
                    position_info += "\n--- 实例 {} ---\n".format(idx)
                    position_info += "状态: 实例已失效，跳过\n"
                    continue
                
                # 关键：通过Occurrence的fullPathName获取实例在装配体中的完整路径
                occ_full_path = occ.fullPathName if hasattr(occ, 'fullPathName') else self._get_occurrence_path(occ)
                
                # 计算该实例的世界坐标系变换矩阵
                world_matrix = self._world_transform(occ)
                local_matrix = occ.transform2  # 实例在父组件中的局部变换（用于对比）
                
                # 记录局部坐标（便于对比世界坐标是否正确）
                local_trans = local_matrix.translation
                world_trans = world_matrix.translation

                position_info += f"\n--- 实例 {idx}（{occ_full_path}） ---\n"
                position_info += f"局部坐标（父组件内）: X={local_trans.x:.6f}, Y={local_trans.y:.6f}, Z={local_trans.z:.6f}\n"
                position_info += f"世界坐标（装配体中）: X={world_trans.x:.6f}, Y={world_trans.y:.6f}, Z={world_trans.z:.6f}\n"
                
                # 添加坐标差异分析（便于调试）
                coord_diff = abs(world_trans.x - local_trans.x) + abs(world_trans.y - local_trans.y) + abs(world_trans.z - local_trans.z)
                if coord_diff > 0.001:  # 如果差异大于1mm，记录警告
                    position_info += f"⚠️ 坐标差异较大: {coord_diff:.6f}mm（可能存在多层装配变换）\n"
                
                # 添加旋转信息（四元数）
                rotation = world_matrix.rotation
                position_info += "旋转信息（四元数）: X={:.6f}, Y={:.6f}, Z={:.6f}, W={:.6f}\n".format(
                    rotation.x, rotation.y, rotation.z, rotation.w
                )
                
                # 添加变换矩阵详细信息（用于调试）
                position_info += "世界变换矩阵:\n"
                matrix_data = world_matrix.asArray()
                for row in range(4):
                    row_start = row * 4
                    position_info += "  [{:.6f}, {:.6f}, {:.6f}, {:.6f}]\n".format(
                        matrix_data[row_start], matrix_data[row_start + 1],
                        matrix_data[row_start + 2], matrix_data[row_start + 3]
                    )
                
                # 添加配置信息（如果有）
                if hasattr(occ, 'isConfiguration') and occ.isConfiguration:
                    position_info += "配置实例: 是\n"
                    if hasattr(occ, 'configurationRow'):
                        position_info += "配置行: {}\n".format(occ.configurationRow)

            return position_info
        except Exception as ex:
            self.log.exception(f"获取组件 {component.name} 位置信息失败: {str(ex)}")
            return "组件名称: {}\n获取位置失败: {}".format(component.name, str(ex))

    def _find_component_occurrences(self, parent_component, target_component, found_occurrences, depth=0, max_depth=20):
        """
        递归查找所有引用目标组件的occurrences（修复死循环/重复问题）
        depth: 当前递归深度，max_depth: 最大深度（避免无限递归）
        """
        self.log.debug(f"在组件 {parent_component.name} 中查找目标组件 {target_component.name}，深度={depth}")
        
        # 1. 限制递归深度（Fusion装配体层级一般不超过20层，足够覆盖所有场景）
        if depth > max_depth:
            self.log.warning(f"递归深度超过{max_depth}层，跳过子装配体: {parent_component.name}")
            return
        
        # 2. 遍历当前组件的实例，去重后添加
        occ_count = parent_component.occurrences.count
        self.log.debug(f"组件 {parent_component.name} 有 {occ_count} 个实例")
        
        for i in range(occ_count):
            try:
                occ = parent_component.occurrences.item(i)
                
                # 安全地获取实例名称
                try:
                    occ_name = occ.fullPathName if hasattr(occ, 'fullPathName') else f"实例_{i}"
                except:
                    occ_name = f"实例_{i}"
                    
                self.log.debug(f"  检查实例 {i+1}/{occ_count}: {occ_name}")
                
                # 安全地比较组件
                try:
                    if occ.component == target_component:
                        # 安全地检查是否已存在
                        try:
                            existing = False
                            for existing_occ in found_occurrences:
                                try:
                                    existing_name = existing_occ.fullPathName if hasattr(existing_occ, 'fullPathName') else "unknown"
                                    if existing_name == occ_name:
                                        existing = True
                                        break
                                except:
                                    pass
                                    
                            if not existing:
                                found_occurrences.append(occ)
                                self.log.debug(f"  ✅ 找到目标实例: {occ_name}（深度：{depth}）")
                            else:
                                self.log.debug(f"  ⚠️ 实例已存在，跳过: {occ_name}")
                        except Exception as check_ex:
                            self.log.warning(f"检查实例存在性失败: {str(check_ex)}")
                            found_occurrences.append(occ)
                    else:
                        # 安全地获取组件名称
                        try:
                            actual_comp_name = occ.component.name if hasattr(occ.component, 'name') else "unknown"
                            self.log.debug(f"  ❌ 不是目标组件（期望: {target_component.name}, 实际: {actual_comp_name}）")
                        except:
                            self.log.debug(f"  ❌ 无法获取组件名称进行比较")
                except Exception as comp_ex:
                    self.log.warning(f"比较组件失败: {str(comp_ex)}")
                
                # 3. 递归遍历子组件（深度+1）
                try:
                    comp_name = occ.component.name if hasattr(occ.component, 'name') else "unknown"
                    self.log.debug(f"  递归检查子组件: {comp_name}")
                    self._find_component_occurrences(occ.component, target_component, found_occurrences, depth + 1, max_depth)
                except Exception as recur_ex:
                    self.log.warning(f"递归检查子组件失败: {str(recur_ex)}")
                    
            except Exception as occ_ex:
                self.log.warning(f"处理实例 {i+1} 失败: {str(occ_ex)}")
                continue
        
        self.log.debug(f"组件 {parent_component.name} 查找完成，当前找到 {len(found_occurrences)} 个实例")

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
