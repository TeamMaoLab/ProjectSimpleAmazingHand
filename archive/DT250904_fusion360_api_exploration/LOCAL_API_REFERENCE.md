# Fusion 360 本地API核心参考 - MuJoCo集成专用

## 🎯 目标导向API参考

基于您的需求：**将Fusion 360作为参数配置器，提取装配后的位置、旋转和关节限制信息，用于MuJoCo控制算法验证**

---

## 📋 核心API类层次结构

### 1. 应用入口与设计环境

#### `adsk.core.Application`
```python
# 获取应用实例
app = adsk.core.Application.get()
ui = app.userInterface  # 用户界面交互

# 获取当前活动产品（设计）
design = adsk.fusion.Design.cast(app.activeProduct)
```

#### `adsk.fusion.Design`
```python
# 设计环境核心对象
design = adsk.fusion.Design.cast(app.activeProduct)

# 关键属性
design.rootComponent          # 根组件
design.allComponents         # 所有组件集合
design.allJoints             # 所有关节集合
design.allOccurrences        # 所有装配实例集合
design.unitsManager          # 单位管理器
```

---

## 🔧 组件系统 (Component) - 物理属性提取

### `adsk.fusion.Component`
```python
# 组件是物理属性的基本载体
component = design.rootComponent

# 物理属性（核心！）
physical = component.physicalProperties
mass = physical.mass                    # 质量 (kg)
volume = physical.volume               # 体积 (m³)
center_of_mass = physical.centerOfMass # 质心位置 (Point3D)
inertia = physical.getXYZMomentsOfInertia()  # 惯性张量

# 材料属性
material = component.material
density = material.density              # 密度 (kg/m³)
elastic_modulus = material.elasticModulus  # 弹性模量 (Pa)
poisson_ratio = material.poissonRatio   # 泊松比

# 几何实体
bodies = component.bRepBodies          # BRep实体集合
construction_geometry = component.constructionGeometry  # 构造几何

# 子组件和装配
occurrences = component.occurrences    # 装配实例
joints = component.joints              # 关节集合
```

### `adsk.fusion.PhysicalProperties`
```python
# 物理属性计算器
physical = component.physicalProperties

# 关键方法
physical.mass                          # 实际质量 (kg)
physical.volume                        # 体积 (m³)
physical.centerOfMass                  # 质心 (Point3D)
physical.getXYZMomentsOfInertia()      # 惯性张量 (Vector3D)
physical.getPrincipalAxes()            # 主轴
physical.getPrincipalMomentsOfInertia() # 主惯性矩

# 注意：需要先计算物理属性
physical.calculate()  # 重新计算物理属性
```

---

## 🤝 关节系统 (Joints) - 运动约束提取

### `adsk.fusion.Joint`
```python
# 关节是运动约束的核心
for joint in design.allJoints:
    # 基本信息提取
    joint_name = joint.name
    joint_type = joint.jointMotion.jointType  # 关节类型
    is_suppressed = joint.isSuppressed        # 是否被抑制
    
    # 几何定义
    geometry_one = joint.geometryOrOriginOne  # 第一个几何体
    geometry_two = joint.geometryOrOriginTwo  # 第二个几何体
    
    # 运动学信息
    motion = joint.jointMotion
    origin = motion.origin                   # 关节原点
    rotation = motion.rotation               # 关节旋转
```

### `adsk.fusion.JointMotion`
```python
# 关节运动定义
motion = joint.jointMotion

# 关节类型枚举
adsk.fusion.JointTypes.RigidJointType      # 固定关节
adsk.fusion.JointTypes.RevoluteJointType   # 旋转关节
adsk.fusion.JointTypes.SliderJointType     # 滑动关节
adsk.fusion.JointTypes.CylindricalJointType # 圆柱关节
adsk.fusion.JointTypes.BallJointType       # 球关节
adsk.fusion.JointTypes.PlanarJointType     # 平面关节

# 旋转关节限制（重要！）
if motion.jointType == adsk.fusion.JointTypes.RevoluteJointType:
    rot_limits = motion.rotationLimits
    min_angle = rot_limits.minimumValue     # 最小角度 (弧度)
    max_angle = rot_limits.maximumValue     # 最大角度 (弧度)
    rest_angle = rot_limits.restValue       # 静止角度 (弧度)

# 滑动关节限制
if motion.jointType == adsk.fusion.JointTypes.SliderJointType:
    slide_limits = motion.slideLimits
    min_pos = slide_limits.minimumValue     # 最小位置
    max_pos = slide_limits.maximumValue     # 最大位置
    rest_pos = slide_limits.restValue       # 静止位置
```

---

## 📐 装配关系系统 (Occurrences) - 位置和姿态

### `adsk.fusion.Occurrence`
```python
# 装配实例表示组件在装配中的位置和姿态
for occurrence in design.allOccurrences:
    # 基本信息
    occurrence_name = occurrence.name
    component = occurrence.component        # 引用的组件
    is_visible = occurrence.isLightBulbOn   # 是否可见
    
    # 变换矩阵（核心！）
    transform = occurrence.transform        # 4x4变换矩阵
    
    # 推荐使用 transform2（更精确的变换矩阵）
    transform2 = occurrence.transform2      # 推荐使用的变换矩阵
    
    # 位置和旋转提取
    position = transform.translation        # 位置向量
    rotation = transform.rotation           # 旋转矩阵
    
    # 使用 transform2 获取更精确的位置和旋转
    position2 = transform2.translation     # 更精确的位置向量
    rotation2 = transform2.rotation        # 更精确的旋转矩阵
    
    # 变换矩阵数据（用于MuJoCo）
    matrix_data = transform.asArray()       # 16个元素的数组
    matrix2_data = transform2.asArray()     # 更精确的16个元素数组
    # 格式：[m11, m12, m13, m14, m21, m22, m23, m24, m31, m32, m33, m34, m41, m42, m43, m44]
    # 其中 m41, m42, m43 是位置分量
```

### `adsk.core.Matrix3D`
```python
# 3D变换矩阵
transform = occurrence.transform
transform2 = occurrence.transform2        # 推荐使用

# 关键方法
transform.translation                     # 获取位置向量
transform2.translation                    # 获取更精确的位置向量（推荐）
transform.rotation                        # 获取旋转矩阵
transform2.rotation                       # 获取更精确的旋转矩阵（推荐）
transform.asArray()                       # 转换为数组
transform2.asArray()                      # 转换更精确的数组（推荐）
transform.invert()                        # 矩阵求逆
transform.transformBy(other_matrix)       # 矩阵相乘

# 创建变换矩阵
new_transform = adsk.core.Matrix3D.create()
new_transform.setWithArray(matrix_array)  # 从数组设置

# transform2 与 transform 的区别
# transform2 提供了更精确的变换计算，特别是在复杂装配中
# transform2 考虑了组件的所有变换历史，而不仅仅是最终变换
# 对于需要高精度位置和姿态的应用（如MuJoCo），建议使用 transform2
```

---

## 📦 几何实体系统 (BRep Bodies) - 碰撞几何

### `adsk.fusion.BRepBody`
```python
# BRep实体是碰撞检测的基础
for body in component.bRepBodies:
    # 基本信息
    body_name = body.name
    is_solid = body.isSolid                # 是否为实体
    is_surface = body.isSurface            # 是否为曲面
    
    # 几何属性
    volume = body.volume                   # 体积 (cm³)
    surface_area = body.surfaceArea        # 表面积 (cm²)
    centroid = body.centroid               # 几何中心
    
    # 边界框（用于碰撞检测）
    bounding_box = body.boundingBox
    min_point = bounding_box.minPoint      # 最小点
    max_point = bounding_box.maxPoint      # 最大点
    
    # 顶点、边、面（用于详细几何）
    vertices = body.vertices               # 顶点集合
    edges = body.edges                     # 边集合
    faces = body.faces                     # 面集合
```

### `adsk.fusion.BRepFace`
```python
# 面几何信息
for face in body.faces:
    # 面类型
    face_type = face.geometry.surfaceType  # 平面、圆柱面等
    
    # 面法向量
    normal = face.evaluator.getNormalAtPoint(face.pointOnFace)
    
    # 面积
    area = face.area                       # 面积
```

---

## 🎯 完整数据提取代码模板

### 1. 基础数据提取器
```python
import adsk.core
import adsk.fusion
import json

def extract_fusion_data_for_mujoco():
    """提取Fusion 360数据用于MuJoCo"""
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    
    if not design:
        return None
    
    root = design.rootComponent
    
    mujoco_data = {
        "design_name": design.name,
        "components": {},
        "joints": [],
        "bodies": []
    }
    
    # 提取组件数据
    for component in root.allComponents:
        comp_data = extract_component_data(component)
        mujoco_data["components"][component.name] = comp_data
    
    # 提取关节数据
    for joint in root.allJoints:
        joint_data = extract_joint_data(joint)
        mujoco_data["joints"].append(joint_data)
    
    # 提取几何体数据
    for component in root.allComponents:
        for body in component.bRepBodies:
            body_data = extract_body_data(body, component.name)
            mujoco_data["bodies"].append(body_data)
    
    return mujoco_data

def extract_component_data(component):
    """提取组件数据"""
    physical = component.physicalProperties
    material = component.material
    
    return {
        "mass": physical.mass,
        "volume": physical.volume,
        "center_of_mass": list(physical.centerOfMass.asArray()),
        "inertia": list(physical.getXYZMomentsOfInertia().asArray()),
        "material": {
            "density": material.density,
            "elastic_modulus": material.elasticModulus,
            "poisson_ratio": material.poissonRatio
        }
    }

def extract_joint_data(joint):
    """提取关节数据"""
    motion = joint.jointMotion
    joint_data = {
        "name": joint.name,
        "type": str(motion.jointType),
        "origin": list(motion.origin.asArray())
    }
    
    # 添加关节限制
    if motion.jointType == adsk.fusion.JointTypes.RevoluteJointType:
        limits = motion.rotationLimits
        joint_data["limits"] = {
            "min": limits.minimumValue,
            "max": limits.maximumValue,
            "rest": limits.restValue
        }
    elif motion.jointType == adsk.fusion.JointTypes.SliderJointType:
        limits = motion.slideLimits
        joint_data["limits"] = {
            "min": limits.minimumValue,
            "max": limits.maximumValue,
            "rest": limits.restValue
        }
    
    return joint_data

def extract_body_data(body, component_name):
    """提取几何体数据"""
    return {
        "name": body.name,
        "component": component_name,
        "volume": body.volume * 1e-6,  # cm³ → m³
        "surface_area": body.surface_area,
        "centroid": list(body.centroid.asArray()),
        "bounding_box": {
            "min": list(body.boundingBox.minPoint.asArray()),
            "max": list(body.boundingBox.maxPoint.asArray())
        }
    }
```

### 2. 装配关系提取器
```python
def extract_assembly_structure():
    """提取装配结构"""
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    
    assembly_data = {
        "root_component": design.rootComponent.name,
        "occurrences": []
    }
    
    for occurrence in design.allOccurrences:
        # 推荐使用 transform2 获取更精确的变换数据
        transform = occurrence.transform
        transform2 = occurrence.transform2
        
        assembly_data["occurrences"].append({
            "name": occurrence.name,
            "component": occurrence.component.name,
            "transform": transform.asArray(),
            "transform2": transform2.asArray(),  # 更精确的变换矩阵
            "position": list(transform.translation.asArray()),
            "position2": list(transform2.translation.asArray()),  # 更精确的位置
            "is_visible": occurrence.isLightBulbOn
        })
    
    return assembly_data
```

---

## 🔍 关键API使用技巧

### 1. 单位转换
```python
# Fusion 360内部单位：cm, rad
# MuJoCo单位：m, rad

# 长度转换
length_m = length_cm * 0.01

# 体积转换
volume_m3 = volume_cm3 * 1e-6

# 角度转换（如果需要）
angle_deg = angle_rad * 180 / math.pi
```

### 2. 坐标系转换
```python
# Fusion 360使用右手坐标系
# MuJoCo也使用右手坐标系，通常不需要转换

# 但需要注意原点位置
# 如果需要调整坐标系，可以使用变换矩阵
def transform_to_mujoco_coords(point):
    """将Fusion坐标转换为MuJoCo坐标"""
    # 根据需要调整坐标系
    return point
```

### 3. 错误处理
```python
def safe_extract_data():
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        
        if not design:
            print("当前不是设计环境")
            return None
            
        # 提取数据...
        return extract_fusion_data_for_mujoco()
        
    except Exception as e:
        print(f"数据提取失败: {e}")
        return None
```

---

## 📚 下一步开发建议

### 1. 立即可实现的功能
- ✅ 组件物理属性提取
- ✅ 关节类型和限制提取
- ✅ 装配位置和姿态提取
- ✅ 几何体边界框提取

### 2. 进阶功能
- 🔄 实时数据更新（使用事件系统）
- 🔄 碰撞几何详细提取
- 🔄 材料属性数据库集成
- 🔄 MuJoCo XML自动生成

### 3. 集成工作流
1. **Fusion 360建模** → 设计机械结构
2. **装配约束** → 定义关节和运动限制
3. **数据提取** → 运行此脚本提取参数
4. **MuJoCo仿真** → 使用提取的参数进行控制算法验证

---

## 📅 文档信息

- **创建日期**: 2025-09-04
- **目标**: Fusion 360 → MuJoCo 参数提取
- **覆盖范围**: 组件、关节、装配、几何体
- **状态**: 核心API已整理，立即可用