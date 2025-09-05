# Fusion 360 STEP 到 MuJoCo 转换器 (简化版) 使用说明

## 概述

`generate_mujoco_simple.py` 是一个简化的脚本，用于将 Fusion 360 导出的 STEP 文件和新格式 JSON 数据转换为 MuJoCo XML 文件。

## 新格式特点

- 无质心数据（format_version: 2.1-no-com）
- 直接使用 `pos_m`（位置，单位：米）和 `quat_wxyz`（四元数）
- STEP 文件需要转换为 STL 格式
- 矩阵存储为 column-major 格式

## 使用方法

### 1. 基本用法

```bash
python3 generate_mujoco_simple.py <导出目录路径>
```

例如：
```bash
python3 generate_mujoco_simple.py /path/to/your/export_directory
```

### 2. 使用 uv 环境

```bash
uv run python generate_mujoco_simple.py /path/to/your/export_directory
```

### 3. 高级选项

```bash
# 调整STL导出容差
python3 generate_mujoco_simple.py /path/to/export --stl-tolerance 0.05

# 优先使用FreeCAD进行转换
python3 generate_mujoco_simple.py /path/to/export --prefer-freecad
```

## 输出文件

脚本会在导出目录下创建 `mujoco` 子目录，包含：

- `model.xml` - MuJoCo 模型文件
- `assets/` - 资源文件目录
  - 包含复制的 STEP 文件（需要转换为 STL）
- `viewer.py` - 查看器脚本

## STEP 转 STL

脚本自动进行 STEP 到 STL 的转换，支持两种工具：

### 1. CadQuery（默认优先）
- 优点：Python原生支持，集成度高
- 缺点：需要安装cadquery包
- 安装：`pip install cadquery`

### 2. FreeCAD（备选）
- 优点：处理复杂模型更稳定
- 缺点：需要单独安装FreeCAD
- 安装：从官网下载安装或使用包管理器

### 转换过程

脚本会自动：
1. 尝试使用CadQuery转换STEP文件
2. 如果CadQuery失败，自动尝试FreeCAD
3. 如果都失败，保留原始STEP文件并修改XML引用

### 使用 FreeCAD（推荐）

```python
# FreeCAD 宏示例
import FreeCAD
import Part
import Mesh

def convert_step_to_stl(step_path, stl_path):
    # 打开 STEP 文件
    shape = Part.Shape(step_path)
    
    # 转换为网格
    mesh = Mesh.Mesh()
    mesh.addFacets(shape.tessellate(0.1))
    
    # 保存为 STL
    mesh.write(stl_path)
```

### 使用命令行工具

```bash
# 使用 FreeCAD 命令行
freecad --console --hidden "convert_step_to_stl.py" input.step output.stl

# 使用 OpenCASCADE
opencascade input.step output.stl
```

## 查看器使用

1. 进入生成的 mujoco 目录：
```bash
cd /path/to/export_directory/mujoco
```

2. 运行查看器：
```bash
python3 viewer.py
```

查看器会显示：
- 组件数量和自由度信息
- 每个组件的位置和旋转
- 交互式 3D 视图

## 注意事项

1. **文件名处理**：
   - 中文组件名会自动转换为拼音
   - 特殊字符会被替换为下划线
   - 确保生成的 STL 文件名与 XML 中的 mesh 名称一致

2. **单位转换**：
   - STEP 文件单位：毫米
   - MuJoCo 单位：米
   - 脚本自动添加 0.001 的缩放因子

3. **坐标系**：
   - 使用 JSON 中的 `pos_m` 和 `quat_wxyz`
   - 不需要额外的矩阵解析

4. **依赖安装**：
   ```bash
   # 基础依赖
   pip install pypinyin numpy
   
   # CadQuery（推荐，自动转换STL）
   pip install cadquery
   
   # 或安装FreeCAD（备选方案）
   # macOS: brew install freecad
   # Ubuntu: sudo apt install freecad
   # Windows: 从官网下载安装包
   ```

5. **STL质量**：
   - 默认容差：0.1mm
   - 可通过 `--stl-tolerance` 调整
   - 容差越小，STL质量越高，文件越大

## 与完整版的区别

| 特性 | 简化版 | 完整版 |
|------|--------|--------|
| 质心数据 | ❌ 不支持 | ✅ 支持 |
| 惯量计算 | ❌ 不支持 | ✅ 支持 |
| STEP 转 STL | ✅ 自动（CadQuery/FreeCAD） | ✅ 自动（CadQuery） |
| 矩阵解析 | ❌ 不需要 | ✅ 支持 |
| 重心化 | ❌ 不支持 | ✅ 支持 |
| 复杂度 | 简单 | 复杂 |
| 适用场景 | 快速预览、简单模型 | 完整仿真、精确物理 |

## 故障排除

### 常见问题

1. **找不到 export_data.json**
   - 确保导出目录包含 JSON 文件
   - 检查路径是否正确

2. **STEP 文件不存在**
   - 检查 JSON 中的文件路径
   - 确保 STEP 文件在导出目录中

3. **CadQuery转换失败**
   - 确保已安装：`pip install cadquery`
   - 尝试调整容差：`--stl-tolerance 0.2`
   - 使用FreeCAD备选：`--prefer-freecad`

4. **FreeCAD转换失败**
   - 确保FreeCAD已安装并在PATH中
   - macOS: `/Applications/FreeCAD.app/Contents/MacOS/FreeCAD`
   - 尝试手动转换验证

5. **查看器无法加载**
   - 确保已安装 MuJoCo
   - 检查 STL 文件是否存在
   - 确认 STL 文件名与 XML 匹配

6. **中文文件名问题**
   - 安装 pypinyin：`pip install pypinyin`
   - 或手动重命名文件为英文

### 转换失败处理

如果自动转换失败，脚本会：
1. 保留原始STEP文件（扩展名改为.step）
2. 修改XML中的文件引用
3. 输出警告信息

你可以手动转换：
```bash
# 使用FreeCAD命令行
freecad --console --hidden convert_step.py input.step output.stl

# 或使用在线转换工具
```

## 示例工作流

1. 从 Fusion 360 导出 STEP 文件和 JSON
2. 运行转换脚本（自动转换STL）：
   ```bash
   uv run python generate_mujoco_simple.py /path/to/export
   ```
3. 检查输出：
   ```bash
   ls -la /path/to/export/mujoco/assets/
   # 应该看到 .stl 文件
   ```
4. 运行查看器验证：
   ```bash
   cd /path/to/export/mujoco
   python3 viewer.py
   ```
5. 在 MuJoCo 中使用生成的 model.xml

## 扩展功能

如果需要更复杂的功能（如质心计算、惯量分析等），请使用完整版 `build_flat_mj_final.py`。