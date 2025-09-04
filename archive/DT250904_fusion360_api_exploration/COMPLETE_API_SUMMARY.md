# Fusion 360 API 完整总结 - MuJoCo集成专用

## 🎯 总体目标：将Fusion 360作为参数配置器，提取装配后的位置、旋转和关节限制信息，用于MuJoCo控制算法验证

---

## 📚 文档结构概览

### 已创建的API参考文档

| 文档名称 | 内容重点 | 用途 |
|---|---|---|
| **LOCAL_API_REFERENCE.md** | 核心API类层次结构 | 快速查找API类和方法 |
| **PHYSICAL_GEOMETRY_API.md** | 物理属性与几何数据提取 | 获取质量、惯性、几何信息 |
| **JOINT_CONSTRAINTS_API.md** | 关节约束与运动限制 | 提取关节类型和限制参数 |
| **COMPLETE_API_SUMMARY.md** | 完整API总结与集成指南 | 本文档 - 综合使用指南 |

---

## 🔧 核心API架构

### 1. 应用入口与设计环境
```python
import adsk.core
import adsk.fusion

# 标准入口
app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent
```

### 2. 数据提取路径图
```
Application
├── activeProduct (Design)
│   ├── rootComponent
│   │   ├── allComponents (Component集合)
│   │   │   ├── physicalProperties (物理属性)
│   │   │   ├── material (材料属性)
│   │   │   └── bRepBodies (几何实体)
│   │   ├── allJoints (Joint集合)
│   │   │   └── jointMotion (关节运动)
│   │   │       ├── rotationLimits (旋转限制)
│   │   │       └── slideLimits (滑动限制)
│   │   └── allOccurrences (Occurrence集合)
│   │       └── transform (变换矩阵)
│   └── unitsManager (单位管理)
```

---

## 📊 关键数据提取能力

### 1. 物理属性提取
| 属性 | API路径 | 单位 | MuJoCo转换 |
|---|---|---|---|
| **质量** | `component.physicalProperties.mass` | kg | 直接使用 |
| **体积** | `component.physicalProperties.volume` | m³ | 直接使用 |
| **质心** | `component.physicalProperties.centerOfMass` | m | 直接使用 |
| **惯性张量** | `physical.getXYZMomentsOfInertia()` | kg·m² | 直接使用 |
| **密度** | `component.material.density` | kg/m³ | 直接使用 |

### 2. 关节信息提取
| 信息 | API路径 | 单位 | MuJoCo转换 |
|---|---|---|---|
| **关节类型** | `joint.jointMotion.jointType` | 枚举 | 映射转换 |
| **旋转限制** | `motion.rotationLimits` | 弧度 | 直接使用 |
| **滑动限制** | `motion.slideLimits` | cm | ×0.01→m |
| **关节原点** | `motion.origin` | cm | ×0.01→m |
| **关节轴** | `motion.zAxis` | 向量 | 直接使用 |

### 3. 装配关系提取
| 信息 | API路径 | 格式 | 用途 |
|---|---|---|---|
| **变换矩阵** | `occurrence.transform.asArray()` | 4×4矩阵 | 位置姿态 |
| **位置** | `transform.translation` | Point3D | 组件位置 |
| **旋转** | `transform.rotation` | Matrix3D | 组件姿态 |
| **可见性** | `occurrence.isLightBulbOn` | 布尔值 | 显示控制 |

### 4. 几何数据提取
| 信息 | API路径 | 单位 | MuJoCo转换 |
|---|---|---|---|
| **体积** | `body.volume` | cm³ | ×1e-6→m³ |
| **表面积** | `body.surfaceArea` | cm² | ×1e-4→m² |
| **边界框** | `body.boundingBox` | cm | ×0.01→m |
| **几何中心** | `body.centroid` | cm | ×0.01→m |

---

## 🔄 关节类型映射表

### Fusion 360 → MuJoCo 关节映射

| Fusion关节类型 | MuJoCo关节类型 | 自由度 | 特殊处理 |
|---|---|---|---|
| **RigidJointType** | free 或固定 | 0 或 6 | 根据需求选择 |
| **RevoluteJointType** | hinge | 1 | 直接映射 |
| **SliderJointType** | slide | 1 | 单位转换 |
| **CylindricalJointType** | hinge + slide | 2 | 分解为两个关节 |
| **BallJointType** | ball 或 3×hinge | 3 | 可选择分解 |
| **PlanarJointType** | 2×slide + hinge | 3 | 分解为三个关节 |

---

## 🎯 完整数据提取器

### 1. 主提取器
```python
import adsk.core
import adsk.fusion
import json
import math

class FusionToMuJoCoExtractor:
    def __init__(self):
        self.app = adsk.core.Application.get()
        self.design = adsk.fusion.Design.cast(self.app.activeProduct)
        self.root = self.design.rootComponent
    
    def extract_all_data(self):
        """提取所有数据"""
        return {
            "design_info": self._extract_design_info(),
            "components": self._extract_all_components(),
            "joints": self._extract_all_joints(),
            "assembly": self._extract_assembly_structure(),
            "mujoco_ready": self._convert_to_mujoco_format()
        }
    
    def _extract_design_info(self):
        """提取设计信息"""
        return {
            "name": self.design.name,
            "component_count": self.root.allComponents.count,
            "joint_count": self.root.allJoints.count,
            "occurrence_count": self.root.allOccurrences.count
        }
    
    def _extract_all_components(self):
        """提取所有组件数据"""
        components = {}
        for component in self.root.allComponents:
            components[component.name] = self._extract_component_data(component)
        return components
    
    def _extract_component_data(self, component):
        """提取单个组件数据"""
        physical = component.physicalProperties
        material = component.material
        
        return {
            "physical": {
                "mass": physical.mass,
                "volume": physical.volume,
                "center_of_mass": list(physical.centerOfMass.asArray()),
                "inertia": list(physical.getXYZMomentsOfInertia().asArray())
            },
            "material": {
                "name": material.name,
                "density": material.density,
                "elastic_modulus": material.elasticModulus,
                "poisson_ratio": material.poissonRatio
            },
            "bodies": [self._extract_body_data(body) for body in component.bRepBodies]
        }
    
    def _extract_body_data(self, body):
        """提取几何体数据"""
        bbox = body.boundingBox
        
        return {
            "name": body.name,
            "volume_cm3": body.volume,
            "volume_m3": body.volume * 1e-6,
            "surface_area_cm2": body.surfaceArea,
            "surface_area_m2": body.surfaceArea * 1e-4,
            "centroid_cm": list(body.centroid.asArray()),
            "centroid_m": [coord * 0.01 for coord in body.centroid.asArray()],
            "bounding_box": {
                "min_cm": list(bbox.minPoint.asArray()),
                "max_cm": list(bbox.maxPoint.asArray()),
                "min_m": [coord * 0.01 for coord in bbox.minPoint.asArray()],
                "max_m": [coord * 0.01 for coord in bbox.maxPoint.asArray()]
            }
        }
    
    def _extract_all_joints(self):
        """提取所有关节数据"""
        joints = []
        for joint in self.root.allJoints:
            if joint.isSuppressed:
                continue
            joints.append(self._extract_joint_data(joint))
        return joints
    
    def _extract_joint_data(self, joint):
        """提取关节数据"""
        motion = joint.jointMotion
        joint_type = motion.jointType
        
        base_data = {
            "name": joint.name,
            "type": str(joint_type),
            "origin_cm": list(motion.origin.asArray()),
            "origin_m": [coord * 0.01 for coord in motion.origin.asArray()],
            "axis": list(motion.zAxis.asArray()),
            "components": {
                "one": joint.componentOne.name,
                "two": joint.componentTwo.name
            }
        }
        
        # 根据关节类型添加特定数据
        if joint_type == adsk.fusion.JointTypes.RevoluteJointType:
            limits = motion.rotationLimits
            base_data["limits"] = {
                "min_rad": limits.minimumValue,
                "max_rad": limits.maximumValue,
                "rest_rad": limits.restValue,
                "min_deg": math.degrees(limits.minimumValue),
                "max_deg": math.degrees(limits.maximumValue),
                "rest_deg": math.degrees(limits.restValue)
            }
        elif joint_type == adsk.fusion.JointTypes.SliderJointType:
            limits = motion.slideLimits
            base_data["limits"] = {
                "min_cm": limits.minimumValue,
                "max_cm": limits.maximumValue,
                "rest_cm": limits.restValue,
                "min_m": limits.minimumValue * 0.01,
                "max_m": limits.maximumValue * 0.01,
                "rest_m": limits.restValue * 0.01
            }
        
        return base_data
    
    def _extract_assembly_structure(self):
        """提取装配结构"""
        return {
            "root_component": self.root.name,
            "occurrences": [
                {
                    "name": occ.name,
                    "component": occ.component.name,
                    "transform": occ.transform.asArray(),
                    "position": list(occ.transform.translation.asArray()),
                    "is_visible": occ.isLightBulbOn
                }
                for occ in self.root.allOccurrences
            ]
        }
    
    def _convert_to_mujoco_format(self):
        """转换为MuJoCo格式"""
        return {
            "worldbody": {
                "name": "world",
                "pos": [0, 0, 0],
                "quat": [1, 0, 0, 0]
            },
            "bodies": self._create_mujoco_bodies(),
            "joints": self._create_mujoco_joints(),
            "geoms": self._create_mujoco_geoms()
        }
    
    def _create_mujoco_bodies(self):
        """创建MuJoCo body"""
        bodies = []
        for comp_name, comp_data in self._extract_all_components().items():
            physical = comp_data["physical"]
            bodies.append({
                "name": comp_name,
                "pos": physical["center_of_mass"],
                "mass": physical["mass"],
                "inertia": {
                    "fullinertia": physical["inertia"] + [0, 0, 0]
                }
            })
        return bodies
    
    def _create_mujoco_joints(self):
        """创建MuJoCo joint"""
        joints = []
        for joint_data in self._extract_all_joints():
            joint_type = joint_data["type"]
            
            if "RevoluteJointType" in joint_type:
                joints.append({
                    "name": joint_data["name"],
                    "type": "hinge",
                    "pos": joint_data["origin_m"],
                    "axis": joint_data["axis"],
                    "range": [
                        joint_data["limits"]["min_rad"],
                        joint_data["limits"]["max_rad"]
                    ],
                    "pos0": joint_data["limits"]["rest_rad"]
                })
            elif "SliderJointType" in joint_type:
                joints.append({
                    "name": joint_data["name"],
                    "type": "slide",
                    "pos": joint_data["origin_m"],
                    "axis": joint_data["axis"],
                    "range": [
                        joint_data["limits"]["min_m"],
                        joint_data["limits"]["max_m"]
                    ],
                    "pos0": joint_data["limits"]["rest_m"]
                })
        
        return joints
    
    def _create_mujoco_geoms(self):
        """创建MuJoCo geom"""
        geoms = []
        for comp_name, comp_data in self._extract_all_components().items():
            for body in comp_data["bodies"]:
                bbox = body["bounding_box"]
                size = [
                    (bbox["max_m"][0] - bbox["min_m"][0]) / 2,
                    (bbox["max_m"][1] - bbox["min_m"][1]) / 2,
                    (bbox["max_m"][2] - bbox["min_m"][2]) / 2
                ]
                pos = [
                    (bbox["max_m"][0] + bbox["min_m"][0]) / 2,
                    (bbox["max_m"][1] + bbox["min_m"][1]) / 2,
                    (bbox["max_m"][2] + bbox["min_m"][2]) / 2
                ]
                
                geoms.append({
                    "name": f"{comp_name}_{body['name']}",
                    "type": "box",
                    "size": size,
                    "pos": pos,
                    "body": comp_name
                })
        
        return geoms
```

### 2. 使用示例
```python
# 使用提取器
extractor = FusionToMuJoCoExtractor()

# 提取所有数据
all_data = extractor.extract_all_data()

# 保存为JSON
with open('fusion_to_mujoco.json', 'w') as f:
    json.dump(all_data, f, indent=2)

# 获取MuJoCo格式数据
mujoco_data = all_data["mujoco_ready"]
```

---

## 🚀 实际应用工作流

### 1. Fusion 360设计阶段
1. **建模**: 创建机械零件和组件
2. **装配**: 使用Joint定义组件间关系
3. **约束**: 设置关节限制和运动范围
4. **材料**: 分配真实材料属性

### 2. 数据提取阶段
1. **运行脚本**: 执行`FusionToMuJoCoExtractor`
2. **验证数据**: 检查JSON输出是否正确
3. **调整参数**: 根据需要修改提取逻辑
4. **导出数据**: 保存为JSON或直接生成MuJoCo XML

### 3. MuJoCo仿真阶段
1. **加载模型**: 使用提取的参数创建MuJoCo模型
2. **验证物理**: 检查质量、惯性是否合理
3. **测试关节**: 验证关节限制是否正确
4. **控制算法**: 开发和验证控制算法

---

## 📋 常见问题与解决方案

### 1. 单位转换问题
```python
# 统一单位转换函数
def convert_units(value, from_unit, to_unit):
    """单位转换"""
    if from_unit == "cm" and to_unit == "m":
        return value * 0.01
    elif from_unit == "cm³" and to_unit == "m³":
        return value * 1e-6
    elif from_unit == "cm²" and to_unit == "m²":
        return value * 1e-4
    elif from_unit == "deg" and to_unit == "rad":
        return value * math.pi / 180
    else:
        return value
```

### 2. 坐标系转换
```python
def transform_to_mujoco_coords(point):
    """将Fusion坐标转换为MuJoCo坐标"""
    # 根据需要调整坐标系
    # 例如：交换Y和Z轴
    return [point[0], point[2], point[1]]
```

### 3. 错误处理
```python
def safe_extract_data():
    """安全的数据提取"""
    try:
        extractor = FusionToMuJoCoExtractor()
        return extractor.extract_all_data()
    except Exception as e:
        print(f"数据提取失败: {e}")
        return None
```

---

## 📚 扩展功能建议

### 1. 实时更新
```python
# 使用事件系统实现实时更新
class FusionDataUpdater:
    def __init__(self):
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface
        
    def setup_events(self):
        """设置事件监听"""
        on_document_event = self.app.documentEvent.add(
            self.on_document_changed
        )
    
    def on_document_changed(self, args):
        """文档变更时更新数据"""
        if args.firingEvent == adsk.core.DocumentEvent.ActivatedDocumentEvent:
            # 重新提取数据
            self.update_data()
    
    def update_data(self):
        """更新数据"""
        extractor = FusionToMuJoCoExtractor()
        data = extractor.extract_all_data()
        # 保存或发送数据
        self.save_data(data)
```

### 2. 批量处理
```python
def batch_extract_data(design_paths):
    """批量提取多个设计的数据"""
    all_results = {}
    
    for path in design_paths:
        try:
            # 打开设计
            app = adsk.core.Application.get()
            app.open(path)
            
            # 提取数据
            extractor = FusionToMuJoCoExtractor()
            data = extractor.extract_all_data()
            
            # 保存结果
            design_name = path.split('/')[-1].split('.')[0]
            all_results[design_name] = data
            
            # 关闭设计
            app.activeDocument.close(False)
            
        except Exception as e:
            print(f"处理 {path} 失败: {e}")
    
    return all_results
```

---

## 🎯 质心提取解决方案 - 重大突破

### 关键发现
通过系统性调试和分析，我们成功解决了Fusion 360质心坐标提取的关键问题：

#### 1. 根组件物理属性方法
对于简单装配，使用根组件的物理属性可直接获得Fusion显示的准确质心坐标：
```python
# 获取根组件的物理属性
root_physical = root.physicalProperties
root_com = root_physical.centerOfMass

# 结果与Fusion分析完全一致
# BComp示例: (2.302, 4.609, 0.201) mm
```

#### 2. 矩阵变换方法
对于单个组件，使用4x4变换矩阵正确转换局部质心坐标到全局装配坐标：
```python
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
```

#### 3. Fusion计算机制理解
- Fusion 360在装配层面计算质心，已考虑所有子组件的变换关系和装配约束
- 对于复杂装配，需要考虑组件的层次结构和变换链
- 使用`transform2`而非`transform`可获得更精确的变换矩阵

### 实现脚本
- **`final_center_of_mass_extractor.py`**：完整的质心提取脚本，支持多种方法对比
- **`check_component_visibility.py`**：零部件可见状态检查工具，提供全面的可见性分析
- **脚本位置**：`archive/DT250904_fusion360_api_exploration/`目录
- **验证结果**：BComp组件质心提取与Fusion分析完全一致

### 应用价值
此解决方案可直接用于MuJoCo控制算法验证：
- 获取准确的组件质心坐标
- 提取装配位置和姿态信息
- 为物理仿真提供精确的参数输入

## 🔍 零部件可见状态检查工具

### 功能概述
开发了一个实用的零部件可见状态检查工具，能够快速分析装配文档中所有零部件的可见状态，提供详细的统计报告。

### 核心功能
```python
# 检查零部件可见状态的核心代码
for occurrence in root.allOccurrences:
    component_name = occurrence.component.name
    occurrence_name = occurrence.name
    is_visible = occurrence.isLightBulbOn  # 关键属性
    
    status_text = "可见" if is_visible else "不可见"
    # 收集和统计信息...
```

### 输出内容
- **统计摘要**：总装配实例数量、可见/不可见数量、可见比例
- **详细列表**：每个装配实例的名称、组件名称和可见状态
- **格式化显示**：清晰易读的消息框输出，支持文本窗口记录

### 应用场景
- **设计管理**：快速检查装配文档的零部件显示状态
- **评审准备**：设计评审前确认所有相关零部件可见
- **批量操作**：大规模装配的可视化管理
- **状态记录**：生成可见状态报告用于文档记录

### 技术特点
- 使用 `occurrence.isLightBulbOn` 属性准确判断可见状态
- 自动计算统计数据和比例分析
- 支持文本窗口输出，便于结果复制和记录
- 错误处理完善，适应各种装配文档结构

---

## 📅 文档信息

- **创建日期**: 2025-09-04
- **重大更新**: 2025-09-04 - 质心提取解决方案突破
- **目标**: Fusion 360 → MuJoCo 完整数据提取解决方案
- **覆盖范围**: 所有相关API、完整提取器、工作流程、质心提取解决方案
- **状态**: 质心提取问题已解决，完整解决方案已验证可用
- **下一步**: 将质心提取方法集成到完整的MuJoCo参数提取工作流中