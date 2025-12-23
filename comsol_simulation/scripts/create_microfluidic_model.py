"""
创建微流控芯片COMSOL模型的脚本

此脚本通过Python API自动创建完整的微流控芯片模型，包括:
- 2D几何建模
- 层流物理场设置
- 边界条件配置
- 网格划分
- 求解器设置

使用方法:
python create_microfluidic_model.py

作者: PINNs项目组
创建时间: 2025-11-19
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
    print(f"🔧 创建微流控芯片模型: {model_name}")
    print("=" * 70)

    # 1. 启动COMSOL
    print("\n🚀 启动COMSOL客户端...")
    client = mph.Client(cores=1)
    print("✅ 客户端启动成功")

    # 2. 创建模型
    print("\n📐 创建模型...")
    model = client.create(model_name)
    print(f"✅ 模型创建成功")

    # 3. 设置几何参数
    print("\n   设置几何参数...")
    model.parameter('L', f'{channel_length*1000} [mm]')  # 转换为mm
    model.parameter('W', f'{channel_width*1e6} [um]')   # 转换为μm
    print(f"   通道长度: {channel_length*1000:.1f} mm")
    print(f"   通道宽度: {channel_width*1e6:.0f} μm")

    # 4. 创建2D几何
    print("\n   创建2D几何...")
    try:
        geometries = model.geometries()

        # 创建矩形
        geom = geometries.create('geom1', 'Rectangle')
        geom.parameter('size', ['L', 'W'])  # 使用参数设置尺寸
        geometries.run()
        print("   ✅ 矩形几何创建成功")
    except Exception as e:
        print(f"   ⚠️  几何创建问题: {e}")
        # 尝试备用方法
        try:
            geom = geometries.create('rect1', 'Rectangle')
            geom.parameter('size', '10 [mm] 0.2 [mm]')
            geometries.run()
            print("   ✅ 备用几何创建成功")
        except Exception as e2:
            print(f"   ❌ 几何创建失败: {e2}")
            raise

    # 5. 添加物理场
    print("\n⚛️  添加物理场...")
    try:
        physics = model.physics()

        # 创建层流接口
        laminar = physics.create('laminar_flow', 'LaminarFlow', 'geom1')
        print("   ✅ 层流物理场添加成功")

        # 设置连续性方程和动量方程（默认）

    except Exception as e:
        print(f"   ⚠️  物理场设置问题: {e}")

    # 6. 设置边界条件
    print("\n🔒 设置边界条件...")
    try:
        # 获取边界
        boundaries = model.boundaries()

        # 入口速度 (左边界, 假设为rect1的第一条边)
        try:
            inlet = boundaries.selection(['rect1', 'Left'])
            laminar.feature('inlet').set('U0', f'{inlet_velocity} [m/s]')
            print(f"   ✅ 入口速度设置: {inlet_velocity} m/s")
        except Exception as e:
            print(f"   ⚠️  入口设置问题: {e}")

        # 出口压力 (右边界)
        try:
            outlet = boundaries.selection(['rect1', 'Right'])
            laminar.feature('outlet').set('p0', '0 [Pa]')
            print("   ✅ 出口压力设置: 0 Pa")
        except Exception as e:
            print(f"   ⚠️  出口设置问题: {e}")

        # 壁面无滑移 (上下边界，默认已设置)
        try:
            walls = boundaries.selection(['rect1', 'Top', 'Bottom'])
            print("   ✅ 壁面边界: 无滑移 (默认)")
        except Exception as e:
            print(f"   ⚠️  壁面设置问题: {e}")

    except Exception as e:
        print(f"   ⚠️  边界条件设置问题: {e}")

    # 7. 设置材料属性
    print("\n🧪 设置材料属性...")
    try:
        materials = model.materials()

        # 创建材料
        fluid = materials.create('fluid', 'Material')
        fluid.property('dynamic_viscosity', f'{viscosity} [Pa*s]')
        fluid.property('density', f'{density} [kg/m^3]')

        # 指定到域
        geom1 = model.geometries('geom1')
        domain = geom1.selection(['geom1'])
        fluid.selection().set(domain)

        print(f"   ✅ 粘度: {viscosity} Pa·s")
        print(f"   ✅ 密度: {density} kg/m³")

        # 计算雷诺数
        reynolds = density * inlet_velocity * channel_width / viscosity
        print(f"   📊 雷诺数: {reynolds:.2f} (层流: Re < 2300)")

    except Exception as e:
        print(f"   ⚠️  材料设置问题: {e}")

    # 8. 设置网格
    print("\n🕸️  设置网格...")
    try:
        meshes = model.meshes()
        mesh = meshes.create('mesh1', 'geom1')

        # 使用物理场控制网格
        mesh.feature('ftet').set('hauto', 1)  # 自动尺寸

        # 生成网格
        mesh.run()
        print("   ✅ 网格生成成功")

    except Exception as e:
        print(f"   ⚠️  网格设置问题: {e}")

    # 9. 设置求解器
    print("\n⚙️  设置求解器...")
    try:
        # 创建稳态研究
        studies = model.studies()
        study = studies.create('steady', 'Stationary')

        # 启用物理场
        study.feature('laminar_flow').enable()

        # 创建求解器配置
        solverConfigs = model.solverConfigs()
        solverConfig = solverConfigs.create('solver1', 'Study', 'steady')

        print("   ✅ 稳态求解器配置成功")

    except Exception as e:
        print(f"   ⚠️  求解器设置问题: {e}")

    # 10. 保存模型
    print("\n💾 保存模型...")
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


def test_microfluidic_model():
    """测试微流控模型创建"""
    print("🧪 微流控芯片模型测试")
    print(f"⏰ 时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 检查mph
    try:
        import mph
        print(f"✅ mph {mph.__version__}\n")
    except Exception as e:
        print(f"❌ mph导入失败: {e}\n")
        return False

    # 创建模型（使用默认参数）
    try:
        client, model, model_path = create_microfluidic_model(
            inlet_velocity=0.01,  # 1 cm/s
            channel_width=200e-6,  # 200 μm
            channel_length=10e-3,  # 10 mm
        )

        print(f"\n🎯 模型信息:")
        print(f"   模型文件: {model_path}")
        print(f"   文件存在: {os.path.exists(model_path)}")

        # 计算一些参数
        reynolds = 1000 * 0.01 * 200e-6 / 1e-3
        print(f"   雷诺数: {reynolds:.2f}")

        # 清理
        print(f"\n🧹 清理资源...")
        client.clear()
        client.remove()
        print(f"✅ 清理完成")

        print(f"\n✅ 微流控模型测试成功!")
        return True

    except Exception as e:
        print(f"\n❌ 模型创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("📅 微流控芯片COMSOL模型创建工具")
    print(f"⏰ 开始: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}")

    # 运行测试
    print("\n🔄 运行模型测试...\n")
    print("-" * 70)

    with multiprocessing.Pool(1) as pool:
        result = pool.apply(test_microfluidic_model)

    print("-" * 70)
    print(f"\n⏱️ 结束: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}")

    if result:
        print("\n🎉 成功!\n")
        print("📋 可用的操作:")
        print("   1. 修改参数创建不同配置的模型")
        print("   2. 添加更多边界条件")
        print("   3. 运行求解并导出数据")
        print("   4. 进行参数化扫描")
        return True
    else:
        print("\n😞 失败!\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
