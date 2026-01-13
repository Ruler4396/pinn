# -*- coding: utf-8 -*-
"""
可视化修正后的Y型分岔道 - 按照正确顺序 1→9→8→7→6→5→3→4→2→1
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from yjunction_corrected import create_yjunction_corrected
from base_geometry import BoundaryType


def visualize_corrected():
    """可视化修正后的Y型分岔道"""
    geom = create_yjunction_corrected()
    data = geom.generate()

    # 获取多边形顶点
    polygon_points = np.array(data['polygons'][0]['points'])

    # 创建图形
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    # 定义顶点名称（按顺序 1→9→8→7→6→5→3→4→2→1）
    vertex_names = {
        0: '1\n(inlet_bot)',
        1: '9\n(inlet_top)',
        2: '8\n(main_end_top)',
        3: '7\n(up_port_outer)',
        4: '6\n(up_port_inner)',
        5: '5\n(bifurcation)',
        6: '3\n(low_port_inner)',
        7: '4\n(low_port_outer)',
        8: '2\n(main_end_bot)',
    }

    # 定义连接顺序标签
    edge_labels = [
        '1→9\nINLET',
        '9→8\nWALL-main-top',
        '8→7\nWALL-upper-outer',
        '7→6\nOUTLET1',
        '6→5\nWALL-upper-inner',
        '5→3\nWALL-lower-inner',
        '3→4\nOUTLET2',
        '4→2\nWALL-lower-outer',
        '2→1\nWALL-main-bottom',
    ]

    # 绘制填充多边形
    poly = Polygon(polygon_points, closed=True, facecolor='lightblue',
                   edgecolor='black', linewidth=3, alpha=0.3)
    ax.add_patch(poly)

    # 绘制边界段（带颜色）
    colors = {
        'inlet': 'green',
        'outlet': 'blue',
        'wall': 'red'
    }

    for i, boundary in enumerate(geom.boundaries):
        points = boundary.points
        btype = boundary.boundary_type.value

        if btype == 'inlet':
            color = colors['inlet']
            linewidth = 3
        elif btype in ['outlet1', 'outlet2']:
            color = colors['outlet']
            linewidth = 3
        else:
            color = colors['wall']
            linewidth = 2

        # 绘制边界段
        ax.plot(points[:, 0], points[:, 1], color=color,
               linewidth=linewidth, alpha=0.8)

        # 在边界段中点添加箭头指示方向
        if len(points) >= 2:
            mid_point = np.mean(points, axis=0)
            direction = points[1] - points[0]
            direction = direction / np.linalg.norm(direction)
            ax.arrow(mid_point[0] - 0.1*direction[0], mid_point[1] - 0.1*direction[1],
                    0.2*direction[0], 0.2*direction[1],
                    head_width=0.15, head_length=0.1, fc=color, ec=color, alpha=0.6)

    # 绘制顶点和序号
    for i, (x, y) in enumerate(polygon_points):
        # 绘制顶点
        ax.plot(x, y, 'ko', markersize=12, zorder=5)
        ax.plot(x, y, 'ro', markersize=8, zorder=6)

        # 标注序号和名称
        ax.annotate(vertex_names[i], (x, y), xytext=(20, 20),
                   textcoords='offset points', fontsize=11,
                   color='darkred', fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow',
                            edgecolor='red', alpha=0.9, linewidth=2),
                   arrowprops=dict(arrowstyle='->', color='red', lw=2),
                   zorder=7)

    # 在每条边的中点添加标签
    for i in range(len(polygon_points)):
        p1 = polygon_points[i]
        p2 = polygon_points[(i+1) % len(polygon_points)]
        mid_point = (p1 + p2) / 2

        # 根据边界类型确定颜色
        boundary = geom.boundaries[i]
        btype = boundary.boundary_type.value

        if btype == 'inlet':
            text_color = 'green'
            bbox_color = 'lightgreen'
        elif btype in ['outlet1', 'outlet2']:
            text_color = 'blue'
            bbox_color = 'lightblue'
        else:
            text_color = 'darkred'
            bbox_color = 'mistyrose'

        ax.annotate(edge_labels[i], mid_point, fontsize=9,
                   color=text_color, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor=bbox_color,
                            edgecolor=text_color, alpha=0.9, linewidth=1.5),
                   ha='center', va='center')

    # 设置坐标轴
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=1)
    ax.set_xlabel('X (mm)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y (mm)', fontsize=12, fontweight='bold')
    ax.set_title('Y-Junction Corrected - Vertex Order: 1→9→8→7→6→5→3→4→2→1',
                fontsize=14, fontweight='bold', pad=20)

    # 添加图例
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='green', linewidth=3, label='Inlet'),
        Line2D([0], [0], color='blue', linewidth=3, label='Outlet'),
        Line2D([0], [0], color='red', linewidth=2, label='Wall'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red',
               markersize=8, label='Vertex')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=11,
             framealpha=0.9, edgecolor='black')

    # 添加信息框
    W_main = geom.W_main
    W_branch = geom.W_branch

    info_text = f"Geometry Parameters:\n"
    info_text += f"L_main = {geom.L_main} mm\n"
    info_text += f"L_branch = {geom.L_branch} mm\n"
    info_text += f"W_main = {W_main} mm\n"
    info_text += f"W_branch = {W_branch} mm\n"
    info_text += f"Branch angle = {geom.branch_angle}°\n"
    info_text += f"\nWidth Relationship:\n"
    info_text += f"W_main = 2 × W_branch\n"
    info_text += f"{W_main} mm = 2 × {W_branch} mm\n"
    info_text += f"\nVertex order:\n"
    info_text += f"1→9→8→7→6→5→3→4→2→1"

    ax.text(0.98, 0.02, info_text, transform=ax.transAxes,
           fontsize=10, verticalalignment='bottom',
           horizontalalignment='right',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9,
                    edgecolor='brown', linewidth=2))

    plt.tight_layout()

    # 保存图片
    output_path = os.path.join(
        os.path.dirname(__file__),
        'output',
        'y_junction_corrected_final.png'
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    print(f"Picture saved to: {output_path}")

    # 打印详细信息
    print("\n" + "=" * 70)
    print("Y-JUNCTION CORRECTED - Detailed Information")
    print("=" * 70)

    print(f"\nVertex coordinates (in order 1→9→8→7→6→5→3→4→2→1):")
    print("-" * 70)
    for i, (x, y) in enumerate(polygon_points):
        print(f"  Vertex {vertex_names[i].replace(chr(10), ' '):20s}: ({x:8.4f}, {y:8.4f})")

    print(f"\nBoundary segments:")
    print("-" * 70)
    for i, boundary in enumerate(geom.boundaries):
        points = boundary.points
        length = geom._calculate_length(points)
        print(f"  {edge_labels[i].replace(chr(10), ' '):25s}: {length:6.4f} mm  [{boundary.boundary_type.value}]")

    print("\n" + "=" * 70)
    print("Success! Corrected Y-junction geometry generated.")
    print("=" * 70)

    return output_path


if __name__ == '__main__':
    visualize_corrected()
