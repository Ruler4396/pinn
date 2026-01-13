# -*- coding: utf-8 -*-
"""
T型分岔道几何 - 微流控芯片尺寸

严格按照 tjunction.py 的正确结构：
- 边界段按正确的遍历顺序定义
- 多边形顶点按逆时针顺序排列

典型微流控芯片T型分岔道：
- 通道宽度：200 μm (0.2 mm)
- 主通道长度：10 mm
- 分支通道长度：5 mm
- 分支角度：90°（垂直）

应用场景：
- 液滴生成
- 流体混合
- 细胞分选
"""

import numpy as np
from typing import Dict
from base_geometry import MicrochannelGeometry, BoundaryType


class TJunctionMicrofluidic(MicrochannelGeometry):
    """
    微流控芯片T型分岔道（修复版）

    严格按照 tjunction.py 的正确结构
    """

    def __init__(
        self,
        L_main: float = 10.0,      # 主通道总长度 (mm)
        L_branch: float = 5.0,     # 分支通道长度 (mm)
        W: float = 0.2,            # 通道宽度 (mm) - 200 μm
        junction_x: float = None,  # 分岔点X位置
        units: str = 'μm'          # 使用微米作为单位
    ):
        """
        Args:
            L_main: 主通道总长度 (mm)
            L_branch: 分支通道从主中心线向上的长度 (mm)
            W: 通道宽度 (mm)，推荐值：
                - 0.1 mm (100 μm) - 玻璃芯片
                - 0.2 mm (200 μm) - PDMS芯片（标准）
                - 0.3 mm (300 μm) - 快速流动
                - 0.5 mm (500 μm) - 高通量
            junction_x: 分岔点X坐标，默认在主通道中心
            units: 显示单位（建议用μm）
        """
        super().__init__(units)

        self.W_mm = W  # 内部计算用mm
        self.L_main = L_main
        self.L_branch = L_branch
        self.junction_x = junction_x if junction_x is not None else L_main / 2
        self.half_W = W / 2

        # 转换为μm用于显示
        self.W = W * 1000  # μm

        self.geometry_params = {
            'type': 'T-junction-microfluidic',
            'L_main_mm': L_main,
            'L_branch_mm': L_branch,
            'W_um': int(W * 1000),  # 通道宽度（微米）
            'junction_x_mm': self.junction_x,
            'display_units': units,
            'junction_angle': 90,
            'application': 'droplet_generation',
            'structure': 'based_on_tjunction'
        }

    def generate(self) -> Dict:
        """
        生成T型分岔道几何

        严格按照 tjunction.py 的正确顺序：
        入口底部 → 主通道右下 → 主通道右上 → 分岔点右上 → 分岔点右侧中心
        → 分支末端右上 → 分支末端左上 → 分岔点左侧中心 → 分岔点左下 → 回到入口
        """
        W = self.W_mm
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
            p1    # 回到起点（闭合）
        ])

        # ===== 定义边界段 =====

        # 1. 入口边界（左端面，垂直线段）
        inlet_bottom = np.array([0, -hw])
        inlet_top = np.array([0, hw])
        inlet_points = np.array([inlet_bottom, inlet_top])
        self.add_boundary(inlet_points, BoundaryType.INLET, "INLET")

        # 2. 出口1边界（主通道右端面，垂直线段）
        outlet1_bottom = np.array([Lm, -hw])
        outlet1_top = np.array([Lm, hw])
        outlet1_points = np.array([outlet1_bottom, outlet1_top])
        self.add_boundary(outlet1_points, BoundaryType.OUTLET_1, "OUTLET1")

        # 3. 出口2边界（分支通道上端面，水平线段）
        outlet2_left = np.array([jx - hw, Lb])
        outlet2_right = np.array([jx + hw, Lb])
        outlet2_points = np.array([outlet2_left, outlet2_right])
        self.add_boundary(outlet2_points, BoundaryType.OUTLET_2, "OUTLET2")

        # 4. 壁面边界
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
                    'label': 'T_junction_microfluidic',
                    'points': outer_boundary.tolist(),
                    'type': 'outer_boundary'
                }
            ],
            'params': self.geometry_params
        }


def create_tjunction_standard() -> TJunctionMicrofluidic:
    """
    标准微流控T型分岔道 - 200μm通道

    最常用的配置：
    - 通道宽度：200 μm
    - 主通道：10 mm
    - 分支通道：5 mm
    """
    return TJunctionMicrofluidic(
        L_main=10.0,
        L_branch=5.0,
        W=0.2,  # 200 μm
        units='μm'
    )


def create_tjunction_narrow() -> TJunctionMicrofluidic:
    """
    窄通道T型分岔道 - 100μm通道

    适用于高精度应用：
    - 单细胞分析
    - 精细液滴生成
    """
    return TJunctionMicrofluidic(
        L_main=10.0,
        L_branch=5.0,
        W=0.1,  # 100 μm
        units='μm'
    )


def create_tjunction_wide() -> TJunctionMicrofluidic:
    """
    宽通道T型分岔道 - 500μm通道

    适用于高通量应用：
    - 快速混合
    - 大流量处理
    """
    return TJunctionMicrofluidic(
        L_main=10.0,
        L_branch=5.0,
        W=0.5,  # 500 μm
        units='μm'
    )


if __name__ == '__main__':
    print("=" * 60)
    print("T-Junction Microfluidic Dimensions (Fixed)")
    print("=" * 60)

    geom = create_tjunction_standard()
    data = geom.generate()

    print(f"\n几何参数:")
    for key, value in geom.geometry_params.items():
        print(f"  {key}: {value}")

    geom.print_boundary_summary()

    print("\n" + "=" * 60)
