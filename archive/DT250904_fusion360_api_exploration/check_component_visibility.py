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
        
        # 收集所有装配实例的可见状态
        visibility_info = []
        visible_count = 0
        invisible_count = 0
        
        # 遍历所有装配实例
        for occurrence in root.allOccurrences:
            component_name = occurrence.component.name
            occurrence_name = occurrence.name
            is_visible = occurrence.isLightBulbOn
            
            status_text = "可见" if is_visible else "不可见"
            visibility_info.append(f"{occurrence_name} ({component_name}): {status_text}")
            
            if is_visible:
                visible_count += 1
            else:
                invisible_count += 1
        
        # 构建结果文本
        result_text = f"=== 零部件可见状态检查 ===\n\n"
        result_text += f"总装配实例数量: {root.allOccurrences.count}\n"
        result_text += f"可见零部件数量: {visible_count}\n"
        result_text += f"不可见零部件数量: {invisible_count}\n\n"
        
        result_text += f"--- 详细状态 ---\n"
        for info in visibility_info:
            result_text += f"{info}\n"
        
        # 添加一些统计信息
        if root.allOccurrences.count > 0:
            visibility_percentage = (visible_count / root.allOccurrences.count) * 100
            result_text += f"\n--- 统计信息 ---\n"
            result_text += f"可见比例: {visibility_percentage:.1f}%\n"
        
        # 显示结果
        ui.messageBox(result_text, "零部件可见状态")
        
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