#!/usr/bin/env python3
"""
测试-90度绕Y轴旋转的矩阵和四元数
"""

import numpy as np
import sys
import os

# 添加脚本路径到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_converter import matrix_to_quaternion

def test_negative_90_y_rotation():
    """测试绕Y轴-90度旋转"""
    
    print("🧪 测试绕Y轴-90度旋转")
    print("=" * 60)
    
    # 绕Y轴-90度旋转的矩阵
    angle = -np.pi / 2  # -90度
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)
    
    # 绕Y轴旋转的矩阵（列主序存储的4x4矩阵）
    # [cos(theta), 0, sin(theta), 0]
    # [0, 1, 0, 0]
    # [-sin(theta), 0, cos(theta), 0]
    # [0, 0, 0, 1]
    
    R_neg_90_y = np.array([
        [cos_a, 0, sin_a],
        [0, 1, 0],
        [-sin_a, 0, cos_a]
    ])
    
    print(f"📋 绕Y轴-90度旋转的3x3矩阵:")
    print(f"   [{R_neg_90_y[0,0]:12.10f}, {R_neg_90_y[0,1]:12.10f}, {R_neg_90_y[0,2]:12.10f}]")
    print(f"   [{R_neg_90_y[1,0]:12.10f}, {R_neg_90_y[1,1]:12.10f}, {R_neg_90_y[1,2]:12.10f}]")
    print(f"   [{R_neg_90_y[2,0]:12.10f}, {R_neg_90_y[2,1]:12.10f}, {R_neg_90_y[2,2]:12.10f}]")
    
    # 转换为四元数
    q_neg_90_y = matrix_to_quaternion(R_neg_90_y)
    print(f"\n📋 转换后的四元数: {q_neg_90_y}")
    
    # 对比+90度旋转
    angle_pos = np.pi / 2  # +90度
    cos_pos = np.cos(angle_pos)
    sin_pos = np.sin(angle_pos)
    
    R_pos_90_y = np.array([
        [cos_pos, 0, sin_pos],
        [0, 1, 0],
        [-sin_pos, 0, cos_pos]
    ])
    
    q_pos_90_y = matrix_to_quaternion(R_pos_90_y)
    print(f"\n📋 绕Y轴+90度旋转的四元数: {q_pos_90_y}")
    
    # 分析hang组件的矩阵
    print(f"\n🔍 对比分析:")
    print(f"   -90度四元数: {q_neg_90_y}")
    print(f"   +90度四元数: {q_pos_90_y}")
    print(f"   hang组件四元数: [0.70710678, 0.0, 0.70710678, 0.0]")
    
    # 检查哪个匹配
    hang_quat = np.array([0.70710678, 0.0, 0.70710678, 0.0])
    diff_neg = np.abs(q_neg_90_y - hang_quat)
    diff_pos = np.abs(q_pos_90_y - hang_quat)
    
    print(f"\n📋 差异分析:")
    print(f"   与-90度的最大差异: {np.max(diff_neg):.2e}")
    print(f"   与+90度的最大差异: {np.max(diff_pos):.2e}")
    
    if np.max(diff_neg) < np.max(diff_pos):
        print(f"   ✅ hang组件更接近-90度旋转")
    else:
        print(f"   ✅ hang组件更接近+90度旋转")
    
    # 检查四元数的双覆盖性（q和-q表示相同旋转）
    neg_hang_quat = -hang_quat
    diff_neg_dual = np.abs(q_neg_90_y - neg_hang_quat)
    diff_pos_dual = np.abs(q_pos_90_y - neg_hang_quat)
    
    print(f"\n📋 考虑四元数双覆盖性（q和-q相同）:")
    print(f"   与-90度的最大差异: {np.max(diff_neg_dual):.2e}")
    print(f"   与+90度的最大差异: {np.max(diff_pos_dual):.2e}")
    
    return q_neg_90_y, q_pos_90_y

if __name__ == "__main__":
    test_negative_90_y_rotation()