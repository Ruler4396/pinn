# -*- coding: utf-8 -*-
"""
Y型分岔道几何 - 微流控芯片尺寸（修复版）

严格按照 yjunction_from_lines.py 的正确结构：
- 边界段按正确的遍历顺序定义
- 多边形顶点按逆时针顺序排列

典型微流控芯片Y型分岔道：
- 通道宽度：200 μm (0.2 mm)
- 主通道长度：6 mm
- 分支通道长度：4 mm
- 分支角度：30-45°（对称）
"""

import numpy as np
from typing import Dict
from base_geometry import MicrochannelGeometry, BoundaryType


class YJunctionMicrofluidic(MicrochannelGeometry):
    """
    微流控芯片Y型分岔道（修复版）

    严格按照 yjunction_from_lines.py 的正确结构
    """

    def __init__(
        self,
        L_main: float = 6.0,        # 主通道长度 (mm)
        L_branch: float = 4.0,       # 分支通道长度 (mm)
        W: float = 0.2,              # 通道宽度 (mm) - 200 μm
        branch_angle: float = 30.0,  # 分支角度（度），每侧
        units: str = 'μm'            # 显示单位
    ):
        super().__init__(units)

        self.W_mm = W  # 内部计算用mm
        self.L_main = L_main
        self.L_branch = L_branch
        self.branch_angle = branch_angle
        self.half_W = W / 2

        # 转换为μm用于显示
        self.W = W * 1000  # μm

        # 转换为弧度
        self.angle_rad = np.radians(branch_angle)
        self.total_angle = branch_angle * 2

        self.geometry_params = {
            'type': 'Y-junction-microfluidic',
            'L_main_mm': L_main,
            'L_branch_mm': L_branch,
            'W_um': int(W * 1000),
            'branch_angle': branch_angle,
            'total_angle': self.total_angle,
            'display_units': units,
            'application': 'flow_splitting',
            'structure': 'based_on_yjunction_from_lines'
        }

    def generate(self) -> Dict:
        """
        生成Y型分岔道几何

        严格按照 yjunction_from_lines.py 的正确顺序：
        入口 → 主通道下 → 下分支外壁 → 下分支端口 → 下分支内壁
        → 上分支内壁 → 上分支端口 → 上分支外壁 → 主通道上
        """
        W = self.W_mm
        hw = self.half_W
        Lm = self.L_main
        Lb = self.L_branch
        theta = self.angle_rad

        # 方向向量
        upper_dir = np.array([np.cos(theta), np.sin(theta)])
        lower_dir = np.array([np.cos(theta), -np.sin(theta)])

        # 关键点定义
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
        # 端口的法向量（垂直于分支方向）
        upper_normal = np.array([-np.sin(theta), np.cos(theta)])
        lower_normal = np.array([-np.sin(theta), -np.cos(theta)])

        # 下分支端口（从右侧到左侧，逆时针遍历）
        lower_port_right = lower_end_center + hw * lower_normal
        lower_port_left = lower_end_center - hw * lower_normal

        # 上分支端口（从右侧到左侧，逆时针遍历）
        upper_port_right = upper_end_center + hw * upper_normal
        upper_port_left = upper_end_center - hw * upper_normal

        # 分支外壁起点（在主通道末端）
        lower_branch_outer_start = np.array([Lm, -hw])
        upper_branch_outer_start = np.array([Lm, hw])

        # 分支外壁终点
        lower_branch_outer_end = lower_end_center + hw * np.array([np.sin(theta), -np.cos(theta)])
        upper_branch_outer_end = upper_end_center + hw * np.array([-np.sin(theta), np.cos(theta)])

        # ===== 按照正确的遍历顺序定义边界段 =====
        # 顺序：入口 → 主通道下 → 下分支外壁 → 下分支端口 → 下分支内壁
        #      → 上分支内壁 → 上分支端口 → 上分支外壁 → 主通道上

        # 1. 入口边界（左端面，垂直）
        self.add_boundary(np.array([inlet_top, inlet_bottom]), BoundaryType.INLET, "INLET")

        # 2. 主通道下边缘（从入口到分岔点）
        self.add_boundary(np.array([inlet_bottom, main_end_bottom]), BoundaryType.WALL, "WALL-bottom")

        # 3. 下分支外壁（从分岔点到分支末端外侧）
        self.add_boundary(np.array([main_end_bottom, lower_branch_outer_end]), BoundaryType.WALL, "WALL-lower-outer")

        # 4. 下分支端口（从外侧到内侧，垂直于分支）
        self.add_boundary(np.array([lower_port_right, lower_port_left]), BoundaryType.OUTLET_2, "OUTLET2")

        # 5. 下分支内壁（从内侧端回到分岔点区域）
        # 连接下分支端口内侧到分岔点附近的内壁区域
        # 内壁的终点应该在分岔点附近，连接到上分支内壁
        lower_inner_end = np.array([Lm, 0]) + hw * np.array([np.cos(theta/2), -np.sin(theta/2)])
        self.add_boundary(np.array([lower_port_left, lower_inner_end]), BoundaryType.WALL, "WALL-lower-inner")

        # 6. 上分支内壁（从下分支内壁终点到上分支内壁终点）
        upper_inner_end = np.array([Lm, 0]) + hw * np.array([np.cos(theta/2), np.sin(theta/2)])
        self.add_boundary(np.array([lower_inner_end, upper_inner_end]), BoundaryType.WALL, "WALL-inner")
        self.add_boundary(np.array([upper_inner_end, upper_port_right]), BoundaryType.WALL, "WALL-upper-inner")

        # 7. 上分支端口（从右侧到左侧，垂直于分支）
        self.add_boundary(np.array([upper_port_right, upper_port_left]), BoundaryType.OUTLET_1, "OUTLET1")

        # 8. 上分支外壁（从分支末端外侧到分岔点）
        self.add_boundary(np.array([upper_branch_outer_end, main_end_top]), BoundaryType.WALL, "WALL-upper-outer")

        # 9. 主通道上边缘（从分岔点到入口）
        self.add_boundary(np.array([main_end_top, inlet_top]), BoundaryType.WALL, "WALL-top")

        # 外边界多边形（逆时针顺序，严格按照 yjunction_from_lines.py）
        vertices = []

        # 1. 入口底部
        vertices.append(inlet_bottom)
        # 2. 主通道右下
        vertices.append(main_end_bottom)
        # 3. 下分支外壁终点
        vertices.append(lower_branch_outer_end)
        # 4. 下分支端口（外侧点）
        vertices.append(lower_port_right)
        # 5. 下分支端口（内侧点）
        vertices.append(lower_port_left)
        # 6. 下分支内壁终点
        vertices.append(lower_inner_end)
        # 7. 上分支内壁起点
        vertices.append(upper_inner_end)
        # 8. 上分支端口（内侧点）
        vertices.append(upper_port_right)
        # 9. 上分支端口（外侧点）
        vertices.append(upper_port_left)
        # 10. 上分支外壁终点
        vertices.append(upper_branch_outer_end)
        # 11. 主通道右上
        vertices.append(main_end_top)
        # 12. 入口顶部
        vertices.append(inlet_top)

        outer_boundary = np.array(vertices)

        return {
            'polygons': [
                {
                    'label': 'Y_junction_microfluidic',
                    'points': outer_boundary.tolist(),
                    'type': 'outer_boundary'
                }
            ],
            'params': self.geometry_params
        }


def create_yjunction_standard() -> YJunctionMicrofluidic:
    """
    标准微流控Y型分岔道 - 200μm通道，30°分岔
    """
    return YJunctionMicrofluidic(
        L_main=6.0,
        L_branch=4.0,
        W=0.2,  # 200 μm
        branch_angle=30.0,
        units='μm'
    )


def create_yjunction_wide_angle() -> YJunctionMicrofluidic:
    """
    宽角度Y型分岔道 - 200μm通道，45°分岔
    """
    return YJunctionMicrofluidic(
        L_main=6.0,
        L_branch=4.0,
        W=0.2,  # 200 μm
        branch_angle=45.0,
        units='μm'
    )


def create_yjunction_narrow() -> YJunctionMicrofluidic:
    """
    窄通道Y型分岔道 - 100μm通道
    """
    return YJunctionMicrofluidic(
        L_main=6.0,
        L_branch=4.0,
        W=0.1,  # 100 μm
        branch_angle=30.0,
        units='μm'
    )


if __name__ == '__main__':
    print("=" * 60)
    print("Y-Junction Microfluidic Dimensions (Fixed)")
    print("=" * 60)

    geom = create_yjunction_standard()
    data = geom.generate()

    print(f"\n几何参数:")
    for key, value in geom.geometry_params.items():
        print(f"  {key}: {value}")

    geom.print_boundary_summary()

    print("\n" + "=" * 60)
