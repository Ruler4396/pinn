# -*- coding: utf-8 -*-
"""
Y型分岔道几何生成模块

重新设计的Y型流道几何：
- 主通道：水平方向，从左到右
- 分岔：在主通道末端分成两个对称分支
- 上分支：向上偏转一定角度
- 下分支：向下偏转相同角度
- 分支端口：水平（垂直于分支方向）

形状示意：
         OUTLET1
           ↑
           │ (水平端口)
          ╱
         ╱
        ╱  ← 内壁区域
       ╱
      ┼───────────── INLET
     ╱
    ╱
   ╱
  ↓ (水平端口)
OUTLET2

边界条件：
1. INLET（绿色）：主通道左端 - 速度入口
2. OUTLET1（蓝色）：上分支末端 - 压力出口（水平端口）
3. OUTLET2（紫色）：下分支末端 - 压力出口（水平端口）
4. WALL（红色）：其余所有边界 - 无滑移
"""

import numpy as np
from typing import Dict, List
from base_geometry import MicrochannelGeometry, BoundaryType


class YJunctionGeometry(MicrochannelGeometry):
    """
    Y型分岔道几何生成类

    标准Y型流道：主通道水平，分成两个对称分支
    分支端口水平（垂直于分支方向）
    """

    def __init__(
        self,
        L_main: float = 5.0,       # 主通道长度 (mm)
        L_branch: float = 5.0,      # 分支通道长度 (mm)
        W: float = 0.2,             # 通道宽度 (mm)
        branch_angle: float = 45.0, # 分支角度（度），每侧
        units: str = 'mm'
    ):
        """
        Args:
            L_main: 主通道长度，从入口到分岔点中心 (mm)
            L_branch: 分支通道长度，从主通道末端沿分支方向到出口 (mm)
            W: 通道宽度 (mm)
            branch_angle: 每个分支与主通道的夹角（度）
            units: 长度单位
        """
        super().__init__(units)

        self.W = W
        self.L_main = L_main
        self.L_branch = L_branch
        self.branch_angle = branch_angle  # 每侧角度，度
        self.half_W = W / 2

        # 转换为弧度
        self.angle_rad = np.radians(branch_angle)
        self.total_angle = branch_angle * 2

        self.geometry_params = {
            'type': 'Y-junction',
            'L_main': L_main,
            'L_branch': L_branch,
            'W': W,
            'branch_angle': branch_angle,
            'total_angle': self.total_angle,
            'units': units
        }

    def generate(self) -> Dict:
        """
        生成Y型分岔道几何

        坐标系统：
        - 主通道沿X轴，从x=0到x=L_main
        - 主通道中心线在y=0
        - 分岔点中心在 (L_main, 0)
        - 上分支向上偏转，下分支向下偏转
        - 分支端口水平（垂直于分支方向）

        Returns:
            包含几何数据的字典
        """
        W = self.W
        hw = self.half_W
        Lm = self.L_main
        Lb = self.L_branch
        theta = self.angle_rad

        # ===== 计算方向向量 =====
        # 上分支方向（向上偏转θ角）
        upper_dir = np.array([np.cos(theta), np.sin(theta)])
        # 下分支方向（向下偏转θ角）
        lower_dir = np.array([np.cos(theta), -np.sin(theta)])

        # 分支通道的法向量（垂直于分支方向）
        # 注意：法向量决定了端口的方向
        # 对于上分支：法向量指向左上方（端口水平）
        upper_normal = np.array([-np.sin(theta), np.cos(theta)])
        # 对于下分支：法向量指向左下方（端口水平）
        lower_normal = np.array([-np.sin(theta), -np.cos(theta)])

        # ===== 计算关键点 =====

        # 入口点
        inlet_bottom = np.array([0, -hw])
        inlet_top = np.array([0, hw])

        # 主通道末端（分岔点左侧）
        main_end_bottom = np.array([Lm, -hw])
        main_end_top = np.array([Lm, hw])

        # 分支末端中心（沿分支方向延伸Lb距离）
        upper_end_center = np.array([Lm, 0]) + Lb * upper_dir
        lower_end_center = np.array([Lm, 0]) + Lb * lower_dir

        # 分支端口端点（垂直于分支方向，水平端口）
        # 上分支端口（从端点看：左上到右下）
        upper_outlet_left = upper_end_center - hw * upper_normal   # 左侧点（靠近主通道）
        upper_outlet_right = upper_end_center + hw * upper_normal  # 右侧点（远离主通道）

        # 下分支端口（从端点看：左下到右上）
        lower_outlet_left = lower_end_center - hw * lower_normal   # 左侧点（靠近主通道）
        lower_outlet_right = lower_end_center + hw * lower_normal  # 右侧点（远离主通道）

        # ===== 定义外边界多边形（逆时针）=====
        # 从入口下角开始，沿下分支外壁，经上分支外壁，回到入口上角

        # 注意：我们需要按照正确的逆时针顺序定义边界
        # 下分支的外壁是 lower_outlet_left
        # 上分支的外壁是 upper_outlet_left（靠近主通道的一侧）

        # 重新思考：逆时针遍历
        # 1. 入口下角
        # 2. 主通道末端下角
        # 3. 下分支外侧端点（靠近主通道的，即lower_outlet_left）
        # 4. 下分支内侧端点（远离主通道的，即lower_outlet_right）
        # 5. 上分支内侧端点（远离主通道的，即upper_outlet_right）
        # 6. 上分支外侧端点（靠近主通道的，即upper_outlet_left）
        # 7. 主通道末端上角
        # 8. 入口上角

        # 但是这样的顺序会交叉，所以需要调整

        # 正确的逆时针顺序应该是：
        # 1. 入口下角 (0, -hw)
        # 2. 主通道末端下角 (Lm, -hw)
        # 3. 下分支外侧点 (lower_outlet_left - 靠近主通道)
        # 4. 下分支内侧点 (lower_outlet_right - 远离主通道)
        # 5. 上分支内侧点 (upper_outlet_right - 远离主通道)
        # 6. 上分支外侧点 (upper_outlet_left - 靠近主通道)
        # 7. 主通道末端上角 (Lm, hw)
        # 8. 入口上角 (0, hw)

        outer_boundary = np.array([
            inlet_bottom,         # 1. (0, -hw)
            main_end_bottom,      # 2. (Lm, -hw)
            lower_outlet_left,    # 3. 下分支外侧（靠近主通道）
            lower_outlet_right,   # 4. 下分支内侧（远离主通道）
            upper_outlet_right,   # 5. 上分支内侧（远离主通道）
            upper_outlet_left,    # 6. 上分支外侧（靠近主通道）
            main_end_top,         # 7. (Lm, hw)
            inlet_top,            # 8. (0, hw)
        ])

        # ===== 定义边界段 =====

        # 入口边界（左端面）
        inlet_points = np.array([inlet_bottom, inlet_top])
        self.add_boundary(inlet_points, BoundaryType.INLET, "INLET")

        # 出口1：上分支末端（水平端口）
        # 端口方向：从upper_outlet_right到upper_outlet_left（垂直于分支方向）
        outlet1_points = np.array([upper_outlet_right, upper_outlet_left])
        self.add_boundary(outlet1_points, BoundaryType.OUTLET_1, "OUTLET1")

        # 出口2：下分支末端（水平端口）
        # 端口方向：从lower_outlet_right到lower_outlet_left（垂直于分支方向）
        outlet2_points = np.array([lower_outlet_right, lower_outlet_left])
        self.add_boundary(outlet2_points, BoundaryType.OUTLET_2, "OUTLET2")

        # 壁面边界
        # 下壁面：入口底部到主通道末端底部
        wall_bottom = np.array([inlet_bottom, main_end_bottom])
        self.add_boundary(wall_bottom, BoundaryType.WALL, "WALL-bottom")

        # 下分支外壁：主通道末端底部到下分支外侧点
        wall_lower_outer = np.array([main_end_bottom, lower_outlet_left])
        self.add_boundary(wall_lower_outer, BoundaryType.WALL, "WALL-lower-outer")

        # 下分支端面：下分支外侧点到内侧点
        wall_lower_end = np.array([lower_outlet_left, lower_outlet_right])
        self.add_boundary(wall_lower_end, BoundaryType.WALL, "WALL-lower-end")

        # 内壁：下分支内侧点到上分支内侧点
        wall_inner = np.array([lower_outlet_right, upper_outlet_right])
        self.add_boundary(wall_inner, BoundaryType.WALL, "WALL-inner")

        # 上分支端面：上分支内侧点到外侧点
        wall_upper_end = np.array([upper_outlet_right, upper_outlet_left])
        self.add_boundary(wall_upper_end, BoundaryType.WALL, "WALL-upper-end")

        # 上分支外壁：上分支外侧点到主通道末端顶部
        wall_upper_outer = np.array([upper_outlet_left, main_end_top])
        self.add_boundary(wall_upper_outer, BoundaryType.WALL, "WALL-upper-outer")

        # 上壁面：主通道末端顶部到入口顶部
        wall_top = np.array([main_end_top, inlet_top])
        self.add_boundary(wall_top, BoundaryType.WALL, "WALL-top")

        return {
            'polygons': [
                {
                    'label': 'Y_junction_domain',
                    'points': outer_boundary.tolist(),
                    'type': 'outer_boundary'
                }
            ],
            'params': self.geometry_params
        }


def create_yjunction_standard() -> YJunctionGeometry:
    """创建标准Y型分岔道"""
    return YJunctionGeometry(
        L_main=5.0,
        L_branch=5.0,
        W=0.2,
        branch_angle=45.0,
        units='mm'
    )


if __name__ == '__main__':
    print("=" * 60)
    print("Y-Junction Geometry Test")
    print("=" * 60)

    y_geom = create_yjunction_standard()
    data = y_geom.generate()

    print(f"\n几何参数:")
    for key, value in y_geom.geometry_params.items():
        print(f"  {key}: {value}")

    y_geom.print_boundary_summary()

    print("\n" + "=" * 60)
