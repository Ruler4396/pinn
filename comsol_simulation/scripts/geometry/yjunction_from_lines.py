# -*- coding: utf-8 -*-
"""
Y型分岔道几何 - 直接基于用户绘制的线段

直接使用用户绘制的线段构建几何，保持原有的连接顺序
不做任何"修正"，只是将图形平移到中心线y=0
"""

import numpy as np
from typing import Dict
from base_geometry import MicrochannelGeometry, BoundaryType


class YJunctionFromLines(MicrochannelGeometry):
    """
    基于用户绘制线段的Y型分岔道

    直接使用绘制的线段构建，保持原有连接顺序
    """

    def __init__(self, units='mm'):
        super().__init__(units)

        # 原始绘制的线段数据
        # 线段1: 主通道上边缘
        # 线段2: 入口（左端）
        # 线段3: 主通道下边缘
        # 线段4: 上分支外壁
        # 线段5: 下分支外壁
        # 线段6: 上分支端口
        # 线段7: 上分支内壁
        # 线段8: 下分支内壁
        # 线段9: 下分支端口
        self.raw_lines = [
            (2.045455, 3.989610, 8.009091, 3.989610),
            (1.983117, 3.989610, 1.983117, 3.677922),
            (1.983117, 3.677922, 8.029870, 3.677922),
            (8.029870, 4.031169, 9.983117, 5.963636),
            (8.071429, 3.636364, 9.941558, 2.285714),
            (9.962338, 5.963636, 10.128571, 5.797403),
            (10.128571, 5.797403, 8.133766, 3.844156),
            (8.133766, 3.844156, 10.003896, 2.472727),
            (10.003896, 2.472727, 9.920779, 2.306494),
        ]

        # 计算中心线y坐标（取主通道上下边缘的平均值）
        y_center = (3.989610 + 3.677922) / 2
        self.y_offset = y_center  # 需要平移的距离

        # 通道宽度
        self.W = 3.989610 - 3.677922
        self.half_W = self.W / 2

        # 主通道长度
        self.L_main = 8.0 - 2.0

        # 分支长度
        self.L_branch = 2.7

        # 分支角度（近似）
        self.branch_angle = 40

        self.geometry_params = {
            'type': 'Y-junction-from-lines',
            'source': 'user_drawing_raw',
            'y_offset': self.y_offset,
            'W': self.W,
            'L_main': self.L_main,
            'L_branch': self.L_branch,
            'branch_angle': self.branch_angle,
            'units': units
        }

    def _shift_point(self, x, y):
        """将点平移，使中心线在y=0"""
        return np.array([x, y - self.y_offset])

    def generate(self) -> Dict:
        """
        直接使用绘制的线段构建几何

        按照正确的连接顺序构建边界
        """
        # 定义边界段（按正确的连接顺序）
        # 使用平移后的坐标

        # 入口边界（线段2平移后）
        p1 = self._shift_point(1.983117, 3.989610)
        p2 = self._shift_point(1.983117, 3.677922)
        self.add_boundary(np.array([p1, p2]), BoundaryType.INLET, "INLET")

        # 主通道下边缘（线段3平移后）
        p2 = self._shift_point(1.983117, 3.677922)
        p3 = self._shift_point(8.029870, 3.677922)
        self.add_boundary(np.array([p2, p3]), BoundaryType.WALL, "WALL-bottom")

        # 下分支外壁（线段5平移后）
        p3 = self._shift_point(8.071429, 3.636364)
        p4 = self._shift_point(9.941558, 2.285714)
        self.add_boundary(np.array([p3, p4]), BoundaryType.WALL, "WALL-lower-outer")

        # 下分支端口（线段9平移后）
        p4 = self._shift_point(10.003896, 2.472727)
        p5 = self._shift_point(9.920779, 2.306494)
        self.add_boundary(np.array([p4, p5]), BoundaryType.OUTLET_2, "OUTLET2")

        # 下分支内壁（线段8平移后）
        p5 = self._shift_point(10.003896, 2.472727)
        p6 = self._shift_point(8.133766, 3.844156)
        self.add_boundary(np.array([p5, p6]), BoundaryType.WALL, "WALL-lower-inner")

        # 上分支内壁（线段7平移后）
        p6 = self._shift_point(10.128571, 5.797403)
        p7 = self._shift_point(8.133766, 3.844156)
        self.add_boundary(np.array([p6, p7]), BoundaryType.WALL, "WALL-upper-inner")

        # 上分支端口（线段6平移后）
        p7 = self._shift_point(9.962338, 5.963636)
        p8 = self._shift_point(10.128571, 5.797403)
        self.add_boundary(np.array([p7, p8]), BoundaryType.OUTLET_1, "OUTLET1")

        # 上分支外壁（线段4平移后）
        p8 = self._shift_point(9.983117, 5.963636)
        p9 = self._shift_point(8.029870, 4.031169)
        self.add_boundary(np.array([p8, p9]), BoundaryType.WALL, "WALL-upper-outer")

        # 主通道上边缘（线段1平移后）
        p9 = self._shift_point(8.009091, 3.989610)
        p10 = self._shift_point(2.045455, 3.989610)
        self.add_boundary(np.array([p9, p10]), BoundaryType.WALL, "WALL-top")

        # 构建外边界多边形（逆时针顺序）
        # 按照边界段的连接顺序收集所有唯一的顶点
        vertices = []

        # 入口底部
        vertices.append(self._shift_point(1.983117, 3.677922))
        # 主通道右下
        vertices.append(self._shift_point(8.029870, 3.677922))
        # 下分支外壁终点
        vertices.append(self._shift_point(9.941558, 2.285714))
        # 下分支端口
        vertices.append(self._shift_point(9.920779, 2.306494))
        # 下分支内壁终点
        vertices.append(self._shift_point(10.003896, 2.472727))
        # 下分支内壁起点/上分支内壁起点
        vertices.append(self._shift_point(8.133766, 3.844156))
        # 上分支内壁终点
        vertices.append(self._shift_point(10.128571, 5.797403))
        # 上分支端口
        vertices.append(self._shift_point(9.962338, 5.963636))
        # 上分支外壁终点
        vertices.append(self._shift_point(9.983117, 5.963636))
        # 上分支外壁起点
        vertices.append(self._shift_point(8.029870, 4.031169))
        # 主通道右上
        vertices.append(self._shift_point(8.009091, 3.989610))
        # 入口顶部
        vertices.append(self._shift_point(2.045455, 3.989610))
        # 回到入口底部
        vertices.append(self._shift_point(1.983117, 3.989610))
        vertices.append(self._shift_point(1.983117, 3.677922))

        outer_boundary = np.array(vertices)

        return {
            'polygons': [
                {
                    'label': 'Y_junction_from_lines',
                    'points': outer_boundary.tolist(),
                    'type': 'outer_boundary'
                }
            ],
            'params': self.geometry_params
        }


def create_yjunction_from_lines() -> YJunctionFromLines:
    """直接从用户绘制的线段创建Y型分岔道"""
    return YJunctionFromLines()


if __name__ == '__main__':
    print("=" * 60)
    print("Y-Junction from User Lines (Raw)")
    print("=" * 60)

    geom = create_yjunction_from_lines()
    data = geom.generate()

    print(f"\n几何参数:")
    for key, value in geom.geometry_params.items():
        print(f"  {key}: {value}")

    geom.print_boundary_summary()

    print("\n" + "=" * 60)
