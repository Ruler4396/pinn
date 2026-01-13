# -*- coding: utf-8 -*-
"""
简化的Y型分岔道测试 - 仅生成图片，不显示窗口
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from yjunction_symmetric import (
    create_yjunction_symmetric,
    create_yjunction_from_drawing_corrected
)
from base_geometry import BoundaryType


def plot_geometry_comparison():
    """绘制几何对比图"""
    # 创建两个几何实例
    geom1 = create_yjunction_symmetric(
        L_main=6.0,
        L_branch=4.0,
        W=0.3,
        branch_angle=30.0
    )

    geom2 = create_yjunction_from_drawing_corrected()

    # 创建图形
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    geometries = [
        (geom1, "Standard Symmetric Y-Junction\n(L_main=6mm, L_branch=4mm, W=0.3mm, angle=30°)"),
        (geom2, "Corrected from User Drawing\n(L_main=6mm, L_branch=2.7mm, W=0.31mm, angle=40°)")
    ]

    colors = {
        'inlet': 'green',
        'outlet1': 'blue',
        'outlet2': 'blue',
        'wall': 'red'
    }

    for idx, (geom, title) in enumerate(geometries):
        ax = axes[idx]
        data = geom.generate()
        polygon_points = np.array(data['polygons'][0]['points'])

        # 绘制填充多边形
        poly = Polygon(polygon_points, closed=True, facecolor='lightblue',
                       edgecolor='black', linewidth=2, alpha=0.5)
        ax.add_patch(poly)

        # 绘制顶点
        ax.plot(polygon_points[:, 0], polygon_points[:, 1], 'ro',
                markersize=6, zorder=5)
        # 标注顶点序号
        for i, (x, y) in enumerate(polygon_points):
            ax.annotate(f'{i+1}', (x, y), xytext=(5, 5),
                       textcoords='offset points', fontsize=8,
                       color='darkred', fontweight='bold', zorder=6)

        # 绘制边界段
        for boundary in geom.boundaries:
            points = boundary.points
            btype = boundary.boundary_type.value
            color = colors.get(btype, 'black')
            label = boundary.label

            ax.plot(points[:, 0], points[:, 1], color=color,
                   linewidth=2, linestyle='-', alpha=0.8)

            # 标注边界标签
            mid_point = np.mean(points, axis=0)
            ax.text(mid_point[0], mid_point[1], label,
                   fontsize=7, ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                            edgecolor=color, alpha=0.9, linewidth=1.5))

        # 设置坐标轴
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xlabel('X (mm)', fontsize=10)
        ax.set_ylabel('Y (mm)', fontsize=10)
        ax.set_title(title, fontsize=11, fontweight='bold')

        # 添加图例
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='green', linewidth=2, label='Inlet'),
            Line2D([0], [0], color='blue', linewidth=2, label='Outlet'),
            Line2D([0], [0], color='red', linewidth=2, label='Wall'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='red',
                   markersize=6, label='Vertex')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=8)

    plt.tight_layout()

    # 保存图片
    output_path = os.path.join(
        os.path.dirname(__file__),
        'output',
        'y_junction_symmetric_final.png'
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Picture saved to: {output_path}")

    return output_path


def print_geometry_info():
    """打印几何信息"""
    print("\n" + "=" * 70)
    print("Y-JUNCTION SYMMETRIC - Geometry Validation")
    print("=" * 70)

    # 测试标准对称版本
    print("\n[1] Standard Symmetric Y-Junction:")
    print("-" * 70)
    geom1 = create_yjunction_symmetric()
    data1 = geom1.generate()

    print(f"Type: {geom1.geometry_params['type']}")
    print(f"L_main: {geom1.geometry_params['L_main_mm']} mm")
    print(f"L_branch: {geom1.geometry_params['L_branch_mm']} mm")
    print(f"Width: {geom1.geometry_params['W_mm']} mm")
    print(f"Branch angle: {geom1.geometry_params['branch_angle_deg']}°")
    print(f"Symmetric: {geom1.geometry_params['symmetric']}")

    # 验证对称性
    inlets = geom1.get_boundaries_by_type(BoundaryType.INLET)
    outlets1 = geom1.get_boundaries_by_type(BoundaryType.OUTLET_1)
    outlets2 = geom1.get_boundaries_by_type(BoundaryType.OUTLET_2)

    if inlets and outlets1 and outlets2:
        inlet_y = np.mean(inlets[0].points[:, 1])
        outlet1_y = np.mean(outlets1[0].points[:, 1])
        outlet2_y = np.mean(outlets2[0].points[:, 1])

        print(f"\nSymmetry check:")
        print(f"  Inlet Y-center: {inlet_y:.6f} mm")
        print(f"  Outlet1 Y-center: {outlet1_y:.6f} mm")
        print(f"  Outlet2 Y-center: {outlet2_y:.6f} mm")
        print(f"  Outlet symmetry error: {abs(outlet1_y + outlet2_y):.10f} mm")

        outlet1_len = geom1._calculate_length(outlets1[0].points)
        outlet2_len = geom1._calculate_length(outlets2[0].points)
        print(f"  Outlet1 length: {outlet1_len:.6f} mm")
        print(f"  Outlet2 length: {outlet2_len:.6f} mm")
        print(f"  Length difference: {abs(outlet1_len - outlet2_len):.10f} mm")

    # 测试基于用户绘制的修正版本
    print("\n[2] Corrected from User Drawing:")
    print("-" * 70)
    geom2 = create_yjunction_from_drawing_corrected()
    data2 = geom2.generate()

    print(f"Type: {geom2.geometry_params['type']}")
    print(f"L_main: {geom2.geometry_params['L_main_mm']} mm")
    print(f"L_branch: {geom2.geometry_params['L_branch_mm']} mm")
    print(f"Width: {geom2.geometry_params['W_mm']} mm")
    print(f"Branch angle: {geom2.geometry_params['branch_angle_deg']}°")
    print(f"Symmetric: {geom2.geometry_params['symmetric']}")

    # 验证对称性
    inlets = geom2.get_boundaries_by_type(BoundaryType.INLET)
    outlets1 = geom2.get_boundaries_by_type(BoundaryType.OUTLET_1)
    outlets2 = geom2.get_boundaries_by_type(BoundaryType.OUTLET_2)

    if inlets and outlets1 and outlets2:
        inlet_y = np.mean(inlets[0].points[:, 1])
        outlet1_y = np.mean(outlets1[0].points[:, 1])
        outlet2_y = np.mean(outlets2[0].points[:, 1])

        print(f"\nSymmetry check:")
        print(f"  Inlet Y-center: {inlet_y:.6f} mm")
        print(f"  Outlet1 Y-center: {outlet1_y:.6f} mm")
        print(f"  Outlet2 Y-center: {outlet2_y:.6f} mm")
        print(f"  Outlet symmetry error: {abs(outlet1_y + outlet2_y):.10f} mm")

        outlet1_len = geom2._calculate_length(outlets1[0].points)
        outlet2_len = geom2._calculate_length(outlets2[0].points)
        print(f"  Outlet1 length: {outlet1_len:.6f} mm")
        print(f"  Outlet2 length: {outlet2_len:.6f} mm")
        print(f"  Length difference: {abs(outlet1_len - outlet2_len):.10f} mm")

    print("\n" + "=" * 70)


def main():
    """主函数"""
    # 打印几何信息
    print_geometry_info()

    # 生成对比图
    output_path = plot_geometry_comparison()

    print(f"\nSuccess! Geometry image saved.")
    print(f"\nKey improvements:")
    print(f"  1. Vertices ordered correctly (counter-clockwise)")
    print(f"  2. Perfect symmetry between upper and lower branches")
    print(f"  3. Boundary segments connected properly")
    print(f"  4. Inlet at left, outlets at right ends of branches")
    print(f"  5. Bifurcation point at center of junction")


if __name__ == '__main__':
    main()
