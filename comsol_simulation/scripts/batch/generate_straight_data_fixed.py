#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直通道数据生成脚本 - 使用正确的mph API

基于mph官方文档编写
参考: https://mph.readthedocs.io/en/stable/demonstrations.html

作者: PINNs项目组
日期: 2025-12-24
"""

import mph
import h5py
import numpy as np
from pathlib import Path


def generate_case(client, case_name, v_cm_s, width_um, length_mm=10):
    """生成单个工况"""
    print(f"\n📐 创建模型: {case_name}")
    print(f"   参数: v={v_cm_s:.2f} cm/s, w={width_um} μm")

    # 转换单位
    v_in = v_cm_s / 100  # m/s
    width = width_um * 1e-6  # m
    length = length_mm * 1e-3  # m

    try:
        # 创建模型
        model = client.create(case_name)

        # 创建几何 (2D)
        geom = model.create('geometries', 2)
        rect = geom.create('Rectangle', name=f'{case_name}_rect')
        rect.property('size', (f'{length*1000}', f'{width*1000}'))  # mm单位
        rect.property('pos', ('0', '0'))

        # 构建几何
        model.build(geom)

        # 创建物理场 (层流)
        # 通过Java层直接访问，因为Model类可能不直接支持所有物理场创建
        java_model = model.java

        # 创建组件（如果不存在）
        try:
            comp = java_model.component().create('comp1')
        except:
            comp = java_model.component('comp1')

        # 创建物理场 - 使用Java API
        try:
            physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')
        except:
            physics = java_model.physics('spf')

        # 创建入口边界条件 - 使用Java API
        inlet = physics.feature().create('in1', 'Inlet')
        inlet.selection().all()
        inlet.selection().set([1])  # 选择左边界

        # 设置入口速度 - 使用字符串列表
        inlet.set('U0', [f'{v_in}', '0'])

        # 创建出口边界条件
        outlet = physics.feature().create('out1', 'Outlet')
        outlet.selection().all()
        outlet.selection().set([2])  # 选择右边界
        outlet.set('p0', '0')

        # 创建壁面
        wall = physics.feature().create('wall1', 'Wall')
        wall.selection().all()
        wall.selection().set([3, 4])  # 上下边界

        # 创建材料
        mat = java_model.material().create('mat1')
        mat.label('Water')
        # 设置材料属性
        mat.property('mu', f'{0.001} [Pa*s]')
        mat.property('rho', f'{1000} [kg/m^3]')
        mat.selection().all()

        # 创建网格
        mesh = java_model.mesh().create('mesh1', 'geom1')
        mesh.autoMeshSize(5)  # 常规
        mesh.run()

        # 创建研究并求解
        print("   🔄 正在求解...")
        study = java_model.study().create('std1')
        study.feature().create('stat', 'Stationary')
        study.run()

        # 导出数据
        print("   📊 导出数据...")
        export_data(model, case_name, v_in, width, length)

        # 清理模型
        model.clear()
        print("   ✅ 完成!")
        return True

    except Exception as e:
        print(f"   ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_data(model, case_name, v_in, width, length):
    """导出数据到HDF5"""
    java_model = model.java

    # 创建评估对象
    eval_result = java_model.result().numerical().create('eval1', 'Eval')
    eval_result.set('expr', ['u', 'v', 'p'])

    # 生成网格点
    x_points = np.linspace(0, length, 50)
    y_points = np.linspace(0, width, 20)

    results = []
    for x in x_points:
        for y in y_points:
            try:
                eval_result.set('p', [x, y])
                values = eval_result.getReal()
                if len(values) >= 3:
                    results.append([x, y, values[0], values[1], values[2]])
            except:
                continue

    results = np.array(results)
    if len(results) == 0:
        raise ValueError("无有效数据")

    # 保存HDF5文件
    output_dir = Path(__file__).parent.parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / f"{case_name}.h5"

    with h5py.File(filepath, 'w') as f:
        f.create_dataset('coordinates', data=results[:, :2])
        f.create_dataset('velocity_u', data=results[:, 2])
        f.create_dataset('velocity_v', data=results[:, 3])
        f.create_dataset('pressure', data=results[:, 4])

        # 元数据
        f.attrs['v_in'] = v_in
        f.attrs['width'] = width
        f.attrs['length'] = length
        f.attrs['total_points'] = len(results)

    print(f"   ✅ 数据已保存: {filepath.name} ({len(results)} 点)")


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 直通道数据生成器 (mph标准API)")
    print("=" * 60)
    print("\n生成内容:")
    print("  - 速度: 0.4, 1.2 cm/s (2档)")
    print("  - 宽度: 150, 200, 250 μm (3档)")
    print("  - 总计: 6 组数据\n")

    # 定义参数
    velocities = [0.4, 1.2]  # cm/s
    widths = [150, 200, 250]  # μm

    # 启动COMSOL客户端
    print("🚀 启动COMSOL客户端...")
    client = mph.Client()
    print("   ✅ 客户端启动成功\n")

    success_count = 0
    case_num = 0

    try:
        for v in velocities:
            for w in widths:
                case_num += 1
                case_name = f"v{v:.1f}_w{w}"

                print(f"\n[{case_num}/6] 生成案例...")

                if generate_case(client, case_name, v, w):
                    success_count += 1

    finally:
        # 清理客户端
        try:
            client.clear()
            client.disconnect()
        except:
            pass

    # 汇总
    print("\n" + "=" * 60)
    print("📊 生成完成")
    print("=" * 60)
    print(f"✅ 成功: {success_count}/6")
    print(f"❌ 失败: {6-success_count}/6")

    return success_count == 6


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
