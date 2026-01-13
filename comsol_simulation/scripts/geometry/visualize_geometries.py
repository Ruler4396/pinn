# -*- coding: utf-8 -*-
"""
Geometry Validation and Visualization Script

Validates and visualizes T-junction and Y-junction microfluidic geometries.
"""

import sys
from pathlib import Path
import numpy as np

# 添加项目路径
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

try:
    import matplotlib
    matplotlib.use('Agg')  # 非交互式后端
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon
    from matplotlib.collections import PatchCollection
    print("[OK] Dependencies imported successfully")
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    print("Please ensure: pip install matplotlib numpy")
    sys.exit(1)

# 添加geometry目录到路径
geometry_dir = Path(__file__).parent
sys.path.insert(0, str(geometry_dir))

from base_geometry import BoundaryType


def plot_geometry(geom, title: str, save_path: str = None, show_plot: bool = False):
    """
    Visualize geometry and boundary conditions

    Args:
        geom: Geometry object
        title: Figure title
        save_path: Save path (optional)
        show_plot: Whether to display the plot
    """
    fig, ax = plt.subplots(figsize=(14, 10))

    # Color mapping
    color_map = {
        BoundaryType.INLET: '#2ecc71',      # 绿色
        BoundaryType.OUTLET_1: '#3498db',   # 蓝色
        BoundaryType.OUTLET_2: '#9b59b6',   # 紫色
        BoundaryType.WALL: '#e74c3c'        # 红色
    }

    # Plot geometry domain (filled polygon)
    data = geom.generate()
    if 'polygons' in data and len(data['polygons']) > 0:
        for poly_data in data['polygons']:
            points = np.array(poly_data['points'])
            # 绘制填充区域
            polygon = MplPolygon(points, closed=True, alpha=0.2, facecolor='#ecf0f1', edgecolor='#2c3e50', linewidth=2)
            ax.add_patch(polygon)

    # Plot boundaries
    for boundary in geom.boundaries:
        points = boundary.points
        color = color_map.get(boundary.boundary_type, '#333333')
        linewidth = 4 if boundary.boundary_type in [BoundaryType.INLET,
                                                     BoundaryType.OUTLET_1,
                                                     BoundaryType.OUTLET_2] else 2

        # Plot boundary lines
        ax.plot(points[:, 0], points[:, 1], color=color, linewidth=linewidth,
                label=boundary.label, solid_capstyle='round')

        # Mark boundary type at midpoint
        mid_point = np.mean(points, axis=0)
        offset = 0.3 if boundary.boundary_type in [BoundaryType.INLET,
                                                     BoundaryType.OUTLET_1,
                                                     BoundaryType.OUTLET_2] else 0.15

        # 根据边界类型调整文字位置
        if boundary.boundary_type == BoundaryType.INLET:
            text_offset = (-0.5, 0)
        elif boundary.boundary_type == BoundaryType.OUTLET_1:
            text_offset = (0, -0.5)
        elif boundary.boundary_type == BoundaryType.OUTLET_2:
            text_offset = (0, 0.5)
        else:
            text_offset = (0, offset)

        ax.text(mid_point[0] + text_offset[0], mid_point[1] + text_offset[1],
                boundary.boundary_type.value.upper(),
                fontsize=9, ha='center', va='center', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor=color))

    # Set figure properties
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlabel(f'X ({geom.units})', fontsize=12)
    ax.set_ylabel(f'Y ({geom.units})', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    # 设置英文字体（避免中文字体问题）
    plt.rcParams['font.family'] = 'DejaVu Sans'

    # 创建图例（去重）
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))

    # 添加通道尺寸信息
    info_text = f"通道宽度: {geom.W} {geom.units}\n"
    info_text += f"主通道长: {geom.L_main} {geom.units}\n"
    if hasattr(geom, 'L_branch'):
        info_text += f"分支通道长: {geom.L_branch} {geom.units}\n"
    if hasattr(geom, 'branch_angle'):
        info_text += f"分岔角度: {geom.branch_angle}°/侧"

    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    ax.legend(by_label.values(), by_label.keys(), loc='upper right')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[OK] Visualization saved: {save_path}")

    if show_plot:
        plt.show()

    plt.close()


def test_visualization():
    """Test visualization for both geometries"""
    print("\n" + "=" * 70)
    print("Geometry Visualization Test")
    print("=" * 70)

    # 导入几何类
    from tjunction import create_tjunction_standard
    from yjunction import create_yjunction_standard

    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)

    # T-junction visualization
    print("\n[INFO] Creating T-junction visualization...")
    t_geom = create_tjunction_standard()
    t_geom.generate()

    t_save_path = output_dir / 'tjunction_geometry.png'
    plot_geometry(t_geom, 'T型分岔道几何 (T-Junction Microchannel)', str(t_save_path))
    print(f"  [OK] T-junction saved to: {t_save_path}")

    # Y-junction visualization
    print("\n[INFO] Creating Y-junction visualization...")
    y_geom = create_yjunction_standard()
    y_geom.generate()

    y_save_path = output_dir / 'yjunction_geometry.png'
    plot_geometry(y_geom, 'Y型分岔道几何 (Y-Junction Microchannel)', str(y_save_path))
    print(f"  [OK] Y-junction saved to: {y_save_path}")

    # Side by side comparison
    print("\n[INFO] Creating comparison visualization...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

    # T-junction
    t_geom = create_tjunction_standard()
    t_geom.generate()
    data = t_geom.generate()

    color_map = {
        BoundaryType.INLET: '#2ecc71',
        BoundaryType.OUTLET_1: '#3498db',
        BoundaryType.OUTLET_2: '#9b59b6',
        BoundaryType.WALL: '#e74c3c'
    }

    for poly_data in data['polygons']:
        points = np.array(poly_data['points'])
        polygon = MplPolygon(points, closed=True, alpha=0.2, facecolor='#ecf0f1', edgecolor='#2c3e50', linewidth=2)
        ax1.add_patch(polygon)

    for boundary in t_geom.boundaries:
        points = boundary.points
        color = color_map.get(boundary.boundary_type, '#333333')
        linewidth = 3 if boundary.boundary_type in [BoundaryType.INLET, BoundaryType.OUTLET_1, BoundaryType.OUTLET_2] else 1.5
        ax1.plot(points[:, 0], points[:, 1], color=color, linewidth=linewidth)

    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_title('T型分岔道 (T-Junction)\n90°分岔角', fontsize=12, fontweight='bold')
    ax1.set_xlabel('X (mm)')
    ax1.set_ylabel('Y (mm)')

    # Y-junction
    y_geom = create_yjunction_standard()
    y_geom.generate()
    data = y_geom.generate()

    for poly_data in data['polygons']:
        points = np.array(poly_data['points'])
        polygon = MplPolygon(points, closed=True, alpha=0.2, facecolor='#ecf0f1', edgecolor='#2c3e50', linewidth=2)
        ax2.add_patch(polygon)

    for boundary in y_geom.boundaries:
        points = boundary.points
        color = color_map.get(boundary.boundary_type, '#333333')
        linewidth = 3 if boundary.boundary_type in [BoundaryType.INLET, BoundaryType.OUTLET_1, BoundaryType.OUTLET_2] else 1.5
        ax2.plot(points[:, 0], points[:, 1], color=color, linewidth=linewidth)

    ax2.set_aspect('equal')
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_title('Y型分岔道 (Y-Junction)\n45°/侧分岔角', fontsize=12, fontweight='bold')
    ax2.set_xlabel('X (mm)')
    ax2.set_ylabel('Y (mm)')

    plt.tight_layout()

    comparison_path = output_dir / 'junction_comparison.png'
    plt.savefig(comparison_path, dpi=150, bbox_inches='tight')
    print(f"  [OK] Comparison saved to: {comparison_path}")

    plt.close()

    print("\n" + "=" * 70)
    print("Visualization test completed successfully!")
    print("=" * 70)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Microfluidic geometry validation and visualization')
    parser.add_argument('--test', action='store_true', help='Run visualization tests')
    parser.add_argument('--no-plot', action='store_true', help='Do not display figures (save only)')

    args = parser.parse_args()

    if args.test:
        exit_code = test_visualization()
    else:
        print("[INFO] Use --test flag to run geometry visualization tests")
        exit_code = 0

    sys.exit(exit_code)
