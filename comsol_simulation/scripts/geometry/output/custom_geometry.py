# -*- coding: utf-8 -*-
"""
自定义几何模型 - 从交互式绘图板生成

此文件由 interactive_drawing_board.py 自动生成
包含所有绘制的矩形和线段定义
"""

import numpy as np
from base_geometry import MicrochannelGeometry, BoundaryType


class CustomGeometry(MicrochannelGeometry):
    """
    自定义几何类 - 基于用户绘制的图形
    """

    def __init__(self, units='mm'):
        super().__init__(units)
        self.geometry_params = {
            'type': 'custom_from_drawing',
            'source': 'interactive_drawing_board',
            'units': units
        }

    def generate(self):
        """生成几何数据"""

        # 定义线段
        self.lines = [
            (2.045455, 3.989610, 8.009091, 3.989610),  # 线段1 L=5.96mm, θ=0.0°
            (1.983117, 3.989610, 1.983117, 3.677922),  # 线段2 L=0.31mm, θ=-90.0°
            (1.983117, 3.677922, 8.029870, 3.677922),  # 线段3 L=6.05mm, θ=0.0°
            (8.029870, 4.031169, 9.983117, 5.963636),  # 线段4 L=2.75mm, θ=44.7°
            (8.071429, 3.636364, 9.941558, 2.285714),  # 线段5 L=2.31mm, θ=-35.8°
            (9.962338, 5.963636, 10.128571, 5.797403),  # 线段6 L=0.24mm, θ=-45.0°
            (10.128571, 5.797403, 8.133766, 3.844156),  # 线段7 L=2.79mm, θ=-135.6°
            (8.133766, 3.844156, 10.003896, 2.472727),  # 线段8 L=2.32mm, θ=-36.3°
            (10.003896, 2.472727, 9.920779, 2.306494),  # 线段9 L=0.19mm, θ=-116.6°
        ]

        # 从绘制的线段构建多边形边界
        # 将所有线段的端点提取出来，构成外边界
        points = []

        # 按顺序添加线段端点
        points.append(np.array([2.045455, 3.989610]))  # 线段1起点
        points.append(np.array([8.009091, 3.989610]))  # 线段1终点
        points.append(np.array([1.983117, 3.989610]))  # 线段2起点
        points.append(np.array([1.983117, 3.677922]))  # 线段2终点
        points.append(np.array([1.983117, 3.677922]))  # 线段3起点
        points.append(np.array([8.029870, 3.677922]))  # 线段3终点
        points.append(np.array([8.029870, 4.031169]))  # 线段4起点
        points.append(np.array([9.983117, 5.963636]))  # 线段4终点
        points.append(np.array([8.071429, 3.636364]))  # 线段5起点
        points.append(np.array([9.941558, 2.285714]))  # 线段5终点
        points.append(np.array([9.962338, 5.963636]))  # 线段6起点
        points.append(np.array([10.128571, 5.797403]))  # 线段6终点
        points.append(np.array([10.128571, 5.797403]))  # 线段7起点
        points.append(np.array([8.133766, 3.844156]))  # 线段7终点
        points.append(np.array([8.133766, 3.844156]))  # 线段8起点
        points.append(np.array([10.003896, 2.472727]))  # 线段8终点
        points.append(np.array([10.003896, 2.472727]))  # 线段9起点
        points.append(np.array([9.920779, 2.306494]))  # 线段9终点

        # 定义外边界多边形
        outer_boundary = np.array(points)

        # 定义边界段
        # 注意：这里简化处理，将所有线段都作为壁面
        # 你需要根据实际情况指定入口和出口

        # 添加所有线段作为边界（默认为壁面）
        # 请根据实际情况修改边界类型
        self.add_boundary(np.array([2.045455, 3.989610]), np.array([8.009091, 3.989610]), BoundaryType.INLET, "INLET")  # 线段1
        self.add_boundary(np.array([1.983117, 3.989610]), np.array([1.983117, 3.677922]), BoundaryType.WALL, "WALL_1")  # 线段2
        self.add_boundary(np.array([1.983117, 3.677922]), np.array([8.029870, 3.677922]), BoundaryType.WALL, "WALL_2")  # 线段3
        self.add_boundary(np.array([8.029870, 4.031169]), np.array([9.983117, 5.963636]), BoundaryType.WALL, "WALL_3")  # 线段4
        self.add_boundary(np.array([8.071429, 3.636364]), np.array([9.941558, 2.285714]), BoundaryType.WALL, "WALL_4")  # 线段5
        self.add_boundary(np.array([9.962338, 5.963636]), np.array([10.128571, 5.797403]), BoundaryType.WALL, "WALL_5")  # 线段6
        self.add_boundary(np.array([10.128571, 5.797403]), np.array([8.133766, 3.844156]), BoundaryType.WALL, "WALL_6")  # 线段7
        self.add_boundary(np.array([8.133766, 3.844156]), np.array([10.003896, 2.472727]), BoundaryType.WALL, "WALL_7")  # 线段8
        self.add_boundary(np.array([10.003896, 2.472727]), np.array([9.920779, 2.306494]), BoundaryType.OUTLET_1, "OUTLET1")  # 线段9

        return {
            'polygons': [
                {
                    'label': 'custom_geometry_domain',
                    'points': outer_boundary.tolist(),
                    'type': 'outer_boundary'
                }
            ],
            'params': self.geometry_params
        }


def create_custom_geometry():
    """创建自定义几何对象"""
    return CustomGeometry()


if __name__ == '__main__':
    print("=" * 60)
    print("自定义几何模型测试")
    print("=" * 60)

    geom = create_custom_geometry()
    data = geom.generate()

    print(f"\n几何参数:")
    for key, value in geom.geometry_params.items():
        print(f"  {key}: {value}")

    geom.print_boundary_summary()

    print("\n" + "=" * 60)
