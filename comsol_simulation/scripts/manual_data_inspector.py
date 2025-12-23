"""
人工数据集检查工具

提供简单直观的方式来人工检查生成的数据集质量和真实性
包含交互式查看和详细统计分析功能

作者: PINNs项目组
创建时间: 2025-11-19
"""

import os
import sys
import numpy as np
import h5py
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class ManualDataInspector:
    """人工数据检查器"""

    def __init__(self, data_dir: str = None):
        """
        初始化检查器

        Args:
            data_dir: 数据目录路径
        """
        if data_dir is None:
            data_dir = project_root / "comsol_simulation" / "data"

        self.data_dir = Path(data_dir)
        print(f"📂 数据检查器初始化完成，数据目录: {self.data_dir}")

    def list_available_datasets(self) -> list:
        """
        列出所有可用的数据集

        Returns:
            list: 数据集文件名列表
        """
        h5_files = list(self.data_dir.glob("*.h5"))
        realistic_files = [f for f in h5_files if "realistic" in f.name]

        print(f"\n📋 发现 {len(realistic_files)} 个真实数据集:")
        for i, file_path in enumerate(realistic_files, 1):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"   {i}. {file_path.name} ({size_mb:.2f} MB)")

        return realistic_files

    def load_dataset_simple(self, filename: str) -> Dict:
        """
        简单加载数据集

        Args:
            filename: 数据集文件名

        Returns:
            dict: 简化的数据字典
        """
        file_path = self.data_dir / filename

        with h5py.File(file_path, 'r') as h5file:
            # 基本信息
            info = {}
            if 'info' in h5file:
                info = dict(h5file['info'].attrs)

            # 网格和坐标
            x = h5file['mesh']['x'][:]
            y = h5file['mesh']['y'][:]

            # 干净数据和噪声数据
            solution_data = {}
            if 'solution' in h5file:
                sol = h5file['solution']
                solution_data = {
                    'x': x,
                    'y': y,
                    'u_clean': sol['u_clean'][:],
                    'v_clean': sol['v_clean'][:],
                    'p_clean': sol['p_clean'][:],
                    'u_noisy': sol['u'][:],
                    'v_noisy': sol['v'][:],
                    'p_noisy': sol['p'][:]
                }

                # 如果有缺失数据掩码
                if 'missing_mask' in sol:
                    solution_data['missing_mask'] = sol['missing_mask'][:]

            # 噪声分析
            noise_info = {}
            if 'noise_analysis' in h5file:
                noise_group = h5file['noise_analysis']
                for field in ['u', 'v', 'p']:
                    if field in noise_group:
                        noise_info[field] = dict(noise_group[field].attrs)

        return {
            'filename': filename,
            'info': info,
            'data': solution_data,
            'noise_analysis': noise_info
        }

    def print_basic_info(self, dataset: Dict):
        """
        打印基本信息

        Args:
            dataset: 数据集字典
        """
        print(f"\n{'='*50}")
        print(f"📋 数据集基本信息: {dataset['filename']}")
        print(f"{'='*50}")

        # 基本信息
        info = dataset['info']
        print(f"📅 创建时间: {info.get('creation_time', '未知')}")
        print(f"🔬 数据类型: {info.get('data_type', '未知')}")
        print(f"📊 描述: {info.get('description', '无')}")

        # 数据统计
        data = dataset['data']
        n_points = len(data['x'])
        print(f"\n📈 数据统计:")
        print(f"   数据点数: {n_points}")
        print(f"   X范围: {np.min(data['x']):.3f} ~ {np.max(data['x']):.3f} mm")
        print(f"   Y范围: {np.min(data['y']):.3f} ~ {np.max(data['y']):.3f} mm")

        # 物理量统计
        speed_clean = np.sqrt(data['u_clean']**2 + data['v_clean']**2)
        speed_noisy = np.sqrt(data['u_noisy']**2 + data['v_noisy']**2)

        print(f"\n🔬 物理量统计:")
        print(f"   X方向速度 (干净): {np.min(data['u_clean']):.6f} ~ {np.max(data['u_clean']):.6f} m/s")
        print(f"   Y方向速度 (干净): {np.min(data['v_clean']):.6f} ~ {np.max(data['v_clean']):.6f} m/s")
        print(f"   速度幅值 (干净): {np.min(speed_clean):.6f} ~ {np.max(speed_clean):.6f} m/s")
        print(f"   压力 (干净): {np.min(data['p_clean']):.1f} ~ {np.max(data['p_clean']):.1f} Pa")

        print(f"   X方向速度 (噪声): {np.min(data['u_noisy']):.6f} ~ {np.max(data['u_noisy']):.6f} m/s")
        print(f"   Y方向速度 (噪声): {np.min(data['v_noisy']):.6f} ~ {np.max(data['v_noisy']):.6f} m/s")
        print(f"   速度幅值 (噪声): {np.min(speed_noisy):.6f} ~ {np.max(speed_noisy):.6f} m/s")
        print(f"   压力 (噪声): {np.min(data['p_noisy']):.1f} ~ {np.max(data['p_noisy']):.1f} Pa")

        # 噪声分析
        if dataset['noise_analysis']:
            print(f"\n📊 噪声分析:")
            for field, noise_data in dataset['noise_analysis'].items():
                snr = noise_data.get('snr_db', 'N/A')
                std = noise_data.get('noise_std', 'N/A')
                print(f"   {field}场: SNR = {snr} dB, 噪声标准差 = {std}")

    def show_raw_data_samples(self, dataset: Dict, n_samples: int = 10):
        """
        显示原始数据样本

        Args:
            dataset: 数据集字典
            n_samples: 显示样本数量
        """
        print(f"\n🔍 原始数据样本 (前{n_samples}个点):")
        print(f"{'序号':<4} {'X(mm)':<10} {'Y(mm)':<10} {'U(m/s)':<12} {'V(m/s)':<12} {'P(Pa)':<12}")
        print("-" * 70)

        data = dataset['data']
        for i in range(min(n_samples, len(data['x']))):
            print(f"{i+1:<4} "
                  f"{data['x'][i]:<10.3f} "
                  f"{data['y'][i]:<10.3f} "
                  f"{data['u_noisy'][i]:<12.6f} "
                  f"{data['v_noisy'][i]:<12.6f} "
                  f"{data['p_noisy'][i]:<12.1f}")

        # 如果数据点很多，显示最后几个
        if len(data['x']) > n_samples:
            print("   ...")
            for i in range(max(0, len(data['x'])-3), len(data['x'])):
                print(f"{i+1:<4} "
                      f"{data['x'][i]:<10.3f} "
                      f"{data['y'][i]:<10.3f} "
                      f"{data['u_noisy'][i]:<12.6f} "
                      f"{data['v_noisy'][i]:<12.6f} "
                      f"{data['p_noisy'][i]:<12.1f}")

    def visualize_data_overview(self, dataset: Dict, save_path: Optional[str] = None):
        """
        可视化数据概览

        Args:
            dataset: 数据集字典
            save_path: 保存路径
        """
        data = dataset['data']
        x, y = data['x'], data['y']

        # 计算速度幅值
        speed_clean = np.sqrt(data['u_clean']**2 + data['v_clean']**2)
        speed_noisy = np.sqrt(data['u_noisy']**2 + data['v_noisy']**2)

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f'数据集概览: {dataset["filename"]}', fontsize=16)

        # 1. 采样点分布
        ax1 = axes[0, 0]
        scatter = ax1.scatter(x, y, c=speed_noisy, s=20, cmap='viridis', alpha=0.8)
        ax1.set_xlabel('X (mm)')
        ax1.set_ylabel('Y (mm)')
        ax1.set_title('数据点分布 (颜色=速度)')
        ax1.set_aspect('equal')
        plt.colorbar(scatter, ax=ax1, label='速度 (m/s)')

        # 2. 速度场对比
        ax2 = axes[0, 1]
        ax2.scatter(data['u_clean'], data['u_noisy'], alpha=0.6, s=10, label='U分量')
        ax2.scatter(data['v_clean'], data['v_noisy'], alpha=0.6, s=10, label='V分量')
        max_vel = max(np.max(np.abs(data['u_clean'])), np.max(np.abs(data['v_clean'])))
        ax2.plot([-max_vel, max_vel], [-max_vel, max_vel], 'r--', alpha=0.8, label='理想匹配')
        ax2.set_xlabel('干净数据 (m/s)')
        ax2.set_ylabel('噪声数据 (m/s)')
        ax2.set_title('速度场噪声影响')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. 压力场对比
        ax3 = axes[0, 2]
        ax3.scatter(data['p_clean'], data['p_noisy'], alpha=0.6, s=10, c='orange')
        min_p, max_p = min(np.min(data['p_clean']), np.min(data['p_noisy'])), max(np.max(data['p_clean']), np.max(data['p_noisy']))
        ax3.plot([min_p, max_p], [min_p, max_p], 'r--', alpha=0.8, label='理想匹配')
        ax3.set_xlabel('干净压力 (Pa)')
        ax3.set_ylabel('噪声压力 (Pa)')
        ax3.set_title('压力场噪声影响')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 4. 速度幅值直方图
        ax4 = axes[1, 0]
        ax4.hist(speed_clean, bins=30, alpha=0.7, label='干净数据', density=True)
        ax4.hist(speed_noisy, bins=30, alpha=0.7, label='噪声数据', density=True)
        ax4.set_xlabel('速度幅值 (m/s)')
        ax4.set_ylabel('概率密度')
        ax4.set_title('速度幅值分布')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        # 5. 压力直方图
        ax5 = axes[1, 1]
        ax5.hist(data['p_clean'], bins=30, alpha=0.7, label='干净数据', density=True)
        ax5.hist(data['p_noisy'], bins=30, alpha=0.7, label='噪声数据', density=True)
        ax5.set_xlabel('压力 (Pa)')
        ax5.set_ylabel('概率密度')
        ax5.set_title('压力分布')
        ax5.legend()
        ax5.grid(True, alpha=0.3)

        # 6. 误差分析
        ax6 = axes[1, 2]
        u_error = np.abs(data['u_noisy'] - data['u_clean'])
        v_error = np.abs(data['v_noisy'] - data['v_clean'])
        p_error = np.abs(data['p_noisy'] - data['p_clean'])

        ax6.hist(u_error, bins=20, alpha=0.7, label=f'U误差 (均值:{np.mean(u_error):.2e})')
        ax6.hist(v_error, bins=20, alpha=0.7, label=f'V误差 (均值:{np.mean(v_error):.2e})')
        ax6.hist(p_error, bins=20, alpha=0.7, label=f'P误差 (均值:{np.mean(p_error):.1f})')
        ax6.set_xlabel('绝对误差')
        ax6.set_ylabel('频次')
        ax6.set_title('测量误差分析')
        ax6.legend()
        ax6.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"📈 数据概览图已保存: {save_path}")
        else:
            plt.show()

    def check_physical_consistency(self, dataset: Dict):
        """
        检查物理一致性

        Args:
            dataset: 数据集字典
        """
        print(f"\n🔬 物理一致性检查:")

        data = dataset['data']
        x, y = data['x'], data['y']
        u, v = data['u_noisy'], data['v_noisy']
        p = data['p_noisy']

        # 1. 检查速度范围的合理性
        speed = np.sqrt(u**2 + v**2)
        max_speed = np.max(speed)
        avg_speed = np.mean(speed)

        print(f"   📊 速度分析:")
        print(f"      最大速度: {max_speed:.6f} m/s")
        print(f"      平均速度: {avg_speed:.6f} m/s")
        print(f"      速度范围合理性: {'✓' if max_speed < 0.1 else '⚠️'} (微流控通常 < 0.1 m/s)")

        # 2. 检查压力降的合理性
        min_pressure = np.min(p)
        max_pressure = np.max(p)
        pressure_drop = max_pressure - min_pressure

        print(f"   📊 压力分析:")
        print(f"      压力范围: {min_pressure:.1f} ~ {max_pressure:.1f} Pa")
        print(f"      压力降: {pressure_drop:.1f} Pa")
        print(f"      压力范围合理性: {'✓' if pressure_drop < 50000 else '⚠️'} (微流控通常 < 50 kPa)")

        # 3. 估算雷诺数
        # 假设特征尺寸为通道宽度 (约0.2mm = 2e-4 m)，水为工质
        channel_width = 0.2e-3  # m
        kinematic_viscosity = 1e-6  # m²/s (水)
        reynolds_number = avg_speed * channel_width / kinematic_viscosity

        print(f"   📊 流动特征:")
        print(f"      估算雷诺数: {reynolds_number:.1f}")
        print(f"      流动状态: {'层流' if reynolds_number < 2300 else '湍流'}")

        # 4. 检查数据完整性
        if 'missing_mask' in data:
            missing_ratio = np.mean(data['missing_mask']) * 100
            print(f"   📊 数据完整性:")
            print(f"      缺失数据比例: {missing_ratio:.1f}%")
            print(f"      数据质量: {'优秀' if missing_ratio < 2 else '良好' if missing_ratio < 5 else '一般'}")

        # 5. 检查噪声水平
        noise_analysis = dataset['noise_analysis']
        if noise_analysis:
            print(f"   📊 噪声水平:")
            for field, noise_data in noise_analysis.items():
                snr = noise_data.get('snr_db', 0)
                if snr > 40:
                    quality = "优秀"
                elif snr > 30:
                    quality = "良好"
                elif snr > 20:
                    quality = "一般"
                else:
                    quality = "较差"
                print(f"      {field}场信噪比: {snr:.1f} dB ({quality})")

        print(f"\n📋 总体评估:")
        issues = []
        if max_speed >= 0.1:
            issues.append("速度范围可能不合理")
        if pressure_drop >= 50000:
            issues.append("压力降可能过高")
        if reynolds_number >= 2300:
            issues.append("可能不是层流状态")

        if not issues:
            print("   ✅ 数据集物理特征合理，适合PINNs训练")
        else:
            print("   ⚠️ 发现以下潜在问题:")
            for issue in issues:
                print(f"      - {issue}")

    def interactive_inspection(self, filename: str):
        """
        交互式数据检查

        Args:
            filename: 数据集文件名
        """
        print(f"\n🔍 开始交互式检查: {filename}")

        # 加载数据集
        dataset = self.load_dataset_simple(filename)

        # 1. 打印基本信息
        self.print_basic_info(dataset)

        # 2. 显示原始数据样本
        self.show_raw_data_samples(dataset, n_samples=15)

        # 3. 物理一致性检查
        self.check_physical_consistency(dataset)

        # 4. 可视化数据概览
        vis_path = self.data_dir / f"manual_inspection_{filename.replace('.h5', '.png')}"
        self.visualize_data_overview(dataset, str(vis_path))

        # 5. 导出CSV文件用于Excel查看
        csv_path = self.data_dir / f"inspection_data_{filename.replace('.h5', '.csv')}"
        self.export_to_csv(dataset, str(csv_path))

        print(f"\n✅ 交互式检查完成!")
        print(f"📊 可视化图: {vis_path}")
        print(f"📄 CSV文件: {csv_path}")

    def export_to_csv(self, dataset: Dict, csv_path: str):
        """
        导出数据到CSV文件

        Args:
            dataset: 数据集字典
            csv_path: CSV文件路径
        """
        data = dataset['data']
        df = pd.DataFrame({
            'X_mm': data['x'],
            'Y_mm': data['y'],
            'U_clean_m_s': data['u_clean'],
            'V_clean_m_s': data['v_clean'],
            'P_clean_Pa': data['p_clean'],
            'U_noisy_m_s': data['u_noisy'],
            'V_noisy_m_s': data['v_noisy'],
            'P_noisy_Pa': data['p_noisy']
        })

        # 如果有缺失数据掩码，添加到CSV
        if 'missing_mask' in data:
            df['Is_Missing'] = data['missing_mask'].astype(int)

        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"💾 数据已导出到CSV: {csv_path}")


def main():
    """主函数 - 交互式数据检查"""
    print("🌟 人工数据集检查工具")

    # 创建检查器
    inspector = ManualDataInspector()

    # 列出可用数据集
    datasets = inspector.list_available_datasets()

    if not datasets:
        print("❌ 未找到真实数据集文件")
        return

    print(f"\n选择要检查的数据集:")
    for i, dataset_path in enumerate(datasets, 1):
        print(f"   {i}. {dataset_path.name}")

    # 自动选择第一个数据集进行检查（避免交互式输入问题）
    print(f"\n🔍 自动选择第一个数据集进行详细检查...")
    selected_dataset = datasets[0]

    # 执行交互式检查
    inspector.interactive_inspection(selected_dataset.name)

    # 可选：检查其他数据集
    if len(datasets) > 1:
        print(f"\n📋 简要检查其他 {len(datasets)-1} 个数据集...")
        for i, dataset_path in enumerate(datasets[1:], 2):
            print(f"\n{'='*50}")
            print(f"📋 快速检查数据集 {i}: {dataset_path.name}")
            print(f"{'='*50}")

              try:
                dataset = inspector.load_dataset_simple(dataset_path.name)
                inspector.print_basic_info(dataset)
                inspector.check_physical_consistency(dataset)
            except Exception as e:
                print(f"❌ 检查失败: {e}")


if __name__ == "__main__":
    main()