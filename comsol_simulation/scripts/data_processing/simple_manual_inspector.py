"""
简化人工数据检查工具

提供简单直观的方式来人工检查生成的数据集质量和真实性

作者: PINNs项目组
创建时间: 2025-11-19
"""

import os
import sys
import numpy as np
import h5py
import matplotlib.pyplot as plt
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def load_and_inspect_dataset(filename):
    """加载并检查单个数据集"""
    data_dir = project_root / "comsol_simulation" / "data"
    file_path = data_dir / filename

    print(f"\n{'='*60}")
    print(f"📋 人工检查数据集: {filename}")
    print(f"{'='*60}")

    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return

    # 显示文件大小
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"📁 文件大小: {file_size_mb:.2f} MB")

    try:
        with h5py.File(file_path, 'r') as h5file:
            print(f"✅ 文件格式: HDF5")

            # 1. 基本信息
            print(f"\n📊 基本信息:")
            if 'info' in h5file:
                info_attrs = dict(h5file['info'].attrs)
                for key, value in info_attrs.items():
                    print(f"   {key}: {value}")

            # 2. 数据结构
            print(f"\n📂 数据结构:")
            for key in h5file.keys():
                group = h5file[key]
                if isinstance(group, h5py.Group):
                    print(f"   📁 {key}/ (组)")
                    for subkey in group.keys():
                        if isinstance(group[subkey], h5py.Dataset):
                            shape = group[subkey].shape
                            dtype = group[subkey].dtype
                            print(f"      📄 {subkey}: {shape} {dtype}")
                        else:
                            print(f"      📁 {subkey}/ (子组)")
                else:
                    print(f"   📄 {key}: {group.shape} {group.dtype}")

            # 3. 加载关键数据
            print(f"\n🔍 数据内容分析:")

            # 网格数据
            if 'mesh' in h5file:
                mesh_group = h5file['mesh']
                x = mesh_group['x'][:]
                y = mesh_group['y'][:]
                n_points = len(x)

                print(f"   📍 网格点数: {n_points}")
                print(f"   📍 X范围: {np.min(x):.3f} ~ {np.max(x):.3f} mm")
                print(f"   📍 Y范围: {np.min(y):.3f} ~ {np.max(y):.3f} mm")

            # 求解数据
            if 'solution' in h5file:
                sol = h5file['solution']

                # 干净数据
                u_clean = sol['u_clean'][:]
                v_clean = sol['v_clean'][:]
                p_clean = sol['p_clean'][:]

                # 噪声数据
                u_noisy = sol['u'][:]
                v_noisy = sol['v'][:]
                p_noisy = sol['p'][:]

                # 计算速度幅值
                speed_clean = np.sqrt(u_clean**2 + v_clean**2)
                speed_noisy = np.sqrt(u_noisy**2 + v_noisy**2)

                print(f"\n   🌊 流场数据:")
                print(f"      U速度 (干净): {np.min(u_clean):.6f} ~ {np.max(u_clean):.6f} m/s")
                print(f"      V速度 (干净): {np.min(v_clean):.6f} ~ {np.max(v_clean):.6f} m/s")
                print(f"      速度幅值 (干净): {np.min(speed_clean):.6f} ~ {np.max(speed_clean):.6f} m/s")
                print(f"      压力 (干净): {np.min(p_clean):.1f} ~ {np.max(p_clean):.1f} Pa")

                print(f"\n      U速度 (噪声): {np.min(u_noisy):.6f} ~ {np.max(u_noisy):.6f} m/s")
                print(f"      V速度 (噪声): {np.min(v_noisy):.6f} ~ {np.max(v_noisy):.6f} m/s")
                print(f"      速度幅值 (噪声): {np.min(speed_noisy):.6f} ~ {np.max(speed_noisy):.6f} m/s")
                print(f"      压力 (噪声): {np.min(p_noisy):.1f} ~ {np.max(p_noisy):.1f} Pa")

                # 缺失数据
                if 'missing_mask' in sol:
                    missing_mask = sol['missing_mask'][:]
                    missing_count = np.sum(missing_mask)
                    missing_ratio = missing_count / len(missing_mask) * 100
                    print(f"      缺失数据: {missing_count}/{len(missing_mask)} ({missing_ratio:.1f}%)")

            # 4. 噪声分析
            if 'noise_analysis' in h5file:
                print(f"\n📈 噪声分析:")
                noise_group = h5file['noise_analysis']
                for field in noise_group.keys():
                    field_attrs = dict(noise_group[field].attrs)
                    print(f"      {field}场:")
                    for attr_name, attr_value in field_attrs.items():
                        if attr_name == 'snr_db':
                            print(f"         信噪比: {attr_value:.1f} dB")
                        elif attr_name == 'noise_std':
                            print(f"         噪声标准差: {attr_value:.2e}")
                        else:
                            print(f"         {attr_name}: {attr_value}")

            # 5. 物理合理性检查
            print(f"\n🔬 物理合理性检查:")

            # 速度检查
            if 'solution' in h5file:
                max_speed = np.max(speed_clean)
                avg_speed = np.mean(speed_clean)

                print(f"   ⚡ 速度特征:")
                print(f"      最大速度: {max_speed:.6f} m/s")
                print(f"      平均速度: {avg_speed:.6f} m/s")

                if max_speed < 0.1:
                    print(f"      ✅ 速度范围合理 (微流控通常 < 0.1 m/s)")
                else:
                    print(f"      ⚠️  速度可能过高 (微流控通常 < 0.1 m/s)")

                # 压力检查
                pressure_range = np.max(p_clean) - np.min(p_clean)
                print(f"   💨 压力特征:")
                print(f"      压力降: {pressure_range:.1f} Pa")

                if pressure_range < 50000:
                    print(f"      ✅ 压力降合理 (微流控通常 < 50 kPa)")
                else:
                    print(f"      ⚠️  压力降可能过高")

                # 雷诺数估算
                channel_width = 0.2e-3  # 假设0.2mm通道宽度
                kinematic_viscosity = 1e-6  # 水的运动粘度
                reynolds_number = avg_speed * channel_width / kinematic_viscosity

                print(f"   🌊 流动特征:")
                print(f"      估算雷诺数: {reynolds_number:.1f}")

                if reynolds_number < 2300:
                    print(f"      ✅ 层流状态 (适合PINNs训练)")
                else:
                    print(f"      ⚠️  可能不是层流状态")

            # 6. 显示部分原始数据
            print(f"\n📋 原始数据样本 (前10个点):")
            print(f"{'序号':<4} {'X(mm)':<8} {'Y(mm)':<8} {'U(m/s)':<12} {'V(m/s)':<12} {'P(Pa)':<10}")
            print("-" * 70)

            n_show = min(10, len(x))
            for i in range(n_show):
                print(f"{i+1:<4} "
                      f"{x[i]:<8.3f} "
                      f"{y[i]:<8.3f} "
                      f"{u_noisy[i]:<12.6f} "
                      f"{v_noisy[i]:<12.6f} "
                      f"{p_noisy[i]:<10.1f}")

            # 7. 生成简单的可视化
            if 'solution' in h5file:
                print(f"\n📊 生成数据可视化...")
                create_simple_visualization(x, y, u_noisy, v_noisy, p_noisy,
                                          filename.replace('.h5', '_manual_check.png'))

    except Exception as e:
        print(f"❌ 读取文件时出错: {e}")
        import traceback
        traceback.print_exc()


def create_simple_visualization(x, y, u, v, p, save_name):
    """创建简单的数据可视化"""
    try:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('人工数据检查 - 可视化', fontsize=16)

        # 1. 数据点分布
        ax1 = axes[0, 0]
        speed = np.sqrt(u**2 + v**2)
        scatter = ax1.scatter(x, y, c=speed, s=10, cmap='viridis', alpha=0.7)
        ax1.set_xlabel('X (mm)')
        ax1.set_ylabel('Y (mm)')
        ax1.set_title('数据点分布 (颜色=速度)')
        ax1.set_aspect('equal')
        plt.colorbar(scatter, ax=ax1, label='速度 (m/s)')

        # 2. 速度场矢量图
        ax2 = axes[0, 1]
        # 为了清晰显示，每隔几个点画一个箭头
        skip = max(1, len(x) // 50)
        ax2.quiver(x[::skip], y[::skip], u[::skip], v[::skip],
                  speed[::skip], cmap='viridis', alpha=0.7)
        ax2.set_xlabel('X (mm)')
        ax2.set_ylabel('Y (mm)')
        ax2.set_title('速度场矢量图')
        ax2.set_aspect('equal')

        # 3. 压力分布
        ax3 = axes[1, 0]
        scatter = ax3.scatter(x, y, c=p, s=10, cmap='coolwarm', alpha=0.7)
        ax3.set_xlabel('X (mm)')
        ax3.set_ylabel('Y (mm)')
        ax3.set_title('压力分布')
        ax3.set_aspect('equal')
        plt.colorbar(scatter, ax=ax3, label='压力 (Pa)')

        # 4. 数据统计
        ax4 = axes[1, 1]
        ax4.axis('off')

        # 统计信息
        stats_text = f"""数据统计信息:

总数据点数: {len(x)}
X范围: {np.min(x):.3f} ~ {np.max(x):.3f} mm
Y范围: {np.min(y):.3f} ~ {np.max(y):.3f} mm

速度统计:
  U: {np.min(u):.6f} ~ {np.max(u):.6f} m/s
  V: {np.min(v):.6f} ~ {np.max(v):.6f} m/s
  速度幅值: {np.min(speed):.6f} ~ {np.max(speed):.6f} m/s

压力统计:
  P: {np.min(p):.1f} ~ {np.max(p):.1f} Pa
  压力降: {np.max(p) - np.min(p):.1f} Pa

平均雷诺数 ≈ {np.mean(speed) * 0.2e-3 / 1e-6:.1f} (层流)
"""
        ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes,
                fontsize=10, verticalalignment='top', fontfamily='monospace')

        plt.tight_layout()

        # 保存图片
        output_dir = project_root / "comsol_simulation" / "data"
        save_path = output_dir / save_name
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"✅ 可视化图已保存: {save_path}")

    except Exception as e:
        print(f"❌ 生成可视化时出错: {e}")


def main():
    """主函数"""
    print("🌟 简化人工数据检查工具")

    # 查找所有真实数据集
    data_dir = project_root / "comsol_simulation" / "data"
    h5_files = list(data_dir.glob("*.h5"))
    realistic_files = [f for f in h5_files if "realistic" in f.name]

    if not realistic_files:
        print("❌ 未找到真实数据集文件")
        return

    print(f"📁 发现 {len(realistic_files)} 个真实数据集")

    # 逐一检查每个数据集
    for i, file_path in enumerate(realistic_files, 1):
        load_and_inspect_dataset(file_path.name)

        # 如果不是最后一个文件，询问是否继续
        if i < len(realistic_files):
            print(f"\n📋 已完成 {i}/{len(realistic_files)} 个数据集检查")
            # 由于无法使用input，自动继续检查

    print(f"\n✅ 所有数据集检查完成！")
    print(f"📂 可视化图保存在: {data_dir}")


if __name__ == "__main__":
    main()