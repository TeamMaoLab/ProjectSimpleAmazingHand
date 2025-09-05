# Fusion 360 物理属性与几何数据API详解

## 🎯 目标：精确提取MuJoCo所需的物理和几何参数

---

## 📊 物理属性提取API

### 1. 核心物理属性类

#### `adsk.fusion.PhysicalProperties`
```python
# 物理属性计算器 - 获取真实物理参数
physical = component.physicalProperties

# 关键属性和方法
physical.mass                          # 质量 (kg)
physical.volume                        # 体积 (m³)
physical.density                       # 密度 (kg/m³)
physical.centerOfMass                  # 质心位置 (Point3D)
physical.surfaceArea                   # 表面积 (m²)

# 惯性张量计算
physical.getXYZMomentsOfInertia()      # 返回Vector3D (Ixx, Iyy, Izz)
physical.getPrincipalAxes()            # 主轴方向
physical.getPrincipalMomentsOfInertia() # 主惯性矩

# 重新计算物理属性（当设计变更时）
physical.calculate()                   # 强制重新计算
```

#### 物理属性提取示例
```python
def extract_complete_physics(component):
    """提取完整物理属性"""
    physical = component.physicalProperties
    
    # 确保物理属性已计算
    physical.calculate()
    
    physics_data = {
        "mass": physical.mass,  # kg
        "volume": physical.volume,  # m³
        "density": physical.density,  # kg/m³
        "surface_area": physical.surfaceArea,  # m²
        
        # 质心位置
        "center_of_mass": {
            "x": physical.centerOfMass.x,
            "y": physical.centerOfMass.y,
            "z": physical.centerOfMass.z
        },
        
        # 惯性张量
        "inertia_tensor": {
            "Ixx": physical.getXYZMomentsOfInertia().x,
            "Iyy": physical.getXYZMomentsOfInertia().y,
            "Izz": physical.getXYZMomentsOfInertia().z
        },
        
        # 主惯性矩
        "principal_inertia": {
            "I1": physical.getPrincipalMomentsOfInertia().x,
            "I2": physical.getPrincipalMomentsOfInertia().y,
            "I3": physical.getPrincipalMomentsOfInertia().z
        }
    }
    
    return physics_data
```

### 2. 材料属性API

#### `adsk.fusion.Material`
```python
# 材料属性 - 定义物理行为
material = component.material

# 关键材料属性
material.name                          # 材料名称
material.density                       # 密度 (kg/m³)
material.elasticModulus                # 弹性模量 (Pa)
material.poissonRatio                  # 泊松比
material.yieldStrength                 # 屈服强度 (Pa)
material.ultimateTensileStrength       # 抗拉强度 (Pa)
material.thermalConductivity           # 热导率 (W/m·K)
material.specificHeat                  # 比热容 (J/kg·K)

# 材料外观属性
material.opacity                       # 不透明度
material.color                         # 颜色
material.reflectivity                  # 反射率
```

#### 材料属性提取示例
```python
def extract_material_properties(component):
    """提取材料属性"""
    material = component.material
    
    material_data = {
        "name": material.name,
        "physical_properties": {
            "density": material.density,  # kg/m³
            "elastic_modulus": material.elasticModulus,  # Pa
            "poisson_ratio": material.poissonRatio,
            "yield_strength": material.yieldStrength,  # Pa
            "ultimate_tensile_strength": material.ultimateTensileStrength  # Pa
        },
        "thermal_properties": {
            "thermal_conductivity": material.thermalConductivity,  # W/m·K
            "specific_heat": material.specificHeat  # J/kg·K
        },
        "appearance": {
            "opacity": material.opacity,
            "color": {
                "r": material.color.red,
                "g": material.color.green,
                "b": material.color.blue
            }
        }
    }
    
    return material_data
```

---

## 📐 几何数据提取API

### 1. BRep实体几何

#### `adsk.fusion.BRepBody`
```python
# BRep实体 - 几何形状的基础
body = component.bRepBodies.item(0)

# 基本几何属性
body.name                             # 实体名称
body.isSolid                          # 是否为实体
body.isSurface                        # 是否为曲面
body.isMesh                           # 是否为网格
body.volume                           # 体积 (cm³)
body.surfaceArea                      # 表面积 (cm²)
body.centroid                         # 几何中心 (Point3D)

# 边界框 - 碰撞检测基础
bounding_box = body.boundingBox
bounding_box.minPoint                 # 最小点
bounding_box.maxPoint                 # 最大点
bounding_box.diagonal                 # 对角线长度

# 几何元素集合
body.vertices                         # 顶点集合
body.edges                            # 边集合
body.faces                            # 面集合
body.shells                           # 壳集合
body.loops                            # 环集合
```

#### BRep实体数据提取示例
```python
def extract_brep_body_data(body):
    """提取BRep实体数据"""
    # 单位转换：cm³ → m³, cm² → m²
    volume_m3 = body.volume * 1e-6
    surface_area_m2 = body.surfaceArea * 1e-4
    
    body_data = {
        "name": body.name,
        "type": "solid" if body.isSolid else "surface" if body.isSurface else "mesh",
        "geometry": {
            "volume": volume_m3,  # m³
            "surface_area": surface_area_m2,  # m²
            "centroid": {
                "x": body.centroid.x,
                "y": body.centroid.y,
                "z": body.centroid.z
            }
        },
        "bounding_box": {
            "min_point": {
                "x": body.boundingBox.minPoint.x,
                "y": body.boundingBox.minPoint.y,
                "z": body.boundingBox.minPoint.z
            },
            "max_point": {
                "x": body.boundingBox.maxPoint.x,
                "y": body.boundingBox.maxPoint.y,
                "z": body.boundingBox.maxPoint.z
            },
            "size": {
                "x": body.boundingBox.maxPoint.x - body.boundingBox.minPoint.x,
                "y": body.boundingBox.maxPoint.y - body.boundingBox.minPoint.y,
                "z": body.boundingBox.maxPoint.z - body.boundingBox.minPoint.z
            }
        },
        "topology": {
            "vertex_count": body.vertices.count,
            "edge_count": body.edges.count,
            "face_count": body.faces.count,
            "shell_count": body.shells.count
        }
    }
    
    return body_data
```

### 2. 详细几何元素

#### `adsk.fusion.BRepVertex`
```python
# 顶点 - 几何的基本点
vertex = body.vertices.item(0)

# 顶点属性
vertex.point                          # 3D点坐标
vertex.geometry                       # 底层几何
vertex.edges                          # 连接的边
vertex.faces                          # 连接的面
```

#### `adsk.fusion.BRepEdge`
```python
# 边 - 连接顶点的线
edge = body.edges.item(0)

# 边属性
edge.startVertex                      # 起始顶点
edge.endVertex                        # 结束顶点
edge.length                           # 长度
edge.isClosed                         # 是否为闭合边
edge.curve                            # 底层曲线
edge.faces                            # 相邻面
edge.evaluator                        # 几何计算器

# 边类型判断
edge.isLine                           # 是否为直线
edge.isCircle                         # 是否为圆
edge.isEllipse                        # 是否为椭圆
edge.isSpline                         # 是否为样条
```

#### `adsk.fusion.BRepFace`
```python
# 面 - 几何表面
face = body.faces.item(0)

# 面属性
face.geometry                         # 底层曲面
face.normal                           # 面法向量
face.area                             # 面积
face.perimeter                        # 周长
face.isPlanar                         # 是否为平面
face.edges                            # 边界边
face.vertices                         # 顶点
face.loops                            # 环
face.evaluator                        # 几何计算器

# 面类型判断
face.isPlane                          # 是否为平面
face.isCylinder                       # 是否为圆柱面
face.isCone                           # 是否为圆锥面
face.isSphere                         # 是否为球面
face.isTorus                          # 是否为圆环面
```

#### 详细几何数据提取示例
```python
def extract_detailed_geometry(body):
    """提取详细几何数据"""
    geometry_data = {
        "vertices": [],
        "edges": [],
        "faces": []
    }
    
    # 提取顶点数据
    for vertex in body.vertices:
        geometry_data["vertices"].append({
            "id": vertex.tempId,
            "point": {
                "x": vertex.point.x,
                "y": vertex.point.y,
                "z": vertex.point.z
            }
        })
    
    # 提取边数据
    for edge in body.edges:
        geometry_data["edges"].append({
            "id": edge.tempId,
            "length": edge.length,
            "type": "line" if edge.isLine else "circle" if edge.isCircle else "curve",
            "start_vertex": edge.startVertex.tempId,
            "end_vertex": edge.endVertex.tempId
        })
    
    # 提取面数据
    for face in body.faces:
        # 获取面法向量
        normal = face.evaluator.getNormalAtPoint(face.pointOnFace)
        
        geometry_data["faces"].append({
            "id": face.tempId,
            "area": face.area,
            "type": "plane" if face.isPlanar else "cylinder" if face.isCylinder else "surface",
            "normal": {
                "x": normal.x,
                "y": normal.y,
                "z": normal.z
            },
            "edge_count": face.edges.count
        })
    
    return geometry_data
```

---

## 🔄 几何计算器API

### 1. 几何计算器基础

#### `adsk.core.SurfaceEvaluator`
```python
# 几何计算器 - 用于精确几何计算
evaluator = face.evaluator

# 关键计算方法
evaluator.getNormalAtPoint(point)     # 获取点处的法向量
evaluator.getCurvatureAtPoint(point)   # 获取点处的曲率
evaluator.getArea()                    # 计算面积
evaluator.getPerimeter()               # 计算周长
evaluator.isPointOnFace(point)         # 判断点是否在面上
evaluator.getClosestPointTo(point)     # 获取最近点
```

#### 几何计算示例
```python
def analyze_face_geometry(face):
    """分析面几何"""
    evaluator = face.evaluator
    
    # 获取面中心点
    point_on_face = face.pointOnFace
    
    # 计算法向量
    normal = evaluator.getNormalAtPoint(point_on_face)
    
    # 计算曲率
    curvature = evaluator.getCurvatureAtPoint(point_on_face)
    
    # 计算面积和周长
    area = evaluator.getArea()
    perimeter = evaluator.getPerimeter()
    
    return {
        "center_point": {
            "x": point_on_face.x,
            "y": point_on_face.y,
            "z": point_on_face.z
        },
        "normal": {
            "x": normal.x,
            "y": normal.y,
            "z": normal.z
        },
        "curvature": {
            "mean": curvature.meanCurvature,
            "gaussian": curvature.gaussianCurvature,
            "principal": {
                "min": curvature.minPrincipalCurvature,
                "max": curvature.maxPrincipalCurvature
            }
        },
        "area": area,
        "perimeter": perimeter
    }
```

---

## 🎯 完整物理几何数据提取器

### 1. 综合数据提取器
```python
def extract_complete_physics_geometry(design):
    """提取完整的物理和几何数据"""
    root = design.rootComponent
    
    complete_data = {
        "design_info": {
            "name": design.name,
            "component_count": root.allComponents.count,
            "body_count": sum(comp.bRepBodies.count for comp in root.allComponents)
        },
        "components": {}
    }
    
    # 遍历所有组件
    for component in root.allComponents:
        component_data = {
            "physical_properties": extract_complete_physics(component),
            "material_properties": extract_material_properties(component),
            "bodies": []
        }
        
        # 遍历所有实体
        for body in component.bRepBodies:
            body_data = extract_brep_body_data(body)
            body_data["detailed_geometry"] = extract_detailed_geometry(body)
            component_data["bodies"].append(body_data)
        
        complete_data["components"][component.name] = component_data
    
    return complete_data
```

### 2. MuJoCo专用数据提取器
```python
def extract_mujoco_specific_data(design):
    """提取MuJoCo特定的数据"""
    root = design.rootComponent
    
    mujoco_data = {
        "worldbody": {
            "name": "world",
            "pos": [0, 0, 0],
            "quat": [1, 0, 0, 0]
        },
        "bodies": [],
        "joints": [],
        "geoms": []
    }
    
    # 提取组件作为MuJoCo body
    for component in root.allComponents:
        physical = component.physicalProperties
        
        # 创建MuJoCo body
        mujoco_body = {
            "name": component.name,
            "pos": list(physical.centerOfMass.asArray()),
            "mass": physical.mass,
            "inertia": {
                "fullinertia": [
                    physical.getXYZMomentsOfInertia().x,
                    physical.getXYZMomentsOfInertia().y,
                    physical.getXYZMomentsOfInertia().z,
                    0, 0, 0  # 假设惯性积为0
                ]
            }
        }
        
        mujoco_data["bodies"].append(mujoco_body)
        
        # 提取几何体作为MuJoCo geom
        for body in component.bRepBodies:
            bbox = body.boundingBox
            
            # 使用边界框创建简化几何
            mujoco_geom = {
                "name": f"{component.name}_{body.name}",
                "type": "box",
                "size": [
                    (bbox.maxPoint.x - bbox.minPoint.x) / 2,
                    (bbox.maxPoint.y - bbox.minPoint.y) / 2,
                    (bbox.maxPoint.z - bbox.minPoint.z) / 2
                ],
                "pos": [
                    (bbox.maxPoint.x + bbox.minPoint.x) / 2,
                    (bbox.maxPoint.y + bbox.minPoint.y) / 2,
                    (bbox.maxPoint.z + bbox.minPoint.z) / 2
                ],
                "body": component.name
            }
            
            mujoco_data["geoms"].append(mujoco_geom)
    
    return mujoco_data
```

---

## 📚 使用建议

### 1. 单位转换注意事项
- **Fusion 360内部单位**: cm, rad
- **MuJoCo单位**: m, rad
- **转换公式**: 
  - 长度: `m = cm * 0.01`
  - 面积: `m² = cm² * 0.0001`
  - 体积: `m³ = cm³ * 0.000001`

### 2. 性能优化建议
- 对于大型装配，考虑分批提取数据
- 使用`adsk.doEvents()`保持UI响应
- 缓存计算结果避免重复计算

### 3. 数据验证
- 检查物理属性的合理性
- 验证几何体的封闭性
- 确认惯性张量的正定性

---

## 📅 文档信息

- **创建日期**: 2025-09-04
- **目标**: MuJoCo物理和几何参数提取
- **覆盖范围**: 物理属性、材料属性、几何数据
- **状态**: 完整API已整理，代码示例已提供