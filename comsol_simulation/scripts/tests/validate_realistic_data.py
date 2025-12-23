"""
真实数据集验证和分析工具

用于检查生成的真实数据集的质量和有效性
提供多种验证指标和可视化方法

作者: PINNs项目组
创建时间: 2025-11-19
"""

import os
import sys
import numpy as np
import h5py
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple
# import seaborn as sns  # 可选，如果需要更高级的可视化

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class RealisticDataValidator:
    """真实数据集验证器"""

    def __init__(self, data_dir: str = None):
        """
        初始化验证器

        Args:
            data_dir: 数据目录路径
        """
        if data_dir is None:
            data_dir = project_root / "comsol_simulation" / "data"

        self.data_dir = Path(data_dir)

    def load_realistic_dataset(self, filename: str) -> Dict:
        """
        加载真实数据集

        Args:
            filename: 数据集文件名

        Returns:
            dict: 数据集字典
        """
        file_path = self.data_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {file_path}")

        print(f"📁 加载真实数据集: {filename}")

        with h5py.File(file_path, 'r') as h5file:
            data = {}

            # 加载基本信息
            info_group = h5file.get('info')
            if info_group:
                data['info'] = dict(info_group.attrs)

            # 加载网格数据
            mesh_group = h5file.get('mesh')
            if mesh_group:
                data['mesh'] = {
                    'x': mesh_group['x'][:],
                    'y': mesh_group['y'][:],
                    'num_nodes': mesh_group.attrs.get('num_nodes', len(mesh_group['x']))  # 添加默认值
                }

            # 加载求解数据（包含噪声）
            solution_group = h5file.get('solution')
            if solution_group:
                data['solution'] = {
                    'u': solution_group['u'][:],
                    'v': solution_group['v'][:],
                    'p': solution_group['p'][:],
                    'u_clean': solution_group['u_clean'][:],
                    'v_clean': solution_group['v_clean'][:],
                    'p_clean': solution_group['p_clean'][:],
                    'missing_mask': solution_group['missing_mask'][:]
                }

            # 加载采样信息
            sampling_group = h5file.get('sampling')
            if sampling_group:
                data['sampling'] = dict(sampling_group.attrs)

            # 加载噪声分析
            noise_group = h5file.get('noise_analysis')
            if noise_group:
                data['noise_analysis'] = {}
                for field in ['u', 'v', 'p']:
                    if field in noise_group:
                        data['noise_analysis'][field] = dict(noise_group[field].attrs)

        print(f"✅ 数据集加载完成")
        return data

    def validate_data_integrity(self, data: Dict) -> Dict:
        """
        验证数据完整性

        Args:
            data: 数据集字典

        Returns:
            dict: 验证结果
        """
        print("🔍 验证数据完整性...")

        validation_results = {}

        # 1. 检查数据形状
        mesh_points = len(data['mesh']['x'])
        solution_points = len(data['solution']['u'])

        validation_results['shape_consistency'] = {
            'mesh_points': mesh_points,
            'solution_points': solution_points,
            'consistent': mesh_points == solution_points
        }

        # 2. 检查缺失数据
        missing_mask = data['solution']['missing_mask']
        missing_count = np.sum(missing_mask)
        missing_ratio = missing_count / len(missing_mask)

        validation_results['missing_data'] = {
            'missing_count': int(missing_count),
            'missing_ratio': float(missing_ratio),
            'total_points': len(missing_mask)
        }

        # 3. 检查数据范围合理性
        u_clean = data['solution']['u_clean']
        v_clean = data['solution']['v_clean']
        p_clean = data['solution']['p_clean']

        # 检查速度范围（微流控通常0-0.1 m/s）
        speed_clean = np.sqrt(u_clean**2 + v_clean**2)
        validation_results['velocity_range'] = {
            'u_min': float(np.min(u_clean)),
            'u_max': float(np.max(u_clean)),
            'v_min': float(np.min(v_clean)),
            'v_max': float(np.max(v_clean)),
            'speed_max': float(np.max(speed_clean)),
            'reasonable': np.max(speed_clean) < 0.1  # 10cm/s上限
        }

        # 4. 检查压力范围（微流控通常-10kPa到10kPa）
        validation_results['pressure_range'] = {
            'p_min': float(np.min(p_clean)),
            'p_max': float(np.max(p_clean)),
            'range': float(np.max(p_clean) - np.min(p_clean)),
            'reasonable': abs(np.max(p_clean) - np.min(p_clean)) < 20000  # 20kPa上限
        }

        # 5. 检查噪声水平
        if 'noise_analysis' in data:
            noise_analysis = data['noise_analysis']
            validation_results['noise_levels'] = {}
            for field in ['u', 'v', 'p']:
                if field in noise_analysis:
                    validation_results['noise_levels'][field] = {
                        'snr_db': noise_analysis[field].get('snr_db', 0),
                        'noise_std': noise_analysis[field].get('noise_std', 0)
                    }

        # 6. 检查采样信息
        if 'sampling' in data:
            sampling = data['sampling']
            validation_results['sampling_info'] = {
                'strategy': sampling.get('strategy', 'unknown'),
                'original_points': sampling.get('original_points', 0),
                'sampled_points': sampling.get('sampled_points', 0),
                'sampling_ratio': sampling.get('sampling_ratio', 0)
            }
        else:
            # 如果没有采样信息，提供默认值
            validation_results['sampling_info'] = {
                'strategy': 'unknown',
                'original_points': mesh_points,
                'sampled_points': mesh_points,
                'sampling_ratio': 1.0
            }

        print("✅ 数据完整性验证完成")
        return validation_results

    def generate_validation_report(self, filename: str) -> Dict:
        """
        生成完整的验证报告

        Args:
            filename: 数据集文件名

        Returns:
            dict: 完整的验证报告
        """
        print(f"📋 生成验证报告: {filename}")

        # 加载数据
        data = self.load_realistic_dataset(filename)

        # 验证数据完整性
        validation_results = self.validate_data_integrity(data)

        # 生成报告
        report = {
            'dataset_info': {
                'filename': filename,
                'file_size_mb': round(os.path.getsize(self.data_dir / filename) / (1024*1024), 2),
                'creation_time': data['info'].get('creation_time', 'unknown'),
                'data_type': data['info'].get('data_type', 'unknown')
            },
            'validation_results': validation_results
        }

        return report, data

    def visualize_data_validation(self, data: Dict, validation_results: Dict,
                                save_path: str = None):
        """
        可视化数据验证结果

        Args:
            data: 数据集字典
            validation_results: 验证结果
            save_path: 保存路径
        """
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f'真实数据集验证分析 - {data["info"].get("data_type", "Unknown")}',
                    fontsize=16)

        # 提取数据
        x = data['mesh']['x']
        y = data['mesh']['y']
        u_clean = data['solution']['u_clean']
        v_clean = data['solution']['v_clean']
        p_clean = data['solution']['p_clean']
        u_noisy = data['solution']['u']
        v_noisy = data['solution']['v']
        p_noisy = data['solution']['p']
        missing_mask = data['solution']['missing_mask']

        # 1. 采样点分布
        ax1 = axes[0, 0]
        scatter = ax1.scatter(x[~missing_mask], y[~missing_mask],
                            c='blue', s=10, alpha=0.6, label='有效数据点')
        if np.any(missing_mask):
            ax1.scatter(x[missing_mask], y[missing_mask],
                       c='red', s=10, alpha=0.6, label='缺失数据点')
        ax1.set_xlabel('X (mm)')
        ax1.set_ylabel('Y (mm)')
        ax1.set_title(f'采样点分布 ({validation_results["sampling_info"]["strategy"]})')
        ax1.legend()
        ax1.set_aspect('equal')

        # 2. 速度场对比（干净 vs 噪声）
        ax2 = axes[0, 1]
        speed_clean = np.sqrt(u_clean**2 + v_clean**2)
        speed_noisy = np.sqrt(u_noisy**2 + v_noisy**2)

        # 只显示有效数据点
        valid_mask = ~missing_mask
        scatter = ax2.scatter(speed_clean[valid_mask], speed_noisy[valid_mask],
                            alpha=0.6, s=10)

        # 添加y=x参考线
        max_speed = max(np.max(speed_clean), np.max(speed_noisy))
        ax2.plot([0, max_speed], [0, max_speed], 'r--', alpha=0.8, label='y=x (完美匹配)')
        ax2.set_xlabel('干净速度幅值 (m/s)')
        ax2.set_ylabel('噪声速度幅值 (m/s)')
        ax2.set_title('速度场噪声影响')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. 压力场对比（干净 vs 噪声）
        ax3 = axes[0, 2]
        valid_mask = ~missing_mask
        scatter = ax3.scatter(p_clean[valid_mask], p_noisy[valid_mask],
                            alpha=0.6, s=10, c='orange')

        # 添加y=x参考线
        min_p, max_p = min(np.min(p_clean), np.min(p_noisy)), max(np.max(p_clean), np.max(p_noisy))
        ax3.plot([min_p, max_p], [min_p, max_p], 'r--', alpha=0.8, label='y=x (完美匹配)')
        ax3.set_xlabel('干净压力 (Pa)')
        ax3.set_ylabel('噪声压力 (Pa)')
        ax3.set_title('压力场噪声影响')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 4. 噪声统计分析
        ax4 = axes[1, 0]
        if 'noise_levels' in validation_results:
            fields = list(validation_results['noise_levels'].keys())
            snr_values = [validation_results['noise_levels'][field]['snr_db'] for field in fields]

            bars = ax4.bar(fields, snr_values, alpha=0.7,
                          color=['skyblue', 'lightgreen', 'salmon'])
            ax4.set_ylabel('信噪比 (dB)')
            ax4.set_title('各物理量信噪比')
            ax4.grid(True, alpha=0.3)

            # 添加数值标签
            for bar, snr in zip(bars, snr_values):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{snr:.1f} dB', ha='center', va='bottom')

        # 5. 数据质量指标
        ax5 = axes[1, 1]
        quality_metrics = [
            ('数据完整性', f"{(1-validation_results['missing_data']['missing_ratio'])*100:.1f}%"),
            ('速度合理性', '✓' if validation_results['velocity_range']['reasonable'] else '✗'),
            ('压力合理性', '✓' if validation_results['pressure_range']['reasonable'] else '✗'),
            ('形状一致性', '✓' if validation_results['shape_consistency']['consistent'] else '✗')
        ]

        y_pos = np.arange(len(quality_metrics))
        colors = ['green' if '✓' in metric[1] else 'red' for metric in quality_metrics]

        bars = ax5.barh(y_pos, [1]*len(quality_metrics), color=colors, alpha=0.7)
        ax5.set_yticks(y_pos)
        ax5.set_yticklabels([f"{metric[0]}: {metric[1]}" for metric in quality_metrics])
        ax5.set_xlim(0, 1)
        ax5.set_title('数据质量检查')
        ax5.set_xticks([])

        # 6. 采样策略效果
        ax6 = axes[1, 2]
        sampling_info = validation_results['sampling_info']

        # 创建饼图显示采样比例
        sizes = [sampling_info['sampled_points'],
                sampling_info['original_points'] - sampling_info['sampled_points']]
        labels = ['采样点', '未采样点']
        colors = ['lightblue', 'lightgray']

        wedges, texts, autotexts = ax6.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                          startangle=90)
        ax6.set_title(f'采样策略: {sampling_info["strategy"]}\n'
                     f'采样率: {sampling_info["sampling_ratio"]*100:.1f}%')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"📈 验证可视化已保存: {save_path}")
        else:
            plt.show()

    def compare_datasets(self, filenames: List[str]) -> Dict:
        """
        比较多个数据集

        Args:
            filenames: 数据集文件名列表

        Returns:
            dict: 比较结果
        """
        print("📊 比较多个数据集...")

        comparison_results = {}

        for filename in filenames:
            report, data = self.generate_validation_report(filename)
            comparison_results[filename] = {
                'report': report,
                'key_metrics': {
                    'sampling_strategy': report['validation_results']['sampling_info']['strategy'],
                    'sampling_ratio': report['validation_results']['sampling_info']['sampling_ratio'],
                    'missing_ratio': report['validation_results']['missing_data']['missing_ratio'],
                    'max_speed': report['validation_results']['velocity_range']['speed_max'],
                    'pressure_range': report['validation_results']['pressure_range']['range']
                }
            }

        print("✅ 数据集比较完成")
        return comparison_results


def main():
    """主函数 - 演示数据验证流程"""
    print("🌟 真实数据集验证和分析工具")

    # 创建验证器
    validator = RealisticDataValidator()

    # 查找所有真实数据集文件
    realistic_files = list(validator.data_dir.glob("realistic_data_*.h5"))

    if not realistic_files:
        print("❌ 未找到真实数据集文件")
        return

    print(f"📁 找到 {len(realistic_files)} 个真实数据集文件")

    # 为每个数据集生成验证报告
    all_reports = {}

    for file_path in realistic_files:
        filename = file_path.name
        print(f"\n{'='*60}")
        print(f"📋 验证数据集: {filename}")
        print(f"{'='*60}")

        try:
            # 生成验证报告
            report, data = validator.generate_validation_report(filename)
            all_reports[filename] = report

            # 打印关键信息
            validation = report['validation_results']

            print(f"\n📊 数据集信息:")
            print(f"   文件大小: {report['dataset_info']['file_size_mb']} MB")
            print(f"   采样策略: {validation['sampling_info']['strategy']}")
            print(f"   采样率: {validation['sampling_info']['sampling_ratio']*100:.1f}%")
            print(f"   缺失数据: {validation['missing_data']['missing_ratio']*100:.1f}%")

            print(f"\n🔍 物理量范围:")
            print(f"   最大速度: {validation['velocity_range']['speed_max']:.6f} m/s")
            print(f"   压力范围: {validation['pressure_range']['range']:.1f} Pa")

            if 'noise_levels' in validation:
                print(f"\n📈 噪声水平:")
                for field, noise_info in validation['noise_levels'].items():
                    print(f"   {field}: SNR = {noise_info['snr_db']:.1f} dB")

            print(f"\n✅ 数据质量检查:")
            print(f"   数据完整性: {(1-validation['missing_data']['missing_ratio'])*100:.1f}%")
            print(f"   速度合理性: {'✓' if validation['velocity_range']['reasonable'] else '✗'}")
            print(f"   压力合理性: {'✓' if validation['pressure_range']['reasonable'] else '✗'}")
            print(f"   形状一致性: {'✓' if validation['shape_consistency']['consistent'] else '✗'}")

            # 生成验证可视化
            vis_path = validator.data_dir / f"validation_report_{filename.replace('.h5', '.png')}"
            validator.visualize_data_validation(data, validation, str(vis_path))

        except Exception as e:
            print(f"❌ 验证过程中出现错误: {e}")
            import traceback
            traceback.print_exc()

    # 生成数据集比较总结
    print(f"\n{'='*60}")
    print("📊 数据集比较总结")
    print(f"{'='*60}")

    if len(all_reports) > 1:
        filenames = list(all_reports.keys())
        comparison = validator.compare_datasets(filenames)

        print(f"\n📋 关键指标对比:")
        print(f"{'文件名':<40} {'策略':<15} {'采样率':<10} {'缺失率':<10} {'最大速度':<12}")
        print("-" * 90)

        for filename, metrics in comparison.items():
            key_metrics = metrics['key_metrics']
            print(f"{filename:<40} "
                  f"{key_metrics['sampling_strategy']:<15} "
                  f"{key_metrics['sampling_ratio']*100:>8.1f}% "
                  f"{key_metrics['missing_ratio']*100:>8.1f}% "
                  f"{key_metrics['max_speed']:>10.6f}")

    print(f"\n✅ 所有数据集验证完成！")
    print(f"📂 验证报告保存在: {validator.data_dir}")


if __name__ == "__main__":
    main()