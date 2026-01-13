# -*- coding: utf-8 -*-
"""
Y型分岔道几何 - 正确的流道宽度关系

关键设计原则：
1. 流道完全对称（关于X轴）
2. 主通道宽度 W_main = 2 × 分支通道宽度 W_branch
3. 保证流动连续性：入口面积 = 出口1面积 + 出口2面积
"""

import numpy as np
from typing import Dict
from base_geometry import MicrochannelGeometry, BoundaryType


class YJunctionCorrected(MicrochannelGeometry):
    """
    修正后的Y型分岔道几何生成类

    正确的顶点连接顺序：1→9→8→7→6→5→3→4→2→1

    流道宽度关系：
    - 主通道宽度：W_main
    - 分支通道宽度：W_branch = W_main / 2
    - 这样保证：A_inlet = A_outlet1 + A_outlet2
    """

    def __init__(
        self,
        L_main: float = 6.0,        # 主通道长度 (mm)
        L_branch: float = 2.7,       # 分支通道长度 (mm)
        W_main: float = 0.4,         # 主通道宽度 (mm)
        branch_angle: float = 40.0,  # 分支角度（度），每侧
        units: str = 'mm'
    ):
        """
        Args:
            L_main: 主通道长度，从入口到分岔点 (mm)
            L_branch: 分支通道长度 (mm)
            W_main: 主通道宽度 (mm)
            branch_angle: 每个分支与主通道的夹角（度）
            units: 长度单位
        """
        super().__init__(units)

        # 主通道宽度
        self.W_main = W_main
        self.half_W_main = W_main / 2

        # 分支通道宽度 = 主通道宽度的一半
        self.W_branch = W_main / 2
        self.half_W_branch = self.W_branch / 2

        self.L_main = L_main
        self.L_branch = L_branch
        self.branch_angle = branch_angle

        # 转换为弧度
        self.angle_rad = np.radians(branch_angle)

        self.geometry_params = {
            'type': 'Y-junction-corrected',
            'L_main_mm': L_main,
            'L_branch_mm': L_branch,
            'W_main_mm': W_main,
            'W_branch_mm': W_main / 2,
            'branch_angle_deg': branch_angle,
            'units': units,
            'source': 'corrected_width_relationship',
            'vertex_order': '1→9→8→7→6→5→3→4→2→1',
            'flow_continuity': 'A_inlet = A_outlet1 + A_outlet2'
        }

    def generate(self) -> Dict:
        """
        生成修正后的Y型分岔道几何

        正确的顶点连接顺序：1→9→8→7→6→5→3→4→2→1

        流道设计：
        - 1, 9: 入口两端，距离 = W_main
        - 8, 2: 主通道末端两端，距离 = W_main
        - 7, 6: 上分支端口两端，距离 = W_branch
        - 3, 4: 下分支端口两端，距离 = W_branch
        - 5: 分岔点 (L_main, 0)

        Returns:
            包含几何数据的字典
        """
        Wm = self.W_main
        hwm = self.half_W_main
        Wb = self.W_branch
        hwb = self.half_W_branch
        Lm = self.L_main
        Lb = self.L_branch
        theta = self.angle_rad

        # 方向向量
        upper_dir = np.array([np.cos(theta), np.sin(theta)])
        lower_dir = np.array([np.cos(theta), -np.sin(theta)])

        # 法向量（垂直于分支方向，指向外侧）
        upper_normal = np.array([-np.sin(theta), np.cos(theta)])
        lower_normal = np.array([-np.sin(theta), -np.cos(theta)])

        # ============ 按顺序定义顶点 ============

        # 顶点 1: 入口底部
        v1 = np.array([0.0, -hwm])

        # 顶点 9: 入口顶部
        v9 = np.array([0.0, hwm])

        # 顶点 8: 主通道末端顶部
        v8 = np.array([Lm, hwm])

        # 顶点 7: 上分支端口外侧（远离中心线）
        upper_end_center = np.array([Lm, 0.0]) + Lb * upper_dir
        v7 = upper_end_center + hwb * upper_normal  # 外侧

        # 顶点 6: 上分支端口内侧（靠近分岔点）
        v6 = upper_end_center - hwb * upper_normal  # 内侧

        # 顶点 5: 分岔点（主通道中心）
        v5 = np.array([Lm, 0.0])

        # 顶点 3: 下分支端口内侧（靠近分岔点）
        lower_end_center = np.array([Lm, 0.0]) + Lb * lower_dir
        v3 = lower_end_center - hwb * lower_normal  # 内侧

        # 顶点 4: 下分支端口外侧（远离中心线）
        v4 = lower_end_center + hwb * lower_normal  # 外侧

        # 顶点 2: 主通道末端底部
        v2 = np.array([Lm, -hwm])

        # ============ 按顺序定义边界段 1→9→8→7→6→5→3→4→2→1 ============

        # 1 → 9: 入口边界（从顶部到底部，逆时针）
        self.add_boundary(np.array([v9, v1]), BoundaryType.INLET, "INLET")

        # 9 → 8: 主通道上边缘
        self.add_boundary(np.array([v9, v8]), BoundaryType.WALL, "WALL-main-top")

        # 8 → 7: 上分支外壁
        self.add_boundary(np.array([v8, v7]), BoundaryType.WALL, "WALL-upper-outer")

        # 7 → 6: 上分支端口（出口1，从外侧到内侧）
        self.add_boundary(np.array([v7, v6]), BoundaryType.OUTLET_1, "OUTLET1")

        # 6 → 5: 上分支内壁
        self.add_boundary(np.array([v6, v5]), BoundaryType.WALL, "WALL-upper-inner")

        # 5 → 3: 下分支内壁（从分岔点到下分支端口内侧）
        self.add_boundary(np.array([v5, v3]), BoundaryType.WALL, "WALL-lower-inner")

        # 3 → 4: 下分支端口（出口2，从内侧到外侧）
        self.add_boundary(np.array([v3, v4]), BoundaryType.OUTLET_2, "OUTLET2")

        # 4 → 2: 下分支外壁
        self.add_boundary(np.array([v4, v2]), BoundaryType.WALL, "WALL-lower-outer")

        # 2 → 1: 主通道下边缘
        self.add_boundary(np.array([v2, v1]), BoundaryType.WALL, "WALL-main-bottom")

        # ============ 构建外边界多边形 ============
        # 按照正确的连接顺序：1→9→8→7→6→5→3→4→2→1
        outer_boundary = np.array([v1, v9, v8, v7, v6, v5, v3, v4, v2])

        return {
            'polygons': [
                {
                    'label': 'Y_junction_corrected',
                    'points': outer_boundary.tolist(),
                    'type': 'outer_boundary'
                }
            ],
            'params': self.geometry_params
        }


def create_yjunction_corrected() -> YJunctionCorrected:
    """
    创建修正后的Y型分岔道

    流道宽度关系：
    - 主通道宽度：0.4 mm
    - 分支通道宽度：0.2 mm（每个）
    - 这样满足：W_main = 2 × W_branch
    """
    return YJunctionCorrected(
        L_main=6.0,
        L_branch=2.7,
        W_main=0.4,  # 主通道宽度
        branch_angle=40.0,
        units='mm'
    )


if __name__ == '__main__':
    print("=" * 70)
    print("Y-Junction Corrected (Correct Width Relationship)")
    print("=" * 70)

    geom = create_yjunction_corrected()
    data = geom.generate()

    print(f"\n几何参数:")
    for key, value in geom.geometry_params.items():
        print(f"  {key}: {value}")

    # 打印顶点坐标
    points = np.array(data['polygons'][0]['points'])
    print(f"\n顶点坐标 (按连接顺序 1→9→8→7→6→5→3→4→2→1):")
    print("-" * 70)
    vertex_names = ['1(inlet_bot)', '9(inlet_top)', '8(main_end_top)',
                    '7(up_port_outer)', '6(up_port_inner)', '5(bifurcation)',
                    '3(low_port_inner)', '4(low_port_outer)', '2(main_end_bot)']
    for i, (name, point) in enumerate(zip(vertex_names, points)):
        print(f"  {name:20s}: ({point[0]:8.4f}, {point[1]:8.4f})")

    # 验证流道宽度
    print(f"\n流道宽度验证:")
    print("-" * 70)
    inlet_width = geom._calculate_length(geom.boundaries[0].points)
    outlet1_width = geom._calculate_length(geom.boundaries[3].points)
    outlet2_width = geom._calculate_length(geom.boundaries[6].points)

    print(f"  主通道宽度 (入口):  {inlet_width:.4f} mm")
    print(f"  上分支宽度 (出口1): {outlet1_width:.4f} mm")
    print(f"  下分支宽度 (出口2): {outlet2_width:.4f} mm")
    print(f"  宽度关系: W_main = {inlet_width:.4f} mm ≈ 2 × W_branch = {2*outlet1_width:.4f} mm")
    print(f"  验证: {abs(inlet_width - 2*outlet1_width) < 0.001}")

    geom.print_boundary_summary()

    print("\n" + "=" * 70)
