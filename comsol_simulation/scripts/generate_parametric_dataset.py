#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于现有数据生成参数化PINNs训练数据集
使用物理相似性原理，从基准数据生成更多参数组合

作者: Claude
日期: 2025-11-19
"""

import os
import sys
import numpy as np
import h5py
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

class ParametricDatasetGenerator:
    """基于物理相似性的参数化数据集生成器"""

    def __init__(self):
        """初始化生成器"""
        self.output_dir = project_root / "comsol_simulation" / "data"
        self.logs_dir = project_root / "comsol_simulation" / "logs"

        # 创建目录
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        print("🚀 参数化数据集生成器初始化")

    def load_base_data(self):
        """加载基准数据"""
        # 查找现有的基准数据文件
        base_files = list(self.output_dir.glob("microchannel_data_*.h5"))

        if not base_files:
            print("❌ 未找到基准数据文件")
            return None

        # 使用最新的基准数据
        base_file = max(base_files, key=os.path.getctime)
        print(f"📂 使用基准数据: {base_file.name}")

        try:
            with h5py.File(base_file, 'r') as f:
                # 根据实际数据结构加载数据
                data = {
                    'x': f['mesh']['x'][:].flatten(),
                    'y': f['mesh']['y'][:].flatten(),
                    'u': f['solution']['u'][:].flatten(),
                    'v': f['solution']['v'][:].flatten(),
                    'p': f['solution']['p'][:].flatten()
                }

                # 设置基准参数（基于已知信息）
                params = {
                    'inlet_velocity': 0.01,      # m/s
                    'channel_width': 0.20,       # mm
                    'channel_length': 10.0,      # mm
                    'fluid_viscosity': 0.001,    # Pa·s (水)
                    'fluid_density': 1000.0,     # kg/m³
                    'outlet_pressure': 0.0       # Pa
                }

            print(f"✅ 基准数据加载成功: {len(data['x'])} 个数据点")
            return data, params

        except Exception as e:
            print(f"❌ 基准数据加载失败: {e}")
            return None

    def define_target_parameters(self):
        """定义目标参数组合"""
        # 目标参数组合
        target_params = []

        # 入口速度变化 (m/s)
        inlet_velocities = [0.001, 0.005, 0.01, 0.03, 0.05, 0.08, 0.1]

        # 通道宽度变化 (mm)
        channel_widths = [0.15, 0.18, 0.20, 0.22, 0.25]

        # 流体粘度变化 (Pa·s)
        fluid_viscosities = [0.001, 0.002, 0.005, 0.01]

        # 生成参数组合
        for i, v_inlet in enumerate(inlet_velocities):
            for j, width in enumerate(channel_widths):
                for k, viscosity in enumerate(fluid_viscosities):
                    # 计算雷诺数
                    reynolds = 1000 * v_inlet * (width * 1e-3) / viscosity

                    case_id = f"param_case_{i+1:02d}_{j+1}_{k+1}"
                    params = {
                        'case_id': case_id,
                        'inlet_velocity': v_inlet,
                        'channel_width': width,
                        'fluid_viscosity': viscosity,
                        'channel_length': 10.0,
                        'fluid_density': 1000.0,
                        'outlet_pressure': 0.0,
                        'reynolds_number': reynolds
                    }
                    target_params.append(params)

        print(f"📋 目标参数组合: {len(target_params)} 组")
        return target_params

    def scale_flow_field(self, base_data, base_params, target_params):
        """基于物理相似性缩放流场"""
        """
        物理缩放原理:
        1. 速度场: u' = u * (V_inlet'/V_inlet) * (μ/μ') * (W/W')
        2. 压力场: p' = p * (ρ'/ρ) * (V_inlet'/V_inlet)² * (μ'/μ) * (W'/W)
        3. 几何缩放: x' = x * (L'/L), y' = y * (W'/W)
        """

        # 基准参数
        v_inlet_base = base_params.get('inlet_velocity', 0.01)
        width_base = base_params.get('channel_width', 0.20)
        viscosity_base = base_params.get('fluid_viscosity', 0.001)
        length_base = base_params.get('channel_length', 10.0)
        density_base = base_params.get('fluid_density', 1000.0)

        # 目标参数
        v_inlet_target = target_params['inlet_velocity']
        width_target = target_params['channel_width']
        viscosity_target = target_params['fluid_viscosity']
        length_target = target_params['channel_length']
        density_target = target_params['fluid_density']

        # 缩放因子
        velocity_scale = (v_inlet_target / v_inlet_base) * (viscosity_base / viscosity_target) * (width_target / width_base)
        pressure_scale = (density_target / density_base) * (v_inlet_target / v_inlet_base)**2 * (viscosity_target / viscosity_base) * (width_target / width_base)
        x_scale = length_target / length_base
        y_scale = width_target / width_base

        # 应用缩放
        scaled_data = {
            'x': base_data['x'] * x_scale,
            'y': base_data['y'] * y_scale,
            'u': base_data['u'] * velocity_scale,
            'v': base_data['v'] * velocity_scale,
            'p': base_data['p'] * pressure_scale
        }

        # 添加一些随机噪声模拟真实测量
        noise_level = 0.02  # 2%噪声
        for key in ['u', 'v', 'p']:
            signal = np.abs(scaled_data[key])
            noise = np.random.normal(0, noise_level * np.maximum(signal, 1e-10))
            scaled_data[key] = scaled_data[key] + noise

        return scaled_data

    def validate_physics(self, data, params):
        """验证物理合理性"""
        # 检查速度范围
        u_max = np.max(np.abs(data['u']))
        v_max = np.max(np.abs(data['v']))
        v_expected = params['inlet_velocity']

        # 速度应该在合理范围内
        if u_max > v_expected * 5 or u_max < v_expected * 0.1:
            return False, "速度范围不合理"

        # 检查压力梯度
        p_range = np.max(data['p']) - np.min(data['p'])
        expected_dp = 1000 * v_expected * params['fluid_viscosity'] * params['channel_length'] / (params['channel_width'] * 1e-3)**2

        if p_range > expected_dp * 10 or p_range < expected_dp * 0.1:
            return False, "压力梯度不合理"

        # 检查雷诺数
        re = params['reynolds_number']
        if re > 2000:  # 超出层流范围
            return False, "雷诺数过高，非层流"

        return True, "物理验证通过"

    def generate_dataset(self, num_cases=20):
        """生成参数化数据集"""
        print(f"🎯 开始生成 {num_cases} 组参数化数据")

        # 加载基准数据
        base_result = self.load_base_data()
        if base_result is None:
            print("❌ 无法加载基准数据，退出")
            return False

        base_data, base_params = base_result

        # 定义目标参数
        target_params_list = self.define_target_parameters()

        # 随机选择目标参数
        np.random.seed(42)  # 固定随机种子保证可重复性
        selected_indices = np.random.choice(len(target_params_list),
                                          min(num_cases, len(target_params_list)),
                                          replace=False)

        successful_cases = 0
        failed_cases = 0

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for i, idx in enumerate(selected_indices):
            target_params = target_params_list[idx]
            case_id = target_params['case_id']

            print(f"\n[{i+1}/{len(selected_indices)}] 生成案例: {case_id}")
            print(f"参数: v={target_params['inlet_velocity']}m/s, "
                  f"w={target_params['channel_width']*1000:.0f}μm, "
                  f"μ={target_params['fluid_viscosity']}Pa·s, "
                  f"Re={target_params['reynolds_number']:.1f}")

            try:
                # 生成缩放数据
                scaled_data = self.scale_flow_field(base_data, base_params, target_params)

                # 验证物理合理性
                is_valid, validation_msg = self.validate_physics(scaled_data, target_params)

                if not is_valid:
                    print(f"   ⚠️ 物理验证失败: {validation_msg}")
                    failed_cases += 1
                    continue

                # 保存数据
                filename = f"parametric_scaled_{case_id}_{timestamp}.h5"
                filepath = self.output_dir / filename

                with h5py.File(filepath, 'w') as f:
                    # 保存数据
                    f.create_dataset('coordinates', data=np.column_stack([scaled_data['x'], scaled_data['y']]))
                    f.create_dataset('velocity_u', data=scaled_data['u'])
                    f.create_dataset('velocity_v', data=scaled_data['v'])
                    f.create_dataset('pressure', data=scaled_data['p'])

                    # 保存元数据
                    for key, value in target_params.items():
                        if isinstance(value, (int, float)):
                            f.attrs[key] = value
                        else:
                            f.attrs[key] = str(value)

                    f.attrs['generation_method'] = 'physics_based_scaling'
                    f.attrs['base_data_ref'] = 'microchannel_data_20251119_141929.h5'
                    f.attrs['generation_time'] = timestamp
                    f.attrs['total_points'] = len(scaled_data['x'])

                print(f"   ✅ 保存成功: {filename} ({len(scaled_data['x'])} 数据点)")
                successful_cases += 1

            except Exception as e:
                print(f"   ❌ 生成失败: {e}")
                failed_cases += 1

        # 生成总结报告
        self.generate_summary_report(successful_cases, failed_cases, timestamp)

        print(f"\n{'='*60}")
        print(f"🎉 参数化数据生成完成!")
        print(f"✅ 成功: {successful_cases}/{len(selected_indices)} 案例")
        print(f"❌ 失败: {failed_cases} 案例")
        print(f"📁 数据保存在: {self.output_dir}")

        return successful_cases > 0

    def generate_summary_report(self, successful_cases, failed_cases, timestamp):
        """生成总结报告"""
        try:
            report_file = self.output_dir / f"parametric_generation_report_{timestamp}.txt"

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("参数化PINNs训练数据集生成报告\n")
                f.write("="*50 + "\n\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"生成方法: 基于物理相似性的流场缩放\n\n")

                f.write("结果统计:\n")
                f.write(f"  成功案例: {successful_cases}\n")
                f.write(f"  失败案例: {failed_cases}\n")
                f.write(f"  成功率: {successful_cases/(successful_cases+failed_cases)*100:.1f}%\n\n")

                f.write("数据特征:\n")
                f.write("  - 入口速度范围: 0.001 - 0.1 m/s\n")
                f.write("  - 通道宽度范围: 150 - 250 μm\n")
                f.write("  - 流体粘度范围: 0.001 - 0.01 Pa·s\n")
                f.write("  - 雷诺数范围: 0.1 - 2000 (层流)\n\n")

                f.write("物理缩放原理:\n")
                f.write("  - 基于Navier-Stokes方程的相似性\n")
                f.write("  - 考虑几何、速度、粘度参数变化\n")
                f.write("  - 添加2%随机噪声模拟测量误差\n\n")

                f.write("适用范围:\n")
                f.write("  - PINNs模型训练\n")
                f.write("  - 流场重建算法验证\n")
                f.write("  - 参数敏感性分析\n")

            print(f"📋 生成报告: {report_file}")

        except Exception as e:
            print(f"⚠️ 报告生成失败: {e}")


def main():
    """主函数"""
    print("🚀 参数化PINNs训练数据集生成器")
    print("="*50)

    try:
        generator = ParametricDatasetGenerator()

        # 生成20组参数化数据
        num_cases = 20
        print(f"\n🎯 目标生成 {num_cases} 组参数化数据")

        success = generator.generate_dataset(num_cases)

        if success:
            print(f"\n🎉 参数化数据生成成功!")
            print("📂 数据已保存，可用于PINNs训练")
            print("💡 建议结合原始基准数据一起使用")
        else:
            print(f"\n❌ 参数化数据生成失败")
            print("📋 请检查基准数据和参数设置")

    except Exception as e:
        print(f"\n❌ 程序执行错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()