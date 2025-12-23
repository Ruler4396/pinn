#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动COMSOL数据生成脚本 - 非交互式版本
直接执行无需用户确认

作者: Claude
日期: 2025-11-19
"""

import os
import sys
import time
import json
import h5py
import numpy as np
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    import mph
    print("✅ mph模块导入成功")
except ImportError:
    print("❌ mph模块未安装，请先安装: pip install mph")
    sys.exit(1)

class AutoDataGenerator:
    """自动数据生成器"""

    def __init__(self, max_cases=10):  # 限制为10个案例用于快速测试
        """初始化自动生成器"""
        self.max_cases = max_cases
        self.comsol_path = r"E:\COMSOL63\Multiphysics\bin\win64\comsol.exe"

        # 目录设置
        self.output_dir = project_root / "comsol_simulation" / "data"
        self.models_dir = project_root / "comsol_simulation" / "models"
        self.logs_dir = project_root / "comsol_simulation" / "logs"

        # 创建目录
        for directory in [self.output_dir, self.models_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # 定义参数组合（限制数量）
        self.define_test_parameters()

        # 状态跟踪
        self.total_cases = len(self.parameter_combinations)
        self.completed_cases = []
        self.failed_cases = []
        self.start_time = None

        print(f"🚀 自动数据生成器初始化完成")
        print(f"   - 总案例数: {self.total_cases}")

    def define_test_parameters(self):
        """定义测试参数组合"""
        # 使用代表性参数组合进行快速测试
        test_params = [
            {'inlet_velocity': 0.001, 'channel_width': 0.20, 'fluid_viscosity': 0.001},  # 低Re
            {'inlet_velocity': 0.01, 'channel_width': 0.20, 'fluid_viscosity': 0.001},   # 中Re
            {'inlet_velocity': 0.05, 'channel_width': 0.20, 'fluid_viscosity': 0.001},   # 高Re
            {'inlet_velocity': 0.01, 'channel_width': 0.15, 'fluid_viscosity': 0.001},   # 窄通道
            {'inlet_velocity': 0.01, 'channel_width': 0.25, 'fluid_viscosity': 0.001},   # 宽通道
            {'inlet_velocity': 0.01, 'channel_width': 0.20, 'fluid_viscosity': 0.01},    # 高粘度
            {'inlet_velocity': 0.03, 'channel_width': 0.18, 'fluid_viscosity': 0.002},   # 中等参数
            {'inlet_velocity': 0.02, 'channel_width': 0.22, 'fluid_viscosity': 0.005},   # 另一组中等参数
            {'inlet_velocity': 0.08, 'channel_width': 0.16, 'fluid_viscosity': 0.001},   # 高速窄通道
            {'inlet_velocity': 0.001, 'channel_width': 0.24, 'fluid_viscosity': 0.008},  # 低速高粘度
        ]

        self.parameter_combinations = []
        for i, params in enumerate(test_params[:self.max_cases]):
            # 计算雷诺数
            re_estimate = 1000 * params['inlet_velocity'] * (params['channel_width'] * 1e-3) / params['fluid_viscosity']

            case_params = {
                'case_id': f'auto_case_{i+1:02d}',
                'inlet_velocity': params['inlet_velocity'],
                'channel_width': params['channel_width'],
                'fluid_viscosity': params['fluid_viscosity'],
                'channel_length': 10.0,  # mm
                'fluid_density': 1000.0,  # kg/m³
                'outlet_pressure': 0.0,    # Pa
                'estimated_reynolds': re_estimate
            }
            self.parameter_combinations.append(case_params)

        print(f"📋 测试参数组合定义完成 ({len(self.parameter_combinations)} 个案例):")
        for i, p in enumerate(self.parameter_combinations):
            print(f"   {p['case_id']}: v={p['inlet_velocity']}m/s, w={p['channel_width']*1000:.0f}μm, μ={p['fluid_viscosity']}Pa·s, Re={p['estimated_reynolds']:.1f}")

    def log_message(self, message):
        """记录日志信息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)

    def create_and_run_model(self, params):
        """创建并运行单个模型"""
        try:
            self.log_message(f"开始处理: {params['case_id']}")

            # 创建COMSOL客户端
            client = mph.Client(self.comsol_path)
            model = client.create(f"microfluidic_{params['case_id']}")

            # 几何设置
            model.geom().create("geom1", 2)
            model.geom("geom1").lengthUnit("mm")

            rect1 = model.geom("geom1").create("r1", "Rectangle")
            rect1.set("size", [params['channel_length'], params['channel_width']])
            rect1.set("pos", [0.0, 0.0])
            model.geom("geom1").run()

            # 物理场设置
            model.physics().create("spf", "LaminarFlow", "geom1")

            model.physics("spf").feature().create("defns", "DefaultNodeSettings")
            model.physics("spf").feature("defns").selection().all()
            model.physics("spf").feature("defns").set("rho", str(params['fluid_density']))
            model.physics("spf").feature("defns").set("mu", str(params['fluid_viscosity']))

            # 边界条件
            inlet = model.physics("spf").feature().create("in1", "InletVelocity", 2)
            inlet.selection().set([1])
            inlet.set("U0", str(params['inlet_velocity']))

            outlet = model.physics("spf").feature().create("out1", "OutletPressure", 2)
            outlet.selection().set([2])
            outlet.set("p0", str(params['outlet_pressure']))

            wall = model.physics("spf").feature().create("wall1", "Wall", 2)
            wall.selection().set([3, 4])

            # 网格生成
            model.mesh().create("mesh1", "geom1")
            model.mesh("mesh1").automatic(True)
            model.mesh("mesh1").run()

            # 求解
            study = model.study().create("std1")
            study.feature().create("stat", "Stationary")
            model.study("std1").run()

            # 数据导出
            self.export_simulation_data(model, params)

            # 清理
            client.clear()
            return True

        except Exception as e:
            self.log_message(f"❌ 处理失败: {params['case_id']} - {str(e)}")
            try:
                client.clear()
            except:
                pass
            return False

    def export_simulation_data(self, model, params):
        """导出模拟数据"""
        try:
            # 创建评估
            model.result().numerical().create("eval1", "Eval")
            model.result().numerical("eval1").set("expr", ["u", "v", "p"])

            # 生成数据网格 (20x20 用于快速测试)
            grid_size = 20
            x_points = np.linspace(0, params['channel_length'], grid_size)
            y_points = np.linspace(0, params['channel_width'], grid_size)

            results = []
            for x in x_points:
                for y in y_points:
                    try:
                        model.result().numerical("eval1").set("p", [x, y])
                        values = model.result().numerical("eval1").getReal()
                        if len(values) >= 3:
                            results.append([x, y, values[0], values[1], values[2]])
                    except:
                        continue

            results = np.array(results)
            if len(results) == 0:
                raise ValueError("无有效数据")

            # 保存数据
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"auto_data_{params['case_id']}_{timestamp}.h5"
            filepath = self.output_dir / filename

            with h5py.File(filepath, 'w') as f:
                f.create_dataset('x', data=results[:, 0])
                f.create_dataset('y', data=results[:, 1])
                f.create_dataset('u', data=results[:, 2])
                f.create_dataset('v', data=results[:, 3])
                f.create_dataset('p', data=results[:, 4])

                # 元数据
                for key, value in params.items():
                    if isinstance(value, (int, float)):
                        f.attrs[key] = value
                    else:
                        f.attrs[key] = str(value)

                f.attrs['total_points'] = len(results)
                f.attrs['generation_time'] = timestamp

            self.log_message(f"✅ 数据导出成功: {filename} ({len(results)} 点)")

        except Exception as e:
            raise Exception(f"数据导出失败: {str(e)}")

    def run_all_cases(self):
        """运行所有案例"""
        self.start_time = time.time()

        self.log_message(f"🚀 开始自动生成 {self.total_cases} 个案例的数据")
        self.log_message(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        successful = 0

        for i, params in enumerate(self.parameter_combinations, 1):
            self.log_message(f"\n[{i}/{self.total_cases}] 处理案例: {params['case_id']}")

            case_start_time = time.time()
            if self.create_and_run_model(params):
                successful += 1
                self.completed_cases.append(params['case_id'])
                status = "✅ 成功"
            else:
                self.failed_cases.append(params['case_id'])
                status = "❌ 失败"

            case_time = time.time() - case_start_time
            self.log_message(f"{status} - 用时: {case_time:.1f}秒")

            # 进度更新
            progress = i / self.total_cases * 100
            elapsed = time.time() - self.start_time
            if i > 0:
                eta = elapsed / i * (self.total_cases - i)
                self.log_message(f"进度: {progress:.1f}%, 已用时: {elapsed/60:.1f}分钟, 预计剩余: {eta/60:.1f}分钟")

        # 最终统计
        total_time = time.time() - self.start_time
        success_rate = successful / self.total_cases * 100

        self.log_message(f"\n{'='*60}")
        self.log_message(f"🎉 自动生成完成!")
        self.log_message(f"✅ 成功: {successful}/{self.total_cases} ({success_rate:.1f}%)")
        self.log_message(f"❌ 失败: {len(self.failed_cases)}")
        self.log_message(f"⏰ 总用时: {total_time/60:.1f} 分钟")
        self.log_message(f"📁 数据保存在: {self.output_dir}")

        # 生成快速总结
        self.generate_summary(success_rate, total_time)

        return successful == self.total_cases

    def generate_summary(self, success_rate, total_time):
        """生成总结报告"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_file = self.output_dir / f"auto_summary_{timestamp}.txt"

            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("COMSOL自动数据生成总结\n")
                f.write("="*40 + "\n\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"成功案例: {len(self.completed_cases)}/{self.total_cases}\n")
                f.write(f"成功率: {success_rate:.1f}%\n")
                f.write(f"总用时: {total_time/60:.1f} 分钟\n\n")

                f.write("成功案例:\n")
                for case_id in self.completed_cases:
                    f.write(f"  ✅ {case_id}\n")

                if self.failed_cases:
                    f.write("\n失败案例:\n")
                    for case_id in self.failed_cases:
                        f.write(f"  ❌ {case_id}\n")

            self.log_message(f"📋 总结报告: {summary_file}")

        except Exception as e:
            self.log_message(f"报告生成失败: {str(e)}")


def main():
    """主函数"""
    print("🚀 COMSOL自动数据生成器启动")
    print("="*50)

    try:
        # 创建自动生成器 (生成10个测试案例)
        generator = AutoDataGenerator(max_cases=10)

        print(f"\n🎯 将自动生成 {generator.total_cases} 个测试案例")
        print("预计用时: 5-15分钟\n")

        # 直接开始执行
        success = generator.run_all_cases()

        if success:
            print(f"\n🎉 所有案例生成成功!")
            print("📂 数据文件已保存，可用于PINNs训练")
        else:
            print(f"\n⚠️  有 {len(generator.failed_cases)} 个案例失败")
            print("请检查COMSOL环境和日志文件")

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 执行错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()