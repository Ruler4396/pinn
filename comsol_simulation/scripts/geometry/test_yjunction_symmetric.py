# -*- coding: utf-8 -*-
"""
测试并可视化对称的Y型分岔道
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from yjunction_symmetric import (
    create_yjunction_symmetric,
    create_yjunction_symmetric_smooth,
    create_yjunction_from_drawing_corrected
)
from yjunction_microfluidic import create_yjunction_standard
from base_geometry import BoundaryType


def plot_geometry(geom, ax, title, show_vertices=True, show_boundaries=True):
    """绘制几何形状"""
    data = geom.generate()

    # 获取多边形顶点
    polygon_points = np.array(data['polygons'][0]['points'])

    # 绘制填充多边形
    poly = Polygon(polygon_points, closed=True, facecolor='lightblue',
                   edgecolor='black', linewidth=2, alpha=0.5)
    ax.add_patch(poly)

    # 绘制顶点
    if show_vertices:
        ax.plot(polygon_points[:, 0], polygon_points[:, 1], 'ro',
                markersize=6, label='vertices')
        # 标注顶点序号
        for i, (x, y) in enumerate(polygon_points):
            ax.annotate(f'{i+1}', (x, y), xytext=(5, 5),
                       textcoords='offset points', fontsize=8, color='red')

    # 绘制边界段
    if show_boundaries:
        colors = {
            'inlet': 'green',
            'outlet1': 'blue',
            'outlet2': 'blue',
            'wall': 'red'
        }

        for boundary in geom.boundaries:
            points = boundary.points
            btype = boundary.boundary_type.value
            color = colors.get(btype, 'black')
            label = boundary.label

            ax.plot(points[:, 0], points[:, 1], color=color,
                   linewidth=2, linestyle='-', alpha=0.7)

            # 标注边界类型
            mid_point = np.mean(points, axis=0)
            ax.text(mid_point[0], mid_point[1], label,
                   fontsize=7, ha='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

    # 设置坐标轴
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_title(title)

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


def test_symmetry(geom, title):
    """测试几何的对称性"""
    data = geom.generate()
    points = np.array(data['polygons'][0]['points'])

    # 计算几何中心
    center_x = np.mean(points[:, 0])
    center_y = np.mean(points[:, 1])

    print(f"\n{title} - 对称性检查:")
    print(f"  几何中心: ({center_x:.3f}, {center_y:.3f})")

    # 检查X轴对称性（上下对称）
    # 找到对称点对
    symmetric_pairs = []
    n = len(points)
    for i in range(n):
        for j in range(i+1, n):
            p1 = points[i]
            p2 = points[j]
            # 检查是否关于X轴对称
            if abs(p1[0] - p2[0]) < 0.01 and abs(p1[1] + p2[1]) < 0.01:
                symmetric_pairs.append((i, j))

    print(f"  对称点对数: {len(symmetric_pairs)}")

    # 检查入口和出口的对称性
    from base_geometry import BoundaryType
    inlets = geom.get_boundaries_by_type(BoundaryType.INLET)
    outlets1 = geom.get_boundaries_by_type(BoundaryType.OUTLET_1)
    outlets2 = geom.get_boundaries_by_type(BoundaryType.OUTLET_2)

    if inlets and outlets1 and outlets2:
        inlet_y = np.mean(inlets[0].points[:, 1])
        outlet1_y = np.mean(outlets1[0].points[:, 1])
        outlet2_y = np.mean(outlets2[0].points[:, 1])

        print(f"  入口Y中心: {inlet_y:.3f}")
        print(f"  出口1Y中心: {outlet1_y:.3f}")
        print(f"  出口2Y中心: {outlet2_y:.3f}")
        print(f"  出口对称偏差: {abs(outlet1_y + outlet2_y):.6f}")

        # 检查出口长度是否相等
        outlet1_len = geom._calculate_length(outlets1[0].points)
        outlet2_len = geom._calculate_length(outlets2[0].points)
        print(f"  出口1长度: {outlet1_len:.3f} mm")
        print(f"  出口2长度: {outlet2_len:.3f} mm")
        print(f"  长度偏差: {abs(outlet1_len - outlet2_len):.6f} mm")


def main():
    """主测试函数"""
    from base_geometry import BoundaryType

    # 创建多个几何实例进行对比
    geometries = [
        (create_yjunction_symmetric(), "对称Y型 (标准)"),
        (create_yjunction_from_drawing_corrected(), "对称Y型 (基于用户绘制)"),
        (create_yjunction_symmetric_smooth(), "对称Y型 (平滑过渡)"),
    ]

    # 创建图形
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for i, (geom, title) in enumerate(geometries):
        if i < len(axes):
            plot_geometry(geom, axes[i], title)
            test_symmetry(geom, title)

    # 最后一个子图对比
    if len(geometries) < len(axes):
        ax = axes[len(geometries)]
        for geom, title in geometries:
            data = geom.generate()
            points = np.array(data['polygons'][0]['points'])
            ax.plot(points[:, 0], points[:, 1], marker='o', label=title,
                   linewidth=2, markersize=4, alpha=0.7)

        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_title('几何对比')
        ax.legend()

    plt.tight_layout()

    # 保存图片
    output_path = os.path.join(
        os.path.dirname(__file__),
        'output',
        'y_junction_symmetric_comparison.png'
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n图片已保存至: {output_path}")

    # 打印详细信息
    print("\n" + "=" * 60)
    print("详细几何参数")
    print("=" * 60)

    for geom, title in geometries:
        print(f"\n{title}:")
        geom.print_boundary_summary()

    # 显示图形
    plt.show()


if __name__ == '__main__':
    main()
