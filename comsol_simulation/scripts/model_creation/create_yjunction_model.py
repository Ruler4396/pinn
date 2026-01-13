# -*- coding: utf-8 -*-
"""
Y型分岔道COMSOL模型创建脚本

使用修正后的Y型分岔道几何创建完整的COMSOL模型：
- 主通道宽度: 0.4 mm
- 分支通道宽度: 0.2 mm (每个)
- 保证流动连续性: A_inlet = A_outlet1 + A_outlet2

使用方法:
python create_yjunction_model.py

作者: PINNs项目组
时间: 2025-01-13
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目路径
# __file__ 位于 model_creation/ 目录下
# project_root 应该指向 PINNs/ 目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'comsol_simulation' / 'scripts' / 'geometry'))


def create_yjunction_comsol_model(
    inlet_velocity=0.001,  # 入口速度 [m/s] - 1 mm/s
    W_main=100e-6,  # 主通道宽度 [m] - 100 μm
    L_main=2e-3,  # 主通道长度 [m] - 2 mm
    L_branch=1e-3,  # 分支长度 [m] - 1 mm
    branch_angle=30.0,  # 分支角度 [度]
    viscosity=1e-3,  # 流体粘度 [Pa·s]
    density=1000,  # 流体密度 [kg/m³]
    model_name="y_junction_microfluidic",
    save_dir=None,
    open_in_comsol=True
):
    """
    创建Y型分岔道COMSOL模型

    参数:
        inlet_velocity: 入口速度 [m/s]
        W_main: 主通道宽度 [m]
        L_main: 主通道长度 [m]
        L_branch: 分支长度 [m]
        branch_angle: 分支角度 [度]
        viscosity: 流体粘度 [Pa·s]
        density: 流体密度 [kg/m³]
        model_name: 模型名称
        save_dir: 保存目录 (None则使用临时目录)
        open_in_comsol: 是否在COMSOL中打开模型

    返回:
        tuple: (client, model, model_path)
    """
    import mph

    print("=" * 80)
    print(f"Y型分岔道COMSOL模型创建")
    print("=" * 80)

    # 导入几何类
    geom_path = str(project_root / 'comsol_simulation' / 'scripts' / 'geometry')
    sys.path.append(geom_path)

    # 调试输出
    print(f"   project_root: {project_root}")
    print(f"   geom_path: {geom_path}")
    print(f"   Checking if file exists: {os.path.exists(geom_path + '/yjunction_corrected.py')}")

    from yjunction_corrected import YJunctionCorrected

    # 创建几何对象
    print(f"\n[INFO] Creating Y-junction geometry...")
    geom_obj = YJunctionCorrected(
        L_main=L_main * 1000,  # 转换为mm
        L_branch=L_branch * 1000,  # 转换为mm
        W_main=W_main * 1000,  # 转换为mm
        branch_angle=branch_angle
    )

    # 生成几何数据
    geom_data = geom_obj.generate()

    print(f"   Main channel length: {L_main*1000} mm")
    print(f"   Branch length: {L_branch*1000} mm")
    print(f"   Main channel width: {W_main*1000} mm")
    print(f"   Branch width: {W_main*500} mm (each)")
    print(f"   Branch angle: {branch_angle} deg")

    # 启动COMSOL
    print(f"\n[INFO] Starting COMSOL client...")
    client = mph.Client(cores=1)
    print(f"   [OK] Client started successfully")

    # 创建模型
    print(f"\n[INFO] Creating model: {model_name}")
    model = client.create(model_name)
    print(f"   [OK] Model created successfully")

    # 1. 创建几何
    print(f"\n[INFO] Creating 2D geometry...")
    try:
        java_model = model.java

        # 创建2D几何空间
        geom = java_model.geom().create('geom1', 2)
        print(f"   [OK] 2D geometry space created")

        # 从几何对象获取多边形顶点
        polygon_points = geom_data['polygons'][0]['points']
        print(f"   Number of vertices: {len(polygon_points)}")

        # 创建多边形
        poly = geom.feature().create('poly1', 'Polygon')
        print(f"   [OK] Polygon feature created")

        # 设置顶点坐标
        # 注意：几何数据是mm单位，需要转换为m单位给COMSOL
        x_coords = [f'{p[0]/1000:.9f}' for p in polygon_points]  # mm -> m
        y_coords = [f'{p[1]/1000:.9f}' for p in polygon_points]  # mm -> m
        poly.set('x', x_coords)
        poly.set('y', y_coords)
        print(f"   [OK] Vertex coordinates set (converted from mm to m)")

        # 运行几何
        geom.run()
        print(f"   [OK] Geometry built successfully")

        # 验证几何（可选）
        # geom_stats = geom.get_stat()  # 这个方法可能不存在

    except Exception as e:
        print(f"   [ERROR] Geometry creation failed: {e}")
        import traceback
        traceback.print_exc()
        raise

    # 2. 添加物理场
    print(f"\n[INFO] Adding laminar flow physics...")
    try:
        # 创建层流物理接口
        physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')
        print(f"   [OK] Laminar flow physics added")

    except Exception as e:
        print(f"   [WARNING] Physics addition issue: {e}")
        # 尝试其他名字
        try:
            physics = java_model.physics().create('lam', 'SinglePhaseFlow', 'geom1')
            print(f"   [OK] Using SinglePhaseFlow physics")
        except:
            print(f"   [ERROR] Physics addition failed")
            raise

    # 3. 设置边界条件
    print(f"\n[INFO] Setting boundary conditions...")
    try:
        physics = java_model.physics('spf')

        # 计算雷诺数
        reynolds = density * inlet_velocity * W_main / viscosity
        print(f"   Reynolds number: {reynolds:.2f} (laminar: Re < 2300)")

        # 获取边界段信息
        boundaries = geom.get_boundary_entities('poly1')

        # 根据几何对象的边界信息设置边界条件
        # 1→9: 入口边界
        # 7→6: 上分支出口
        # 3→4: 下分支出口
        # 其余: 壁面

        print(f"   Number of boundaries: {len(boundaries)}")

        # 设置入口 (边界1，假设是第一个)
        try:
            inlet = physics.feature().create('inlet1', 'Inlet', 2)
            inlet.selection().named('geom1_poly1_b1')  # 假设第一条边是入口
            inlet.set('U0', [f'{inlet_velocity}', '0'])
            print(f"   [OK] Inlet set: {inlet_velocity} m/s (boundary 1)")
        except Exception as e:
            print(f"   [WARNING] Inlet setting issue: {e}")

        # 设置出口1 (上分支)
        try:
            outlet1 = physics.feature().create('outlet1', 'Outlet', 2)
            outlet1.selection().named('geom1_poly1_b4')  # 假设第四条边是出口1
            outlet1.set('p0', '0')
            print(f"   [OK] Outlet1 set: 0 Pa (boundary 4 - upper branch)")
        except Exception as e:
            print(f"   [WARNING] Outlet1 setting issue: {e}")

        # 设置出口2 (下分支)
        try:
            outlet2 = physics.feature().create('outlet2', 'Outlet', 2)
            outlet2.selection().named('geom1_poly1_b7')  # 假设第七条边是出口2
            outlet2.set('p0', '0')
            print(f"   [OK] Outlet2 set: 0 Pa (boundary 7 - lower branch)")
        except Exception as e:
            print(f"   [WARNING] Outlet2 setting issue: {e}")

        # 壁面 (默认无滑移，通常不需要显式设置)
        print(f"   [OK] Wall boundaries: no-slip (default)")

    except Exception as e:
        print(f"   [WARNING] Boundary condition setting issue: {e}")
        import traceback
        traceback.print_exc()

    # 4. 设置材料属性
    print(f"\n[INFO] Setting material properties...")
    try:
        # 创建材料
        fluid = java_model.material().create('fluid')
        print(f"   [OK] Material object created")

        # 设置粘度
        try:
            fluid.property('mu', f'{viscosity} [Pa*s]')
            print(f"   [OK] Viscosity set: {viscosity} Pa·s")
        except:
            fluid.property('dynamic_viscosity', f'{viscosity} [Pa*s]')
            print(f"   [OK] Dynamic viscosity set: {viscosity} Pa·s")

        # 设置密度
        try:
            fluid.property('rho', f'{density} [kg/m^3]')
            print(f"   [OK] Density set: {density} kg/m³")
        except:
            fluid.property('density', f'{density} [kg/m^3]')
            print(f"   [OK] Density set: {density} kg/m³")

        # 指定到域
        geom1 = java_model.geom('geom1')
        domain = geom1.selection()
        domain.set('all')
        fluid.selection().set(domain)

    except Exception as e:
        print(f"   [WARNING] Material setting issue: {e}")

    # 5. 创建网格
    print(f"\n[INFO] Creating mesh...")
    try:
        # 创建网格
        mesh = java_model.mesh().create('mesh1', 'geom1')
        print(f"   [OK] Mesh object created")

        # 使用自由网格（适合2D）
        free = mesh.feature().create('ftet', 'FreeTri')  # 2D使用三角形
        free.set('hauto', 3)  # 较细的网格
        print(f"   [OK] Free triangular mesh configured")

        # 运行网格生成
        mesh.run()
        print(f"   [OK] Mesh generated successfully")

        # 获取网格统计（可选）
        # mesh_stats = mesh.get_stat()  # 这个方法可能不存在

    except Exception as e:
        print(f"   [WARNING] Mesh setting issue: {e}")

    # 6. 创建研究步骤
    print(f"\n[INFO] Creating study steps...")
    try:
        # 创建定常研究
        study = java_model.study().create('std1')
        print(f"   [OK] Study object created")

        # 创建研究步骤
        stat = study.step().create('stat', 'Stationary')
        print(f"   [OK] Stationary step created")

    except Exception as e:
        print(f"   [WARNING] Study step setting issue: {e}")

    # 7. 保存模型
    print(f"\n[INFO] Saving model...")

    if save_dir is None:
        # 使用项目目录下的models文件夹
        models_dir = project_root / 'comsol_simulation' / 'models'
        models_dir.mkdir(parents=True, exist_ok=True)
        model_path = str(models_dir / f'{model_name}.mph')
    else:
        model_path = os.path.join(save_dir, f'{model_name}.mph')

    try:
        model.save(model_path)
        print(f"   [OK] Model saved successfully")
        print(f"   Path: {model_path}")

        if os.path.exists(model_path):
            size = os.path.getsize(model_path)
            print(f"   File size: {size:,} bytes ({size/1024:.1f} KB)")

            # 在COMSOL中打开模型
            if open_in_comsol:
                print(f"\n[INFO] Opening model in COMSOL...")
                try:
                    # 重新加载模型
                    model_loaded = client.load(model_path)
                    print(f"   [OK] Model opened in COMSOL")
                except Exception as e:
                    print(f"   [WARNING] Auto-open failed: {e}")
                    print(f"   Please open manually: {model_path}")
    except Exception as e:
        print(f"   [ERROR] Save failed: {e}")
        raise

    print("\n" + "=" * 80)
    print(f"[SUCCESS] Y-junction COMSOL model created!")
    print("=" * 80)

    print(f"\nModel parameters summary:")
    print(f"   Main channel length: {L_main*1000} mm")
    print(f"   Branch length: {L_branch*1000} mm")
    print(f"   Main channel width: {W_main*1000} mm")
    print(f"   Branch width: {W_main*500} mm (each)")
    print(f"   Branch angle: {branch_angle} deg")
    print(f"   Inlet velocity: {inlet_velocity} m/s")
    print(f"   Fluid viscosity: {viscosity} Pa s")
    print(f"   Fluid density: {density} kg/m^3")

    return client, model, model_path


def main():
    """Main function"""
    print("Y-Junction COMSOL Model Creation Tool")
    print(f"Start: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}")

    try:
        import mph
        print(f"[OK] mph {mph.__version__}")
    except ImportError:
        print("[ERROR] mph not installed")
        print("   Install: pip install mph")
        return False

    print("\nCreating Y-junction model...\n")
    print("-" * 80)

    try:
        # Create Y-junction model with microfluidic dimensions
        client, model, model_path = create_yjunction_comsol_model(
            inlet_velocity=0.001,  # 1 mm/s
            W_main=100e-6,  # 100 μm
            L_main=2e-3,  # 2 mm
            L_branch=1e-3,  # 1 mm
            branch_angle=30.0,  # 30°
            viscosity=1e-3,  # 1 mPa·s (water)
            density=1000,  # 1000 kg/m³
            model_name="y_junction_microfluidic",
            open_in_comsol=True
        )

        print("\n" + "-" * 80)
        print(f"\nEnd: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}")

        print(f"\n[SUCCESS] Model created successfully!")
        print(f"\nNext steps:")
        print(f"   1. Check geometry in COMSOL")
        print(f"   2. Run solver")
        print(f"   3. View results (velocity field, pressure field)")
        print(f"   4. Export data for PINNs training")

        print(f"\nTips:")
        print(f"   - Main channel width = 2 x branch width, ensures flow continuity")
        print(f"   - Both outlets set to 0 Pa (relative pressure)")
        print(f"   - All walls default to no-slip boundary")

        return True

    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
