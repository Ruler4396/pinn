#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直通道数据生成脚本 - 使用底层Java API

直接使用COMSOL Java API设置边界条件
参考: https://doc.comsol.com/6.3/doc/com.comsol.help.cfd/cfd_ug_fluidflow_single.06.008.html

作者: PINNs项目组
日期: 2025-12-24
"""

import mph
import h5py
import numpy as np
from pathlib import Path


def create_straight_channel_model(client, case_name, v_cm_s, width_um):
    """创建直通道模型"""
    print(f"\n📐 创建模型: {case_name}")
    print(f"   参数: v={v_cm_s:.2f} cm/s, w={width_um} μm")

    # 转换单位
    v_in = v_cm_s / 100  # m/s
    width = width_um * 1e-6  # m
    length = 0.01  # 10 mm

    try:
        # 创建模型
        model = client.create(case_name)
        java_model = model.java

        # 创建组件和几何
        comp = java_model.component().create("comp1")
        geom = comp.geom().create("geom1", 2)
        geom.lengthUnit("mm")

        # 创建矩形
        rect1 = geom.feature().create("rect1", "Rectangle")
        rect1.set("size", [f"{length*1000}", f"{width*1000}"])
        rect1.set("pos", ["0", "0"])

        # 运行几何
        geom.run()

        # 添加层流物理场
        physics = comp.physics().create("spf", "LaminarFlow", "geom1")

        # 创建入口边界条件 - 使用Velocity而不是Inlet
        # 根据COMSOL 6.3文档，使用Velocity边界条件
        inlet = physics.feature().create("in1", "Velocity", 2)
        inlet.selection().set([1])  # 左边界

        # 设置速度分量 - 使用正确的属性名
        # Velocity边界条件使用 u, v 作为速度分量
        try:
            inlet.set("u0", f"{v_in}")
            inlet.set("v0", "0")
        except Exception as e:
            # 如果失败，尝试其他属性名
            print(f"   ⚠️ 尝试其他属性名: {e}")
            # 尝试使用属性组
            inlet.property("normalFlow", "on")
            inlet.property("u0", f"{v_in}")
            inlet.property("v0", "0")

        # 创建出口边界条件
        outlet = physics.feature().create("out1", "Pressure", 2)
        outlet.selection().set([2])  # 右边界
        outlet.set("p0", "0")

        # 创建壁面
        wall = physics.feature().create("wall1", "Wall", 2)
        wall.selection().set([3, 4])  # 上下边界

        # 设置材料
        mat = comp.material().create("mat1")
        mat.label("Water")
        mat.propertyGroup("def").set("materialtype", "1")  # 液体
        mat.propertyGroup("def").set("kinematicviscosity", f"{0.001/1000} [m^2/s]")
        mat.propertyGroup("def").set("density", f"{1000} [kg/m^3]")
        mat.selection().all()

        # 创建网格
        mesh = comp.mesh().create("mesh1", "geom1")
        mesh.autoMeshSize(5)
        mesh.run()

        # 创建研究并求解
        print("   🔄 正在求解...")
        study = comp.study().create("std1")
        study.feature().create("stat", "Stationary")
        study.run()

        print("   ✅ 求解完成!")

        # 导出数据
        export_data(model, case_name, v_in, width, length)

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
    eval_result = java_model.result().numerical().create("eval1", "Eval")
    eval_result.set("expr", ["u", "v", "p"])

    # 生成网格点
    x_points = np.linspace(0, length, 50)
    y_points = np.linspace(0, width, 20)

    results = []
    for x in x_points:
        for y in y_points:
            try:
                eval_result.set("p", [x, y])
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
    print("🚀 直通道数据生成器 (Java API)")
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

                if create_straight_channel_model(client, case_name, v, w):
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
