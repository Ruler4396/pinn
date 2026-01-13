# -*- coding: utf-8 -*-
"""
Y型分岔道几何 - 完全对称版本

修复了以下问题：
1. 多边形顶点按正确的逆时针顺序连接
2. 上下分支完全对称
3. 边界段连接顺序正确，形成闭合多边形
"""

import numpy as np
from typing import Dict, List
from base_geometry import MicrochannelGeometry, BoundaryType


class YJunctionSymmetric(MicrochannelGeometry):
    """
    完全对称的Y型分岔道

    几何特征：
    - 入口在左侧，垂直于主通道
    - 主通道水平延伸，然后分成两个对称的分支
    - 两个出口分别位于上下分支的末端
    - 分岔处平滑过渡，内壁连接正确
    """

    def __init__(
        self,
        L_main: float = 6.0,        # 主通道长度 (mm)
        L_branch: float = 4.0,       # 分支通道长度 (mm)
        W: float = 0.3,              # 通道宽度 (mm)
        branch_angle: float = 30.0,  # 分支角度（度），每侧相对于主通道
        units: str = 'mm'
    ):
        super().__init__(units)

        self.L_main = L_main
        self.L_branch = L_branch
        self.W = W
        self.half_W = W / 2
        self.branch_angle = branch_angle

        # 转换为弧度
        self.angle_rad = np.radians(branch_angle)

        self.geometry_params = {
            'type': 'Y-junction-symmetric',
            'L_main_mm': L_main,
            'L_branch_mm': L_branch,
            'W_mm': W,
            'branch_angle_deg': branch_angle,
            'symmetric': True,
            'units': units
        }

    def generate(self) -> Dict:
        """
        生成完全对称的Y型分岔道几何

        顶点顺序（逆时针，从入口底部开始）：
        1. 入口底部 → 2. 主通道末端底部 → 3. 下分支外壁终点
        → 4. 下分支端口外侧 → 5. 下分支端口内侧 → 6. 分岔点
        → 7. 上分支端口内侧 → 8. 上分支端口外侧 → 9. 上分支外壁终点
        → 10. 主通道末端顶部 → 11. 入口顶部 → 回到起点
        """
        W = self.W
        hw = self.half_W
        Lm = self.L_main
        Lb = self.L_branch
        theta = self.angle_rad

        # ============ 定义关键顶点 ============

        # 入口边界（左端，垂直于主通道）
        inlet_bottom = np.array([0.0, -hw])
        inlet_top = np.array([0.0, hw])

        # 主通道末端（分岔点左侧）
        main_end_bottom = np.array([Lm, -hw])
        main_end_top = np.array([Lm, hw])

        # 分支末端中心点
        branch_center_x = Lm
        branch_center_y = 0.0

        upper_branch_center = np.array([
            branch_center_x + Lb * np.cos(theta),
            branch_center_y + Lb * np.sin(theta)
        ])

        lower_branch_center = np.array([
            branch_center_x + Lb * np.cos(theta),
            branch_center_y - Lb * np.sin(theta)
        ])

        # 分支端口法向量（垂直于分支方向）
        upper_normal = np.array([-np.sin(theta), np.cos(theta)])
        lower_normal = np.array([-np.sin(theta), -np.cos(theta)])

        # 上分支端口端点（从外侧到内侧，逆时针遍历）
        upper_port_outer = upper_branch_center + hw * upper_normal
        upper_port_inner = upper_branch_center - hw * upper_normal

        # 下分支端口端点（从外侧到内侧，逆时针遍历）
        lower_port_inner = lower_branch_center + hw * lower_normal  # 内侧点（靠近分岔点）
        lower_port_outer = lower_branch_center - hw * lower_normal  # 外侧点（远离分岔点）

        # 分岔点（主通道中心，两个分支内壁的汇合点）
        bifurcation_point = np.array([Lm, 0.0])

        # ============ 定义边界段 ============
        # 注意：边界段的终点是下一段的起点，确保连续性

        # 1. 入口边界（垂直，从顶部到底部，逆时针）
        self.add_boundary(
            np.array([inlet_top, inlet_bottom]),
            BoundaryType.INLET,
            "INLET"
        )

        # 2. 主通道下边缘（从入口到分岔点）
        self.add_boundary(
            np.array([inlet_bottom, main_end_bottom]),
            BoundaryType.WALL,
            "WALL-main-bottom"
        )

        # 3. 下分支外壁（从主通道末端到分支端口外侧）
        # 使用三次贝塞尔曲线或直线连接
        # 这里使用直线简化，实际可能需要平滑曲线
        # 外壁起点是主通道末端底部
        # 外壁终点需要连接到分支端口的外侧点
        # 由于分支有角度，需要计算正确的连接点
        lower_outer_start = main_end_bottom
        lower_outer_end = lower_port_outer
        self.add_boundary(
            np.array([lower_outer_start, lower_outer_end]),
            BoundaryType.WALL,
            "WALL-lower-outer"
        )

        # 4. 下分支端口（从外侧到内侧，垂直于分支方向）
        # 注意：下分支端口是从外侧点到内侧点
        # 但逆时针遍历应该是：外侧 → 内侧
        # 检查：lower_port_outer 是外侧，lower_port_inner 是内侧
        self.add_boundary(
            np.array([lower_port_outer, lower_port_inner]),
            BoundaryType.OUTLET_2,
            "OUTLET2"
        )

        # 5. 下分支内壁（从端口内侧到分岔点）
        self.add_boundary(
            np.array([lower_port_inner, bifurcation_point]),
            BoundaryType.WALL,
            "WALL-lower-inner"
        )

        # 6. 上分支内壁（从分岔点到端口内侧）
        self.add_boundary(
            np.array([bifurcation_point, upper_port_inner]),
            BoundaryType.WALL,
            "WALL-upper-inner"
        )

        # 7. 上分支端口（从内侧到外侧，垂直于分支方向）
        self.add_boundary(
            np.array([upper_port_inner, upper_port_outer]),
            BoundaryType.OUTLET_1,
            "OUTLET1"
        )

        # 8. 上分支外壁（从端口外侧到主通道末端顶部）
        upper_outer_end = upper_port_outer
        upper_outer_start = main_end_top
        self.add_boundary(
            np.array([upper_outer_end, upper_outer_start]),
            BoundaryType.WALL,
            "WALL-upper-outer"
        )

        # 9. 主通道上边缘（从分岔点回到入口）
        self.add_boundary(
            np.array([main_end_top, inlet_top]),
            BoundaryType.WALL,
            "WALL-main-top"
        )

        # ============ 构建外边界多边形 ============
        # 按逆时针顺序收集顶点
        vertices = [
            inlet_bottom,           # 1. 入口底部
            main_end_bottom,        # 2. 主通道末端底部
            lower_outer_end,        # 3. 下分支端口外侧
            lower_port_inner,       # 4. 下分支端口内侧
            bifurcation_point,      # 5. 分岔点
            upper_port_inner,       # 6. 上分支端口内侧
            upper_outer_end,        # 7. 上分支端口外侧
            main_end_top,           # 8. 主通道末端顶部
            inlet_top,              # 9. 入口顶部
        ]

        outer_boundary = np.array(vertices)

        return {
            'polygons': [
                {
                    'label': 'Y_junction_symmetric',
                    'points': outer_boundary.tolist(),
                    'type': 'outer_boundary'
                }
            ],
            'params': self.geometry_params
        }


class YJunctionSymmetricSmooth(MicrochannelGeometry):
    """
    带平滑过渡的完全对称Y型分岔道

    在分岔处使用圆弧过渡，减少流动分离
    """

    def __init__(
        self,
        L_main: float = 6.0,        # 主通道长度 (mm)
        L_branch: float = 4.0,       # 分支通道长度 (mm)
        W: float = 0.3,              # 通道宽度 (mm)
        branch_angle: float = 30.0,  # 分支角度（度），每侧
        smooth_radius: float = 0.5,  # 过渡圆弧半径 (mm)
        units: str = 'mm'
    ):
        super().__init__(units)

        self.L_main = L_main
        self.L_branch = L_branch
        self.W = W
        self.half_W = W / 2
        self.branch_angle = branch_angle
        self.smooth_radius = smooth_radius
        self.angle_rad = np.radians(branch_angle)

        self.geometry_params = {
            'type': 'Y-junction-symmetric-smooth',
            'L_main_mm': L_main,
            'L_branch_mm': L_branch,
            'W_mm': W,
            'branch_angle_deg': branch_angle,
            'smooth_radius_mm': smooth_radius,
            'symmetric': True,
            'units': units
        }

    def _generate_arc(self, center: np.ndarray, radius: float,
                      start_angle: float, end_angle: float,
                      num_points: int = 20) -> np.ndarray:
        """生成圆弧上的点"""
        angles = np.linspace(start_angle, end_angle, num_points)
        x = center[0] + radius * np.cos(angles)
        y = center[1] + radius * np.sin(angles)
        return np.column_stack([x, y])

    def generate(self) -> Dict:
        """生成带平滑过渡的Y型分岔道"""
        W = self.W
        hw = self.half_W
        Lm = self.L_main
        Lb = self.L_branch
        theta = self.angle_rad
        R = self.smooth_radius

        # 基础顶点（与对称版本相同）
        inlet_bottom = np.array([0.0, -hw])
        inlet_top = np.array([0.0, hw])
        main_end_bottom = np.array([Lm, -hw])
        main_end_top = np.array([Lm, hw])

        upper_branch_center = np.array([
            Lm + Lb * np.cos(theta),
            Lb * np.sin(theta)
        ])
        lower_branch_center = np.array([
            Lm + Lb * np.cos(theta),
            -Lb * np.sin(theta)
        ])

        upper_normal = np.array([-np.sin(theta), np.cos(theta)])
        lower_normal = np.array([-np.sin(theta), -np.cos(theta)])

        upper_port_outer = upper_branch_center + hw * upper_normal
        upper_port_inner = upper_branch_center - hw * upper_normal
        lower_port_inner = lower_branch_center + hw * lower_normal
        lower_port_outer = lower_branch_center - hw * lower_normal

        bifurcation_point = np.array([Lm, 0.0])

        # 生成平滑过渡的圆弧
        # 下分支外壁圆弧
        lower_outer_center = main_end_bottom + R * np.array([np.cos(theta), -np.sin(theta)])
        lower_arc_start_angle = np.pi  # 从左侧开始
        lower_arc_end_angle = -theta   # 到分支方向
        lower_outer_arc = self._generate_arc(
            lower_outer_center, R,
            lower_arc_start_angle, lower_arc_end_angle
        )

        # 上分支外壁圆弧
        upper_outer_center = main_end_top + R * np.array([np.cos(theta), np.sin(theta)])
        upper_arc_start_angle = np.pi
        upper_arc_end_angle = theta
        upper_outer_arc = self._generate_arc(
            upper_outer_center, R,
            upper_arc_start_angle, upper_arc_end_angle
        )

        # 添加边界段
        self.add_boundary(np.array([inlet_top, inlet_bottom]), BoundaryType.INLET, "INLET")
        self.add_boundary(np.array([inlet_bottom, main_end_bottom]), BoundaryType.WALL, "WALL-main-bottom")

        # 使用圆弧作为外壁
        self.add_boundary(lower_outer_arc, BoundaryType.WALL, "WALL-lower-outer-arc")

        # 连接圆弧到端口
        arc_end_lower = lower_outer_arc[-1]
        self.add_boundary(np.array([arc_end_lower, lower_port_outer]), BoundaryType.WALL, "WALL-lower-outer-connect")
        self.add_boundary(np.array([lower_port_outer, lower_port_inner]), BoundaryType.OUTLET_2, "OUTLET2")
        self.add_boundary(np.array([lower_port_inner, bifurcation_point]), BoundaryType.WALL, "WALL-lower-inner")
        self.add_boundary(np.array([bifurcation_point, upper_port_inner]), BoundaryType.WALL, "WALL-upper-inner")
        self.add_boundary(np.array([upper_port_inner, upper_port_outer]), BoundaryType.OUTLET_1, "OUTLET1")

        # 连接端口到圆弧
        self.add_boundary(np.array([upper_port_outer, upper_outer_arc[-1]]), BoundaryType.WALL, "WALL-upper-outer-connect")

        # 使用圆弧作为上外壁
        self.add_boundary(upper_outer_arc, BoundaryType.WALL, "WALL-upper-outer-arc")

        self.add_boundary(np.array([main_end_top, inlet_top]), BoundaryType.WALL, "WALL-main-top")

        # 构建多边形顶点（简化为关键点）
        vertices = [
            inlet_bottom,
            main_end_bottom,
            lower_port_outer,
            lower_port_inner,
            bifurcation_point,
            upper_port_inner,
            upper_port_outer,
            main_end_top,
            inlet_top,
        ]

        outer_boundary = np.array(vertices)

        return {
            'polygons': [
                {
                    'label': 'Y_junction_symmetric_smooth',
                    'points': outer_boundary.tolist(),
                    'type': 'outer_boundary',
                    'arc_points': {
                        'lower_outer': lower_outer_arc.tolist(),
                        'upper_outer': upper_outer_arc.tolist()
                    }
                }
            ],
            'params': self.geometry_params
        }


# ============ 便捷创建函数 ============

def create_yjunction_symmetric(
    L_main: float = 6.0,
    L_branch: float = 4.0,
    W: float = 0.3,
    branch_angle: float = 30.0
) -> YJunctionSymmetric:
    """
    创建标准对称Y型分岔道

    Args:
        L_main: 主通道长度 (mm)
        L_branch: 分支长度 (mm)
        W: 通道宽度 (mm)
        branch_angle: 分支角度（度），每侧
    """
    return YJunctionSymmetric(
        L_main=L_main,
        L_branch=L_branch,
        W=W,
        branch_angle=branch_angle,
        units='mm'
    )


def create_yjunction_symmetric_smooth(
    L_main: float = 6.0,
    L_branch: float = 4.0,
    W: float = 0.3,
    branch_angle: float = 30.0,
    smooth_radius: float = 0.5
) -> YJunctionSymmetricSmooth:
    """
    创建带平滑过渡的对称Y型分岔道

    Args:
        L_main: 主通道长度 (mm)
        L_branch: 分支长度 (mm)
        W: 通道宽度 (mm)
        branch_angle: 分支角度（度），每侧
        smooth_radius: 过渡圆弧半径 (mm)
    """
    return YJunctionSymmetricSmooth(
        L_main=L_main,
        L_branch=L_branch,
        W=W,
        branch_angle=branch_angle,
        smooth_radius=smooth_radius,
        units='mm'
    )


# ============ 基于用户绘制的对称修正版本 ============

def create_yjunction_from_drawing_corrected() -> YJunctionSymmetric:
    """
    基于用户绘制的尺寸，创建修正的对称Y型分岔道

    从 drawn_geometry.txt 提取的参数：
    - 通道宽度: 约 0.31 mm
    - 主通道长度: 约 6.0 mm
    - 分支长度: 约 2.7 mm
    - 分支角度: 约 40°
    """
    return YJunctionSymmetric(
        L_main=6.0,
        L_branch=2.7,
        W=0.31,
        branch_angle=40.0,
        units='mm'
    )


if __name__ == '__main__':
    print("=" * 60)
    print("Y-Junction Symmetric - 完全对称版本")
    print("=" * 60)

    # 测试标准对称版本
    print("\n--- 标准对称Y型分岔道 ---")
    geom = create_yjunction_symmetric()
    data = geom.generate()

    print(f"\n几何参数:")
    for key, value in geom.geometry_params.items():
        print(f"  {key}: {value}")

    geom.print_boundary_summary()

    # 测试基于用户绘制的修正版本
    print("\n--- 基于用户绘制的修正版本 ---")
    geom_corrected = create_yjunction_from_drawing_corrected()
    data_corrected = geom_corrected.generate()

    print(f"\n几何参数:")
    for key, value in geom_corrected.geometry_params.items():
        print(f"  {key}: {value}")

    geom_corrected.print_boundary_summary()

    print("\n" + "=" * 60)
