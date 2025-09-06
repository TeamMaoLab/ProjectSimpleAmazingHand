# Fusion 360 到 MuJoCo 转换项目

**版本**: v2.0 | **状态**: ✅ 完成 | **日期**: 2025-09-06

## 快速概览

完整实现 Fusion 360 到 MuJoCo 的数据转换，彻底解决坐标计算和旋转方向问题，确保视觉效果完全一致。

## 🎯 核心成果

### ✅ 位置转换 (精度 1e-9)
- 从列主序矩阵正确提取位置信息
- 厘米 → 米 单位转换
- 扁平化结构生成

### ✅ 旋转修复 (关键突破)
- **问题**: 旋转方向与 Fusion 360 相反
- **解决**: 列主序矩阵提取后转置 `.T`
- **结果**: 视觉效果完全一致
- **验证**: 用户实测两个方向旋转均正确

## 📁 项目结构

```
├── scripts/
│   ├── main_converter.py        # 主转换脚本
│   ├── test_rotation.py         # 基础测试
│   └── debug_*.py              # 调试工具
├── docs/
│   ├── coordinate_fix.md        # 完整技术文档
│   └── roadmap.md               # 项目路线图
└── examples/                    # 示例数据
```

## 🚀 快速使用

```bash
# 转换数据
uv run python3 scripts/main_converter.py <export_dir>

# 验证旋转
uv run python3 scripts/test_rotation.py
```

## 🔧 关键技术

### 旋转修复核心代码
```python
# 列主序提取 + 转置 = 正确旋转方向
R = np.array([
    [matrix[0], matrix[4], matrix[8]],
    [matrix[1], matrix[5], matrix[9]],
    [matrix[2], matrix[6], matrix[10]]
]).T
quaternion = matrix_to_quaternion(R)
```

### 位置提取
```python
# 索引 (3,7,11) 提取厘米单位位置
tx_cm, ty_cm, tz_cm = matrix[3], matrix[7], matrix[11]
position = [tx_cm * 0.01, ty_cm * 0.01, tz_cm * 0.01]
```

## ✅ 验证状态

- [x] 坐标精度测试
- [x] 旋转方向测试  
- [x] 用户实际验证
- [x] 完整测试套件

## 📖 文档

- **[完整技术文档](docs/coordinate_fix.md)** - 详细技术说明和实现细节
- **[项目路线图](docs/roadmap.md)** - 发展规划

## 📈 版本历史

- **v2.0** (2025-09-06) - 旋转方向修复，用户验证通过
- **v1.0** (2025-09-05) - 基础位置转换实现

---

**总结**: 转换流程现已完全可用，可准确将 Fusion 360 装配转换为 MuJoCo 仿真模型。