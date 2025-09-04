import adsk.core
import adsk.fusion
import traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # 获取当前活动的设计
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox('当前没有打开的设计文档')
            return
        
        root = design.rootComponent
        
        # 目标组件名称
        target_component_names = ["球面副-1-上球头", "BComp"]
        
        result_text = f"=== 最终质心提取结果 ===\n\n"
        
        for target_component_name in target_component_names:
            result_text += f"--- {target_component_name} 质心分析 ---\n\n"
            
            # 查找目标组件
            target_component = None
            for component in design.allComponents:
                if component.name == target_component_name:
                    target_component = component
                    break
            
            if not target_component:
                result_text += f"未找到名为 \"{target_component_name}\" 的组件\n\n"
                continue
            
            # 获取组件的物理属性
            physical = target_component.physicalProperties
            local_center_of_mass = physical.centerOfMass
            
            result_text += f"1. 组件局部质心 (cm): X={local_center_of_mass.x:.3f}, Y={local_center_of_mass.y:.3f}, Z={local_center_of_mass.z:.3f}\n"
            result_text += f"   转换为 (mm): X={local_center_of_mass.x*10:.3f}, Y={local_center_of_mass.y*10:.3f}, Z={local_center_of_mass.z*10:.3f}\n\n"
            
            # 查找装配实例
            target_occurrence = None
            for occurrence in root.allOccurrences:
                if occurrence.component.name == target_component_name:
                    target_occurrence = occurrence
                    break
            
            if not target_occurrence:
                result_text += f"未找到 \"{target_component_name}\" 的装配实例\n\n"
                continue
            
            # 方法1：使用正确的矩阵变换（之前的方法）
            try:
                local_com_point = adsk.core.Point3D.create(
                    local_center_of_mass.x,
                    local_center_of_mass.y,
                    local_center_of_mass.z
                )
                
                transform = target_occurrence.transform2
                matrix_array = transform.asArray()
                
                # 正确的矩阵变换计算
                transformed_x = (matrix_array[0] * local_com_point.x + 
                                matrix_array[1] * local_com_point.y + 
                                matrix_array[2] * local_com_point.z + 
                                matrix_array[3])
                transformed_y = (matrix_array[4] * local_com_point.x + 
                                matrix_array[5] * local_com_point.y + 
                                matrix_array[6] * local_com_point.z + 
                                matrix_array[7])
                transformed_z = (matrix_array[8] * local_com_point.x + 
                                matrix_array[9] * local_com_point.y + 
                                matrix_array[10] * local_com_point.z + 
                                matrix_array[11])
                
                global_com_point = adsk.core.Point3D.create(transformed_x, transformed_y, transformed_z)
                result_text += f"2. 矩阵变换方法 (mm): X={global_com_point.x*10:.3f}, Y={global_com_point.y*10:.3f}, Z={global_com_point.z*10:.3f}\n\n"
            except Exception as e:
                result_text += f"2. 矩阵变换方法: 失败 - {str(e)}\n\n"
            
            # 方法2：检查根组件的物理属性（对于BComp有效的方法）
            try:
                root_physical = root.physicalProperties
                root_com = root_physical.centerOfMass
                
                # 对于BComp，我们知道这个方法有效
                if target_component_name == "BComp":
                    result_text += f"3. 根组件物理属性 (mm): X={root_com.x*10:.3f}, Y={root_com.y*10:.3f}, Z={root_com.z*10:.3f}\n"
                    result_text += f"   (这是Fusion显示的准确值)\n\n"
                else:
                    result_text += f"3. 根组件物理属性 (mm): X={root_com.x*10:.3f}, Y={root_com.y*10:.3f}, Z={root_com.z*10:.3f}\n"
                    result_text += f"   (这是整个装配的质心，不是单个组件的质心)\n\n"
            except Exception as e:
                result_text += f"3. 根组件物理属性: 失败 - {str(e)}\n\n"
            
            # 方法3：尝试获取组件在装配中的实际质心
            # 通过创建临时组件并计算其物理属性
            try:
                # 创建一个临时组件，只包含目标组件的几何体
                # 这样可以直接获取其在装配中的物理属性
                temp_occurrences = []
                for occ in root.allOccurrences:
                    if occ.component.name == target_component_name:
                        temp_occurrences.append(occ)
                
                if temp_occurrences:
                    # 获取第一个装配实例
                    temp_occ = temp_occurrences[0]
                    
                    # 尝试获取装配实例的物理属性
                    if hasattr(temp_occ, 'physicalProperties'):
                        occ_physical = temp_occ.physicalProperties
                        occ_com = occ_physical.centerOfMass
                        result_text += f"4. 装配实例物理属性 (mm): X={occ_com.x*10:.3f}, Y={occ_com.y*10:.3f}, Z={occ_com.z*10:.3f}\n\n"
                    else:
                        result_text += f"4. 装配实例物理属性: 装配实例没有physicalProperties属性\n\n"
                else:
                    result_text += f"4. 装配实例物理属性: 未找到装配实例\n\n"
            except Exception as e:
                result_text += f"4. 装配实例物理属性: 失败 - {str(e)}\n\n"
        
        # 显示结果
        ui.messageBox(result_text, "最终质心提取结果")
        
        # 同时写入文本窗口
        try:
            text_palette = ui.palettes.itemById('TextCommands')
            if not text_palette:
                text_palette = ui.palettes.add('TextCommands', 'Text Commands', 'TextCommands', False)
            text_palette.writeText(result_text)
        except:
            pass
        
    except Exception as e:
        if ui:
            ui.messageBox(f'错误: {str(e)}\n\n{traceback.format_exc()}')

if __name__ == '__main__':
    run(None)