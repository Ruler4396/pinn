"""
自动化参数化扫描脚本

基于成功的模型，创建多组参数扫描，生成训练数据集。

作者: PINNs项目组
时间: 2025-11-19
"""

import mph
import numpy as np
import os
import tempfile
from pathlib import Path

def create_parametric_model(
    inlet_velocity=0.01,
    channel_width=200e-6,
    channel_length=10e-3,
    viscosity=1e-3,
    density=1000,
    model_name="parametric_model"
):
    """创建参数化模型"""
    print("=" * 70)
    print(f"🔧 创建参数化模型: {model_name}")
    print("=" * 70)

    # 计算雷诺数
    reynolds = density * inlet_velocity * channel_width / viscosity
    print(f"\n📊 参数:")
    print(f"   入口速度: {inlet_velocity*100:.1f} cm/s")
    print(f"   通道宽度: {channel_width*1e6:.0f} μm")
    print(f"   通道长度: {channel_length*1000:.1f} mm")
    print(f"   粘度: {viscosity:.4f} Pa·s")
    print(f"   雷诺数: {reynolds:.2f}")

    client = mph.Client(cores=1)
    model = client.create(model_name)

    # 设置参数
    model.parameter('v_in', f'{inlet_velocity} [m/s]')
    model.parameter('W', f'{channel_width*1e6} [um]')
    model.parameter('L', f'{channel_length*1000} [mm]')

    # 创建几何（使用之前的成功方法）
    java_model = model.java
    geom = java_model.geom().create('geom1', 2)
    rect = geom.feature().create('rect1', 'Rectangle')
    rect.set('size', [f'{channel_length*1000}', f'{channel_width*1000}'])
    geom.run()

    # 添加物理场
    physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')

    # 设置边界条件（使用参数）
    inlet = physics.feature('inlet')
    inlet.set('U0', [f'{inlet_velocity}', '0'])

    outlet = physics.feature('outlet')
    outlet.set('p0', '0')

    # 设置材料
    fluid = java_model.material().create('fluid')
    fluid.property('mu', f'{viscosity} [Pa*s]')
    fluid.property('rho', f'{density} [kg/m^3]')
    geom1 = java_model.geom('geom1')
    domain = geom1.selection()
    domain.set('all')
    fluid.selection().set(domain)

    # 创建网格
    mesh = java_model.mesh().create('mesh1', 'geom1')
    free = mesh.feature().create('ftet', 'FreeTet')
    free.set('hauto', 1)
    mesh.run()

    # 创建研究
    studies = java_model.study().create('steady')
    java_model.solver().create('sv', 'SteadyState')
    java_model.solver('sv').feature('v').set('initstep', 0.01)
    java_model.solver('sv').feature('v').set('init茅野', '0.1')

    print(f"✅ 参数化模型创建成功")
    return client, model


def run_parametric_sweep():
    """运行参数化扫描"""
    print("=" * 70)
    print("🚀 参数化扫描")
    print("=" * 70)

    # 定义参数范围
    velocities = [0.001, 0.005, 0.01]  # 3个速度
    widths = [150e-6, 200e-6, 250e-6]  # 3个宽度

    print(f"\n📋 参数组合:")
    print(f"   速度: {len(velocities)} 个值")
    print(f"   宽度: {len(widths)} 个值")
    print(f"   总组合: {len(velocities) * len(widths)} 组")

    results = []

    for i, v in enumerate(velocities):
        for j, w in enumerate(widths):
            case_id = f"case_{i*len(widths)+j+1:02d}"
            print(f"\n🔄 运行 {case_id}...")
            print(f"   速度: {v*100:.1f} cm/s, 宽度: {w*1e6:.0f} μm")

            try:
                # 创建模型
                client, model = create_parametric_model(
                    inlet_velocity=v,
                    channel_width=w,
                    model_name=f"param_{case_id}"
                )

                # 保存模型
                temp_dir = tempfile.gettempdir()
                model_path = os.path.join(temp_dir, f'{case_id}.mph')
                model.save(model_path)
                print(f"   ✅ 模型已保存")

                # 清理
                client.clear()
                client.remove()

                results.append({
                    'case': case_id,
                    'velocity': v,
                    'width': w,
                    'status': 'success',
                    'model_path': model_path
                })

            except Exception as e:
                print(f"   ❌ 失败: {e}")
                results.append({
                    'case': case_id,
                    'velocity': v,
                    'width': w,
                    'status': 'failed',
                    'error': str(e)
                })

    # 总结
    print(f"\n" + "=" * 70)
    print(f"📊 扫描结果总结")
    print(f"=" * 70)

    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"✅ 成功: {success_count}/{len(results)}")
    print(f"❌ 失败: {len(results)-success_count}/{len(results)}")

    return results


def main():
    """主函数"""
    print("📅 自动化参数化扫描工具")
    print(f"⏰ 时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = run_parametric_sweep()

    print(f"\n" + "=" * 70)
    print(f"✅ 参数化扫描完成")
    print(f"=" * 70)

    return len(results) > 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
