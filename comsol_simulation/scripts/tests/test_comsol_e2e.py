#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试：创建并求解一个简单的COMSOL模型

作者: PINNs项目组
日期: 2025-12-24
"""

import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    import mph
    print("✅ mph模块导入成功 (版本: {})".format(mph.__version__))
except ImportError:
    print("❌ mph模块未安装，请执行: pip install mph")
    sys.exit(1)


def main():
    print("=" * 70)
    print("🧪 COMSOL端到端测试")
    print("=" * 70)
    print("将创建一个简单的直通道模型并求解")
    print()

    client = None
    try:
        # 1. 启动COMSOL客户端
        print("[1/6] 启动COMSOL客户端...")
        client = mph.Client()
        print("      ✅ 客户端启动成功")

        # 2. 创建模型
        print("\n[2/6] 创建模型...")
        model = client.create("test_channel")
        java_model = model.java
        print("      ✅ 模型创建成功")

        # 3. 创建几何 (10mm x 0.2mm 矩形)
        print("\n[3/6] 创建几何...")
        geom = java_model.geom().create('geom1', 2)
        geom.lengthUnit('mm')

        rect1 = geom.feature().create('rect1', 'Rectangle')
        rect1.set('size', ['10', '0.2'])
        rect1.set('pos', ['0', '0'])
        geom.run()
        print("      ✅ 几何创建成功 (10mm x 0.2mm)")

        # 4. 设置物理场
        print("\n[4/6] 设置层流物理场...")
        physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')

        # 材料 (水)
        mat = java_model.material().create('mat1')
        mat.property('mu', '0.001 [Pa*s]')
        mat.property('rho', '1000 [kg/m^3]')
        mat.selection().all()

        # 入口 (左边界, 速度0.5 cm/s)
        inlet = physics.feature().create('in1', 'InletVelocity', 2)
        inlet.selection().set([1])
        inlet.set('U0', ['0.005', '0'])

        # 出口 (右边界, 压力0)
        outlet = physics.feature().create('out1', 'OutletPressure', 2)
        outlet.selection().set([2])
        outlet.set('p0', '0')

        # 壁面 (上下边界, 无滑移)
        wall = physics.feature().create('wall1', 'Wall', 2)
        wall.selection().set([3, 4])

        print("      ✅ 物理场设置成功")

        # 5. 生成网格
        print("\n[5/6] 生成网格...")
        mesh = java_model.mesh().create('mesh1', 'geom1')
        mesh.autoMeshSize(5)
        mesh.run()
        print("      ✅ 网格生成成功")

        # 6. 求解
        print("\n[6/6] 求解Navier-Stokes方程...")
        study = java_model.study().create('std1')
        study.feature().create('stat', 'Stationary')

        start = time.time()
        study.run()
        elapsed = time.time() - start

        print("      ✅ 求解完成! (用时: {:.1f}秒)".format(elapsed))

        # 成功!
        print("\n" + "=" * 70)
        print("🎉 测试成功!")
        print("=" * 70)
        print("\n✅ COMSOL Python API工作正常")
        print("✅ 可以开始使用数据生成脚本")
        print("\n推荐命令:")
        print("  python comsol_simulation/scripts/batch/generate_straight_extended.py")
        print("  python comsol_simulation/scripts/batch/generate_tjunction_dataset.py")

        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ 测试失败")
        print("=" * 70)
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理
        if client is not None:
            try:
                client.clear()
                print("\n✅ 清理完成")
            except:
                pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
