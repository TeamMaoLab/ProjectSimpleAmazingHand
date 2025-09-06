#!/usr/bin/env python3
"""
测试旋转矩阵到四元数的转换
验证修复后的旋转方向是否正确
"""

import numpy as np
import sys
import os

# 添加脚本路径到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_converter import matrix_to_quaternion

def test_rotation_conversions():
    """测试各种旋转矩阵的转换"""
    
    print("🧪 测试旋转矩阵到四元数的转换")
    print("=" * 60)
    
    # 测试1: 单位矩阵（无旋转）
    print("\n📋 测试1: 单位矩阵（无旋转）")
    R_identity = np.array([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]
    ])
    q_identity = matrix_to_quaternion(R_identity)
    print(f"   旋转矩阵:\n{R_identity}")
    print(f"   四元数: {q_identity}")
    print(f"   期望: [1, 0, 0, 0]")
    
    # 测试2: 绕Z轴旋转90度
    print("\n📋 测试2: 绕Z轴旋转90度")
    angle = np.pi / 2  # 90度
    R_z90 = np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle), np.cos(angle), 0],
        [0, 0, 1]
    ])
    q_z90 = matrix_to_quaternion(R_z90)
    print(f"   旋转矩阵:\n{R_z90}")
    print(f"   四元数: {q_z90}")
    print(f"   期望约: [0.707, 0, 0, 0.707]")
    
    # 测试3: 绕X轴旋转90度
    print("\n📋 测试3: 绕X轴旋转90度")
    R_x90 = np.array([
        [1, 0, 0],
        [0, np.cos(angle), -np.sin(angle)],
        [0, np.sin(angle), np.cos(angle)]
    ])
    q_x90 = matrix_to_quaternion(R_x90)
    print(f"   旋转矩阵:\n{R_x90}")
    print(f"   四元数: {q_x90}")
    print(f"   期望约: [0.707, 0.707, 0, 0]")
    
    # 测试4: 绕Y轴旋转90度
    print("\n📋 测试4: 绕Y轴旋转90度")
    R_y90 = np.array([
        [np.cos(angle), 0, np.sin(angle)],
        [0, 1, 0],
        [-np.sin(angle), 0, np.cos(angle)]
    ])
    q_y90 = matrix_to_quaternion(R_y90)
    print(f"   旋转矩阵:\n{R_y90}")
    print(f"   四元数: {q_y90}")
    print(f"   期望约: [0.707, 0, 0.707, 0]")
    
    # 测试5: 模拟Fusion 360的4x4矩阵提取
    print("\n📋 测试5: 模拟Fusion 360的4x4矩阵提取")
    # 模拟一个绕Z轴旋转45度的4x4矩阵
    angle_45 = np.pi / 4
    cos_45 = np.cos(angle_45)
    sin_45 = np.sin(angle_45)
    
    # Fusion 360格式的4x4矩阵（行主序）
    matrix_4x4 = [
        cos_45, -sin_45, 0, 10,    # 第一行
        sin_45, cos_45, 0, 20,     # 第二行
        0, 0, 1, 30,               # 第三行
        0, 0, 0, 1                # 第四行
    ]
    
    # 提取3x3旋转子矩阵（行主序）
    R_extracted = np.array([
        [matrix_4x4[0], matrix_4x4[1], matrix_4x4[2]],
        [matrix_4x4[4], matrix_4x4[5], matrix_4x4[6]],
        [matrix_4x4[8], matrix_4x4[9], matrix_4x4[10]]
    ])
    
    q_extracted = matrix_to_quaternion(R_extracted)
    print(f"   4x4矩阵: {matrix_4x4}")
    print(f"   提取的3x3矩阵:\n{R_extracted}")
    print(f"   四元数: {q_extracted}")
    print(f"   期望约: [0.924, 0, 0, 0.383]")
    
    # 验证四元数是否为单位四元数
    print("\n🔍 验证四元数归一化:")
    test_quaternions = [q_identity, q_z90, q_x90, q_y90, q_extracted]
    for i, q in enumerate(test_quaternions):
        norm = np.linalg.norm(q)
        print(f"   测试{i+1}: 四元数范数 = {norm:.6f} {'✅' if abs(norm - 1.0) < 1e-6 else '❌'}")
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    test_rotation_conversions()