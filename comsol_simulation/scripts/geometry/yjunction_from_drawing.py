# -*- coding: utf-8 -*-
"""
Y型分岔道几何生成模块 - 基于用户绘图

根据用户在交互式绘图板上绘制的形状生成的Y型流道几何

几何参数（从用户绘图中提取）：
- 通道宽度：约 0.4 mm
- 主通道长度：约 6 mm（从入口到分岔点）
- 分支长度：约 4 mm
- 分支角度：约 35°（每侧）

形状示意：
         OUTLET1
           ↑
           │
          ╱
         ╱
        ╱
       ╱
      ┼─────────── INLET
     ╱
    ╱
   ╱
  ↓
OUTLET2
"""

import numpy as np
from typing import Dict
from base_geometry import MicrochannelGeometry, BoundaryType


class YJunctionFromDrawing(MicrochannelGeometry):
    """
    基于用户绘图的Y型分岔道几何生成类
    """

    def __init__(
        self,
        L_main: float = 6.0,        # 主通道长度 (mm)
        L_branch: float = 4.0,       # 分支通道长度 (mm)
        W: float = 0.4,              # 通道宽度 (mm)
        branch_angle: float = 35.0,  # 分支角度（度），每侧
        units: str = 'mm'
    ):
        """
        Args:
            L_main: 主通道长度，从入口到分岔点 (mm)
            L_branch: 分支通道长度 (mm)
            W: 通道宽度 (mm)
            branch_angle: 每个分支与主通道的夹角（度）
            units: 长度单位
        """
        super().__init__(units)

        self.W = W
        self.L_main = L_main
        self.L_branch = L_branch
        self.branch_angle = branch_angle
        self.half_W = W / 2

        # 转换为弧度
        self.angle_rad = np.radians(branch_angle)

        self.geometry_params = {
            'type': 'Y-junction-from-drawing',
            'L_main': L_main,
            'L_branch': L_branch,
            'W': W,
            'branch_angle': branch_angle,
            'units': units
        }

    def generate(self) -> Dict:
        """
        生成Y型分岔道几何

        坐标系统：
        - 主通道沿X轴，从x=0到x=L_main
        - 主通道中心线在y=0
        - 分岔点在 (L_main, 0)

        Returns:
            包含几何数据的字典
        """
        W = self.W
        hw = self.half_W
        Lm = self.L_main
        Lb = self.L_branch
        theta = self.angle_rad

        # 方向向量
        upper_dir = np.array([np.cos(theta), np.sin(theta)])
        lower_dir = np.array([np.cos(theta), -np.sin(theta)])

        # 法向量（垂直于分支方向）
        upper_normal = np.array([-np.sin(theta), np.cos(theta)])
        lower_normal = np.array([-np.sin(theta), -np.cos(theta)])

        # 入口点
        inlet_bottom = np.array([0, -hw])
        inlet_top = np.array([0, hw])

        # 主通道末端（分岔点左侧）
        main_end_bottom = np.array([Lm, -hw])
        main_end_top = np.array([Lm, hw])

        # 分支末端中心
        upper_end_center = np.array([Lm, 0]) + Lb * upper_dir
        lower_end_center = np.array([Lm, 0]) + Lb * lower_dir

        # 分支端口端点（垂直于分支方向）
        upper_outlet_left = upper_end_center - hw * upper_normal
        upper_outlet_right = upper_end_center + hw * upper_normal

        lower_outlet_left = lower_end_center - hw * lower_normal
        lower_outlet_right = lower_end_center + hw * lower_normal

        # 外边界多边形（逆时针）
        outer_boundary = np.array([
            inlet_bottom,         # 1. 入口下角
            main_end_bottom,      # 2. 主通道末端下角
            lower_outlet_left,    # 3. 下分支外侧
            lower_outlet_right,   # 4. 下分支内侧
            upper_outlet_right,   # 5. 上分支内侧
            upper_outlet_left,    # 6. 上分支外侧
            main_end_top,         # 7. 主通道末端上角
            inlet_top,            # 8. 入口上角
        ])

        # 定义边界段
        # 入口边界
        inlet_points = np.array([inlet_bottom, inlet_top])
        self.add_boundary(inlet_points, BoundaryType.INLET, "INLET")

        # 出口1：上分支末端
        outlet1_points = np.array([upper_outlet_right, upper_outlet_left])
        self.add_boundary(outlet1_points, BoundaryType.OUTLET_1, "OUTLET1")

        # 出口2：下分支末端
        outlet2_points = np.array([lower_outlet_right, lower_outlet_left])
        self.add_boundary(outlet2_points, BoundaryType.OUTLET_2, "OUTLET2")

        # 壁面边界
        wall_bottom = np.array([inlet_bottom, main_end_bottom])
        self.add_boundary(wall_bottom, BoundaryType.WALL, "WALL-bottom")

        wall_lower_outer = np.array([main_end_bottom, lower_outlet_left])
        self.add_boundary(wall_lower_outer, BoundaryType.WALL, "WALL-lower-outer")

        wall_lower_end = np.array([lower_outlet_left, lower_outlet_right])
        self.add_boundary(wall_lower_end, BoundaryType.WALL, "WALL-lower-end")

        wall_inner = np.array([lower_outlet_right, upper_outlet_right])
        self.add_boundary(wall_inner, BoundaryType.WALL, "WALL-inner")

        wall_upper_end = np.array([upper_outlet_right, upper_outlet_left])
        self.add_boundary(wall_upper_end, BoundaryType.WALL, "WALL-upper-end")

        wall_upper_outer = np.array([upper_outlet_left, main_end_top])
        self.add_boundary(wall_upper_outer, BoundaryType.WALL, "WALL-upper-outer")

        wall_top = np.array([main_end_top, inlet_top])
        self.add_boundary(wall_top, BoundaryType.WALL, "WALL-top")

        return {
            'polygons': [
                {
                    'label': 'Y_junction_from_drawing',
                    'points': outer_boundary.tolist(),
                    'type': 'outer_boundary'
                }
            ],
            'params': self.geometry_params
        }


def create_yjunction_from_drawing() -> YJunctionFromDrawing:
    """
    创建基于用户绘图的Y型分岔道

    从用户的绘图中提取的参数：
    - 通道宽度：0.4 mm
    - 主通道长度：6 mm
    - 分支长度：4 mm
    - 分支角度：35°
    """
    return YJunctionFromDrawing(
        L_main=6.0,
        L_branch=4.0,
        W=0.4,
        branch_angle=35.0,
        units='mm'
    )


if __name__ == '__main__':
    print("=" * 60)
    print("Y-Junction from Drawing Test")
    print("=" * 60)

    geom = create_yjunction_from_drawing()
    data = geom.generate()

    print(f"\n几何参数:")
    for key, value in geom.geometry_params.items():
        print(f"  {key}: {value}")

    geom.print_boundary_summary()

    print("\n" + "=" * 60)
