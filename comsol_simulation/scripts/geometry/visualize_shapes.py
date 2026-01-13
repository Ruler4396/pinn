# -*- coding: utf-8 -*-
"""
Simple Geometry Visualization Script

用于可视化Y型流道和T型流道的几何形状
重点展示：内部中空区域、端口封闭边界
"""

import sys
from pathlib import Path
import numpy as np

# 添加geometry目录到路径
geometry_dir = Path(__file__).parent
sys.path.insert(0, str(geometry_dir))

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon
    from matplotlib.collections import PatchCollection
    print("[OK] matplotlib imported successfully")
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    print("Please run: pip install matplotlib numpy")
    sys.exit(1)

from base_geometry import BoundaryType
from tjunction import TJunctionGeometry
from yjunction import YJunctionGeometry


def visualize_single_geometry(geom, title: str, save_path: str = None):
    """
    可视化单个几何形状

    Args:
        geom: 几何对象
        title: 图片标题
        save_path: 保存路径
    """
    fig, ax = plt.subplots(figsize=(12, 10))

    # 生成几何数据
    data = geom.generate()

    # 颜色映射
    color_map = {
        BoundaryType.INLET: '#2ecc71',      # 绿色 - 入口
        BoundaryType.OUTLET_1: '#3498db',   # 蓝色 - 出口1
        BoundaryType.OUTLET_2: '#9b59b6',   # 紫色 - 出口2
        BoundaryType.WALL: '#e74c3c'        # 红色 - 壁面
    }

    # 绘制流道区域（内部中空部分用浅色填充表示）
    if 'polygons' in data and len(data['polygons']) > 0:
        for poly_data in data['polygons']:
            points = np.array(poly_data['points'])
            # 浅灰色填充表示这是中空的流道区域
            polygon = MplPolygon(points, closed=True,
                                facecolor='#f0f0f0',
                                edgecolor='#333333',
                                linewidth=2.5,
                                alpha=0.8)
            ax.add_patch(polygon)

    # 绘制边界
    for boundary in geom.boundaries:
        points = boundary.points
        color = color_map.get(boundary.boundary_type, '#333333')

        # 端口边界用更粗的线
        linewidth = 4 if boundary.boundary_type in [BoundaryType.INLET,
                                                     BoundaryType.OUTLET_1,
                                                     BoundaryType.OUTLET_2] else 2

        # 绘制边界线
        ax.plot(points[:, 0], points[:, 1], color=color, linewidth=linewidth,
                solid_capstyle='round', solid_joinstyle='round')

        # 在边界中点添加标签
        mid_point = np.mean(points, axis=0)

        # 根据边界类型设置标签偏移
        if boundary.boundary_type == BoundaryType.INLET:
            text_offset = (-1.5, 0)
            label = "INLET\n(入口)"
        elif boundary.boundary_type == BoundaryType.OUTLET_1:
            text_offset = (0, -0.8)
            label = "OUTLET1\n(出口1)"
        elif boundary.boundary_type == BoundaryType.OUTLET_2:
            text_offset = (0, 0.8)
            label = "OUTLET2\n(出口2)"
        else:
            text_offset = (0, 0.3)
            label = "WALL\n(壁面)"

        ax.text(mid_point[0] + text_offset[0], mid_point[1] + text_offset[1],
                label,
                fontsize=9, ha='center', va='center', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                         alpha=0.9, edgecolor=color, linewidth=1.5))

    # 设置图形属性
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linestyle='--', color='#999999')
    ax.set_xlabel(f'X ({geom.units})', fontsize=12)
    ax.set_ylabel(f'Y ({geom.units})', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

    # 添加尺寸信息框
    info_text = "几何参数:\n"
    info_text += f"通道宽度 W = {geom.W} {geom.units}\n"
    info_text += f"主通道长度 L_main = {geom.L_main} {geom.units}\n"
    if hasattr(geom, 'L_branch'):
        info_text += f"分支通道长度 L_branch = {geom.L_branch} {geom.units}\n"
    if hasattr(geom, 'branch_angle'):
        info_text += f"分岔角度 = {geom.branch_angle}°/侧"

    ax.text(0.02, 0.98, info_text,
            transform=ax.transAxes, fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow',
                     alpha=0.8, edgecolor='#999999'))

    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2ecc71', edgecolor='black', label='INLET - 入口（速度边界）'),
        Patch(facecolor='#3498db', edgecolor='black', label='OUTLET1 - 出口1（压力边界）'),
        Patch(facecolor='#9b59b6', edgecolor='black', label='OUTLET2 - 出口2（压力边界）'),
        Patch(facecolor='#e74c3c', edgecolor='black', label='WALL - 壁面（无滑移）')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[OK] 保存图片: {save_path}")

    plt.close()


def main():
    """主函数：生成Y型和T型流道的可视化图片"""

    output_dir = geometry_dir / 'output'
    output_dir.mkdir(exist_ok=True)

    print("\n" + "=" * 60)
    print("微流控几何形状可视化")
    print("=" * 60)

    # ==================== T型流道 ====================
    print("\n[1/2] 生成T型流道几何...")

    t_geom = TJunctionGeometry(
        L_main=10.0,      # 主通道长度 10mm
        L_branch=5.0,     # 分支通道长度 5mm
        W=0.2,            # 通道宽度 0.2mm (200μm)
        units='mm'
    )

    t_save_path = output_dir / 't_junction_shape.png'
    visualize_single_geometry(t_geom, 'T型分岔道 (T-Junction)\n内部中空，端口封闭', str(t_save_path))
    print(f"[OK] T型流道图片已保存")

    # ==================== Y型流道 ====================
    print("\n[2/2] 生成Y型流道几何...")

    y_geom = YJunctionGeometry(
        L_main=10.0,       # 主通道长度 10mm
        L_branch=5.0,      # 分支通道长度 5mm
        W=0.2,             # 通道宽度 0.2mm (200μm)
        branch_angle=45.0, # 分岔角度 45度/侧
        units='mm'
    )

    y_save_path = output_dir / 'y_junction_shape.png'
    visualize_single_geometry(y_geom, 'Y型分岔道 (Y-Junction)\n内部中空，端口封闭', str(y_save_path))
    print(f"[OK] Y型流道图片已保存")

    # ==================== 对比图 ====================
    print("\n[3/3] 生成对比图...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

    color_map = {
        BoundaryType.INLET: '#2ecc71',
        BoundaryType.OUTLET_1: '#3498db',
        BoundaryType.OUTLET_2: '#9b59b6',
        BoundaryType.WALL: '#e74c3c'
    }

    # T型流道
    t_data = t_geom.generate()
    for poly_data in t_data['polygons']:
        points = np.array(poly_data['points'])
        polygon = MplPolygon(points, closed=True, facecolor='#f0f0f0',
                           edgecolor='#333333', linewidth=2, alpha=0.8)
        ax1.add_patch(polygon)

    for boundary in t_geom.boundaries:
        points = boundary.points
        color = color_map.get(boundary.boundary_type, '#333333')
        linewidth = 3.5 if boundary.boundary_type in [BoundaryType.INLET,
                                                       BoundaryType.OUTLET_1,
                                                       BoundaryType.OUTLET_2] else 2
        ax1.plot(points[:, 0], points[:, 1], color=color, linewidth=linewidth,
                solid_capstyle='round')

    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_title('T型分岔道 (T-Junction)\n90°垂直分岔', fontsize=13, fontweight='bold')
    ax1.set_xlabel('X (mm)')
    ax1.set_ylabel('Y (mm)')

    # Y型流道
    y_data = y_geom.generate()
    for poly_data in y_data['polygons']:
        points = np.array(poly_data['points'])
        polygon = MplPolygon(points, closed=True, facecolor='#f0f0f0',
                           edgecolor='#333333', linewidth=2, alpha=0.8)
        ax2.add_patch(polygon)

    for boundary in y_geom.boundaries:
        points = boundary.points
        color = color_map.get(boundary.boundary_type, '#333333')
        linewidth = 3.5 if boundary.boundary_type in [BoundaryType.INLET,
                                                       BoundaryType.OUTLET_1,
                                                       BoundaryType.OUTLET_2] else 2
        ax2.plot(points[:, 0], points[:, 1], color=color, linewidth=linewidth,
                solid_capstyle='round')

    ax2.set_aspect('equal')
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_title('Y型分岔道 (Y-Junction)\n45°/侧 对称分岔', fontsize=13, fontweight='bold')
    ax2.set_xlabel('X (mm)')
    ax2.set_ylabel('Y (mm)')

    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2ecc71', label='INLET (入口)'),
        Patch(facecolor='#3498db', label='OUTLET1 (出口1)'),
        Patch(facecolor='#9b59b6', label='OUTLET2 (出口2)'),
        Patch(facecolor='#e74c3c', label='WALL (壁面)')
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=4, fontsize=10)

    plt.tight_layout()
    comparison_path = output_dir / 'junction_comparison.png'
    plt.savefig(comparison_path, dpi=150, bbox_inches='tight')
    print(f"[OK] 对比图片已保存")

    plt.close()

    print("\n" + "=" * 60)
    print("可视化完成！")
    print(f"图片保存位置: {output_dir}")
    print("=" * 60)

    # 打印图片路径
    print(f"\n生成的图片:")
    print(f"  1. T型流道: {t_save_path}")
    print(f"  2. Y型流道: {y_save_path}")
    print(f"  3. 对比图:   {comparison_path}")


if __name__ == '__main__':
    main()
