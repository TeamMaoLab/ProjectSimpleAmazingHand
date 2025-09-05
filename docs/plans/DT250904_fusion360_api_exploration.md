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
- **`export_visible_components_stl.py`**：可见零部件STL导出工具，整合质心提取、可见性检查和STL导出功能
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

### 🚀 可见零部件STL导出工具

#### 功能特点
- **批量导出**：一键导出所有可见零部件的STL文件
- **精确坐标**：记录每个STL文件的世界坐标位置和变换矩阵
- **质心信息**：提取每个零部件的局部和世界坐标质心
- **JSON映射**：生成详细的映射文件，便于后续处理
- **世界坐标系**：STL文件使用世界坐标系，便于直接导入其他软件

#### 技术实现
- 整合了质心提取、可见性检查和STL导出三大功能
- 使用装配链遍历计算精确的世界坐标变换
- 支持复杂装配结构的多层变换计算
- 自动生成时间戳目录，避免文件覆盖

#### 输出格式
```
visible_components_stl_YYYYMMDD_HHMMSS/
├── Component1_Occurrence1_001.stl
├── Component1_Occurrence2_002.stl
├── Component2_Occurrence1_003.stl
└── export_data.json  # 包含所有坐标和变换矩阵信息
```

#### 应用场景
- MuJoCo仿真准备
- 3D打印批量处理
- 可视化展示
- 跨软件数据交换

### 🔄 MuJoCo XML生成工具

#### 功能特点
- **一键转换**：从STL导出数据直接生成可运行的MuJoCo仿真环境
- **智能重命名**：使用pypinyin将中文文件名转换为拼音，避免编码问题
- **完整工作流**：包含XML生成、文件整理、查看器创建的完整流程
- **位置验证**：自动生成查看器脚本，便于验证组件位置是否正确

#### 技术实现
- 支持pypinyin库的智能中文转换
- 完整的MuJoCo XML结构生成
- 自动创建assets目录和文件映射
- 错误处理和降级方案

#### 输出格式
```
visible_components_stl_YYYYMMDD_HHMMSS/
├── mujoco/
│   ├── assets/           # 重命名后的STL文件
│   ├── model.xml        # MuJoCo模型文件
│   └── viewer.py        # 查看器启动脚本
├── export_data.json     # 原始数据
└── *.stl               # 原始STL文件
```

#### 使用方法
```bash
# 安装依赖
pip install pypinyin

# 转换STL导出数据
python generate_mujoco_xml.py /path/to/export_dir

# 启动查看器验证
cd /path/to/export_dir/mujoco
python viewer.py
```