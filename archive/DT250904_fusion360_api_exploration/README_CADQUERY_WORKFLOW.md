# Fusion 360 → MuJoCo 工作流 (基于 CadQuery)

本目录包含使用 CadQuery 将 Fusion 360 STEP 模型转换为 MuJoCo 仿真模型的完整工具链。

## 🚀 功能特性

- ✅ **STEP 文件处理**: 直接读取 Fusion 360 导出的 STEP 文件
- ✅ **精确几何计算**: 使用 OpenCASCADE 计算质心、包围盒、体积和惯量
- ✅ **多种重心化模式**: 支持质心(COM)、包围盒(BBox)或无重心化
- ✅ **完整惯量支持**: 计算 6D 惯量张量，支持 fullinertia 和 diaginertia
- ✅ **精确位置控制**: 正确处理变换矩阵和缩放因子
- ✅ **调试工具**: 包含验证脚本和调试信息输出
- ✅ **可视化验证**: 集成 MuJoCo 查看器进行位置验证

## 📁 文件说明

### 核心工具

- `build_flat_mj.py` - 主要转换脚本，STEP → STL + MuJoCo XML
- `validate_flat_mj.py` - 模型验证工具，检查位置、旋转、质量等
- `test_cadquery.py` - CadQuery 环境测试脚本

### 辅助文件

- `README_CADQUERY_WORKFLOW.md` - 本文档
- `debug_pose.csv` - 生成的位置调试数据
- `model.xml` - 生成的 MuJoCo 模型文件

## 🛠️ 安装依赖

```bash
# 安装 CadQuery (包含 OpenCASCADE)
pip install cadquery

# 安装其他可选依赖
pip install numpy trimesh mujoco

# 如果需要中文转拼音
pip install pypinyin
```

## 🧪 环境测试

运行测试脚本验证环境：

```bash
python test_cadquery.py
```

预期输出：
```
🧪 CadQuery 功能测试
==================================================

🔍 CadQuery 基本功能...
✅ CadQuery 导入成功
✅ 基本几何创建成功
✅ STL 导出成功: test_box.stl
✅ 测试文件清理成功

🔍 OCP 质量属性...
✅ OCP 模块导入成功
✅ 体积计算成功: 1000.0 mm³
✅ 体积计算正确

🔍 STEP 文件导入...
✅ STEP 导入成功，找到 2 个 solid
✅ 包围盒计算成功: 50.000 x 30.000 x 20.000 mm
✅ 质心计算成功: (25.000, 15.000, 10.000) mm

==================================================
📊 测试结果摘要:
  CadQuery 基本功能: ✅ 通过
  OCP 质量属性: ✅ 通过
  STEP 文件导入: ✅ 通过

==================================================
🎉 所有测试通过！CadQuery 环境配置正确。
```

## 📋 数据格式要求

JSON 数据文件应包含以下结构：

```json
{
  "components": {
    "组件名称": [
      {
        "occurrence_name": "实例名称",
        "step_path": "/path/to/component.step",
        "world_transform_matrix": [
          [0.001, 0, 0, 0],
          [0, 0.001, 0, 0],
          [0, 0, 0.001, 0],
          [tx, ty, tz, 1]
        ],
        "center_of_mass": {
          "world": {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0
          }
        }
      }
    ]
  }
}
```

### 变换矩阵说明

- **格式**: 4x4 行向量矩阵
- **缩放**: 统一缩放因子 s=0.001 (mm→m)
- **旋转**: 左上 3x3 矩阵 (包含缩放)
- **平移**: 最后一行前 3 列 (单位: 米)

## 🚀 使用方法

### 基本转换

```bash
# 基本用法 (默认质心化，钢的密度)
python build_flat_mj.py export_data.json --out mj_output

# 指定重心化模式
python build_flat_mj.py export_data.json --recenter com    # 质心化 (默认)
python build_flat_mj.py export_data.json --recenter bbox   # 包围盒居中
python build_flat_mj.py export_data.json --recenter none   # 无重心化

# 指定材料密度
python build_flat_mj.py export_data.json --density 2700.0  # 铝的密度

# 调整 STL 导出精度
python build_flat_mj.py export_data.json --tolerance 0.01
```

### 高级选项

```bash
# 不生成惯量信息
python build_flat_mj.py export_data.json --no-inertia

# 使用对角惯量 (而非完整惯量张量)
python build_flat_mj.py export_data.json --no-fullinertia

# 组合使用
python build_flat_mj.py export_data.json \
  --recenter bbox \
  --density 1000.0 \
  --no-fullinertia \
  --tolerance 0.02 \
  --out water_simulation
```

## 🔍 验证和调试

### 模型验证

```bash
# 基本验证
python validate_flat_mj.py mj_output/model.xml export_data.json

# 启动查看器进行可视化验证
python validate_flat_mj.py mj_output/model.xml export_data.json --viewer

# 静默模式 (只输出摘要)
python validate_flat_mj.py mj_output/model.xml export_data.json --quiet
```

### 调试信息

转换过程会生成以下调试信息：

1. **控制台输出**:
   - 每个 STEP 文件的处理状态
   - 质心/包围盒坐标
   - 质量和体积计算结果
   - 缩放因子一致性检查

2. **XML 注释**:
   - 每个组件的 delta_mm (重心化偏移)
   - 原始变换矩阵 t(m) 和缩放 s
   - 质量和体积信息

3. **debug_pose.csv**:
   - 位置恢复误差验证
   - 原始位置 vs 计算位置对比

## 📊 输出结构

```
mj_output/
├── model.xml              # MuJoCo 模型文件
├── debug_pose.csv         # 位置调试数据
└── assets/                # 资源目录
    ├── part1.stl          # 转换后的 STL 文件
    ├── part2.stl
    └── ...
```

## 🔧 工作原理

### 1. STEP 文件处理

```python
# 加载 STEP 文件
shape = cq.importers.importStep(step_path)
solids = shape.solids().vals()
comp = cq.Compound.makeCompound(solids)
```

### 2. 几何计算

```python
# 计算质心
com = comp.CenterOfMass()

# 计算包围盒
bb = comp.BoundingBox()
center = [(bb.xmin+bb.xmax)/2, ...]

# 计算质量和惯量
props = GProp_GProps()
brepgprop_VolumeProperties(comp.wrapped, props)
volume_mm3 = props.Mass()
I_tensor = props.MatrixOfInertia()
```

### 3. 变换矩阵解析

```python
# 解析行向量格式
M = np.array(entry["world_transform_matrix"])
R_scaled = M[0:3, 0:3]  # 旋转+缩放
t = M[3, 0:3]           # 平移(米)

# 提取缩放因子
s = np.linalg.norm(R_scaled[0])
R = (R_scaled / s).T    # 纯旋转矩阵
```

### 4. 重心化补偿

```python
# 计算补偿后的位置
delta_mm = com  # 或包围盒中心
delta_m = delta_mm * mesh_scale
body_pos = t - R @ delta_m
```

### 5. 惯量计算

```python
# 单位转换
volume_m3 = volume_mm3 * 1e-9
mass = volume_m3 * density
I_kgm2 = I_tensor * 1e-15 * density
```

## 🐛 常见问题

### 1. CadQuery 导入失败

**问题**: `ImportError: No module named 'cadquery'`

**解决**:
```bash
pip install cadquery
```

### 2. STEP 文件找不到

**问题**: `ValueError: STEP 文件中没有找到 solids`

**解决**:
- 检查 STEP 文件路径是否正确
- 确认 STEP 文件包含有效的几何体
- 使用 `test_cadquery.py` 测试 STEP 导入

### 3. 位置不准确

**问题**: 验证显示位置误差较大

**解决**:
- 检查变换矩阵格式是否正确
- 确认缩放因子一致性
- 尝试不同的重心化模式
- 查看 debug_pose.csv 中的误差数据

### 4. 惯量计算错误

**问题**: 惯量值不合理或仿真不稳定

**解决**:
- 确认密度值设置正确
- 检查是否使用了正确的重心化模式
- 验证体积计算是否正确
- 考虑使用 `--no-fullinertia` 选项

### 5. MuJoCo 查看器无法启动

**问题**: `ImportError: No module named 'mujoco'`

**解决**:
```bash
pip install mujoco
```

## 📈 性能优化

### 1. 大型装配体

对于包含大量组件的装配体：

```bash
# 降低 STL 精度以提高性能
python build_flat_mj.py large_assembly.json --tolerance 0.1

# 禁用惯量计算
python build_flat_mj.py large_assembly.json --no-inertia
```

### 2. 重复组件

脚本会自动检测重复的 STEP 文件并避免重复处理。

### 3. 内存使用

处理大型装配体时，建议：
- 增加系统内存
- 分批处理组件
- 使用较低的 STL 精度

## 🔮 未来扩展

### 计划功能

- [ ] 父子层级结构支持
- [ ] 关节和约束自动生成
- [ ] 材料属性数据库
- [ ] 碰撞几何优化
- [ ] 批处理脚本
- [ ] GUI 界面

### 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目遵循 MIT 许可证。