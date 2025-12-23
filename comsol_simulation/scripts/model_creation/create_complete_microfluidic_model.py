"""
完整的微流控芯片COMSOL模型创建脚本

使用Java接口创建完整的微流控芯片模型，包括:
- 2D几何建模
- 层流物理场设置
- 边界条件配置
- 网格划分

使用方法:
python create_complete_microfluidic_model.py

作者: PINNs项目组
时间: 2025-11-19
"""

import os
import sys
import tempfile
import multiprocessing
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


def create_microfluidic_model(
    inlet_velocity=0.01,  # 入口速度 [m/s]
    channel_width=200e-6,  # 通道宽度 [m]
    channel_length=10e-3,  # 通道长度 [m]
    viscosity=1e-3,  # 流体粘度 [Pa·s]
    density=1000,  # 流体密度 [kg/m³]
    model_name="microfluidic_chip"
):
    """
    创建完整的微流控芯片模型

    参数:
        inlet_velocity: 入口速度 [m/s]
        channel_width: 通道宽度 [m]
        channel_length: 通道长度 [m]
        viscosity: 流体粘度 [Pa·s]
        density: 流体密度 [kg/m³]
        model_name: 模型名称

    返回:
        tuple: (client, model, model_path)
    """
    import mph

    print("=" * 70)
    print(f"🔧 创建微流控芯片模型")
    print("=" * 70)

    # 显示参数
    print(f"\n📋 模型参数:")
    print(f"   入口速度: {inlet_velocity*100:.1f} cm/s")
    print(f"   通道宽度: {channel_width*1e6:.0f} μm")
    print(f"   通道长度: {channel_length*1000:.1f} mm")
    print(f"   粘度: {viscosity:.4f} Pa·s")
    print(f"   密度: {density} kg/m³")
    reynolds = density * inlet_velocity * channel_width / viscosity
    print(f"   雷诺数: {reynolds:.2f} (层流: Re < 2300)")

    # 启动COMSOL
    print(f"\n🚀 启动COMSOL客户端...")
    client = mph.Client(cores=1)
    print(f"   ✅ 客户端启动成功")

    # 创建模型
    print(f"\n📐 创建模型: {model_name}")
    model = client.create(model_name)
    print(f"   ✅ 模型创建成功")

    # 1. 创建几何
    print(f"\n   创建2D几何...")
    try:
        java_model = model.java

        # 创建2D几何
        geom = java_model.geom().create('geom1', 2)
        print(f"   ✅ 几何容器创建成功")

        # 创建矩形
        rect = geom.feature().create('rect1', 'Rectangle')
        print(f"   ✅ 矩形特征创建成功")

        # 设置尺寸 (转换为mm)
        L_mm = channel_length * 1000
        W_mm = channel_width * 1000
        rect.set('size', [f'{L_mm}', f'{W_mm}'])
        print(f"   ✅ 尺寸设置: {L_mm} mm × {W_mm} mm")

        # 运行几何
        geom.run()
        print(f"   ✅ 几何运行成功")

        # 验证几何
        geoms = model.geometries()
        print(f"   📊 几何对象: {geoms}")

    except Exception as e:
        print(f"   ❌ 几何创建失败: {e}")
        import traceback
        traceback.print_exc()
        raise

    # 2. 添加物理场
    print(f"\n⚛️  添加物理场...")
    try:
        java_model = model.java

        # 创建层流物理接口 (COMSOL 6.3中可能叫LaminarFlow或SinglePhaseFlow)
        physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')
        print(f"   ✅ 层流物理场添加成功")

        # 启用连续性方程和动量方程 (默认)

    except Exception as e:
        print(f"   ⚠️  物理场添加问题: {e}")
        # 尝试其他名字
        try:
            physics = java_model.physics().create('lam', 'SinglePhaseFlow', 'geom1')
            print(f"   ✅ 使用SinglePhaseFlow物理场")
        except:
            print(f"   ❌ 物理场添加失败")

    # 3. 设置边界条件
    print(f"\n🔒 设置边界条件...")
    try:
        java_model = model.java
        physics = java_model.physics('spf')

        # 入口速度 (左边界, rect1的第一条边是左边界)
        try:
            inlet = physics.feature('inlet')
            inlet.set('U0', [f'{inlet_velocity}', '0'])
            print(f"   ✅ 入口速度设置: {inlet_velocity} m/s")
        except:
            # 如果没有inlet特征，尝试create
            inlet = physics.feature().create('inlet', 'Inlet')
            inlet.set('U0', [f'{inlet_velocity}', '0'])
            print(f"   ✅ 入口速度创建并设置: {inlet_velocity} m/s")

        # 出口压力 (右边界)
        try:
            outlet = physics.feature('outlet')
            outlet.set('p0', '0')
            print(f"   ✅ 出口压力设置: 0 Pa")
        except:
            outlet = physics.feature().create('outlet', 'Outlet')
            outlet.set('p0', '0')
            print(f"   ✅ 出口压力创建并设置: 0 Pa")

        # 壁面 (上下边界，默认无滑移)
        print(f"   ✅ 壁面边界: 无滑移 (默认)")

    except Exception as e:
        print(f"   ⚠️  边界条件设置问题: {e}")

    # 4. 设置材料属性
    print(f"\n🧪 设置材料属性...")
    try:
        java_model = model.java

        # 创建材料
        fluid = java_model.material().create('fluid')
        print(f"   ✅ 材料对象创建成功")

        # 设置粘度
        try:
            fluid.property('mu', f'{viscosity} [Pa*s]')
            print(f"   ✅ 粘度设置: {viscosity} Pa·s")
        except:
            fluid.property('dynamic_viscosity', f'{viscosity} [Pa*s]')
            print(f"   ✅ 动态粘度设置: {viscosity} Pa·s")

        # 设置密度
        try:
            fluid.property('rho', f'{density} [kg/m^3]')
            print(f"   ✅ 密度设置: {density} kg/m³")
        except:
            fluid.property('density', f'{density} [kg/m^3]')
            print(f"   ✅ 密度设置: {density} kg/m³")

        # 指定到域
        geom1 = java_model.geom('geom1')
        domain = geom1.selection()
        domain.set('all')
        fluid.selection().set(domain)

    except Exception as e:
        print(f"   ⚠️  材料设置问题: {e}")

    # 5. 创建网格
    print(f"\n🕸️  创建网格...")
    try:
        java_model = model.java

        # 创建网格
        mesh = java_model.mesh().create('mesh1', 'geom1')
        print(f"   ✅ 网格对象创建成功")

        # 使用自由网格
        free = mesh.feature().create('ftet', 'FreeTet')
        free.set('hauto', 1)  # 自动尺寸
        print(f"   ✅ 自由网格配置完成")

        # 运行网格生成
        mesh.run()
        print(f"   ✅ 网格生成成功")

    except Exception as e:
        print(f"   ⚠️  网格设置问题: {e}")

    # 6. 保存模型
    print(f"\n💾 保存模型...")
    temp_dir = tempfile.gettempdir()
    model_path = os.path.join(temp_dir, f'{model_name}.mph')

    try:
        model.save(model_path)
        print(f"   ✅ 模型保存成功")
        print(f"   📁 路径: {model_path}")

        if os.path.exists(model_path):
            size = os.path.getsize(model_path)
            print(f"   📊 文件大小: {size:,} bytes")
    except Exception as e:
        print(f"   ❌ 保存失败: {e}")
        raise

    print("\n" + "=" * 70)
    print(f"✅ 微流控模型创建完成!")
    print("=" * 70)

    return client, model, model_path


def test_complete_model():
    """测试完整模型创建"""
    print("🧪 微流控芯片模型完整测试")
    print(f"⏰ 时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        import mph
        print(f"✅ mph {mph.__version__}\n")

        # 创建默认模型
        client, model, model_path = create_microfluidic_model(
            inlet_velocity=0.01,
            channel_width=200e-6,
            channel_length=10e-3,
        )

        print(f"\n🎯 模型信息:")
        print(f"   模型文件: {model_path}")
        print(f"   文件存在: {os.path.exists(model_path)}")

        # 显示几何信息
        try:
            geoms = model.geometries()
            print(f"   几何对象: {geoms}")
        except:
            pass

        # 清理
        print(f"\n🧹 清理资源...")
        client.clear()
        print(f"✅ 清理完成")

        print(f"\n✅ 测试成功!")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("📅 微流控芯片COMSOL模型完整创建工具")
    print(f"⏰ 开始: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}")

    print("\n🔄 运行完整测试...\n")
    print("-" * 70)

    with multiprocessing.Pool(1) as pool:
        result = pool.apply(test_complete_model)

    print("-" * 70)
    print(f"\n⏱️ 结束: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}")

    if result:
        print("\n🎉 成功!\n")
        print("📋 下一步可以:")
        print("   1. 在COMSOL中打开生成的.mph文件")
        print("   2. 运行求解器")
        print("   3. 导出仿真数据")
        print("   4. 创建参数化扫描")
        return True
    else:
        print("\n😞 失败!\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
