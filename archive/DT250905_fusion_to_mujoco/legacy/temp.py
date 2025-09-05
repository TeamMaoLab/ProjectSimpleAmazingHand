import numpy as np
from dataclasses import dataclass

@dataclass
class Pose:
    pos: np.ndarray  # shape (3,)
    quat: np.ndarray # (w,x,y,z)

def flat16_to_mat4(flat16):
    """把长度16的列表按行主序变成 4x4 矩阵"""
    M = np.array(flat16, dtype=float).reshape(4,4)
    return M

def mat4_to_pos_quat(T):
    """从 4x4 变换矩阵得到 (pos[m], quat)"""
    R = T[:3,:3]
    t = T[:3, 3]
    # 旋转矩阵转四元数 (w,x,y,z)
    # 用稳定算法
    tr = np.trace(R)
    if tr > 0:
        S = np.sqrt(tr + 1.0) * 2
        w = 0.25 * S
        x = (R[2,1] - R[1,2]) / S
        y = (R[0,2] - R[2,0]) / S
        z = (R[1,0] - R[0,1]) / S
    else:
        # 找最大对角元素
        if R[0,0] > R[1,1] and R[0,0] > R[2,2]:
            S = np.sqrt(1.0 + R[0,0] - R[1,1] - R[2,2]) * 2
            w = (R[2,1] - R[1,2]) / S
            x = 0.25 * S
            y = (R[0,1] + R[1,0]) / S
            z = (R[0,2] + R[2,0]) / S
        elif R[1,1] > R[2,2]:
            S = np.sqrt(1.0 + R[1,1] - R[0,0] - R[2,2]) * 2
            w = (R[0,2] - R[2,0]) / S
            x = (R[0,1] + R[1,0]) / S
            y = 0.25 * S
            z = (R[1,2] + R[2,1]) / S
        else:
            S = np.sqrt(1.0 + R[2,2] - R[0,0] - R[1,1]) * 2
            w = (R[1,0] - R[0,1]) / S
            x = (R[0,2] + R[2,0]) / S
            y = (R[1,2] + R[2,1]) / S
            z = 0.25 * S
    quat = np.array([w,x,y,z], dtype=float)
    # 归一化（防数值误差）
    quat /= np.linalg.norm(quat)
    return Pose(pos=t, quat=quat)

def mm_to_m(vec3):
    return np.array(vec3, dtype=float) / 1000.0

def compose_relative(parent_T, child_T):
    """给父、子 4x4（世界），求子相对父 4x4"""
    T_rel = np.linalg.inv(parent_T) @ child_T
    return T_rel

# ====== 示例使用 ======
current_matrix = [
  1.0, 0.0, 0.0, 10.0,
  0.0, 1.0, 0.0, -0.4,
  0.0, 0.0, 1.0, 0.0,
  0.0, 0.0, 0.0, 1.0
]

T = flat16_to_mat4(current_matrix)

# 1) 直接得到世界坐标下的 pos/quat (先转米)
pose_world = mat4_to_pos_quat(T)
pos_m = mm_to_m(pose_world.pos)
quat = pose_world.quat
print("世界 pos(m):", pos_m)
print("quat (w x y z):", quat)

# 2) 如果还有第二个零件 child_matrix
child_matrix = [
  1,0,0,16.0,
  0,1,0,-0.92,
  0,0,1,0.0,
  0,0,0,1
]
parent_T = T
child_T  = flat16_to_mat4(child_matrix)
T_rel = compose_relative(parent_T, child_T)
rel_pose = mat4_to_pos_quat(T_rel)
rel_pos_m = mm_to_m(rel_pose.pos)
print("子相对父 pos(m):", rel_pos_m)
print("子相对父 quat:", rel_pose.quat)

# 3) 结果可直接写入 MJCF:
# <body name="child" pos="{} {} {}" quat="{} {} {} {}"></body>
