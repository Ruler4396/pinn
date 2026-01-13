# -*- coding: utf-8 -*-
"""
简化的Y型分岔道COMSOL模型创建脚本

专注于正确设置边界条件和求解器
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'comsol_simulation' / 'scripts' / 'geometry'))


def create_simple_yjunction_model():
    """创建简化的Y型分岔道模型"""
    import mph

    print("=" * 80)
    print("Creating Simple Y-Junction COMSOL Model")
    print("=" * 80)

    # 导入几何类
    from yjunction_corrected import YJunctionCorrected

    # 创建几何对象（微流控尺寸）
    print("\n[INFO] Creating geometry...")
    geom_obj = YJunctionCorrected(
        L_main=2.0,  # 2 mm
        L_branch=1.0,  # 1 mm
        W_main=0.1,  # 0.1 mm = 100 μm
        branch_angle=30.0  # 30°
    )

    geom_data = geom_obj.generate()
    polygon_points = geom_data['polygons'][0]['points']

    print(f"   Vertices: {len(polygon_points)}")
    print(f"   Coordinate range: X=[{min(p[0] for p in polygon_points):.3f}, {max(p[0] for p in polygon_points):.3f}] mm")
    print(f"                      Y=[{min(p[1] for p in polygon_points):.3f}, {max(p[1] for p in polygon_points):.3f}] mm")

    # 启动COMSOL
    print("\n[INFO] Starting COMSOL...")
    client = mph.Client(cores=1)
    print("[OK] Connected")

    # 创建模型
    print("\n[INFO] Creating model...")
    model = client.create("y_junction_simple")
    java_model = model.java
    print("[OK] Model created")

    # 1. 创建几何
    print("\n[INFO] Creating geometry...")
    geom = java_model.geom().create("geom1", 2)
    print("[OK] Geometry space created")

    # 创建多边形（注意：COMSOL使用米，所以需要转换）
    poly = geom.feature().create("poly1", "Polygon")
    x_coords = [f"{p[0]/1000:.9f}" for p in polygon_points]  # mm -> m
    y_coords = [f"{p[1]/1000:.9f}" for p in polygon_points]  # mm -> m
    poly.set("x", x_coords)
    poly.set("y", y_coords)
    print("[OK] Polygon created")

    # 运行几何
    geom.run()
    print("[OK] Geometry built")

    # 2. 添加物理场（使用最简单的方法）
    print("\n[INFO] Adding physics...")
    try:
        physics = java_model.physics().create("spf", "LaminarFlow", "geom1")
        print("[OK] Laminar flow physics added")
    except:
        try:
            physics = java_model.physics().create("spf", "FluidFlow", "geom1")
            print("[OK] Fluid flow physics added")
        except:
            print("[WARNING] Could not add physics, using default")

    # 3. 设置材料（使用内置材料）
    print("\n[INFO] Setting material...")
    try:
        # 尝试使用内置材料
        mat = java_model.material().create("mat1", "Water")
        mat.selection().all()
        print("[OK] Water material assigned")
    except Exception as e:
        print(f"[WARNING] Using default material: {e}")

    # 4. 创建网格（使用最简单的设置）
    print("\n[INFO] Creating mesh...")
    mesh = java_model.mesh().create("mesh1", "geom1")

    # 使用最简单的网格设置
    try:
        # 自由三角形网格
        free_tri = mesh.feature().create("ftri", "FreeTri")
        free_tri.set("hauto", 5)  # 使用字符串而不是整数
        print("[OK] Free triangular mesh configured")
    except Exception as e:
        print(f"[WARNING] Mesh config issue: {e}")
        print("[INFO] Using default mesh")

    # 运行网格生成
    try:
        mesh.run()
        print("[OK] Mesh generated")
    except Exception as e:
        print(f"[WARNING] Mesh generation issue: {e}")

    # 5. 设置边界条件（手动选择边界）
    print("\n[INFO] Setting boundary conditions...")
    try:
        physics = java_model.physics("spf")

        # 获取所有边界
        # 注意：我们需要手动确定哪个边界是哪个
        # 根据我们的几何顺序，边界1应该是入口
        # 边界4和边界7应该是出口

        # 设置入口（假设边界1）
        inlet = physics.feature().create("inlet1", "Inlet", 2)
        inlet.selection().named("geom1_poly1_b1")  # 第一条边
        inlet.set("U0", ["0.001", "0"])  # 1 mm/s
        print("[OK] Inlet set (boundary 1): 1 mm/s")

        # 设置出口1（假设边界4）
        outlet1 = physics.feature().create("outlet1", "Outlet", 2)
        outlet1.selection().named("geom1_poly1_b4")  # 第四条边
        outlet1.set("p0", "0")  # 0 Pa
        print("[OK] Outlet1 set (boundary 4): 0 Pa")

        # 设置出口2（假设边界7）
        outlet2 = physics.feature().create("outlet2", "Outlet", 2)
        outlet2.selection().named("geom1_poly1_b7")  # 第七条边
        outlet2.set("p0", "0")  # 0 Pa
        print("[OK] Outlet2 set (boundary 7): 0 Pa")

        print("[INFO] Wall boundaries: no-slip (default)")

    except Exception as e:
        print(f"[WARNING] Boundary condition issue: {e}")
        print("[HELP] You may need to manually set boundary conditions in COMSOL")

    # 6. 创建研究
    print("\n[INFO] Creating study...")
    try:
        study = java_model.study().create("std1")
        print("[OK] Study created")

        # 添加定常步骤
        try:
            stat = study.create("stat", "Stationary")
            print("[OK] Stationary step added")
        except:
            print("[WARNING] Could not add stationary step")
            print("[INFO] Using default study configuration")

    except Exception as e:
        print(f"[WARNING] Study creation issue: {e}")

    # 7. 保存模型
    print("\n[INFO] Saving model...")
    models_dir = project_root / 'comsol_simulation' / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = str(models_dir / 'y_junction_simple.mph')

    model.save(model_path)
    print(f"[OK] Model saved: {model_path}")

    if os.path.exists(model_path):
        size = os.path.getsize(model_path)
        print(f"   File size: {size:,} bytes ({size/1024:.1f} KB)")

    print("\n" + "=" * 80)
    print("[SUCCESS] Model created!")
    print("=" * 80)

    print("\nNext steps:")
    print("1. The model should now be open in COMSOL")
    print("2. Check the geometry (should be ~3mm long)")
    print("3. Verify boundary conditions (inlet and two outlets)")
    print("4. If needed, manually adjust boundary conditions")
    print("5. Click 'Compute' to solve")
    print("6. Check results (velocity field, pressure field)")

    return model, model_path


if __name__ == '__main__':
    try:
        model, path = create_simple_yjunction_model()
        print(f"\n[SUCCESS] Model created at: {path}")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
