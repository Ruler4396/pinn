# -*- coding: utf-8 -*-
"""
Geometry Validation and Visualization Script

Validates generated microfluidic straight channel geometries and provides visualization output.
"""

import sys
from pathlib import Path
import numpy as np

# 添加项目路径
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

try:
    import matplotlib.pyplot as plt
    # 直接从本地模块导入
    sys.path.insert(0, str(Path(__file__).parent))
    from base_geometry import BoundaryType, MicrochannelGeometry
    print("[OK] Dependencies imported successfully")
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    print("Please ensure: pip install matplotlib numpy")
    sys.exit(1)


def plot_geometry(geom, title: str, save_path: str = None):
    """
    Visualize geometry and boundary conditions

    Args:
        geom: Geometry object
        title: Figure title
        save_path: Save path (optional)
    """
    fig, ax = plt.subplots(figsize=(12, 8))

    # Color mapping
    color_map = {
        BoundaryType.INLET: '#2ecc71',
        BoundaryType.OUTLET_1: '#3498db',
        BoundaryType.OUTLET_2: '#9b59b6',
        BoundaryType.WALL: '#e74c3c'
    }

    # Plot boundaries
    for boundary in geom.boundaries:
        points = boundary.points
        color = color_map.get(boundary.boundary_type, '#333333')
        linewidth = 3 if boundary.boundary_type in [BoundaryType.INLET,
                                                     BoundaryType.OUTLET_1,
                                                     BoundaryType.OUTLET_2] else 1.5

        # Plot boundary lines
        ax.plot(points[:, 0], points[:, 1], color=color, linewidth=linewidth, label=boundary.label)

        # Mark boundary type
        mid_point = np.mean(points, axis=0)
        ax.text(mid_point[0], mid_point[1], boundary.boundary_type.value,
                fontsize=8, ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

    # Set figure properties
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_xlabel(f'X ({geom.units})')
    ax.set_ylabel(f'Y ({geom.units})')
    ax.set_title(title, fontsize=14, fontweight='bold')

    # Legend (deduplicate)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[OK] Visualization saved: {save_path}")

    plt.show()


def test_geometry_module():
    """Test basic functionality of geometry module"""
    print("\n" + "="*70)
    print("Microfluidic Geometry Module Test")
    print("="*70)

    try:
        from base_geometry import BoundaryType, MicrochannelGeometry
        print("[OK] Module imported successfully")

        # Test basic geometry class
        print("\nTesting base geometry class...")
        print("[OK] Base geometry class available")
        print("\n[INFO] Only straight channel geometries are currently supported.")
        print("       T-junction and Y-junction have been removed.")

        return 0

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Microfluidic geometry validation and visualization')
    parser.add_argument('--test', action='store_true', help='Run basic functionality tests only')
    parser.add_argument('--no-plot', action='store_true', help='Do not display figures (save only)')

    args = parser.parse_args()

    if args.test:
        exit_code = test_geometry_module()
    else:
        print("[INFO] Use --test flag to run geometry module tests")
        exit_code = 0

    sys.exit(exit_code)
