# Fusion 360 关节约束与运动限制API详解

## 🎯 目标：精确提取MuJoCo所需的关节类型、运动限制和约束信息

---

## 📋 关节系统核心API

### 1. 关节基础类

#### `adsk.fusion.Joint`
```python
# 关节 - 定义组件间的运动关系
joint = design.allJoints.item(0)

# 基本属性
joint.name                            # 关节名称
joint.isSuppressed                    # 是否被抑制（禁用）
joint.isValid                         # 关节是否有效
joint.parent                          # 父关节
joint.jointMotion                     # 关节运动对象
joint.geometryOrOriginOne             # 第一个几何体或原点
joint.geometryOrOriginTwo             # 第二个几何体或原点

# 关节连接的组件
occurrence_one = joint.occurrenceOne   # 第一个装配实例
occurrence_two = joint.occurrenceTwo   # 第二个装配实例
component_one = joint.componentOne     # 第一个组件
component_two = joint.componentTwo     # 第二个组件
```

#### 关节基本信息提取
```python
def extract_joint_basic_info(joint):
    """提取关节基本信息"""
    return {
        "name": joint.name,
        "is_suppressed": joint.isSuppressed,
        "is_valid": joint.isValid,
        "connected_components": {
            "component_one": joint.componentOne.name,
            "component_two": joint.componentTwo.name
        },
        "connected_occurrences": {
            "occurrence_one": joint.occurrenceOne.name,
            "occurrence_two": joint.occurrenceTwo.name
        }
    }
```

### 2. 关节运动系统

#### `adsk.fusion.JointMotion`
```python
# 关节运动 - 定义关节的运动类型和限制
motion = joint.jointMotion

# 关节类型（核心！）
motion.jointType                      # 关节类型枚举

# 关节原点和方向
motion.origin                         # 关节原点 (Point3D)
motion.rotation                       # 关节旋转 (Matrix3D)
motion.zAxis                          # Z轴方向 (Vector3D)

# 运动限制对象
motion.rotationLimits                 # 旋转限制
motion.slideLimits                    # 滑动限制
```

#### 关节类型枚举详解
```python
# 关节类型枚举值
adsk.fusion.JointTypes.RigidJointType        # 固定关节 - 无自由度
adsk.fusion.JointTypes.RevoluteJointType     # 旋转关节 - 1个旋转自由度
adsk.fusion.JointTypes.SliderJointType       # 滑动关节 - 1个平移自由度
adsk.fusion.JointTypes.CylindricalJointType  # 圆柱关节 - 1个旋转+1个平移自由度
adsk.fusion.JointTypes.BallJointType         # 球关节 - 3个旋转自由度
adsk.fusion.JointTypes.PlanarJointType       # 平面关节 - 2个平移+1个旋转自由度

# MuJoCo关节类型映射
FUSION_TO_MUJOCO_MAPPING = {
    "RigidJointType": "free",      # 或根据需求固定
    "RevoluteJointType": "hinge",
    "SliderJointType": "slide",
    "CylindricalJointType": "hinge+slide",  # 需要分解为两个关节
    "BallJointType": "ball",
    "PlanarJointType": "planar"     # 需要特殊处理
}
```

---

## 🔄 旋转关节限制API

### 1. 旋转限制对象

#### `adsk.fusion.RotationLimits`
```python
# 旋转限制 - 定义旋转关节的角度限制
rot_limits = motion.rotationLimits

# 限制值（弧度）
rot_limits.minimumValue              # 最小角度
rot_limits.maximumValue              # 最大角度
rot_limits.restValue                 # 静止角度

# 限制状态
rot_limits.isMinimumValueSuppressed  # 是否抑制最小值限制
rot_limits.isMaximumValueSuppressed  # 是否抑制最大值限制
rot_limits.isRestValueSuppressed     # 是否抑制静止值限制
```

#### 旋转关节数据提取
```python
def extract_revolute_joint_data(joint):
    """提取旋转关节数据"""
    motion = joint.jointMotion
    rot_limits = motion.rotationLimits
    
    # 转换为度（可选）
    min_deg = math.degrees(rot_limits.minimumValue)
    max_deg = math.degrees(rot_limits.maximumValue)
    rest_deg = math.degrees(rot_limits.restValue)
    
    return {
        "type": "revolute",
        "origin": list(motion.origin.asArray()),
        "axis": list(motion.zAxis.asArray()),  # 旋转轴
        "limits": {
            "min": rot_limits.minimumValue,    # 弧度
            "max": rot_limits.maximumValue,    # 弧度
            "rest": rot_limits.restValue,      # 弧度
            "min_deg": min_deg,                # 度
            "max_deg": max_deg,                # 度
            "rest_deg": rest_deg               # 度
        },
        "limits_suppressed": {
            "min": rot_limits.isMinimumValueSuppressed,
            "max": rot_limits.isMaximumValueSuppressed,
            "rest": rot_limits.isRestValueSuppressed
        }
    }
```

### 2. 旋转关节的MuJoCo映射
```python
def map_revolute_to_mujoco(joint_data):
    """将旋转关节映射到MuJoCo格式"""
    return {
        "type": "hinge",
        "pos": joint_data["origin"],
        "axis": joint_data["axis"],
        "range": [
            joint_data["limits"]["min"],
            joint_data["limits"]["max"]
        ],
        "pos0": joint_data["limits"]["rest"]
    }
```

---

## 📏 滑动关节限制API

### 1. 滑动限制对象

#### `adsk.fusion.SlideLimits`
```python
# 滑动限制 - 定义滑动关节的位置限制
slide_limits = motion.slideLimits

# 限制值（厘米）
slide_limits.minimumValue             # 最小位置
slide_limits.maximumValue             # 最大位置
slide_limits.restValue                # 静止位置

# 限制状态
slide_limits.isMinimumValueSuppressed # 是否抑制最小值限制
slide_limits.isMaximumValueSuppressed # 是否抑制最大值限制
slide_limits.isRestValueSuppressed    # 是否抑制静止值限制
```

#### 滑动关节数据提取
```python
def extract_slider_joint_data(joint):
    """提取滑动关节数据"""
    motion = joint.jointMotion
    slide_limits = motion.slideLimits
    
    # 转换为米（MuJoCo单位）
    min_m = slide_limits.minimumValue * 0.01
    max_m = slide_limits.maximumValue * 0.01
    rest_m = slide_limits.restValue * 0.01
    
    return {
        "type": "slider",
        "origin": list(motion.origin.asArray()),
        "axis": list(motion.zAxis.asArray()),  # 滑动轴
        "limits": {
            "min": slide_limits.minimumValue,   # 厘米
            "max": slide_limits.maximumValue,   # 厘米
            "rest": slide_limits.restValue,     # 厘米
            "min_m": min_m,                     # 米
            "max_m": max_m,                     # 米
            "rest_m": rest_m                    # 米
        },
        "limits_suppressed": {
            "min": slide_limits.isMinimumValueSuppressed,
            "max": slide_limits.isMaximumValueSuppressed,
            "rest": slide_limits.isRestValueSuppressed
        }
    }
```

### 2. 滑动关节的MuJoCo映射
```python
def map_slider_to_mujoco(joint_data):
    """将滑动关节映射到MuJoCo格式"""
    return {
        "type": "slide",
        "pos": joint_data["origin"],
        "axis": joint_data["axis"],
        "range": [
            joint_data["limits"]["min_m"],
            joint_data["limits"]["max_m"]
        ],
        "pos0": joint_data["limits"]["rest_m"]
    }
```

---

## 🌐 复杂关节类型API

### 1. 圆柱关节

#### `adsk.fusion.CylindricalJointMotion`
```python
# 圆柱关节 - 旋转+滑动组合
motion = joint.jointMotion

# 圆柱关节特有属性
motion.rotationLimits                # 旋转限制
motion.slideLimits                   # 滑动限制
motion.radius                        # 半径（如果有）
```

#### 圆柱关节数据提取
```python
def extract_cylindrical_joint_data(joint):
    """提取圆柱关节数据"""
    motion = joint.jointMotion
    
    # 提取旋转部分
    rot_limits = motion.rotationLimits
    rotation_data = {
        "min": rot_limits.minimumValue,
        "max": rot_limits.maximumValue,
        "rest": rot_limits.restValue
    }
    
    # 提取滑动部分
    slide_limits = motion.slideLimits
    slide_data = {
        "min": slide_limits.minimumValue * 0.01,  # 转换为米
        "max": slide_limits.maximumValue * 0.01,
        "rest": slide_limits.restValue * 0.01
    }
    
    return {
        "type": "cylindrical",
        "origin": list(motion.origin.asArray()),
        "axis": list(motion.zAxis.asArray()),
        "rotation": rotation_data,
        "slide": slide_data,
        # MuJoCo需要分解为两个关节
        "mujoco_joints": [
            {
                "type": "hinge",
                "pos": motion.origin.asArray(),
                "axis": motion.zAxis.asArray(),
                "range": [rotation_data["min"], rotation_data["max"]],
                "pos0": rotation_data["rest"]
            },
            {
                "type": "slide",
                "pos": motion.origin.asArray(),
                "axis": motion.zAxis.asArray(),
                "range": [slide_data["min"], slide_data["max"]],
                "pos0": slide_data["rest"]
            }
        ]
    }
```

### 2. 球关节

#### `adsk.fusion.BallJointMotion`
```python
# 球关节 - 3个旋转自由度
motion = joint.jointMotion

# 球关节特有属性
motion.rotationLimits                # 旋转限制（如果有）
motion.swingLimits                   # 摆动限制
motion.twistLimits                   # 扭转限制
```

#### 球关节数据提取
```python
def extract_ball_joint_data(joint):
    """提取球关节数据"""
    motion = joint.jointMotion
    
    return {
        "type": "ball",
        "origin": list(motion.origin.asArray()),
        # 球关节通常没有限制，但可以检查
        "has_limits": hasattr(motion, 'swingLimits'),
        "swing_limits": None,
        "twist_limits": None
    }
    
    # 如果有摆动限制
    if hasattr(motion, 'swingLimits') and motion.swingLimits:
        swing_limits = motion.swingLimits
        return {
            "type": "ball",
            "origin": list(motion.origin.asArray()),
            "swing_limits": {
                "cone_angle": swing_limits.coneAngle,
                "has_swing_limits": True
            }
        }
```

### 3. 平面关节

#### `adsk.fusion.PlanarJointMotion`
```python
# 平面关节 - 2个平移+1个旋转
motion = joint.jointMotion

# 平面关节特有属性
motion.slideLimitsX                  # X方向滑动限制
motion.slideLimitsY                  # Y方向滑动限制
motion.rotationLimits                # 旋转限制
```

#### 平面关节数据提取
```python
def extract_planar_joint_data(joint):
    """提取平面关节数据"""
    motion = joint.jointMotion
    
    # 提取X方向滑动
    slide_x = motion.slideLimitsX
    slide_x_data = {
        "min": slide_x.minimumValue * 0.01,
        "max": slide_x.maximumValue * 0.01,
        "rest": slide_x.restValue * 0.01
    }
    
    # 提取Y方向滑动
    slide_y = motion.slideLimitsY
    slide_y_data = {
        "min": slide_y.minimumValue * 0.01,
        "max": slide_y.maximumValue * 0.01,
        "rest": slide_y.restValue * 0.01
    }
    
    # 提取旋转
    rot_limits = motion.rotationLimits
    rotation_data = {
        "min": rot_limits.minimumValue,
        "max": rot_limits.maximumValue,
        "rest": rot_limits.restValue
    }
    
    return {
        "type": "planar",
        "origin": list(motion.origin.asArray()),
        "slide_x": slide_x_data,
        "slide_y": slide_y_data,
        "rotation": rotation_data,
        # MuJoCo需要分解为三个关节
        "mujoco_joints": [
            {
                "type": "slide",
                "pos": motion.origin.asArray(),
                "axis": [1, 0, 0],  # X轴
                "range": [slide_x_data["min"], slide_x_data["max"]],
                "pos0": slide_x_data["rest"]
            },
            {
                "type": "slide",
                "pos": motion.origin.asArray(),
                "axis": [0, 1, 0],  # Y轴
                "range": [slide_y_data["min"], slide_y_data["max"]],
                "pos0": slide_y_data["rest"]
            },
            {
                "type": "hinge",
                "pos": motion.origin.asArray(),
                "axis": [0, 0, 1],  # Z轴
                "range": [rotation_data["min"], rotation_data["max"]],
                "pos0": rotation_data["rest"]
            }
        ]
    }
```

---

## 🎯 完整关节数据提取器

### 1. 通用关节提取器
```python
def extract_all_joint_data(design):
    """提取所有关节数据"""
    root = design.rootComponent
    
    joints_data = {
        "joint_count": root.allJoints.count,
        "joints": []
    }
    
    for joint in root.allJoints:
        if joint.isSuppressed:
            continue  # 跳过被抑制的关节
            
        motion = joint.jointMotion
        joint_type = motion.jointType
        
        # 基本信息提取
        basic_info = extract_joint_basic_info(joint)
        
        # 根据关节类型提取特定数据
        if joint_type == adsk.fusion.JointTypes.RigidJointType:
            joint_data = {
                **basic_info,
                "type": "rigid",
                "origin": list(motion.origin.asArray())
            }
        elif joint_type == adsk.fusion.JointTypes.RevoluteJointType:
            joint_data = {
                **basic_info,
                **extract_revolute_joint_data(joint)
            }
        elif joint_type == adsk.fusion.JointTypes.SliderJointType:
            joint_data = {
                **basic_info,
                **extract_slider_joint_data(joint)
            }
        elif joint_type == adsk.fusion.JointTypes.CylindricalJointType:
            joint_data = {
                **basic_info,
                **extract_cylindrical_joint_data(joint)
            }
        elif joint_type == adsk.fusion.JointTypes.BallJointType:
            joint_data = {
                **basic_info,
                **extract_ball_joint_data(joint)
            }
        elif joint_type == adsk.fusion.JointTypes.PlanarJointType:
            joint_data = {
                **basic_info,
                **extract_planar_joint_data(joint)
            }
        else:
            joint_data = {
                **basic_info,
                "type": "unknown",
                "joint_type_str": str(joint_type)
            }
        
        joints_data["joints"].append(joint_data)
    
    return joints_data
```

### 2. MuJoCo关节转换器
```python
def convert_joints_to_mujoco(joints_data):
    """将Fusion关节数据转换为MuJoCo格式"""
    mujoco_joints = []
    
    for joint in joints_data["joints"]:
        if joint["type"] == "rigid":
            # 固定关节通常不需要转换为MuJoCo关节
            continue
        elif joint["type"] == "revolute":
            mujoco_joint = map_revolute_to_mujoco(joint)
            mujoco_joint["name"] = joint["name"]
            mujoco_joints.append(mujoco_joint)
        elif joint["type"] == "slider":
            mujoco_joint = map_slider_to_mujoco(joint)
            mujoco_joint["name"] = joint["name"]
            mujoco_joints.append(mujoco_joint)
        elif joint["type"] == "cylindrical":
            # 圆柱关节分解为两个关节
            for i, sub_joint in enumerate(joint["mujoco_joints"]):
                sub_joint["name"] = f"{joint['name']}_{i}"
                mujoco_joints.append(sub_joint)
        elif joint["type"] == "ball":
            # 球关节转换为3个旋转关节
            origin = joint["origin"]
            axes = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            for i, axis in enumerate(axes):
                mujoco_joint = {
                    "type": "hinge",
                    "name": f"{joint['name']}_{i}",
                    "pos": origin,
                    "axis": axis,
                    "range": [-3.14159, 3.14159],  # ±180度
                    "pos0": 0
                }
                mujoco_joints.append(mujoco_joint)
        elif joint["type"] == "planar":
            # 平面关节分解为三个关节
            for sub_joint in joint["mujoco_joints"]:
                sub_joint["name"] = f"{joint['name']}_{sub_joint['type']}"
                mujoco_joints.append(sub_joint)
    
    return mujoco_joints
```

---

## 📊 关系图和装配树

### 1. 装配关系提取
```python
def extract_assembly_hierarchy(design):
    """提取装配层次结构"""
    root = design.rootComponent
    
    hierarchy = {
        "root": root.name,
        "components": {},
        "joints": [],
        "relationships": []
    }
    
    # 提取组件层次
    for component in root.allComponents:
        component_info = {
            "name": component.name,
            "parent": None,
            "children": [],
            "joints": []
        }
        hierarchy["components"][component.name] = component_info
    
    # 提取关节关系
    for joint in root.allJoints:
        if joint.isSuppressed:
            continue
            
        joint_info = {
            "name": joint.name,
            "component_one": joint.componentOne.name,
            "component_two": joint.componentTwo.name,
            "type": str(joint.jointMotion.jointType)
        }
        
        hierarchy["joints"].append(joint_info)
        
        # 建立父子关系（简化版）
        comp_one = joint.componentOne.name
        comp_two = joint.componentTwo.name
        
        # 假设第一个组件是父组件
        if comp_two in hierarchy["components"]:
            hierarchy["components"][comp_two]["parent"] = comp_one
        if comp_one in hierarchy["components"] and comp_two not in hierarchy["components"][comp_one]["children"]:
            hierarchy["components"][comp_one]["children"].append(comp_two)
    
    return hierarchy
```

### 2. 关节依赖图
```python
def build_joint_dependency_graph(joints_data):
    """构建关节依赖图"""
    graph = {
        "nodes": [],
        "edges": []
    }
    
    # 添加节点（组件）
    components = set()
    for joint in joints_data["joints"]:
        components.add(joint["connected_components"]["component_one"])
        components.add(joint["connected_components"]["component_two"])
    
    for comp in components:
        graph["nodes"].append({
            "id": comp,
            "label": comp
        })
    
    # 添加边（关节）
    for joint in joints_data["joints"]:
        graph["edges"].append({
            "source": joint["connected_components"]["component_one"],
            "target": joint["connected_components"]["component_two"],
            "label": joint["name"],
            "type": joint["type"]
        })
    
    return graph
```

---

## 📚 使用建议

### 1. 关节类型选择建议
- **简单旋转**: 使用`RevoluteJointType`
- **线性运动**: 使用`SliderJointType`
- **旋转+平移**: 使用`CylindricalJointType`
- **多轴旋转**: 使用`BallJointType`
- **平面运动**: 使用`PlanarJointType`

### 2. 限制设置建议
- **旋转限制**: 使用弧度值，考虑机械限位
- **滑动限制**: 使用厘米值，注意转换为米
- **静止位置**: 设置为自然状态或中间位置

### 3. MuJoCo集成建议
- 复杂关节需要分解为多个简单关节
- 注意坐标系转换
- 考虑关节的默认位置和方向

---

## 📅 文档信息

- **创建日期**: 2025-09-04
- **目标**: MuJoCo关节约束和运动限制提取
- **覆盖范围**: 所有关节类型、限制设置、MuJoCo映射
- **状态**: 完整API已整理，代码示例已提供