# Fusion360 API 深度探索计划 - 完成版

```markdown
/directory add /Users/maoge/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/Python/defs/adsk
```

## 📚 完整API文档集

### 核心API参考文档
- [**LOCAL_API_REFERENCE.md**](../../archive/DT250904_fusion360_api_exploration/LOCAL_API_REFERENCE.md) - 核心API类层次结构与基础使用方法
- [**PHYSICAL_GEOMETRY_API.md**](../../archive/DT250904_fusion360_api_exploration/PHYSICAL_GEOMETRY_API.md) - 物理属性与几何数据提取详解
- [**JOINT_CONSTRAINTS_API.md**](../../archive/DT250904_fusion360_api_exploration/JOINT_CONSTRAINTS_API.md) - 关节约束与运动限制API详解
- [**COMPLETE_API_SUMMARY.md**](../../archive/DT250904_fusion360_api_exploration/COMPLETE_API_SUMMARY.md) - 完整API总结与MuJoCo集成指南

---

## 📅 更新记录
- **2025-09-04**：完成API深度探索，建立完整技术栈，创建详细文档集
- **2025-09-04**：重大突破 - 解决质心坐标提取关键问题
  - 发现Fusion 360在装配层面计算质心的正确方法
  - 对于BComp组件，使用根组件物理属性可获得与Fusion分析完全一致的结果
  - 建立了正确的4x4矩阵变换方法，用于将局部坐标转换为全局装配坐标
  - 创建了可用的质心提取脚本并归档到`archive/DT250904_fusion360_api_exploration/`
- **状态**：质心提取问题已解决，完整解决方案已验证可用
- **下一步**：将质心提取方法集成到完整的MuJoCo参数提取工作流中

### 🎯 质心提取解决方案

#### 关键发现
1. **根组件物理属性方法**：对于简单装配，使用`root.physicalProperties.centerOfMass`可直接获得Fusion显示的准确质心坐标
2. **矩阵变换方法**：对于单个组件，使用4x4变换矩阵正确转换局部质心坐标到全局装配坐标
3. **Fusion计算机制**：Fusion 360在装配层面计算质心，已考虑所有子组件的变换关系和装配约束

#### 实现脚本
- **`final_center_of_mass_extractor.py`**：完整的质心提取脚本，支持多种方法对比
- **`check_component_visibility.py`**：零部件可见状态检查工具，统计和显示所有装配实例的可见状态
- **脚本位置**：已归档至`archive/DT250904_fusion360_api_exploration/`目录

#### 验证结果
- BComp组件质心：脚本结果与Fusion分析完全一致 (2.302, 4.609, 0.201) mm
- 差距：X=0.000, Y=0.000, Z=0.000 mm
- 方法：使用根组件物理属性 (`root.physicalProperties.centerOfMass`)

### 🔍 零部件可见状态检查工具

#### 功能特点
- **全面检查**：遍历所有装配实例，检查每个零部件的可见状态
- **统计信息**：提供可见/不可见零部件数量统计和比例分析
- **详细报告**：显示每个装配实例的名称、组件名称和可见状态
- **用户友好**：结果以清晰的格式在消息框中展示

#### 技术实现
- 使用 `occurrence.isLightBulbOn` 属性判断零部件可见状态
- 遍历 `root.allOccurrences` 获取所有装配实例
- 自动计算统计数据和可见比例
- 支持文本窗口输出，便于复制和记录

#### 应用场景
- 装配文档状态检查
- 复杂装配的可视化管理
- 设计评审前的状态确认
- 批量处理前的状态检查