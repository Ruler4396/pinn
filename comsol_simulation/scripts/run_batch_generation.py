#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMSOL批量数据生成脚本 - 优化版本
分批处理，降低内存占用，提高稳定性

针对AMD R5 5500U优化：
- 分批处理，每批5个案例
- 进度监控和错误恢复
- 自动重试机制
- 资源清理

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

class BatchDataGenerator:
    """批量数据生成器 - 针对移动CPU优化"""

    def __init__(self, batch_size=5, max_retries=2):
        """
        初始化批量生成器

        Args:
            batch_size: 每批处理的案例数量 (推荐5个，适合6核CPU)
            max_retries: 最大重试次数
        """
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.comsol_path = r"E:\COMSOL63\Multiphysics\bin\win64\comsol.exe"

        # 目录设置
        self.output_dir = project_root / "comsol_simulation" / "data"
        self.models_dir = project_root / "comsol_simulation" / "models"
        self.logs_dir = project_root / "comsol_simulation" / "logs"

        # 创建目录
        for directory in [self.output_dir, self.models_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # 定义参数组合
        self.define_optimized_parameters()

        # 状态跟踪
        self.total_cases = len(self.parameter_combinations)
        self.completed_cases = []
        self.failed_cases = []
        self.log_file = self.logs_dir / f"batch_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        print(f"🚀 批量数据生成器初始化完成")
        print(f"   - 每批处理: {self.batch_size}个案例")
        print(f"   - 总案例数: {self.total_cases}")
        print(f"   - 预计批数: {(self.total_cases + batch_size - 1) // batch_size}")

    def define_optimized_parameters(self):
        """定义优化的参数组合 - 确保计算效率和数据质量"""

        # 优化参数选择 - 基于物理合理性和计算效率
        inlet_velocities = [0.001, 0.01, 0.03, 0.05, 0.1]  # m/s，覆盖不同Re
        channel_widths = [0.15, 0.20, 0.25]  # mm，标准微通道尺寸
        fluid_viscosities = [0.001, 0.01]  # Pa·s，水和较粘流体

        self.parameter_combinations = []

        for i, v_inlet in enumerate(inlet_velocities):
            for j, width in enumerate(channel_widths):
                for k, viscosity in enumerate(fluid_viscosities):

                    # 计算预估雷诺数
                    re_estimate = 1000 * v_inlet * (width * 1e-3) / viscosity

                    case_id = f"case_{i+1:02d}_{j+1}_{k+1}"
                    params = {
                        'case_id': case_id,
                        'inlet_velocity': v_inlet,
                        'channel_width': width,
                        'fluid_viscosity': viscosity,
                        'channel_length': 10.0,  # mm
                        'fluid_density': 1000.0,  # kg/m³
                        'outlet_pressure': 0.0,    # Pa
                        'estimated_reynolds': re_estimate,
                        'priority': 'high' if 1 < re_estimate < 100 else 'normal'  # 优先处理合理Re范围
                    }
                    self.parameter_combinations.append(params)

        # 按优先级排序
        self.parameter_combinations.sort(key=lambda x: x['priority'], reverse=True)

        print(f"📋 参数组合定义完成:")
        print(f"   - 入口速度范围: {min(inlet_velocities)} - {max(inlet_velocities)} m/s")
        print(f"   - 通道宽度范围: {min(channel_widths)*1000:.0f} - {max(channel_widths)*1000:.0f} μm")
        print(f"   - 流体粘度: {fluid_viscosities} Pa·s")
        print(f"   - 雷诺数范围: {min([p['estimated_reynolds'] for p in self.parameter_combinations]):.1f} - {max([p['estimated_reynolds'] for p in self.parameter_combinations]):.1f}")

    def log_message(self, message, level="INFO"):
        """记录日志信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"

        print(message)

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def create_single_model(self, params, attempt=1):
        """创建单个COMSOL模型 - 简化版，提高成功率"""
        try:
            self.log_message(f"创建模型: {params['case_id']} (尝试 {attempt})")

            # 使用轻量级客户端启动
            client = mph.Client(self.comsol_path, cores=4)  # 限制核心使用

            # 创建模型
            model_name = f"microfluidic_{params['case_id']}"
            model = client.create(model_name)

            # 2D几何
            model.geom().create("geom1", 2)
            model.geom("geom1").lengthUnit("mm")

            # 矩形通道
            rect1 = model.geom("geom1").create("r1", "Rectangle")
            rect1.set("size", [params['channel_length'], params['channel_width']])
            rect1.set("pos", [0.0, 0.0])
            model.geom("geom1").run()

            # 层流物理场
            model.physics().create("spf", "LaminarFlow", "geom1")

            # 材料属性
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

            # 自适应网格 - 针对移动CPU优化
            model.mesh().create("mesh1", "geom1")
            element_size = max(params['channel_width'] / 8, params['channel_width'] / 15)  # 平衡质量和速度
            model.mesh("mesh1").set("maxsize", element_size)
            model.mesh("mesh1").set("minsize", element_size / 4)
            model.mesh("mesh1").automatic(True)
            model.mesh("mesh1").run()

            # 研究
            study = model.study().create("std1")
            study.feature().create("stat", "Stationary")

            self.log_message(f"模型创建成功: {params['case_id']}")
            return model, client

        except Exception as e:
            self.log_message(f"模型创建失败: {params['case_id']} - {str(e)}", "ERROR")
            return None, None

    def run_simulation_optimized(self, model, params):
        """运行优化的模拟"""
        try:
            self.log_message(f"开始模拟: {params['case_id']}")

            # 设置求解器参数 - 针对移动CPU优化
            model.study("std1").feature("stat").set("solnum", "auto")
            model.study("std1").feature("stat").set("funclist", "all")

            # 运行求解
            model.study("std1").run()

            self.log_message(f"模拟完成: {params['case_id']}")
            return True

        except Exception as e:
            self.log_message(f"模拟失败: {params['case_id']} - {str(e)}", "ERROR")
            return False

    def export_data_optimized(self, model, params):
        """优化的数据导出"""
        try:
            self.log_message(f"导出数据: {params['case_id']}")

            # 创建评估组
            model.result().numerical().create("eval1", "Eval")
            model.result().numerical("eval1").set("expr", ["u", "v", "p"])
            model.result().numerical("eval1").set("unit", ["m/s", "m/s", "Pa"])

            # 生成数据点 - 降低密度以提高速度
            grid_points = 30  # 从50降到30，减少计算量
            x_points = np.linspace(0, params['channel_length'], grid_points)
            y_points = np.linspace(0, params['channel_width'], grid_points)

            # 批量评估
            results = []
            eval_points = []

            for x in x_points:
                for y in y_points:
                    eval_points.append([x, y])

            # 分批评估以避免内存问题
            batch_eval_size = 100
            for i in range(0, len(eval_points), batch_eval_size):
                batch_points = eval_points[i:i+batch_eval_size]

                try:
                    for point in batch_points:
                        model.result().numerical("eval1").set("p", point)
                        values = model.result().numerical("eval1").getReal()
                        if len(values) >= 3:
                            results.append([point[0], point[1], values[0], values[1], values[2]])
                except:
                    continue

            # 转换为数组
            results = np.array(results)

            if len(results) == 0:
                self.log_message(f"无有效数据: {params['case_id']}", "ERROR")
                return False

            # 保存到HDF5
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"batch_data_{params['case_id']}_{timestamp}.h5"
            filepath = self.output_dir / filename

            with h5py.File(filepath, 'w') as f:
                # 数据集
                f.create_dataset('x_coordinates', data=results[:, 0])
                f.create_dataset('y_coordinates', data=results[:, 1])
                f.create_dataset('velocity_u', data=results[:, 2])
                f.create_dataset('velocity_v', data=results[:, 3])
                f.create_dataset('pressure', data=results[:, 4])

                # 组合数据便于读取
                f.create_dataset('coordinates', data=results[:, :2])
                f.create_dataset('velocity', data=results[:, 2:4])

                # 元数据
                for key, value in params.items():
                    if isinstance(value, (int, float)):
                        f.attrs[key] = value
                    else:
                        f.attrs[key] = str(value)

                # 额外信息
                f.attrs['total_points'] = len(results)
                f.attrs['grid_resolution'] = grid_points
                f.attrs['generation_time'] = timestamp
                f.attrs['reynolds_number'] = params['estimated_reynolds']

            self.log_message(f"数据导出成功: {filename} ({len(results)} 数据点)")
            return True

        except Exception as e:
            self.log_message(f"数据导出失败: {params['case_id']} - {str(e)}", "ERROR")
            return False

    def process_single_case(self, params):
        """处理单个案例 - 带重试机制"""
        for attempt in range(1, self.max_retries + 1):
            try:
                self.log_message(f"处理案例: {params['case_id']} (尝试 {attempt}/{self.max_retries})")

                # 创建模型
                model, client = self.create_single_model(params, attempt)
                if model is None:
                    continue

                # 运行模拟
                if not self.run_simulation_optimized(model, params):
                    client.clear()
                    continue

                # 导出数据
                if not self.export_data_optimized(model, params):
                    client.clear()
                    continue

                # 成功完成
                client.clear()
                return True

            except Exception as e:
                self.log_message(f"案例处理异常: {params['case_id']} - {str(e)}", "ERROR")
                try:
                    client.clear()
                except:
                    pass

        # 所有尝试都失败
        return False

    def process_batch(self, batch_params):
        """处理一批案例"""
        batch_start_time = time.time()
        self.log_message(f"\n{'='*50}")
        self.log_message(f"开始处理新批次 ({len(batch_params)} 个案例)")

        batch_success = 0

        for i, params in enumerate(batch_params):
            case_start_time = time.time()

            # 显示案例信息
            re = params['estimated_reynolds']
            self.log_message(f"案例 {params['case_id']}: v={params['inlet_velocity']}m/s, "
                           f"w={params['channel_width']*1000:.0f}μm, μ={params['fluid_viscosity']}Pa·s, Re={re:.1f}")

            # 处理案例
            if self.process_single_case(params):
                self.completed_cases.append(params['case_id'])
                batch_success += 1
                status = "✅ 成功"
            else:
                self.failed_cases.append(params['case_id'])
                status = "❌ 失败"

            case_time = time.time() - case_start_time
            self.log_message(f"{status} - 用时: {case_time:.1f}秒")

            # 强制垃圾回收
            import gc
            gc.collect()

        batch_time = time.time() - batch_start_time
        self.log_message(f"批次完成: {batch_success}/{len(batch_params)} 成功, 用时: {batch_time/60:.1f}分钟")

        return batch_success

    def run_all_batches(self):
        """运行所有批次"""
        start_time = time.time()
        total_batches = (self.total_cases + self.batch_size - 1) // self.batch_size

        self.log_message(f"\n🚀 开始批量生成数据")
        self.log_message(f"总案例数: {self.total_cases}")
        self.log_message(f"每批大小: {self.batch_size}")
        self.log_message(f"总批次数: {total_batches}")
        self.log_message(f"预计用时: {self.total_cases * 2 / 60:.1f} 分钟")

        # 分批处理
        for batch_idx in range(total_batches):
            start_idx = batch_idx * self.batch_size
            end_idx = min(start_idx + self.batch_size, self.total_cases)
            batch_params = self.parameter_combinations[start_idx:end_idx]

            self.log_message(f"\n📍 进度: 批次 {batch_idx+1}/{total_batches}")

            # 处理当前批次
            self.process_batch(batch_params)

            # 显示总体进度
            progress = (batch_idx + 1) / total_batches * 100
            elapsed = time.time() - start_time
            if batch_idx > 0:
                eta = elapsed / (batch_idx + 1) * (total_batches - batch_idx - 1)
                self.log_message(f"📊 总进度: {progress:.1f}%, 已用时: {elapsed/60:.1f}分钟, 预计剩余: {eta/60:.1f}分钟")

            # 批次间休息 - 让CPU冷却
            if batch_idx < total_batches - 1:
                self.log_message("⏸️ 批次间休息30秒...")
                time.sleep(30)

        # 完成统计
        total_time = time.time() - start_time
        success_rate = len(self.completed_cases) / self.total_cases * 100

        self.log_message(f"\n{'='*60}")
        self.log_message(f"🎉 批量生成完成!")
        self.log_message(f"✅ 成功案例: {len(self.completed_cases)}/{self.total_cases} ({success_rate:.1f}%)")
        self.log_message(f"❌ 失败案例: {len(self.failed_cases)}")
        self.log_message(f"⏰ 总用时: {total_time/60:.1f} 分钟")
        self.log_message(f"⚡ 平均每案例: {total_time/self.total_cases:.1f} 秒")
        self.log_message(f"📁 数据保存位置: {self.output_dir}")
        self.log_message(f"📋 日志文件: {self.log_file}")

        # 保存总结报告
        self.save_final_report(total_time, success_rate)

        return len(self.failed_cases) == 0

    def save_final_report(self, total_time, success_rate):
        """保存最终报告"""
        try:
            report_file = self.output_dir / f"final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            report = {
                "generation_info": {
                    "timestamp": datetime.now().isoformat(),
                    "total_cases": self.total_cases,
                    "successful_cases": len(self.completed_cases),
                    "failed_cases": len(self.failed_cases),
                    "success_rate": success_rate,
                    "total_time_minutes": total_time / 60,
                    "average_time_per_case": total_time / self.total_cases,
                    "batch_size": self.batch_size
                },
                "completed_cases": self.completed_cases,
                "failed_cases": self.failed_cases,
                "parameter_ranges": {
                    "inlet_velocity": [p['inlet_velocity'] for p in self.parameter_combinations],
                    "channel_width": [p['channel_width'] for p in self.parameter_combinations],
                    "fluid_viscosity": [p['fluid_viscosity'] for p in self.parameter_combinations],
                    "reynolds_range": [p['estimated_reynolds'] for p in self.parameter_combinations]
                },
                "system_info": {
                    "cpu_optimization": "AMD R5 5500U mobile optimized",
                    "batch_processing": True,
                    "memory_management": "enabled",
                    "retry_mechanism": f"{self.max_retries} attempts"
                }
            }

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            self.log_message(f"📄 最终报告已保存: {report_file}")

        except Exception as e:
            self.log_message(f"报告保存失败: {str(e)}", "ERROR")


def main():
    """主函数"""
    print("🚀 COMSOL批量数据生成器启动")
    print("="*50)

    try:
        # 创建生成器 - 针对6核移动CPU优化
        generator = BatchDataGenerator(batch_size=5, max_retries=2)

        # 确认执行
        print(f"\n📋 准备生成{generator.total_cases}组数据")
        print(f"⚡ 每批处理5个案例，优化CPU使用")
        print(f"⏱️  预计用时: {generator.total_cases * 2 / 60:.0f} 分钟")

        response = input("\n确认开始批量生成? (y/N): ").lower().strip()
        if response not in ['y', 'yes']:
            print("❌ 用户取消操作")
            return

        # 执行批量生成
        success = generator.run_all_batches()

        if success:
            print("\n🎉 所有数据生成成功! 可以开始PINNs训练了!")
            print("📂 请检查输出目录中的HDF5文件")
        else:
            print(f"\n⚠️  有{len(generator.failed_cases)}个案例失败")
            print("📋 请查看日志文件了解详情")

    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序执行错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()