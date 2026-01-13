# -*- coding: utf-8 -*-
"""
诊断并修复COMSOL Y型分岔道模型问题

检查边界条件、材料属性和求解器设置
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'comsol_simulation' / 'scripts' / 'geometry'))


def diagnose_and_fix_comsol_model():
    """诊断并修复COMSOL模型"""
    import mph

    print("=" * 80)
    print("Diagnosing COMSOL Y-Junction Model")
    print("=" * 80)

    # 模型路径
    model_path = str(project_root / 'comsol_simulation' / 'models' / 'y_junction_microfluidic.mph')

    if not os.path.exists(model_path):
        print(f"[ERROR] Model file not found: {model_path}")
        return False

    print(f"\n[INFO] Loading model: {model_path}")

    try:
        # 连接到COMSOL
        client = mph.Client(cores=1)
        print("[OK] COMSOL client started")

        # 加载模型
        model = client.load(model_path)
        print("[OK] Model loaded")

        java_model = model.java

        # 1. 检查几何
        print("\n" + "=" * 80)
        print("1. Checking Geometry")
        print("=" * 80)

        try:
            geom = java_model.geom('geom1')
            print(f"[OK] Geometry object found: {geom}")

            # 获取几何信息
            geom_info = geom.get_info()
            print(f"[INFO] Geometry info: {geom_info}")

            # 获取边界信息
            try:
                boundaries = geom.get_boundary_entities()
                print(f"[OK] Boundaries: {len(boundaries)} found")
                for i, b in enumerate(boundaries):
                    print(f"   Boundary {i+1}: {b}")
            except Exception as e:
                print(f"[WARNING] Could not get boundary entities: {e}")

        except Exception as e:
            print(f"[ERROR] Geometry check failed: {e}")

        # 2. 检查物理场
        print("\n" + "=" * 80)
        print("2. Checking Physics")
        print("=" * 80)

        try:
            physics = java_model.physics('spf')
            print(f"[OK] Physics found: spf")

            # 获取物理场特征
            features = physics.features()
            print(f"[INFO] Physics features: {features}")

            # 检查入口
            try:
                inlet = physics.feature('inlet1')
                print(f"[OK] Inlet feature found")
                print(f"   Property 'U0': {inlet.property('U0')}")
            except Exception as e:
                print(f"[WARNING] Inlet not found: {e}")
                print("[ACTION] Creating inlet...")
                try:
                    inlet = physics.feature().create('inlet1', 'Inlet', 2)
                    inlet.set('U0', ['0.001', '0'])  # 1 mm/s
                    print("[OK] Inlet created with velocity 1 mm/s")
                except Exception as e2:
                    print(f"[ERROR] Failed to create inlet: {e2}")

            # 检查出口
            for outlet_name in ['outlet1', 'outlet2']:
                try:
                    outlet = physics.feature(outlet_name)
                    print(f"[OK] {outlet_name} found")
                    print(f"   Property 'p0': {outlet.property('p0')}")
                except Exception as e:
                    print(f"[WARNING] {outlet_name} not found: {e}")
                    print(f"[ACTION] Creating {outlet_name}...")
                    try:
                        outlet = physics.feature().create(outlet_name, 'Outlet', 2)
                        outlet.set('p0', '0')
                        print(f"[OK] {outlet_name} created with pressure 0 Pa")
                    except Exception as e2:
                        print(f"[ERROR] Failed to create {outlet_name}: {e2}")

        except Exception as e:
            print(f"[ERROR] Physics check failed: {e}")

        # 3. 检查材料
        print("\n" + "=" * 80)
        print("3. Checking Material")
        print("=" * 80)

        try:
            materials = java_model.materials()
            print(f"[INFO] Materials: {materials}")

            for mat_name in materials:
                try:
                    mat = java_model.material(mat_name)
                    print(f"[INFO] Material: {mat_name}")
                    print(f"   Label: {mat.label()}")

                    # 检查属性
                    try:
                        props = mat.properties()
                        print(f"   Properties: {props}")
                    except:
                        pass

                except Exception as e:
                    print(f"[WARNING] Error checking material {mat_name}: {e}")

        except Exception as e:
            print(f"[ERROR] Material check failed: {e}")

        # 4. 检查网格
        print("\n" + "=" * 80)
        print("4. Checking Mesh")
        print("=" * 80)

        try:
            mesh = java_model.mesh('mesh1')
            print(f"[OK] Mesh found")

            features = mesh.features()
            print(f"[INFO] Mesh features: {features}")

            # 检查网格是否已生成
            try:
                mesh_stats = mesh.get_stat()
                print(f"[INFO] Mesh stats: {mesh_stats}")
            except:
                print("[WARNING] Mesh not yet generated")

        except Exception as e:
            print(f"[ERROR] Mesh check failed: {e}")

        # 5. 检查研究
        print("\n" + "=" * 80)
        print("5. Checking Study")
        print("=" * 80)

        try:
            study = java_model.study('std1')
            print(f"[OK] Study found")

            try:
                steps = study.steps()
                print(f"[INFO] Study steps: {steps}")
            except:
                print("[WARNING] Could not get study steps")

        except Exception as e:
            print(f"[ERROR] Study check failed: {e}")

        # 6. 尝试求解
        print("\n" + "=" * 80)
        print("6. Attempting to Solve")
        print("=" * 80)

        try:
            print("[INFO] Attempting to run solver...")
            job = study.run()
            print(f"[OK] Solver job started: {job}")

            # 等待求解完成
            print("[INFO] Waiting for solver to complete...")
            import time
            time.sleep(5)  # 等待5秒

            # 检查求解状态
            if job.is_finished():
                print("[OK] Solver completed successfully!")
            elif job.is_running():
                print("[INFO] Solver still running...")
            else:
                print("[WARNING] Solver may have failed")

        except Exception as e:
            print(f"[ERROR] Solver failed: {e}")
            print("\n[HELP] Common issues:")
            print("   1. Boundary conditions not properly assigned")
            print("   2. Material properties not set")
            print("   3. Mesh quality issues")
            print("   4. Initial conditions not appropriate")

        # 7. 保存修复后的模型
        print("\n" + "=" * 80)
        print("7. Saving Fixed Model")
        print("=" * 80)

        try:
            model.save(model_path)
            print(f"[OK] Model saved: {model_path}")
        except Exception as e:
            print(f"[ERROR] Save failed: {e}")

        print("\n" + "=" * 80)
        print("[DONE] Diagnostic complete")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n[ERROR] Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = diagnose_and_fix_comsol_model()
    sys.exit(0 if success else 1)
