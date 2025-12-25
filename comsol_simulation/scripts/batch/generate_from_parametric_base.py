#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于参数化基准模型生成数据

使用现有的参数化模型，通过修改参数和求解来生成数据
这是更可靠的方法，避免了复杂的边界条件API

作者: PINNs项目组
日期: 2025-12-24
"""

import mph
import h5py
import numpy as np
from pathlib import Path


def generate_from_base_model(client, base_model_path, case_name, v_cm_s, width_um):
    """基于基准模型生成新工况 - 直接修改边界条件"""
    print(f"\n📐 生成工况: {case_name}")
    print(f"   参数: v={v_cm_s:.2f} cm/s, w={width_um} μm")

    try:
        # 加载基准模型
        print(f"   📂 加载基准模型...")
        model = client.load(base_model_path)
        java_model = model.java

        # 设置参数
        v_in = v_cm_s / 100  # m/s
        width = width_um * 1e-6  # m

        # 尝试直接修改边界条件
        print(f"   🔧 设置边界条件...")

        # 获取层流物理场
        physics = java_model.physics("spf")

        # 找到入口边界条件并修改速度
        # 从诊断结果得知，tag是"inlet"
        inlet = physics.feature("inlet")
        if inlet is not None:
            print(f"   ✅ 找到入口: {inlet.label()} (tag: {inlet.tag()})")
            try:
                # 设置速度 - 使用U0in属性
                inlet.set("U0in", f"{v_in}")
                print(f"   ✅ 入口速度设置为 {v_in} m/s")
            except Exception as e:
                print(f"   ⚠️ 设置速度失败: {e}")
        else:
            print(f"   ⚠️ 未找到入口边界条件，使用参数设置")

        # 设置模型参数（如果边界条件使用参数）
        java_model.param().set("v_in", f"{v_in} [m/s]")
        java_model.param().set("W", f"{width_um} [um]")

        # 如果需要修改几何
        # geom = java_model.geom("geom1")
        # geom.feature("r1").set("w", f"{width_um} [um]")

        # 求解 - 动态查找研究
        print(f"   🔄 正在求解...")
        studies = java_model.study()
        study_iter = studies.iterator()

        # 获取第一个研究
        if study_iter.hasNext():
            study = study_iter.next()
            study_tag = str(study.tag())
            study_label = str(study.label())
            print(f"   使用研究: {study_label} (tag: {study_tag})")
            study.run()
        else:
            raise ValueError("模型中没有找到研究")

        print(f"   ✅ 求解完成!")

        # 导出数据
        export_data(model, case_name, v_in, width)

        # 清理模型
        model.clear()

        return True

    except Exception as e:
        print(f"   ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_data(model, case_name, v_in, width):
    """导出数据到HDF5 - 使用Java API直接获取解数据"""
    java_model = model.java

    try:
        print(f"   📊 正在提取数据...")

        # 获取解
        sol = java_model.solution("sol1")
        if sol is None:
            # 尝试查找可用的解
            sols = java_model.solution()
            sol_iter = sols.iterator()
            if sol_iter.hasNext():
                sol = sol_iter.next()
                print(f"   使用解: {sol.tag()}")
            else:
                raise ValueError("没有找到解")

        # 创建数据集用于评估
        # 使用Java API创建EvalGlobal特征
        result = java_model.result()

        # 创建评估特征
        eval_node = result.numerical().create("eval1", "EvalGlobal")
        eval_node.set("expr", ["x", "y", "u", "v", "p"])
        eval_node.set("unit", ["m", "m", "m/s", "m/s", "Pa"])

        # 获取数据
        # EvalGlobal返回的是一个标量值，不是场数据
        # 我们需要使用Eval来获取场数据
        result.numerical().remove("eval1")

        # 改用Eval - 在网格上评估
        eval_node = result.numerical().create("eval1", "Eval")
        eval_node.set("expr", ["x", "y", "u", "v", "p"])

        # 获取数据 - 使用Java的getRealData方法
        data = eval_node.getRealData()
        eval_node.getComplexData()

        # 清理
        result.numerical().remove("eval1")

        # 转换为numpy数组
        x = np.array(data[0]).flatten()
        y = np.array(data[1]).flatten()
        u = np.array(data[2]).flatten()
        v = np.array(data[3]).flatten()
        p = np.array(data[4]).flatten()

        # 验证数据
        if len(x) == 0:
            raise ValueError("未获取到有效数据")

        print(f"   📊 获取到 {len(x)} 个数据点")
        print(f"   📊 U范围: [{u.min():.6f}, {u.max():.6f}] m/s")
        print(f"   📊 P范围: [{p.min():.2f}, {p.max():.2f}] Pa")

    except Exception as e:
        print(f"   ⚠️ Java API方法失败: {e}")
        # 回退到mph的evaluate方法
        print(f"   回退到mph.evaluate()...")
        x = np.array(model.evaluate('x')).flatten()
        y = np.array(model.evaluate('y')).flatten()
        u = np.array(model.evaluate('u')).flatten()
        v = np.array(model.evaluate('v')).flatten()
        p = np.array(model.evaluate('p')).flatten()

        print(f"   📊 获取到 {len(x)} 个数据点")
        print(f"   📊 U范围: [{u.min():.6f}, {u.max():.6f}] m/s")
        print(f"   📊 P范围: [{p.min():.2f}, {p.max():.2f}] Pa")

    # 保存HDF5文件 - 使用与现有文件相同的格式
    output_dir = Path(__file__).parent.parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / f"{case_name}.h5"

    with h5py.File(filepath, 'w') as f:
        # 使用与现有文件相同的键名
        f.create_dataset('x', data=x)
        f.create_dataset('y', data=y)
        f.create_dataset('u', data=u)
        f.create_dataset('v', data=v)
        f.create_dataset('p', data=p)

        # 元数据
        f.attrs['v_in_cm_s'] = v_in * 100
        f.attrs['width_um'] = width * 1e6
        f.attrs['total_points'] = len(x)

    print(f"   ✅ 数据已保存: {filepath.name} ({len(x)} 点)")


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 参数化基准模型数据生成器")
    print("=" * 60)
    print("\n生成内容:")
    print("  - 速度: 0.4, 1.2 cm/s (2档)")
    print("  - 宽度: 150, 200, 250 μm (3档)")
    print("  - 总计: 6 组数据\n")

    # 定义参数
    velocities = [0.4, 1.2]  # cm/s
    widths = [150, 200, 250]  # μm

    # 基准模型路径 - 尝试使用microfluidic_chip.mph
    base_model_path = Path(__file__).parent.parent.parent / "models" / "microfluidic_chip.mph"

    if not base_model_path.exists():
        print(f"⚠️ 基准模型不存在: {base_model_path}")
        print(f"\n💡 请先创建参数化基准模型")
        print(f"   1. 在COMSOL GUI中创建直通道模型")
        print(f"   2. 设置参数: v_in, W")
        print(f"   3. 保存为: {base_model_path}")
        return False

    print(f"📂 使用基准模型: {base_model_path.name}")

    # 启动COMSOL客户端
    print("\n🚀 启动COMSOL客户端...")
    client = mph.Client()
    print("   ✅ 客户端启动成功\n")

    success_count = 0
    case_num = 0

    try:
        for v in velocities:
            for w in widths:
                case_num += 1
                case_name = f"v{v:.1f}_w{w}"

                print(f"[{case_num}/6] ", end="")

                if generate_from_base_model(client, base_model_path, case_name, v, w):
                    success_count += 1

    finally:
        # 清理客户端
        try:
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
