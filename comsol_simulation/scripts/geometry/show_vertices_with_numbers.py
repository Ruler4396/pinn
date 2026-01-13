# -*- coding: utf-8 -*-
"""
显示Y型流道顶点序号 - 用于用户确认正确的连接顺序
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from yjunction_symmetric import create_yjunction_from_drawing_corrected
from base_geometry import BoundaryType


def show_vertex_numbers():
    """显示顶点序号"""
    # 使用基于用户绘制的修正版本
    geom = create_yjunction_from_drawing_corrected()
    data = geom.generate()

    # 获取多边形顶点
    polygon_points = np.array(data['polygons'][0]['points'])

    # 创建图形
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    # 绘制填充多边形
    poly = Polygon(polygon_points, closed=True, facecolor='lightblue',
                   edgecolor='black', linewidth=2, alpha=0.3)
    ax.add_patch(poly)

    # 绘制顶点和序号
    print("\n顶点坐标列表:")
    print("=" * 60)
    for i, (x, y) in enumerate(polygon_points):
        print(f"顶点 {i+1}: ({x:8.4f}, {y:8.4f})")

        # 绘制顶点
        ax.plot(x, y, 'ro', markersize=10, zorder=5)
        ax.plot(x, y, 'ko', markersize=12, fillstyle='none', zorder=5)

        # 标注序号（稍大一些，清晰可见）
        ax.annotate(f'{i+1}', (x, y), xytext=(15, 15),
                   textcoords='offset points', fontsize=14,
                   color='darkred', fontweight='bold',
                   bbox=dict(boxstyle='circle,pad=0.5', facecolor='yellow',
                            edgecolor='red', alpha=0.8, linewidth=2),
                   arrowprops=dict(arrowstyle='->', color='red', lw=2),
                   zorder=6)

    # 绘制当前连接顺序（虚线）
    for i in range(len(polygon_points)):
        p1 = polygon_points[i]
        p2 = polygon_points[(i+1) % len(polygon_points)]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'b--', linewidth=1.5, alpha=0.5)
        # 标注连接方向
        mid_x = (p1[0] + p2[0]) / 2
        mid_y = (p1[1] + p2[1]) / 2
        ax.annotate(f'{i+1}→{(i+1)%len(polygon_points)+1}',
                   (mid_x, mid_y), fontsize=8, color='blue',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

    # 设置坐标轴
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlabel('X (mm)', fontsize=12)
    ax.set_ylabel('Y (mm)', fontsize=12)
    ax.set_title('Y-Junction Vertices with Numbers\nPlease specify the correct connection order',
                fontsize=14, fontweight='bold')

    # 添加说明文字
    info_text = "Current vertex order:\n"
    for i in range(len(polygon_points)):
        next_i = (i+1) % len(polygon_points)
        info_text += f"{i+1} → {next_i+1}\n"

    ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
           fontsize=10, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()

    # 保存图片
    output_path = os.path.join(
        os.path.dirname(__file__),
        'output',
        'y_junction_vertices_numbered.png'
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    print(f"\n图片已保存至: {output_path}")

    # 打印当前连接顺序
    print("\n当前连接顺序:")
    print("=" * 60)
    for i in range(len(polygon_points)):
        next_i = (i+1) % len(polygon_points)
        p1 = polygon_points[i]
        p2 = polygon_points[next_i]
        dist = np.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
        print(f"顶点 {i+1} → 顶点 {next_i+1}: 距离 = {dist:.4f} mm")

    print("\n" + "=" * 60)
    print("请告诉我正确的顶点连接顺序，例如：")
    print("  1→2→3→4→5→6→7→8→9→1")
    print("=" * 60)

    return output_path


if __name__ == '__main__':
    show_vertex_numbers()
