#!/usr/bin/env python3
"""
手动验证hang组件的旋转矩阵转换
"""

import numpy as np
import sys
import os

# 添加脚本路径到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_converter import matrix_to_quaternion

def analyze_hang_matrix():
    """分析hang组件的旋转矩阵"""
    
    print("🔍 分析hang组件的旋转矩阵")
    print("=" * 60)
    
    # 从JSON中提取的hang组件矩阵（列主序）
    matrix_hang = [
        5.551115123125783e-17, 0.0, -0.9999999999999996, 6.000000089406967,
        0.0, 1.0, 0.0, -1.12,
        0.9999999999999996, 0.0, 5.551115123125783e-17, 0.0,
        0.0, 0.0, 0.0, 1.0
    ]
    
    print("📋 原始矩阵（列主序）:")
    for i in range(0, 16, 4):
        row = matrix_hang[i:i+4]
        print(f"   [{row[0]:12.10f}, {row[1]:12.10f}, {row[2]:12.10f}, {row[3]:12.10f}]")
    
    # 提取3x3旋转子矩阵（列主序）
    R_col_major = np.array([
        [matrix_hang[0], matrix_hang[4], matrix_hang[8]],
        [matrix_hang[1], matrix_hang[5], matrix_hang[9]],
        [matrix_hang[2], matrix_hang[6], matrix_hang[10]]
    ])
    
    print(f"\n📋 提取的3x3旋转矩阵（列主序）:")
    print(f"   [{R_col_major[0,0]:12.10f}, {R_col_major[0,1]:12.10f}, {R_col_major[0,2]:12.10f}]")
    print(f"   [{R_col_major[1,0]:12.10f}, {R_col_major[1,1]:12.10f}, {R_col_major[1,2]:12.10f}]")
    print(f"   [{R_col_major[2,0]:12.10f}, {R_col_major[2,1]:12.10f}, {R_col_major[2,2]:12.10f}]")
    
    # 转换为四元数
    quaternion = matrix_to_quaternion(R_col_major)
    print(f"\n📋 转换后的四元数: {quaternion}")
    
    # 分析这个旋转矩阵代表什么
    print(f"\n🔍 旋转分析:")
    print(f"   矩阵行列式: {np.linalg.det(R_col_major):.10f}")
    print(f"   矩阵迹: {np.trace(R_col_major):.10f}")
    
    # 检查是否为绕Y轴的旋转
    # 绕Y轴旋转theta的矩阵形式：
    # [cos(theta), 0, sin(theta)]
    # [0, 1, 0]
    # [-sin(theta), 0, cos(theta)]
    
    cos_theta = R_col_major[0, 0]
    sin_theta = -R_col_major[2, 0]  # 注意符号
    
    theta = np.arctan2(sin_theta, cos_theta)
    theta_deg = np.degrees(theta)
    
    print(f"   推断的绕Y轴旋转角度: {theta_deg:.2f} 度")
    
    # 检查与JSON中直接给出的四元数是否一致
    json_quaternion = [0.7071067811865477, 0.0, 0.7071067811865472, 0.0]
    print(f"\n📋 JSON中直接给出的四元数: {json_quaternion}")
    
    # 计算两个四元数的差异
    diff = np.array(quaternion) - np.array(json_quaternion)
    print(f"   与JSON四元数的差异: {diff}")
    print(f"   最大差异: {np.max(np.abs(diff)):.2e}")
    
    # 检查四元数是否表示相同的旋转（考虑四元数的双覆盖性）
    # 如果 q 和 -q 表示相同的旋转
    neg_diff = np.array(quaternion) + np.array(json_quaternion)
    print(f"   与负JSON四元数的差异: {neg_diff}")
    print(f"   最大负差异: {np.max(np.abs(neg_diff)):.2e}")
    
    return quaternion, json_quaternion

if __name__ == "__main__":
    analyze_hang_matrix()