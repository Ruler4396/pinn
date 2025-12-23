"""
数据充分性评估脚本

评估现有数据是否足以支撑毕设的8个功能和3个创新点
"""

import numpy as np
from pathlib import Path


class DataAdequacyEvaluator:
    """数据充分性评估器"""

    def __init__(self):
        self.current_data = {
            'geometry': ['straight'],  # 仅直流道
            'width_um': [150, 200, 250],
            'length_mm': [10],
            'velocity_cms': [0.15, 0.77, 1.54],
            'density_kgm3': [1000],  # 仅水
            'viscosity_pas': [0.001],  # 仅水
            'reynolds': [0.23, 0.31, 0.39, 1.15, 1.54, 1.92, 2.31, 3.08, 3.84],
            'total_points': 4.7e6,
        }

        # 功能需求映射
        self.function_requirements = {
            'F1_流场可视化': {
                'need': '训练PINN模型',
                'data_required': '至少1组完整流场数据',
                'current_coverage': 0.9,  # 9组数据
                'status': '✅ 充足',
            },
            'F2_流体参数配置': {
                'need': '不同密度、粘度的数据',
                'data_required': '至少3种密度 × 3种粘度 = 9组',
                'current_coverage': 0.1,  # 仅1种密度和粘度
                'status': '❌ 不足',
            },
            'F3_几何建模': {
                'need': '直流道、T型、Y型分岔道数据',
                'data_required': '每种几何至少3组参数',
                'current_coverage': 0.3,  # 仅直流道
                'status': '⚠️ 部分覆盖',
            },
            'F4_任意点查询': {
                'need': 'PINN模型作为连续函数',
                'data_required': '高密度网格数据',
                'current_coverage': 0.8,  # 500K点/组
                'status': '✅ 充足',
            },
            'F5_稀疏数据重建': {
                'need': '基础数据集 + 稀疏采样验证集',
                'data_required': '至少5组基础数据',
                'current_coverage': 0.9,  # 9组基础数据
                'status': '✅ 充足',
            },
            'F6_特征提取': {
                'need': '梯度计算（壁面剪切应力、压力梯度）',
                'data_required': '高密度网格数据',
                'current_coverage': 0.8,  # 500K点/组
                'status': '✅ 充足',
            },
            'F7_物性校准': {
                'need': '不同粘度数据用于校准',
                'data_required': '至少3种粘度',
                'current_coverage': 0.2,  # 仅1种粘度
                'status': '❌ 不足',
            },
            'F8_单条件模拟': {
                'need': '参数化PINN，支持参数变化',
                'data_required': '参数空间采样',
                'current_coverage': 0.4,  # 仅速度和宽度变化
                'status': '⚠️ 部分覆盖',
            },
        }

        # 创新点需求映射
        self.innovation_requirements = {
            'I1_稀疏采样策略': {
                'need': '验证稀疏采样位置（拐角、分岔）',
                'data_required': '含分岔道的几何 + 多采样位置验证',
                'current_coverage': 0.2,  # 无分岔道数据
                'status': '❌ 不足',
            },
            'I2_自适应物理约束': {
                'need': '噪声数据 + 边界条件变化',
                'data_required': '基础数据 + 人工添加噪声',
                'current_coverage': 0.7,  # 可添加噪声
                'status': '⚠️ 需验证',
            },
            'I3_轻量化推理': {
                'need': '参数化PINN + 泛化能力验证',
                'data_required': '参数空间训练 + 插值测试',
                'current_coverage': 0.5,  # 仅2个参数维度
                'status': '⚠️ 需扩展',
            },
        }

    def evaluate_function_coverage(self):
        """评估功能覆盖度"""
        print("=" * 70)
        print("功能覆盖度评估")
        print("=" * 70)

        total_coverage = 0
        status_count = {'✅': 0, '⚠️': 0, '❌': 0}

        for func, req in self.function_requirements.items():
            print(f"\n{func}")
            print(f"  需求: {req['need']}")
            print(f"  数据要求: {req['data_required']}")
            print(f"  当前覆盖: {req['current_coverage']*100:.0f}%")
            print(f"  状态: {req['status']}")

            total_coverage += req['current_coverage']
            status_count[req['status'].split()[0]] += 1

        avg_coverage = total_coverage / len(self.function_requirements)
        print(f"\n{'='*70}")
        print(f"平均覆盖度: {avg_coverage*100:.1f}%")
        print(f"✅ 充足: {status_count['✅']}/8 | ⚠️ 部分覆盖: {status_count['⚠️']}/8 | ❌ 不足: {status_count['❌']}/8")

        return avg_coverage

    def evaluate_innovation_coverage(self):
        """评估创新点覆盖度"""
        print("\n" + "=" * 70)
        print("创新点覆盖度评估")
        print("=" * 70)

        total_coverage = 0
        status_count = {'✅': 0, '⚠️': 0, '❌': 0}

        for innov, req in self.innovation_requirements.items():
            print(f"\n{innov}")
            print(f"  需求: {req['need']}")
            print(f"  数据要求: {req['data_required']}")
            print(f"  当前覆盖: {req['current_coverage']*100:.0f}%")
            print(f"  状态: {req['status']}")

            total_coverage += req['current_coverage']
            status_count[req['status'].split()[0]] += 1

        avg_coverage = total_coverage / len(self.innovation_requirements)
        print(f"\n{'='*70}")
        print(f"平均覆盖度: {avg_coverage*100:.1f}%")
        print(f"✅ 充足: {status_count['✅']}/3 | ⚠️ 部分覆盖: {status_count['⚠️']}/3 | ❌ 不足: {status_count['❌']}/3")

        return avg_coverage

    def generate_data_expansion_plan(self):
        """生成数据扩展建议"""
        print("\n" + "=" * 70)
        print("数据扩展建议")
        print("=" * 70)

        suggestions = [
            {
                'priority': '🔴 高',
                'task': '扩展流体物性参数',
                'current': '1种密度(水) × 1种粘度(水)',
                'required': '3种密度 × 3种粘度 = 9组',
                'impact': '支撑F2(参数配置), F7(物性校准)',
            },
            {
                'priority': '🔴 高',
                'task': '添加分岔道几何',
                'current': '仅直流道',
                'required': 'T型 + Y型分岔道，各3组参数',
                'impact': '支撑F3(几何建模), I1(稀疏采样策略)',
            },
            {
                'priority': '🟡 中',
                'task': '扩展通道长度参数',
                'current': '仅10mm',
                'required': '5mm, 10mm, 15mm三种长度',
                'impact': '支撑F8(单条件模拟), I3(轻量化推理)',
            },
            {
                'priority': '🟡 中',
                'task': '增加速度档位',
                'current': '3档(0.15-1.54 cm/s)',
                'required': '5档覆盖更广Re范围(0.1-3.0)',
                'impact': '提升I3(轻量化推理)泛化能力',
            },
            {
                'priority': '🟢 低',
                'task': '生成噪声数据集',
                'current': '无',
                'required': '基于现有数据添加30-40dB噪声',
                'impact': '支撑I2(自适应物理约束)验证',
            },
        ]

        for s in suggestions:
            print(f"\n{s['priority']} | {s['task']}")
            print(f"  当前: {s['current']}")
            print(f"  需要: {s['required']}")
            print(f"  影响: {s['impact']}")

    def generate_minimum_viable_dataset(self):
        """生成最小可行数据集建议"""
        print("\n" + "=" * 70)
        print("最小可行数据集 (MVP) - 毕设最低要求")
        print("=" * 70)

        mvp_plan = [
            {'几何': '直流道', '参数': 'v×W组合', '数量': '9组', '状态': '✅ 已完成'},
            {'几何': 'T型分岔', '参数': '3组', '数量': '3组', '状态': '❌ 需生成'},
            {'几何': 'Y型分岔', '参数': '3组', '数量': '3组', '状态': '❌ 需生成'},
            {'几何': '不同粘度', '参数': 'μ=0.005', '数量': '3组', '状态': '❌ 需生成'},
        ]

        print(f"\n{'几何类型':<12} {'参数配置':<15} {'数量':<8} {'状态':<12}")
        print("-" * 50)
        total = 0
        for item in mvp_plan:
            print(f"{item['几何']:<12} {item['参数']:<15} {item['数量']:<8} {item['状态']:<12}")
            if '组' in item['数量']:
                total += int(item['数量'].replace('组', ''))

        print("-" * 50)
        print(f"{'总计':<12} {'':<15} {f'{total}组':<8} {'当前: 9组 ({9/total*100:.0f}%)'}")

        print(f"\n建议数据扩展:")
        print(f"  - 优先级1: T型/Y型分岔道各3组 (支撑创新点1)")
        print(f"  - 优先级2: 不同粘度3组 (支撑功能2、7)")
        print(f"  - MVP总计: {9 + 6 + 3} = 18组 (~9.5M数据点)")

    def run_full_evaluation(self):
        """运行完整评估"""
        print("\n" + "=" * 70)
        print("数据充分性评估报告")
        print("=" * 70)

        print("\n当前数据概况:")
        print(f"  - 几何类型: {self.current_data['geometry']}")
        print(f"  - 通道宽度: {self.current_data['width_um']} μm")
        print(f"  - 通道长度: {self.current_data['length_mm']} mm")
        print(f"  - 入口速度: {self.current_data['velocity_cms']} cm/s")
        print(f"  - 流体密度: {self.current_data['density_kgm3']} kg/m³")
        print(f"  - 动力粘度: {self.current_data['viscosity_pas']} Pa·s")
        print(f"  - Reynolds数范围: {min(self.current_data['reynolds']):.2f} - {max(self.current_data['reynolds']):.2f}")
        print(f"  - 总数据量: {self.current_data['total_points']:.1e} 数据点")

        # 评估覆盖度
        func_coverage = self.evaluate_function_coverage()
        innov_coverage = self.evaluate_innovation_coverage()

        # 生成建议
        self.generate_data_expansion_plan()
        self.generate_minimum_viable_dataset()

        # 总结
        print("\n" + "=" * 70)
        print("评估总结")
        print("=" * 70)
        print(f"\n功能覆盖度: {func_coverage*100:.1f}%")
        print(f"创新点覆盖度: {innov_coverage*100:.1f}%")
        print(f"\n总体评估:")

        if func_coverage >= 0.7 and innov_coverage >= 0.6:
            print("  ✅ 数据基本充足，可以开始开发")
            print("  建议: 优先处理分岔道几何和粘度变化")
        elif func_coverage >= 0.5:
            print("  ⚠️ 数据部分充足，可以开始基础开发")
            print("  警告: 部分功能和创新点需要扩展数据")
        else:
            print("  ❌ 数据不足，建议先扩展数据集")

        print("\n建议优先级:")
        print("  1. 🔴 高: 添加T型/Y型分岔道几何数据 (6组)")
        print("  2. 🔴 高: 添加不同粘度数据 (3组)")
        print("  3. 🟡 中: 扩展通道长度参数 (可选)")
        print("  4. 🟢 低: 生成噪声验证数据 (可人工生成)")


def main():
    """主函数"""
    evaluator = DataAdequacyEvaluator()
    evaluator.run_full_evaluation()


if __name__ == "__main__":
    main()
