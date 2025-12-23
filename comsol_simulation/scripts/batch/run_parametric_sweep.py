#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMSOL参数化扫描脚本 - 生成PINNs训练数据集
生成30组不同参数的微流控芯片流场数据

目标参数组合：
- 入口速度: 5个值 (0.001, 0.01, 0.03, 0.05, 0.1 m/s)
- 通道宽度: 3个值 (150, 200, 250 μm)
- 流体粘度: 2个值 (0.001, 0.01 Pa·s)
总计: 5×3×2 = 30组数据

作者: Claude
日期: 2025-11-19
"""

import os
import sys
import time
import numpy as np
import h5py
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    import mph
    print("✅ 成功导入mph模块")
except ImportError:
    print("❌ mph模块未安装，请先安装: pip install mph")
    sys.exit(1)

class MicrofluidicParametricSweep:
    """微流控芯片参数化扫描类"""

    def __init__(self):
        """初始化参数化扫描"""
        self.comsol_path = r"E:\COMSOL63\Multiphysics\bin\win64\comsol.exe"
        self.output_dir = project_root / "comsol_simulation" / "data"
        self.models_dir = project_root / "comsol_simulation" / "models"

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # 定义参数组合
        self.define_parameters()

        # 统计信息
        self.start_time = None
        self.completed_cases = 0
        self.total_cases = len(self.parameter_combinations)

        print(f"🚀 初始化参数化扫描，共{self.total_cases}组数据")

    def define_parameters(self):
        """定义参数扫描组合"""
        # 入口速度 (m/s) - 覆盖层流范围 Re=1-100
        inlet_velocities = [0.001, 0.01, 0.03, 0.05, 0.1]

        # 通道宽度 (μm) - 转换为mm
        channel_widths = [0.15, 0.20, 0.25]  # mm

        # 流体粘度 (Pa·s)
        fluid_viscosities = [0.001, 0.01]  # 水和较粘流体

        # 生成所有参数组合
        self.parameter_combinations = []
        for i, v_inlet in enumerate(inlet_velocities):
            for j, width in enumerate(channel_widths):
                for k, viscosity in enumerate(fluid_viscosities):
                    case_id = f"case_{i+1:02d}_{j+1}_{k+1}"
                    params = {
                        'case_id': case_id,
                        'inlet_velocity': v_inlet,
                        'channel_width': width,
                        'fluid_viscosity': viscosity,
                        'channel_length': 10.0,  # mm
                        'fluid_density': 1000.0,  # kg/m³ (水)
                        'outlet_pressure': 0.0    # Pa
                    }
                    self.parameter_combinations.append(params)

        print(f"📋 参数组合设计完成:")
        print(f"   - 入口速度: {inlet_velocities} m/s")
        print(f"   - 通道宽度: {channel_widths} mm")
        print(f"   - 流体粘度: {fluid_viscosities} Pa·s")
        print(f"   - 总计: {self.total_cases}组参数")

    def create_comsol_model(self, params):
        """使用mph创建COMSOL模型"""
        try:
            print(f"🔧 创建COMSOL模型: {params['case_id']}")

            # 启动COMSOL客户端
            client = mph.Client(self.comsol_path)

            # 创建新模型
            model = client.create("microfluidic_" + params['case_id'])

            # 设置几何
            model.geom().create("geom1", 2)
            model.geom("geom1").lengthUnit("mm")

            # 创建矩形通道
            rect1 = model.geom("geom1").create("r1", "Rectangle")
            rect1.set("size", [params['channel_length'], params['channel_width']])
            rect1.set("pos", [0.0, 0.0])

            # 运行几何操作
            model.geom("geom1").run()

            # 添加物理场
            model.physics().create("spf", "LaminarFlow", "geom1")

            # 设置材料属性
            model.physics("spf").feature().create("defns", "DefaultNodeSettings")
            model.physics("spf").feature("defns").selection().all()

            # 设置流体属性
            model.physics("spf").feature("defns").set("rho", str(params['fluid_density']))
            model.physics("spf").feature("defns").set("mu", str(params['fluid_viscosity']))

            # 入口边界条件 (左边)
            inlet = model.physics("spf").feature().create("in1", "InletVelocity", 2)
            inlet.selection().set([1])
            inlet.set("U0", str(params['inlet_velocity']))

            # 出口边界条件 (右边)
            outlet = model.physics("spf").feature().create("out1", "OutletPressure", 2)
            outlet.selection().set([2])
            outlet.set("p0", str(params['outlet_pressure']))

            # 壁面边界条件 (上下)
            wall = model.physics("spf").feature().create("wall1", "Wall", 2)
            wall.selection().set([3, 4])

            # 创建网格
            model.mesh().create("mesh1", "geom1")
            model.mesh("mesh1").automatic(True)

            # 网格设置 - 优化质量和计算效率
            model.mesh("mesh1").set("maxsize", params['channel_width'] / 10)  # 自适应网格
            model.mesh("mesh1").set("minsize", params['channel_width'] / 100)

            # 运行网格生成
            model.mesh("mesh1").run()

            # 创建研究
            study = model.study().create("std1")
            study.feature().create("stat", "Stationary")

            # 设置求解器
            study.feature("stat").set("studystepstat", "on")

            print(f"   ✅ 模型创建完成: {params['case_id']}")
            return model, client

        except Exception as e:
            print(f"   ❌ 模型创建失败: {e}")
            return None, None

    def run_simulation(self, model, params):
        """运行COMSOL模拟"""
        try:
            print(f"🔄 运行模拟: {params['case_id']}")

            # 运行研究
            model.study("std1").run()

            print(f"   ✅ 模拟完成: {params['case_id']}")
            return True

        except Exception as e:
            print(f"   ❌ 模拟失败: {e}")
            return False

    def export_data(self, model, params):
        """导出模拟数据到HDF5格式"""
        try:
            print(f"💾 导出数据: {params['case_id']}")

            # 创建结果数据集
            model.result().numerical().create("eval1", "Eval")
            model.result().numerical("eval1").set("expr", ["u", "v", "p"])
            model.result().numerical("eval1").set("unit", ["m/s", "m/s", "Pa"])
            model.result().numerical("eval1").set("descr", ["x-velocity", "y-velocity", "pressure"])

            # 生成高质量数据网格
            resolution = 50  # 每个方向50个点
            x_points = np.linspace(0, params['channel_length'], resolution)
            y_points = np.linspace(0, params['channel_width'], resolution)

            # 评估结果
            results = []
            for x in x_points:
                for y in y_points:
                    try:
                        # 设置评估点
                        model.result().numerical("eval1").set("p", [x, y])
                        # 评估结果
                        values = model.result().numerical("eval1").getReal()
                        results.append([x, y] + list(values))
                    except:
                        # 如果某个点失败，使用插值或跳过
                        continue

            # 转换为numpy数组
            results = np.array(results)

            if len(results) == 0:
                print(f"   ❌ 数据导出失败：没有有效数据点")
                return False

            # 创建HDF5文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"parametric_data_{params['case_id']}_{timestamp}.h5"
            filepath = self.output_dir / filename

            with h5py.File(filepath, 'w') as f:
                # 保存数据
                f.create_dataset('coordinates', data=results[:, :2])  # x, y坐标
                f.create_dataset('velocity_u', data=results[:, 2])    # x方向速度
                f.create_dataset('velocity_v', data=results[:, 3])    # y方向速度
                f.create_dataset('pressure', data=results[:, 4])      # 压力

                # 保存参数元数据
                param_group = f.create_group('parameters')
                for key, value in params.items():
                    param_group.attrs[key] = value

                # 保存网格信息
                f.attrs['resolution'] = resolution
                f.attrs['total_points'] = len(results)
                f.attrs['creation_date'] = timestamp
                f.attrs['case_id'] = params['case_id']

                # 保存物理信息
                f.attrs['reynolds_number'] = self.calculate_reynolds(params)
                f.attrs['description'] = f"Microfluidic channel simulation - {params['case_id']}"

            print(f"   ✅ 数据导出成功: {filename}")
            print(f"      - 数据点数: {len(results)}")
            print(f"      - 文件大小: {filepath.stat().st_size / 1024:.1f} KB")

            return True

        except Exception as e:
            print(f"   ❌ 数据导出失败: {e}")
            return False

    def calculate_reynolds(self, params):
        """计算雷诺数"""
        # Re = ρ * V * D_h / μ
        # D_h = 4 * A / P (水力直径，矩形通道)
        width_m = params['channel_width'] * 1e-3  # 转换为米
        height_m = width_m  # 假设正方形截面
        area = width_m * height_m
        perimeter = 2 * (width_m + height_m)
        hydraulic_diameter = 4 * area / perimeter

        reynolds = (params['fluid_density'] * params['inlet_velocity'] *
                   hydraulic_diameter / params['fluid_viscosity'])

        return reynolds

    def run_single_case(self, params):
        """运行单个参数组合的完整流程"""
        case_start_time = time.time()
        print(f"\n🎯 开始处理案例 {params['case_id']}")
        print(f"   参数: v_inlet={params['inlet_velocity']}m/s, "
              f"width={params['channel_width']*1000:.0f}μm, "
              f"μ={params['fluid_viscosity']}Pa·s")

        try:
            # 创建COMSOL模型
            model, client = self.create_comsol_model(params)
            if model is None:
                return False

            # 运行模拟
            if not self.run_simulation(model, params):
                client.clear()
                return False

            # 导出数据
            if not self.export_data(model, params):
                client.clear()
                return False

            # 计算雷诺数并显示
            re = self.calculate_reynolds(params)
            print(f"   📊 雷诺数: Re = {re:.1f}")

            # 清理资源
            client.clear()

            case_time = time.time() - case_start_time
            print(f"   ⏱️  用时: {case_time:.1f}秒")

            self.completed_cases += 1
            return True

        except Exception as e:
            print(f"   ❌ 案例处理失败: {e}")
            return False

    def run_full_sweep(self):
        """运行完整的参数化扫描"""
        print(f"\n🚀 开始参数化扫描 - {self.total_cases}组数据")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        self.start_time = time.time()
        successful_cases = 0

        for i, params in enumerate(self.parameter_combinations, 1):
            print(f"\n{'='*60}")
            print(f"进度: {i}/{self.total_cases} ({i/self.total_cases*100:.1f}%)")

            if self.run_single_case(params):
                successful_cases += 1

            # 显示总体进度
            elapsed = time.time() - self.start_time
            if i > 0:
                avg_time = elapsed / i
                remaining_cases = self.total_cases - i
                eta = avg_time * remaining_cases
                print(f"📈 总体进度: {successful_cases}/{i} 成功")
                print(f"⏱️  已用时: {elapsed/60:.1f}分钟, 预计剩余: {eta/60:.1f}分钟")

        # 完成统计
        total_time = time.time() - self.start_time
        success_rate = successful_cases / self.total_cases * 100

        print(f"\n{'='*60}")
        print(f"🎉 参数化扫描完成!")
        print(f"📊 成功率: {successful_cases}/{self.total_cases} ({success_rate:.1f}%)")
        print(f"⏰ 总用时: {total_time/60:.1f}分钟 ({total_time/3600:.2f}小时)")
        print(f"📁 数据保存在: {self.output_dir}")

        # 生成数据集总结报告
        self.generate_summary_report(successful_cases, total_time)

        return successful_cases == self.total_cases

    def generate_summary_report(self, successful_cases, total_time):
        """生成数据集总结报告"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.output_dir / f"dataset_summary_{timestamp}.txt"

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("COMSOL微流控芯片参数化扫描数据集总结报告\n")
                f.write("="*50 + "\n\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"成功案例: {successful_cases}/{self.total_cases}\n")
                f.write(f"成功率: {successful_cases/self.total_cases*100:.1f}%\n")
                f.write(f"总用时: {total_time/60:.1f} 分钟\n")
                f.write(f"平均每案例: {total_time/self.total_cases:.1f} 秒\n\n")

                f.write("参数范围:\n")
                f.write(f"  入口速度: 0.001 - 0.1 m/s\n")
                f.write(f"  通道宽度: 150 - 250 μm\n")
                f.write(f"  流体粘度: 0.001 - 0.01 Pa·s\n\n")

                f.write("雷诺数范围:\n")
                reynolds = [self.calculate_reynolds(p) for p in self.parameter_combinations]
                f.write(f"  最小值: {min(reynolds):.1f}\n")
                f.write(f"  最大值: {max(reynolds):.1f}\n")
                f.write(f"  平均值: {np.mean(reynolds):.1f}\n\n")

                f.write("数据文件格式: HDF5 (.h5)\n")
                f.write("数据内容: 坐标(x,y), 速度(u,v), 压力(p)\n")
                f.write("典型数据点数: 2000-2500/案例\n\n")

                f.write("适用范围: PINNs训练、流场重建、参数敏感性分析\n")

            print(f"📋 总结报告已生成: {report_file}")

        except Exception as e:
            print(f"⚠️  报告生成失败: {e}")


def main():
    """主函数"""
    print("🚀 COMSOL微流控芯片参数化扫描启动")
    print("="*50)

    try:
        # 创建扫描实例
        sweep = MicrofluidicParametricSweep()

        # 确认执行
        print(f"\n⚠️  准备生成{sweep.total_cases}组COMSOL模拟数据")
        print("预计需要2-4小时计算时间")

        response = input("\n确认继续执行? (y/N): ").lower().strip()
        if response not in ['y', 'yes']:
            print("❌ 用户取消操作")
            return

        # 运行完整扫描
        success = sweep.run_full_sweep()

        if success:
            print("\n🎉 所有数据生成完成! 可以开始PINNs训练了!")
        else:
            print("\n⚠️  部分案例失败，请检查日志文件")

    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序执行错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()