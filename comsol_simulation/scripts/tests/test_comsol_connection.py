#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试COMSOL Python API (mph) 连接

验证:
1. mph模块是否正确安装
2. COMSOL客户端能否启动
3. 能否创建简单模型并求解

作者: PINNs项目组
日期: 2025-12-24
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


def test_mph_import():
    """测试mph模块导入"""
    print("=" * 60)
    print("测试1: mph模块导入")
    print("=" * 60)

    try:
        import mph
        print("✅ mph模块导入成功")
        print(f"   版本: {mph.__version__}")
        return True
    except ImportError as e:
        print(f"❌ mph模块导入失败: {e}")
        print("\n💡 解决方案:")
        print("   pip install mph")
        return False


def test_comsol_discovery():
    """测试COMSOL安装检测"""
    print("\n" + "=" * 60)
    print("测试2: COMSOL安装检测")
    print("=" * 60)

    try:
        import mph

        # 检测COMSOL安装
        try:
            versions = mph.find_comsol()
            print(f"✅ 检测到COMSOL安装:")
            for v in versions:
                print(f"   - {v}")
            return True
        except Exception as e:
            print(f"⚠️ 自动检测失败: {e}")
            print(f"   尝试使用默认路径: E:\\COMSOL63\\Multiphysics\\bin\\win64\\comsol.exe")
            return True
    except Exception as e:
        print(f"❌ 检测失败: {e}")
        return False


def test_client_start():
    """测试启动COMSOL客户端"""
    print("\n" + "=" * 60)
    print("测试3: 启动COMSOL客户端")
    print("=" * 60)

    try:
        import mph

        print("🚀 正在启动COMSOL客户端...")
        print("   (这可能需要10-30秒)")

        # 尝试启动客户端
        try:
            client = mph.Client()
        except:
            # 如果自动启动失败，尝试指定路径
            comsol_path = r"E:\COMSOL63\Multiphysics\bin\win64\comsol.exe"
            print(f"   尝试使用路径: {comsol_path}")
            client = mph.Client(comsol_path)

        print("✅ COMSOL客户端启动成功")
        print(f"   Java对象: {client.java}")

        # 清理 (使用disconnect而不是remove)
        client.clear()
        try:
            client.disconnect()
        except:
            pass  # 有些版本不支持disconnect
        print("✅ 客户端关闭成功")

        return True

    except Exception as e:
        print(f"❌ 客户端启动失败: {e}")
        print("\n💡 可能的原因:")
        print("   1. COMSOL未正确安装")
        print("   2. COMSOL许可证未激活")
        print("   3. COMSOL版本不兼容")
        print("   4. 防火墙阻止连接")
        return False


def test_simple_model():
    """测试创建简单模型"""
    print("\n" + "=" * 60)
    print("测试4: 创建简单模型并求解")
    print("=" * 60)

    try:
        import mph
        import time

        print("📐 创建简单直通道模型...")

        # 启动客户端
        client = mph.Client()

        # 创建模型
        model = client.create("test_model")
        java_model = model.java

        # 创建几何 (2D矩形)
        geom = java_model.geom().create('geom1', 2)
        geom.lengthUnit('mm')

        rect1 = geom.feature().create('rect1', 'Rectangle')
        rect1.set('size', ['10', '0.2'])
        rect1.set('pos', ['0', '0'])
        geom.run()

        print("   ✅ 几何创建成功")

        # 添加层流物理场
        physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')

        # 设置材料 (水)
        mat = java_model.material().create('mat1')
        mat.property('mu', '0.001 [Pa*s]')
        mat.property('rho', '1000 [kg/m^3]')
        mat.selection().all()

        print("   ✅ 物理场创建成功")

        # 入口边界条件
        inlet = physics.feature().create('in1', 'InletVelocity', 2)
        inlet.selection().set([1])
        inlet.set('U0', ['0.005', '0'])

        # 出口边界条件
        outlet = physics.feature().create('out1', 'OutletPressure', 2)
        outlet.selection().set([2])
        outlet.set('p0', '0')

        # 壁面
        wall = physics.feature().create('wall1', 'Wall', 2)
        wall.selection().set([3, 4])

        print("   ✅ 边界条件设置成功")

        # 创建网格
        mesh = java_model.mesh().create('mesh1', 'geom1')
        mesh.autoMeshSize(5)  # 常规
        mesh.run()

        print("   ✅ 网格生成成功")

        # 创建研究并求解
        print("   🔄 开始求解...")
        start_time = time.time()

        study = java_model.study().create('std1')
        study.feature().create('stat', 'Stationary')
        study.run()

        solve_time = time.time() - start_time
        print(f"   ✅ 求解完成 (用时: {solve_time:.1f}秒)")

        # 清理
        client.clear()
        try:
            client.disconnect()
        except:
            pass

        print("\n✅ 端到端测试成功!")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🚀 COMSOL Python API 连接测试")
    print("=" * 60)
    print(f"测试时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = []

    # 运行测试
    if not test_mph_import():
        print("\n❌ mph模块未安装，无法继续测试")
        return False

    results.append(("mph导入", True))

    if not test_comsol_discovery():
        results.append(("COMSOL检测", False))
    else:
        results.append(("COMSOL检测", True))

    if not test_client_start():
        results.append(("客户端启动", False))
        print("\n⚠️ 客户端启动失败，跳过后续测试")
    else:
        results.append(("客户端启动", True))

        if test_simple_model():
            results.append(("简单模型", True))
        else:
            results.append(("简单模型", False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")

    # 判断是否可以开始数据生成
    all_passed = all(r[1] for r in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过!")
        print("\n✅ 您可以开始使用数据生成脚本:")
        print("   python generate_extended_dataset.py")
        print("   python generate_straight_extended.py")
        print("   python generate_tjunction_dataset.py")
    else:
        print("⚠️ 部分测试失败")
        print("\n💡 请根据上述错误信息解决问题:")
        print("   1. 确保COMSOL已正确安装")
        print("   2. 确保COMSOL许可证已激活")
        print("   3. 尝试以管理员权限运行")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
