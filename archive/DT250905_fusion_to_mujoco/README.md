# Fusion 360 到 MuJoCo 转换项目归档

**日期**: 2025-09-05  
**状态**: 已完成（位置计算）  
**版本**: v1.0  

## 项目概述

本项目实现了从 Fusion 360 导出数据到 MuJoCo XML 的转换流程，成功解决了坐标计算和结构生成问题。

## 目录结构

```
DT250905_fusion_to_mujoco/
├── README.md                    # 本文档
├── docs/                        # 文档目录
│   ├── coordinate_fix.md        # 坐标系统修复记录
│   └── roadmap.md               # 项目路线图
├── scripts/                     # 脚本目录
│   ├── main_converter.py        # 主要转换脚本
│   ├── analysis_tools.py        # 分析工具脚本
│   └── test_scripts.py          # 测试脚本
├── examples/                    # 示例数据
│   └── component_positions.json # 示例导出数据
└── legacy/                      # 旧版本脚本
    ├── fusion_export.py         # 早期导出脚本
    ├── mujoco_gen.py            # 早期生成脚本
    └── temp.py                  # 临时测试脚本
```

## 核心成果

### 1. Fusion 360 导出文件
- 实现了零部件位置和矩阵数据的 JSON 格式导出
- 包含组件名称、STL 文件、位置矩阵等信息
- 元数据声明为 "column-major" 但实际数据是行主序格式

### 2. MuJoCo XML 构建
- 基于导出的 JSON 数据生成 MuJoCo 兼容的 XML 文件
- 解决了坐标计算问题：
  - 使用索引 (3,7,11) 提取位置信息（厘米）
  - 使用 0.01 转换因子将厘米转换为米
- 实现了扁平化结构，所有组件直接位于 worldbody 下
- 位置精度达到 1e-9 级别

## 关键技术发现

1. **矩阵格式**: 实际数据是行主序格式，位置信息在索引 (3,7,11)
2. **单位转换**: 矩阵位置值是厘米，需要乘以 0.01 转换为米
3. **结构需求**: 扁平化结构更适合当前仿真需求

## 使用方法

1. 从 Fusion 360 导出零部件位置数据（JSON 格式）
2. 运行转换脚本生成 MuJoCo XML 文件
3. 在 MuJoCo 中加载 XML 文件进行仿真

## 下一步计划

1. 等待包含旋转数据的导出
2. 实现完整的四元数计算
3. 验证位置和旋转的准确性

## 相关文档

- [坐标系统修复记录](docs/coordinate_fix.md)
- [项目路线图](docs/roadmap.md)

## 历史版本

- v1.0 (2025-09-05): 初始版本，实现位置计算和扁平化结构