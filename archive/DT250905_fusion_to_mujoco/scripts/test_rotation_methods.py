#!/usr/bin/env python3
"""
测试不同的旋转转换方法，找到能还原Fusion 360视觉效果的正确方法
"""

import numpy as np
import sys
import os

# 添加脚本路径到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_converter import matrix_to_quaternion

def test_rotation_methods():
    """测试不同的旋转转换方法"""
    
    print("🧪 测试不同的旋转转换方法")
    print("=" * 60)
    
    # hang组件的原始矩阵（从JSON中提取）
    matrix_hang = [
        5.551115123125783e-17, 0.0, -0.9999999999999996, 6.000000089406967,
        0.0, 1.0, 0.0, -1.12,
        0.9999999999999996, 0.0, 5.551115123125783e-17, 0.0,
        0.0, 0.0, 0.0, 1.0
    ]
    
    print("📋 hang组件的原始矩阵:")
    for i in range(0, 16, 4):
        row = matrix_hang[i:i+4]
        print(f"   [{row[0]:12.10f}, {row[1]:12.10f}, {row[2]:12.10f}, {row[3]:12.10f}]")
    
    print(f"\n🔍 方法1: 当前使用的列主序提取")
    # 方法1: 列主序提取（当前使用）
    R1 = np.array([
        [matrix_hang[0], matrix_hang[4], matrix_hang[8]],
        [matrix_hang[1], matrix_hang[5], matrix_hang[9]],
        [matrix_hang[2], matrix_hang[6], matrix_hang[10]]
    ])
    q1 = matrix_to_quaternion(R1)
    print(f"   旋转矩阵:\n{R1}")
    print(f"   四元数: {q1}")
    print(f"   分析: 绕Y轴+90度")
    
    print(f"\n🔍 方法2: 行主序提取")
    # 方法2: 行主序提取
    R2 = np.array([
        [matrix_hang[0], matrix_hang[1], matrix_hang[2]],
        [matrix_hang[4], matrix_hang[5], matrix_hang[6]],
        [matrix_hang[8], matrix_hang[9], matrix_hang[10]]
    ])
    q2 = matrix_to_quaternion(R2)
    print(f"   旋转矩阵:\n{R2}")
    print(f"   四元数: {q2}")
    
    print(f"\n🔍 方法3: 列主序提取 + 矩阵转置")
    # 方法3: 列主序提取 + 矩阵转置
    R3 = np.array([
        [matrix_hang[0], matrix_hang[4], matrix_hang[8]],
        [matrix_hang[1], matrix_hang[5], matrix_hang[9]],
        [matrix_hang[2], matrix_hang[6], matrix_hang[10]]
    ]).T
    q3 = matrix_to_quaternion(R3)
    print(f"   旋转矩阵:\n{R3}")
    print(f"   四元数: {q3}")
    print(f"   分析: 绕Y轴-90度")
    
    print(f"\n🔍 方法4: 行主序提取 + 矩阵转置")
    # 方法4: 行主序提取 + 矩阵转置
    R4 = np.array([
        [matrix_hang[0], matrix_hang[1], matrix_hang[2]],
        [matrix_hang[4], matrix_hang[5], matrix_hang[6]],
        [matrix_hang[8], matrix_hang[9], matrix_hang[10]]
    ]).T
    q4 = matrix_to_quaternion(R4)
    print(f"   旋转矩阵:\n{R4}")
    print(f"   四元数: {q4}")
    
    print(f"\n🔍 方法5: 使用四元数共轭（反转旋转方向）")
    # 方法5: 使用四元数共轭（反转旋转方向）
    q5 = np.array([q1[0], -q1[1], -q1[2], -q1[3]])
    print(f"   原始四元数: {q1}")
    print(f"   共轭四元数: {q5}")
    print(f"   分析: 反转旋转方向")
    
    print(f"\n🔍 方法6: 使用负四元数（双覆盖性）")
    # 方法6: 使用负四元数（双覆盖性）
    q6 = -q1
    print(f"   原始四元数: {q1}")
    print(f"   负四元数: {q6}")
    print(f"   分析: 相同旋转，不同表示")
    
    print(f"\n📋 总结:")
    print(f"   方法1 (当前): {q1} -> 绕Y轴+90度")
    print(f"   方法2 (行主序): {q2}")
    print(f"   方法3 (列主序+转置): {q3} -> 绕Y轴-90度")
    print(f"   方法4 (行主序+转置): {q4}")
    print(f"   方法5 (共轭): {q5} -> 绕Y轴-90度")
    print(f"   方法6 (负四元数): {q6} -> 绕Y轴+90度")
    
    print(f"\n💡 建议:")
    print(f"   如果你在Fusion 360中看到的是-90度效果，但计算得到+90度，")
    print(f"   可以尝试方法3或方法5来反转旋转方向。")
    
    return {
        "method1": q1,
        "method3": q3,
        "method5": q5
    }

if __name__ == "__main__":
    test_rotation_methods()