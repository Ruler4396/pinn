# -*- coding: utf-8 -*-
"""
T型分岔道几何生成模块

重新设计的T型流道几何：
- 主通道：水平方向，从左到右
- 分支通道：垂直向上，从主通道某个位置分出

形状示意：
        │
        │ OUTLET2
        │
  ──────┼─────── OUTLET1
  INLET │
        │

边界条件：
1. INLET（绿色）：主通道左端 - 速度入口
2. OUTLET1（蓝色）：主通道右端 - 压力出口
3. OUTLET2（紫色）：分支通道上端 - 压力出口
4. WALL（红色）：其余所有边界 - 无滑移
"""

import numpy as np
from typing import Dict, List
from base_geometry import MicrochannelGeometry, BoundaryType


class TJunctionGeometry(MicrochannelGeometry):
    """
    T型分岔道几何生成类

    标准T型流道：主通道水平，分支通道垂直向上
    """

    def __init__(
        self,
        L_main: float = 10.0,      # 主通道总长度 (mm)
        L_branch: float = 5.0,     # 分支通道长度 (mm)
        W: float = 0.2,            # 通道宽度 (mm)
        junction_x: float = None,  # 分岔点X位置，默认为主通道中点
        units: str = 'mm'
    ):
        """
        Args:
            L_main: 主通道总长度 (mm)
            L_branch: 分支通道从主中心线向上的长度 (mm)
            W: 通道宽度 (mm)，主通道和分支通道相同
            junction_x: 分岔点X坐标，默认在主通道中心
            units: 长度单位
        """
        super().__init__(units)

        self.W = W
        self.L_main = L_main
        self.L_branch = L_branch
        self.junction_x = junction_x if junction_x is not None else L_main / 2
        self.half_W = W / 2

        self.geometry_params = {
            'type': 'T-junction',
            'L_main': L_main,
            'L_branch': L_branch,
            'W': W,
            'junction_x': self.junction_x,
            'units': units,
            'junction_angle': 90
        }

    def generate(self) -> Dict:
        """
        生成T型分岔道几何

        坐标系统：
        - 主通道沿X轴，从x=0到x=L_main
        - 主通道中心线在y=0
        - 分支通道从x=junction_x垂直向上

        Returns:
            包含几何数据的字典
        """
        W = self.W
        hw = self.half_W
        Lm = self.L_main
        Lb = self.L_branch
        jx = self.junction_x

        # ===== 定义关键点 =====
        # 按逆时针方向定义外边界顶点

        # 主通道部分
        p1 = np.array([0, -hw])        # 入口左下角
        p2 = np.array([Lm, -hw])       # 主通道出口右下角
        p3 = np.array([Lm, hw])        # 主通道出口右上角
        p4 = np.array([jx + hw, hw])   # 分岔点右侧（上边缘）
        p5 = np.array([jx + hw, 0])    # 分岔点右侧（中心线）

        # 分支通道部分（向上）
        p6 = np.array([jx + hw, Lb])   # 分支末端右上
        p7 = np.array([jx - hw, Lb])   # 分支末端左上
        p8 = np.array([jx - hw, 0])    # 分岔点左侧（中心线）
        p9 = np.array([jx - hw, -hw])  # 分岔点左侧（下边缘）
        p10 = np.array([0, -hw])       # 回到入口左下角（与p1相同）

        # 定义外边界多边形（逆时针，确保内部在左侧）
        outer_boundary = np.array([
            p1,   # 入口左下
            p2,   # 主通道右下
            p3,   # 主通道右上
            p4,   # 分岔点右上
            p5,   # 分岔点右侧中心
            p6,   # 分支末端右上
            p7,   # 分支末端左上
            p8,   # 分岔点左侧中心
            p9,   # 分岔点左下
            p10   # 回到起点
        ])

        # ===== 定义边界段 =====

        # 入口边界（左端面，垂直线段）
        inlet_bottom = np.array([0, -hw])
        inlet_top = np.array([0, hw])
        inlet_points = np.array([inlet_bottom, inlet_top])
        self.add_boundary(inlet_points, BoundaryType.INLET, "INLET")

        # 出口1边界（主通道右端面，垂直线段）
        outlet1_bottom = np.array([Lm, -hw])
        outlet1_top = np.array([Lm, hw])
        outlet1_points = np.array([outlet1_bottom, outlet1_top])
        self.add_boundary(outlet1_points, BoundaryType.OUTLET_1, "OUTLET1")

        # 出口2边界（分支通道上端面，水平线段）
        outlet2_left = np.array([jx - hw, Lb])
        outlet2_right = np.array([jx + hw, Lb])
        outlet2_points = np.array([outlet2_left, outlet2_right])
        self.add_boundary(outlet2_points, BoundaryType.OUTLET_2, "OUTLET2")

        # 壁面边界
        # 下壁面：入口底部到主通道出口底部
        wall_bottom = np.array([
            np.array([0, -hw]),
            np.array([Lm, -hw])
        ])
        self.add_boundary(wall_bottom, BoundaryType.WALL, "WALL-bottom")

        # 上壁面第一段：入口顶部到分岔点左侧
        wall_top1 = np.array([
            np.array([0, hw]),
            np.array([jx - hw, hw])
        ])
        self.add_boundary(wall_top1, BoundaryType.WALL, "WALL-top-left")

        # 分岔区域：分岔点左上角到分支末端
        wall_branch_left = np.array([
            np.array([jx - hw, hw]),
            np.array([jx - hw, Lb])
        ])
        self.add_boundary(wall_branch_left, BoundaryType.WALL, "WALL-branch-left")

        # 分支通道顶部（从左侧到右侧）
        wall_branch_top = np.array([
            np.array([jx - hw, Lb]),
            np.array([jx + hw, Lb])
        ])
        self.add_boundary(wall_branch_top, BoundaryType.WALL, "WALL-branch-top")

        # 分岔区域：分支末端到分岔点右侧
        wall_branch_right = np.array([
            np.array([jx + hw, Lb]),
            np.array([jx + hw, hw])
        ])
        self.add_boundary(wall_branch_right, BoundaryType.WALL, "WALL-branch-right")

        # 上壁面第二段：分岔点右侧到主通道出口
        wall_top2 = np.array([
            np.array([jx + hw, hw]),
            np.array([Lm, hw])
        ])
        self.add_boundary(wall_top2, BoundaryType.WALL, "WALL-top-right")

        return {
            'polygons': [
                {
                    'label': 'T_junction_domain',
                    'points': outer_boundary.tolist(),
                    'type': 'outer_boundary'
                }
            ],
            'params': self.geometry_params
        }


def create_tjunction_standard() -> TJunctionGeometry:
    """创建标准T型分岔道"""
    return TJunctionGeometry(
        L_main=10.0,
        L_branch=5.0,
        W=0.2,
        units='mm'
    )


if __name__ == '__main__':
    print("=" * 60)
    print("T-Junction Geometry Test")
    print("=" * 60)

    t_geom = create_tjunction_standard()
    data = t_geom.generate()

    print(f"\n几何参数:")
    for key, value in t_geom.geometry_params.items():
        print(f"  {key}: {value}")

    t_geom.print_boundary_summary()

    print("\n" + "=" * 60)
