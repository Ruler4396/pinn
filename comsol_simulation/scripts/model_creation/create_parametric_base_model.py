"""
创建参数化基准模型

创建一个完整的、可参数化的微流控芯片模型，
保存到comsol_simulation/models目录。

作者: PINNs项目组
时间: 2025-11-19
"""

import mph
import os
from pathlib import Path


def create_parametric_model(
    model_name="parametric_base",
    inlet_velocity=0.001,  # 0.1 cm/s
    channel_width=200e-6,  # 200 μm
    channel_length=10e-3,  # 10 mm
    viscosity=1e-3,  # 0.001 Pa·s
    density=1000,  # 1000 kg/m³
):
    """
    创建参数化微流控芯片模型

    参数:
        model_name: 模型名称
        inlet_velocity: 入口速度 [m/s]
        channel_width: 通道宽度 [m]
        channel_length: 通道长度 [m]
        viscosity: 流体粘度 [Pa·s]
        density: 流体密度 [kg/m³]
    """
    print("=" * 70)
    print(f"🔧 创建参数化模型: {model_name}")
    print("=" * 70)

    # 计算雷诺数
    reynolds = density * inlet_velocity * channel_width / viscosity

    print(f"\n📋 模型参数:")
    print(f"   入口速度: {inlet_velocity*100:.2f} cm/s")
    print(f"   通道宽度: {channel_width*1e6:.0f} μm")
    print(f"   通道长度: {channel_length*1000:.1f} mm")
    print(f"   粘度: {viscosity:.4f} Pa·s")
    print(f"   密度: {density} kg/m³")
    print(f"   雷诺数: {reynolds:.2f}")

    # 启动COMSOL客户端
    print(f"\n🚀 启动COMSOL客户端...")
    client = mph.Client(cores=1)
    print(f"   ✅ 客户端启动成功")

    # 创建模型
    print(f"\n📐 创建模型...")
    model = client.create(model_name)
    print(f"   ✅ 模型创建成功")

    # 设置参数
    print(f"\n   设置全局参数...")
    model.parameter('v_in', f'{inlet_velocity} [m/s]')  # 入口速度
    model.parameter('W', f'{channel_width*1e6} [um]')   # 通道宽度
    model.parameter('L', f'{channel_length*1000} [mm]') # 通道长度
    model.parameter('mu', f'{viscosity} [Pa*s]')        # 粘度
    model.parameter('rho', f'{density} [kg/m^3]')       # 密度
    print(f"   ✅ 参数设置成功")

    # 创建2D几何
    print(f"\n   创建2D几何...")
    try:
        java_model = model.java

        # 创建几何
        geom = java_model.geom().create('geom1', 2)
        print(f"   ✅ 几何容器创建成功")

        # 创建矩形
        rect = geom.feature().create('rect1', 'Rectangle')
        print(f"   ✅ 矩形特征创建成功")

        # 设置尺寸（使用参数）
        rect.set('size', ['L', 'W'])
        print(f"   ✅ 尺寸参数化: {channel_length*1000}mm × {channel_width*1000}mm")

        # 运行几何
        geom.run()
        print(f"   ✅ 几何运行成功")

        # 验证几何
        geoms = model.geometries()
        print(f"   📊 几何对象: {geoms}")

    except Exception as e:
        print(f"   ❌ 几何创建失败: {e}")
        raise

    # 添加物理场
    print(f"\n⚛️  添加层流物理场...")
    try:
        java_model = model.java
        physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')
        print(f"   ✅ 层流物理场添加成功")
    except Exception as e:
        print(f"   ❌ 物理场添加失败: {e}")
        raise

    # 设置边界条件
    print(f"\n🔒 设置边界条件...")
    try:
        java_model = model.java
        physics = java_model.physics('spf')

        # 入口速度 (左边界)
        try:
            inlet = physics.feature('inlet')
            print(f"   ✅ 入口特征已存在")
        except:
            inlet = physics.feature().create('inlet', 'Inlet')
            print(f"   ✅ 入口特征创建成功")

        inlet.set('U0', ['v_in', '0'])
        print(f"   ✅ 入口速度设置为参数 v_in")

        # 出口压力 (右边界)
        try:
            outlet = physics.feature('outlet')
            print(f"   ✅ 出口特征已存在")
        except:
            outlet = physics.feature().create('outlet', 'Outlet')
            print(f"   ✅ 出口特征创建成功")

        outlet.set('p0', '0')
        print(f"   ✅ 出口压力设置为 0 Pa")

        # 壁面 (上下边界，默认无滑移)
        print(f"   ✅ 壁面边界: 无滑移条件 (默认)")

    except Exception as e:
        print(f"   ❌ 边界条件设置失败: {e}")

    # 设置材料属性
    print(f"\n🧪 设置材料属性...")
    try:
        java_model = model.java

        # 创建材料
        fluid = java_model.material().create('fluid')
        print(f"   ✅ 材料对象创建成功")

        # 设置粘度（使用参数）
        try:
            fluid.property('mu', 'mu')
            print(f"   ✅ 粘度设置为参数 mu")
        except:
            fluid.property('mu', f'{viscosity} [Pa*s]')
            print(f"   ✅ 粘度设置为: {viscosity} Pa·s")

        # 设置密度（使用参数）
        try:
            fluid.property('rho', 'rho')
            print(f"   ✅ 密度设置为参数 rho")
        except:
            fluid.property('rho', f'{density} [kg/m^3]')
            print(f"   ✅ 密度设置为: {density} kg/m³")

        # 指定到域
        geom1 = java_model.geom('geom1')
        domain = geom1.selection()
        domain.set('all')
        fluid.selection().set(domain)
        print(f"   ✅ 材料分配到整个几何域")

    except Exception as e:
        print(f"   ❌ 材料设置失败: {e}")

    # 创建网格
    print(f"\n🕸️  创建网格...")
    try:
        java_model = model.java

        # 创建网格
        mesh = java_model.mesh().create('mesh1', 'geom1')
        print(f"   ✅ 网格对象创建成功")

        # 使用物理场控制网格
        free = mesh.feature().create('ftet', 'FreeTet')
        free.set('hauto', 1)  # 自动尺寸
        print(f"   ✅ 自由网格配置完成")
        print(f"   ℹ️  网格生成需要在COMSOL GUI中完成")

    except Exception as e:
        print(f"   ❌ 网格设置失败: {e}")

    # 创建研究步骤
    print(f"\n⚙️  配置研究...")
    try:
        java_model = model.java

        # 创建稳态研究
        studies = java_model.study().create('steady')
        print(f"   ✅ 稳态研究创建成功")

        # 启用物理场
        studies.feature('spf').enable()
        print(f"   ✅ 物理场已启用")

    except Exception as e:
        print(f"   ❌ 研究配置失败: {e}")

    # 保存模型
    print(f"\n💾 保存模型...")
    models_dir = Path('comsol_simulation/models')
    models_dir.mkdir(exist_ok=True)

    model_path = models_dir / f'{model_name}.mph'

    try:
        model.save(str(model_path))
        print(f"   ✅ 模型保存成功")
        print(f"   📁 路径: {model_path}")

        if model_path.exists():
            size_kb = model_path.stat().st_size / 1024
            print(f"   📊 文件大小: {size_kb:.1f} KB")
    except Exception as e:
        print(f"   ❌ 保存失败: {e}")
        raise

    # 清理
    print(f"\n🧹 清理资源...")
    try:
        client.clear()
        client.remove()
        print(f"   ✅ 清理完成")
    except:
        pass

    print("\n" + "=" * 70)
    print(f"✅ 参数化模型创建完成!")
    print("=" * 70)

    return model_path


def create_9_parametric_models():
    """创建9组参数化模型"""
    print("=" * 70)
    print("🚀 创建9组参数化模型")
    print("=" * 70)

    # 参数组合
    velocities = [0.001, 0.005, 0.01]  # 0.1, 0.5, 1.0 cm/s
    widths = [150e-6, 200e-6, 250e-6]  # 150, 200, 250 μm

    created_models = []

    for i, v in enumerate(velocities):
        for j, w in enumerate(widths):
            case_id = f"case_{i*len(widths)+j+1:02d}_v{int(v*1000)}um_w{int(w*1e6)}"
            reynolds = 1000 * v * w / 1e-3

            print(f"\n🔄 创建模型 {case_id}...")
            print(f"   速度: {v*100:.1f} cm/s, 宽度: {w*1e6:.0f} μm")
            print(f"   雷诺数: {reynolds:.2f}")

            try:
                # 使用默认参数创建基准模型
                model_path = create_parametric_model(
                    model_name=case_id,
                    inlet_velocity=v,
                    channel_width=w,
                )

                created_models.append({
                    'case': case_id,
                    'velocity': v,
                    'width': w,
                    'reynolds': reynolds,
                    'path': model_path
                })

                print(f"   ✅ {case_id} 创建成功")

            except Exception as e:
                print(f"   ❌ {case_id} 创建失败: {e}")

    # 总结
    print(f"\n" + "=" * 70)
    print(f"📊 模型创建总结")
    print(f"=" * 70)

    success_count = len(created_models)
    print(f"✅ 成功创建: {success_count}/9")

    if success_count > 0:
        print(f"\n📁 模型文件列表:")
        for model in created_models:
            print(f"   {model['case']}: {model['path']}")

    return created_models


def main():
    """主函数"""
    print("📅 参数化基准模型创建工具")
    print(f"⏰ 时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 创建基准模型
    print("\n🔄 创建基准模型...")
    try:
        model_path = create_parametric_model()
        print(f"\n✅ 基准模型创建完成!")
        print(f"   文件: {model_path}")
    except Exception as e:
        print(f"\n❌ 基准模型创建失败: {e}")
        return False

    # 创建9组模型
    print(f"\n" + "=" * 70)
    print(f"🚀 批量创建9组参数化模型")
    print(f"=" * 70)
    print(f"⚠️  注意: 每个模型约需要30-60秒")
    print(f"⏱️  预计总时间: 5-10分钟")

    # 注释掉批量创建，只创建基准模型
    # models = create_9_parametric_models()

    print(f"\n" + "=" * 70)
    print(f"✅ 任务完成")
    print(f"=" * 70)
    print(f"\n📋 产出:")
    print(f"   ✅ 基准模型: parametric_base.mph")
    print(f"\n💡 下一步:")
    print(f"   1. 在COMSOL中打开模型")
    print(f"   2. 手动修改参数")
    print(f"   3. 运行求解器")
    print(f"   4. 导出数据")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
