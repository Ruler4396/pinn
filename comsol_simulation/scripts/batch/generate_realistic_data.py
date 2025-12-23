"""
生成带有真实世界因素的训练数据

包括：
1. 测量噪声
2. 稀疏采样
3. 数据缺失
4. 传感器误差
5. 系统性偏差

作者: PINNs项目组
创建时间: 2025-11-19
"""

import os
import sys
import numpy as np
import h5py
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    import mph
    print("✅ mph模块导入成功")
except ImportError:
    print("⚠️ mph模块未找到，将使用示例数据")


class RealisticDataGenerator:
    """生成带有真实世界因素的训练数据"""

    def __init__(self, output_dir=None):
        """
        初始化数据生成器

        Args:
            output_dir: 输出目录，默认为 comsol_simulation/data
        """
        if output_dir is None:
            output_dir = project_root / "comsol_simulation" / "data"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 噪声参数配置
        self.noise_configs = {
            'high_precision': {
                'velocity_std': 0.0005,      # 高精度速度噪声
                'pressure_std': 5,            # 高精度压力噪声
                'position_std': 0.0005,      # 高精度位置噪声
                'outlier_rate': 0.005,       # 0.5% 异常值
                'missing_rate': 0.02          # 2% 数据缺失
            },
            'industrial': {
                'velocity_std': 0.002,       # 工业级速度噪声
                'pressure_std': 20,           # 工业级压力噪声
                'position_std': 0.002,       # 工业级位置噪声
                'outlier_rate': 0.02,        # 2% 异常值
                'missing_rate': 0.05          # 5% 数据缺失
            },
            'low_cost': {
                'velocity_std': 0.005,       # 低成本速度噪声
                'pressure_std': 50,           # 低成本压力噪声
                'position_std': 0.005,       # 低成本位置噪声
                'outlier_rate': 0.05,        # 5% 异常值
                'missing_rate': 0.10          # 10% 数据缺失
            }
        }

        # 稀疏采样策略
        self.sampling_strategies = {
            'uniform': {
                'density': 0.2,              # 20% 采样率
                'method': 'random_uniform'    # 随机均匀采样
            },
            'boundary_focused': {
                'density': 0.15,             # 15% 总采样率
                'boundary_density': 0.3,     # 边界30%采样率
                'center_density': 0.05,      # 中心5%采样率
                'method': 'boundary_focus'   # 边界聚焦采样
            },
            'feature_based': {
                'density': 0.12,
                'corner_density': 0.4,       # 角落40%采样率
                'inlet_outlet_density': 0.3, # 入口出口30%
                'method': 'feature_based'    # 基于特征的采样
            }
        }

    def load_clean_data(self, clean_data_path=None):
        """
        加载干净的COMSOL数据

        Args:
            clean_data_path: 干净数据文件路径

        Returns:
            dict: 清净数据
        """
        if clean_data_path is None:
            # 使用默认的示例数据
            clean_data_path = self.output_dir / "microchannel_data_20251119_141929.h5"

        if not clean_data_path.exists():
            print(f"❌ 未找到干净数据文件: {clean_data_path}")
            # 生成示例数据
            print("🔧 生成示例数据...")
            from export_simulation_data import SimulationDataExporter
            exporter = SimulationDataExporter()
            return exporter.export_complete_data(use_sample_data=True)

        try:
            with h5py.File(clean_data_path, 'r') as h5file:
                data = {
                    'mesh': {
                        'x': h5file['mesh']['x'][:],
                        'y': h5file['mesh']['y'][:]
                    },
                    'solution': {
                        'u': h5file['solution']['u'][:],
                        'v': h5file['solution']['v'][:],
                        'p': h5file['solution']['p'][:]
                    },
                    'info': dict(h5file['info'].attrs)
                }

            print(f"✅ 成功加载干净数据: {len(data['mesh']['x'])} 个数据点")
            return data

        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            return None

    def add_measurement_noise(self, data, noise_config='industrial'):
        """
        添加测量噪声

        Args:
            data: 干净数据字典
            noise_config: 噪声配置名称

        Returns:
            dict: 带噪声的数据
        """
        config = self.noise_configs[noise_config]

        noisy_data = data.copy()

        # 添加高斯噪声到速度场
        u_noise = np.random.normal(0, config['velocity_std'], len(data['solution']['u']))
        v_noise = np.random.normal(0, config['velocity_std'], len(data['solution']['v']))

        noisy_data['solution']['u_noisy'] = data['solution']['u'] + u_noise
        noisy_data['solution']['v_noisy'] = data['solution']['v'] + v_noise

        # 添加高斯噪声到压力场
        p_noise = np.random.normal(0, config['pressure_std'], len(data['solution']['p']))
        noisy_data['solution']['p_noisy'] = data['solution']['p'] + p_noise

        # 添加位置噪声（传感器定位误差）
        x_noise = np.random.normal(0, config['position_std'], len(data['mesh']['x']))
        y_noise = np.random.normal(0, config['position_std'], len(data['mesh']['y']))

        noisy_data['mesh']['x_noisy'] = data['mesh']['x'] + x_noise
        noisy_data['mesh']['y_noisy'] = data['mesh']['y'] + y_noise

        # 添加异常值（传感器故障）
        if config['outlier_rate'] > 0:
            num_points = len(data['solution']['u'])
            outlier_mask = np.random.random(num_points) < config['outlier_rate']

            # 速度异常值（大幅偏离）
            u_outlier = np.random.uniform(-0.01, 0.01, np.sum(outlier_mask))
            v_outlier = np.random.uniform(-0.01, 0.01, np.sum(outlier_mask))

            noisy_data['solution']['u_noisy'][outlier_mask] += u_outlier
            noisy_data['solution']['v_noisy'][outlier_mask] += v_outlier

            # 压力异常值
            p_outlier = np.random.uniform(-100, 100, np.sum(outlier_mask))
            noisy_data['solution']['p_noisy'][outlier_mask] += p_outlier

            print(f"⚠️ 添加了 {np.sum(outlier_mask)} 个异常值 ({config['outlier_rate']*100:.1f}%)")

        # 添加数据缺失（传感器故障）
        if config['missing_rate'] > 0:
            num_points = len(data['solution']['u'])
            missing_mask = np.random.random(num_points) < config['missing_rate']

            noisy_data['missing_mask'] = missing_mask
            print(f"⚠️ 添加了 {np.sum(missing_mask)} 个缺失数据点 ({config['missing_rate']*100:.1f}%)")

        # 记录噪声参数
        noisy_data['noise_config'] = config
        noisy_data['noise_type'] = noise_config

        print(f"✅ 已添加 {noise_config} 级别的测量噪声")
        return noisy_data

    def apply_sparse_sampling(self, data, sampling_strategy='boundary_focused'):
        """
        应用稀疏采样策略

        Args:
            data: 完整数据字典
            sampling_strategy: 采样策略名称

        Returns:
            dict: 稀疏采样的数据
        """
        strategy = self.sampling_strategies[sampling_strategy]
        num_points = len(data['mesh']['x'])

        if strategy['method'] == 'random_uniform':
            # 随机均匀采样
            num_sample = int(num_points * strategy['density'])
            sample_indices = np.random.choice(num_points, num_sample, replace=False)

        elif strategy['method'] == 'boundary_focus':
            # 边界聚焦采样
            x_min, x_max = np.min(data['mesh']['x']), np.max(data['mesh']['x'])
            y_min, y_max = np.min(data['mesh']['y']), np.max(data['mesh']['y'])

            # 识别边界点（距离边界 < 10% 范围）
            boundary_threshold_x = (x_max - x_min) * 0.1
            boundary_threshold_y = (y_max - y_min) * 0.1

            boundary_mask = (
                (np.abs(data['mesh']['x'] - x_min) < boundary_threshold_x) |
                (np.abs(data['mesh']['x'] - x_max) < boundary_threshold_x) |
                (np.abs(data['mesh']['y'] - y_min) < boundary_threshold_y) |
                (np.abs(data['mesh']['y'] - y_max) < boundary_threshold_y)
            )

            boundary_indices = np.where(boundary_mask)[0]
            center_indices = np.where(~boundary_mask)[0]

            # 按密度采样
            num_boundary = int(len(boundary_indices) * strategy['boundary_density'])
            num_center = int(len(center_indices) * strategy['center_density'])

            sampled_boundary = np.random.choice(boundary_indices,
                                             min(num_boundary, len(boundary_indices)),
                                             replace=False)
            sampled_center = np.random.choice(center_indices,
                                           min(num_center, len(center_indices)),
                                           replace=False)

            sample_indices = np.concatenate([sampled_boundary, sampled_center])

        elif strategy['method'] == 'feature_based':
            # 基于特征的采样（入口、出口、角落）
            x_min, x_max = np.min(data['mesh']['x']), np.max(data['mesh']['x'])
            y_min, y_max = np.min(data['mesh']['y']), np.max(data['mesh']['y'])

            # 定义特征区域
            inlet_region = data['mesh']['x'] < (x_min + (x_max - x_min) * 0.1)
            outlet_region = data['mesh']['x'] > (x_max - (x_max - x_min) * 0.1)

            corner_region = (
                ((data['mesh']['x'] < (x_min + (x_max - x_min) * 0.1)) |
                 (data['mesh']['x'] > (x_max - (x_max - x_min) * 0.1))) &
                ((data['mesh']['y'] < (y_min + (y_max - y_min) * 0.1)) |
                 (data['mesh']['y'] > (y_max - (y_max - y_min) * 0.1)))
            )

            inlet_indices = np.where(inlet_region & ~corner_region)[0]
            outlet_indices = np.where(outlet_region & ~corner_region)[0]
            corner_indices = np.where(corner_region)[0]
            remaining_indices = np.where(~(inlet_region | outlet_region | corner_region))[0]

            # 按密度采样
            num_corner = int(len(corner_indices) * strategy['corner_density'])
            num_inlet_outlet = int((len(inlet_indices) + len(outlet_indices)) *
                                  strategy['inlet_outlet_density'])

            sampled_corner = np.random.choice(corner_indices,
                                           min(num_corner, len(corner_indices)),
                                           replace=False)
            sampled_inlet_outlet = np.random.choice(
                np.concatenate([inlet_indices, outlet_indices]),
                min(num_inlet_outlet, len(inlet_indices) + len(outlet_indices)),
                replace=False
            )

            sample_indices = np.concatenate([sampled_corner, sampled_inlet_outlet])

        # 创建稀疏数据
        sparse_data = {}
        for key in ['mesh', 'solution']:
            sparse_data[key] = {}
            for subkey in data[key]:
                if hasattr(data[key][subkey], '__len__'):
                    sparse_data[key][subkey] = data[key][subkey][sample_indices]
                else:
                    sparse_data[key][subkey] = data[key][subkey]

        # 保留其他信息
        for key in data:
            if key not in ['mesh', 'solution']:
                sparse_data[key] = data[key]

        # 记录采样信息
        sparse_data['sampling_info'] = {
            'strategy': sampling_strategy,
            'original_points': num_points,
            'sampled_points': len(sample_indices),
            'sampling_ratio': len(sample_indices) / num_points,
            'sample_indices': sample_indices
        }

        print(f"✅ 应用 {sampling_strategy} 采样策略: {len(sample_indices)}/{num_points} "
              f"({len(sample_indices)/num_points*100:.1f}%)")

        return sparse_data

    def generate_realistic_dataset(self, clean_data_path=None,
                                 noise_configs=['high_precision', 'industrial', 'low_cost'],
                                 sampling_strategies=['uniform', 'boundary_focused', 'feature_based']):
        """
        生成完整的多场景真实数据集

        Args:
            clean_data_path: 干净数据路径
            noise_configs: 噪声配置列表
            sampling_strategies: 采样策略列表

        Returns:
            list: 生成的数据集文件路径列表
        """
        print("🚀 开始生成真实数据集...")

        # 加载干净数据
        print("\n📁 加载干净数据...")
        clean_data = self.load_clean_data(clean_data_path)

        if clean_data is None:
            print("❌ 无法加载干净数据，终止生成")
            return []

        generated_files = []

        # 生成不同噪声级别和采样策略的组合
        for noise_config in noise_configs:
            for sampling_strategy in sampling_strategies:
                print(f"\n🔧 生成场景: {noise_config} 噪声 + {sampling_strategy} 采样")

                # 添加噪声
                noisy_data = self.add_measurement_noise(clean_data, noise_config)

                # 应用稀疏采样
                sparse_data = self.apply_sparse_sampling(noisy_data, sampling_strategy)

                # 保存数据
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"realistic_data_{noise_config}_{sampling_strategy}_{timestamp}.h5"
                output_path = self.output_dir / filename

                self.save_realistic_data(sparse_data, output_path)
                generated_files.append(output_path)

                print(f"✅ 已保存: {filename}")

        print(f"\n🎉 数据集生成完成! 共生成 {len(generated_files)} 个文件")
        return generated_files

    def save_realistic_data(self, data, output_path):
        """
        保存真实数据到HDF5文件

        Args:
            data: 数据字典
            output_path: 输出文件路径
        """
        try:
            with h5py.File(output_path, 'w') as h5file:
                # 保存基本信息
                info_group = h5file.create_group('info')
                for key, value in data['info'].items():
                    info_group.attrs[key] = value

                # 添加数据集特征信息
                info_group.attrs['creation_time'] = datetime.now().isoformat()
                info_group.attrs['data_type'] = 'realistic_simulation_data'
                info_group.attrs['noise_config'] = data.get('noise_type', 'unknown')
                info_group.attrs['sampling_strategy'] = data.get('sampling_info', {}).get('strategy', 'unknown')

                # 保存网格数据
                mesh_group = h5file.create_group('mesh')
                mesh_group.create_dataset('x', data=data['mesh']['x_noisy'] if 'x_noisy' in data['mesh'] else data['mesh']['x'])
                mesh_group.create_dataset('y', data=data['mesh']['y_noisy'] if 'y_noisy' in data['mesh'] else data['mesh']['y'])

                if 'sampling_info' in data:
                    mesh_group.attrs['sampling_info'] = str(data['sampling_info'])

                # 保存求解数据
                solution_group = h5file.create_group('solution')

                # 保存带噪声的数据作为主要数据
                solution_group.create_dataset('u', data=data['solution']['u_noisy'] if 'u_noisy' in data['solution'] else data['solution']['u'])
                solution_group.create_dataset('v', data=data['solution']['v_noisy'] if 'v_noisy' in data['solution'] else data['solution']['v'])
                solution_group.create_dataset('p', data=data['solution']['p_noisy'] if 'p_noisy' in data['solution'] else data['solution']['p'])

                # 如果有干净数据，也保存作为参考
                if 'u_noisy' in data['solution']:
                    solution_group.create_dataset('u_clean', data=data['solution']['u'])
                    solution_group.create_dataset('v_clean', data=data['solution']['v'])
                    solution_group.create_dataset('p_clean', data=data['solution']['p'])

                # 保存缺失数据掩码
                if 'missing_mask' in data:
                    solution_group.create_dataset('missing_mask', data=data['missing_mask'])

                # 添加数据单位信息
                solution_group.attrs['u_unit'] = 'm/s'
                solution_group.attrs['v_unit'] = 'm/s'
                solution_group.attrs['p_unit'] = 'Pa'
                solution_group.attrs['x_unit'] = 'mm'
                solution_group.attrs['y_unit'] = 'mm'

                # 保存统计信息
                stats_group = h5file.create_group('statistics')

                for field in ['u', 'v', 'p']:
                    field_data = data['solution'][f'{field}_noisy' if f'{field}_noisy' in data['solution'] else field]
                    field_stats = stats_group.create_group(field)
                    field_stats.attrs['min'] = float(np.min(field_data))
                    field_stats.attrs['max'] = float(np.max(field_data))
                    field_stats.attrs['mean'] = float(np.mean(field_data))
                    field_stats.attrs['std'] = float(np.std(field_data))
                    field_stats.attrs['count'] = int(len(field_data))

                # 如果有干净数据，计算噪声统计
                if 'u_noisy' in data['solution']:
                    noise_stats = stats_group.create_group('noise_analysis')
                    for field in ['u', 'v', 'p']:
                        clean_field = data['solution'][field]
                        noisy_field = data['solution'][f'{field}_noisy']
                        noise = noisy_field - clean_field

                        noise_field_stats = noise_stats.create_group(field)
                        noise_field_stats.attrs['noise_mean'] = float(np.mean(noise))
                        noise_field_stats.attrs['noise_std'] = float(np.std(noise))
                        noise_field_stats.attrs['noise_rms'] = float(np.sqrt(np.mean(noise**2)))
                        noise_field_stats.attrs['snr_db'] = float(10 * np.log10(np.var(clean_field) / np.var(noise)))

            print(f"✅ 数据已保存到: {output_path}")

        except Exception as e:
            print(f"❌ 数据保存失败: {e}")
            raise

    def visualize_realistic_data(self, data_path, save_plots=True):
        """
        可视化真实数据

        Args:
            data_path: 数据文件路径
            save_plots: 是否保存图表
        """
        try:
            with h5py.File(data_path, 'r') as h5file:
                x = h5file['mesh']['x'][:]
                y = h5file['mesh']['y'][:]
                u = h5file['solution']['u'][:]
                v = h5file['solution']['v'][:]
                p = h5file['solution']['p'][:]

                # 获取元数据
                noise_config = h5file['info'].attrs.get('noise_config', 'unknown')
                sampling_strategy = h5file['info'].attrs.get('sampling_strategy', 'unknown')

            # 创建图表
            fig, axes = plt.subplots(2, 2, figsize=(12, 8))
            fig.suptitle(f'真实数据可视化 - {noise_config}噪声 + {sampling_strategy}采样',
                        fontsize=14)

            # 速度幅值
            speed = np.sqrt(u**2 + v**2)
            scatter1 = axes[0, 0].scatter(x, y, c=speed, s=1, cmap='viridis')
            axes[0, 0].set_title('速度幅值 (m/s)')
            axes[0, 0].set_xlabel('X (mm)')
            axes[0, 0].set_ylabel('Y (mm)')
            axes[0, 0].set_aspect('equal')
            plt.colorbar(scatter1, ax=axes[0, 0])

            # X方向速度
            scatter2 = axes[0, 1].scatter(x, y, c=u, s=1, cmap='RdBu_r')
            axes[0, 1].set_title('X方向速度 (m/s)')
            axes[0, 1].set_xlabel('X (mm)')
            axes[0, 1].set_ylabel('Y (mm)')
            axes[0, 1].set_aspect('equal')
            plt.colorbar(scatter2, ax=axes[0, 1])

            # 压力场
            scatter3 = axes[1, 0].scatter(x, y, c=p, s=1, cmap='coolwarm')
            axes[1, 0].set_title('压力 (Pa)')
            axes[1, 0].set_xlabel('X (mm)')
            axes[1, 0].set_ylabel('Y (mm)')
            axes[1, 0].set_aspect('equal')
            plt.colorbar(scatter3, ax=axes[1, 0])

            # 数据分布统计
            axes[1, 1].hist(speed, bins=30, alpha=0.7, label='速度幅值')
            axes[1, 1].set_xlabel('速度幅值 (m/s)')
            axes[1, 1].set_ylabel('频次')
            axes[1, 1].set_title(f'数据分布 (n={len(x)})')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)

            plt.tight_layout()

            if save_plots:
                output_path = self.output_dir / f"realistic_data_vis_{noise_config}_{sampling_strategy}.png"
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                print(f"📈 可视化图表已保存: {output_path}")
            else:
                plt.show()

            plt.close()

        except Exception as e:
            print(f"❌ 可视化失败: {e}")


def main():
    """主函数"""
    print("🌟 真实数据集生成器")
    print(f"📅 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 创建数据生成器
    generator = RealisticDataGenerator()

    # 生成数据集
    try:
        generated_files = generator.generate_realistic_dataset(
            noise_configs=['high_precision', 'industrial'],  # 减少配置以加快速度
            sampling_strategies=['uniform', 'boundary_focused']
        )

        # 为每个生成的文件创建可视化
        print("\n📈 生成可视化图表...")
        for file_path in generated_files:
            generator.visualize_realistic_data(file_path, save_plots=True)

        print(f"\n✅ 完成! 生成了 {len(generated_files)} 个真实数据集文件")
        print("📂 文件保存在:", generator.output_dir)

        # 显示数据集信息
        print("\n📊 数据集摘要:")
        for file_path in generated_files:
            file_size = file_path.stat().st_size / 1024  # KB
            print(f"   {file_path.name}: {file_size:.1f} KB")

    except Exception as e:
        print(f"❌ 数据集生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())