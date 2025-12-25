#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合数据验证脚本 - 检验COMSOL数据的真实性和可靠性

验证维度:
1. 数据完整性 (NaN、无穷值、零值检测)
2. 物理一致性 (质量守恒、边界条件、Reynolds数)
3. 数值特性 (速度分布、压力梯度、壁面条件)
4. 理论对比 (与解析解/理论值比较)
5. 可视化检查 (流线图、速度云图)

作者: PINNs项目组
日期: 2025-12-24
"""

import h5py
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib import rcParams

# 配置中文字体
rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False


class DataValidator:
    """数据验证器"""

    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.data = None
        self.load_data()

    def load_data(self):
        """加载HDF5数据"""
        print(f"\n{'='*60}")
        print(f"📂 加载数据: {self.filepath.name}")
        print('='*60)

        with h5py.File(self.filepath, 'r') as f:
            self.data = {
                'x': f['x'][:],
                'y': f['y'][:],
                'u': f['u'][:],
                'v': f['v'][:],
                'p': f['p'][:]
            }

        # 获取元数据
        with h5py.File(self.filepath, 'r') as f:
            self.metadata = dict(f.attrs)

        n_points = len(self.data['x'])
        print(f"数据点数: {n_points:,}")
        print(f"元数据: {self.metadata}")

    def check_completeness(self):
        """1. 数据完整性检查"""
        print(f"\n{'='*60}")
        print("1️⃣  数据完整性检查")
        print('='*60)

        passed = True
        x, y, u, v, p = self.data['x'], self.data['y'], self.data['u'], self.data['v'], self.data['p']

        # 1.1 NaN值检测
        nan_count = np.isnan(u).sum() + np.isnan(v).sum() + np.isnan(p).sum()
        if nan_count == 0:
            print("  ✅ 无NaN值")
        else:
            print(f"  ❌ 发现{nan_count}个NaN值")
            passed = False

        # 1.2 无穷值检测
        inf_count = np.isinf(u).sum() + np.isinf(v).sum() + np.isinf(p).sum()
        if inf_count == 0:
            print("  ✅ 无穷值")
        else:
            print(f"  ❌ 发现{inf_count}个无穷值")
            passed = False

        # 1.3 全零值检测
        u_max = np.abs(u).max()
        v_max = np.abs(v).max()
        p_range = p.max() - p.min()

        if u_max > 1e-10:
            print(f"  ✅ 速度u非零 (max={u_max:.6f} m/s)")
        else:
            print(f"  ❌ 速度u全为零!")
            passed = False

        if v_max > 1e-10:
            print(f"  ✅ 速度v非零 (max={v_max:.6f} m/s)")
        else:
            print(f"  ⚠️  速度v接近零 (max={v_max:.6f} m/s) - 可能是纯x方向流动")

        if p_range > 1e-5:
            print(f"  ✅ 压力有变化 (range={p_range:.2f} Pa)")
        else:
            print(f"  ❌ 压力无变化!")
            passed = False

        # 1.4 坐标范围检测
        x_min, x_max = x.min(), x.max()
        y_min, y_max = y.min(), y.max()

        print(f"\n  坐标范围:")
        print(f"    X: [{x_min*1000:.2f}, {x_max*1000:.2f}] mm")
        print(f"    Y: [{y_min*1e6:.1f}, {y_max*1e6:.1f}] μm")

        # 验证坐标范围合理性
        if x_min >= 0 and x_max <= 0.02:  # 20mm以内
            print(f"  ✅ X坐标范围合理")
        else:
            print(f"  ⚠️  X坐标范围异常")

        if y_min >= 0 and y_max <= 0.001:  # 1mm以内
            print(f"  ✅ Y坐标范围合理")
        else:
            print(f"  ⚠️  Y坐标范围异常")

        return passed

    def check_physics_consistency(self):
        """2. 物理一致性检查"""
        print(f"\n{'='*60}")
        print("2️⃣  物理一致性检查")
        print('='*60)

        passed = True
        x, y, u, v, p = self.data['x'], self.data['y'], self.data['u'], self.data['v'], self.data['p']

        # 2.1 速度方向检查 (层流应该是主要x方向)
        speed = np.sqrt(u**2 + v**2)
        u_ratio = np.abs(u).mean() / (speed.mean() + 1e-10)

        print(f"  速度方向分析:")
        print(f"    |u|_mean = {np.abs(u).mean():.6f} m/s")
        print(f"    |v|_mean = {np.abs(v).mean():.6f} m/s")
        print(f"    u_ratio = {u_ratio:.3f} (接近1表示主要是x方向)")

        if u_ratio > 0.8:
            print(f"  ✅ 主速度方向正确 (x方向层流)")
        else:
            print(f"  ⚠️  速度方向与预期不符")

        # 2.2 壁面边界条件检查 (壁面速度应接近0)
        y_min, y_max = y.min(), y.max()
        wall_tol = (y_max - y_min) * 0.01  # 1%容差

        # 上壁面
        top_wall = y > y_max - wall_tol
        if np.sum(top_wall) > 0:
            v_top = np.sqrt(u[top_wall]**2 + v[top_wall]**2).mean()
            print(f"\n  上壁面速度: {v_top:.6f} m/s")
            if v_top < 0.001:
                print(f"  ✅ 上壁面满足无滑移条件")
            else:
                print(f"  ⚠️  上壁面速度不为零")

        # 下壁面
        bottom_wall = y < y_min + wall_tol
        if np.sum(bottom_wall) > 0:
            v_bottom = np.sqrt(u[bottom_wall]**2 + v[bottom_wall]**2).mean()
            print(f"  下壁面速度: {v_bottom:.6f} m/s")
            if v_bottom < 0.001:
                print(f"  ✅ 下壁面满足无滑移条件")
            else:
                print(f"  ⚠️  下壁面速度不为零")

        # 2.3 压力分布检查 (入口压力应高于出口压力)
        # 找到x方向的最小和最大坐标区域
        x_5pct = x.min() + 0.05 * (x.max() - x.min())
        x_95pct = x.min() + 0.95 * (x.max() - x.min())

        inlet_region = x < x_5pct
        outlet_region = x > x_95pct

        if np.sum(inlet_region) > 0 and np.sum(outlet_region) > 0:
            p_inlet = p[inlet_region].mean()
            p_outlet = p[outlet_region].mean()

            print(f"\n  压力分布:")
            print(f"    入口压力: {p_inlet:.2f} Pa")
            print(f"    出口压力: {p_outlet:.2f} Pa")
            print(f"    压降: {p_inlet - p_outlet:.2f} Pa")

            if p_inlet > p_outlet:
                print(f"  ✅ 压力从入口到出口递降 (正确)")
            else:
                print(f"  ❌ 压力分布异常!")
                passed = False

        # 2.4 连续性检查 (速度场应该连续，无突变)
        # 计算速度梯度
        if len(u) > 1000:
            # 采样检查
            sample_idx = np.linspace(0, len(u)-1, 1000, dtype=int)
            u_sample = u[sample_idx]
            v_sample = v[sample_idx]

            # 计算相邻点差值
            u_grad = np.abs(np.diff(u_sample))
            v_grad = np.abs(np.diff(v_sample))

            # 找异常大的梯度 (可能是突变)
            u_grad_max = u_grad.max()
            v_grad_max = v_grad.max()
            u_grad_99pct = np.percentile(u_grad, 99)
            v_grad_99pct = np.percentile(v_grad, 99)

            print(f"\n  速度梯度分析:")
            print(f"    u梯度: max={u_grad_max:.6f}, 99%分位={u_grad_99pct:.6f}")
            print(f"    v梯度: max={v_grad_max:.6f}, 99%分位={v_grad_99pct:.6f}")

            if u_grad_max < 10 * u_grad_99pct:
                print(f"  ✅ 速度场连续性好")
            else:
                print(f"  ⚠️  存在速度突变点")

        return passed

    def check_theoretical_consistency(self):
        """3. 理论一致性检查"""
        print(f"\n{'='*60}")
        print("3️⃣  理论一致性检查")
        print('='*60)

        passed = True
        x, y, u, v, p = self.data['x'], self.data['y'], self.data['u'], self.data['v'], self.data['p']

        # 3.1 计算Reynolds数
        speed = np.sqrt(u**2 + v**2)
        u_avg = speed.mean()
        u_max = speed.max()

        # 从元数据或文件名推断参数
        v_in_cm_s = self.metadata.get('v_in_cm_s', None)
        width_um = self.metadata.get('width_um', None)

        if v_in_cm_s is None or width_um is None:
            # 从文件名推断
            filename = self.filepath.stem
            if 'v0.4' in filename:
                v_in_cm_s = 0.4
            elif 'v1.2' in filename:
                v_in_cm_s = 1.2
            else:
                v_in_cm_s = u_avg * 100  # fallback

            if 'w150' in filename:
                width_um = 150
            elif 'w200' in filename:
                width_um = 200
            elif 'w250' in filename:
                width_um = 250
            else:
                width_um = (y.max() - y.min()) * 1e6  # fallback

        # 物理参数
        rho = 1000.0  # kg/m³
        mu = 0.001    # Pa·s
        v_in = v_in_cm_s / 100  # m/s
        width = width_um * 1e-6  # m

        # Reynolds数: Re = ρvD/μ
        Re_theory = rho * v_in * width / mu
        Re_actual = rho * u_avg * width / mu

        print(f"  Reynolds数分析:")
        print(f"    理论值: {Re_theory:.2f}")
        print(f"    实际值: {Re_actual:.2f} (基于平均速度)")
        print(f"    最大值: {rho * u_max * width / mu:.2f} (基于最大速度)")

        if Re_theory < 2000:
            print(f"  ✅ 层流 (Re < 2000)")
        elif Re_theory < 4000:
            print(f"  ⚠️  过渡区 (2000 < Re < 4000)")
        else:
            print(f"  ❌ 湍流 (Re > 4000) - 可能超出层流假设")

        # 3.2 泊肃叶流理论对比 (Poiseuille Flow)
        # 对于充分发展的层流，理论最大速度 = 2 * 平均速度
        u_ratio = u_max / (u_avg + 1e-10)

        print(f"\n  速度分布分析:")
        print(f"    平均速度: {u_avg*100:.2f} cm/s")
        print(f"    最大速度: {u_max*100:.2f} cm/s")
        print(f"    u_max/u_avg: {u_ratio:.2f}")

        # 对于矩形通道，u_max/u_avg 约为 1.5-2.0
        if 1.3 < u_ratio < 2.5:
            print(f"  ✅ 速度分布符合层流特征")
        else:
            print(f"  ⚠️  速度分布与理论预期有偏差")

        # 3.3 压降理论估算 (达西-韦史巴赫方程: ΔP = f·(L/D)·(ρv²/2))
        # 对于层流: f = 64/Re
        L = x.max() - x.min()
        if Re_actual > 0:
            f_friction = 64 / Re_actual
            delta_p_theory = f_friction * (L / width) * (rho * u_avg**2 / 2)

            delta_p_actual = p.max() - p.min()

            print(f"\n  压降分析:")
            print(f"    理论压降: {delta_p_theory:.2f} Pa")
            print(f"    实际压降: {delta_p_actual:.2f} Pa")
            print(f"    比值: {delta_p_actual / (delta_p_theory + 1e-10):.2f}")

            if 0.5 < delta_p_actual / (delta_p_theory + 1e-10) < 2.0:
                print(f"  ✅ 压降与理论值在同一量级")
            else:
                print(f"  ⚠️  压降与理论值偏差较大")

        return passed

    def check_numerical_properties(self):
        """4. 数值特性检查"""
        print(f"\n{'='*60}")
        print("4️⃣  数值特性检查")
        print('='*60)

        passed = True
        x, y, u, v, p = self.data['x'], self.data['y'], self.data['u'], self.data['v'], self.data['p']

        # 4.1 数据密度检查
        x_range = x.max() - x.min()
        y_range = y.max() - y.min()
        area = x_range * y_range
        density = len(u) / area

        print(f"  数据密度: {density:.0f} 点/m²")
        print(f"    相当于每mm²: {density * 1e-6:.1f} 点")

        if density > 1e8:
            print(f"  ✅ 数据密度充足")
        else:
            print(f"  ⚠️  数据密度可能偏低")

        # 4.2 统计分布
        print(f"\n  速度统计分布:")

        for name, data in [('u (m/s)', u), ('v (m/s)', v), ('p (Pa)', p)]:
            print(f"    {name}:")
            print(f"      最小值: {data.min():.6f}")
            print(f"      最大值: {data.max():.6f}")
            print(f"      平均值: {data.mean():.6f}")
            print(f"      标准差: {data.std():.6f}")

        # 4.3 检测异常值
        u_std = u.std()
        v_std = v.std()
        p_std = p.std()

        u_outliers = np.sum(np.abs(u - u.mean()) > 3 * u_std)
        v_outliers = np.sum(np.abs(v - v.mean()) > 3 * v_std)
        p_outliers = np.sum(np.abs(p - p.mean()) > 3 * p_std)

        print(f"\n  异常值检测 (3σ准则):")
        print(f"    u异常值: {u_outliers}/{len(u)} ({100*u_outliers/len(u):.2f}%)")
        print(f"    v异常值: {v_outliers}/{len(v)} ({100*v_outliers/len(v):.2f}%)")
        print(f"    p异常值: {p_outliers}/{len(p)} ({100*p_outliers/len(p):.2f}%)")

        if u_outliers < len(u) * 0.01:
            print(f"  ✅ 异常值比例正常 (<1%)")
        else:
            print(f"  ⚠️  异常值比例较高")

        return passed

    def visualize_data(self, save_dir=None):
        """5. 可视化检查"""
        print(f"\n{'='*60}")
        print("5️⃣  可视化检查")
        print('='*60)

        x, y, u, v, p = self.data['x'], self.data['y'], self.data['u'], self.data['v'], self.data['p']

        # 创建图形
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'{self.filepath.name} 数据可视化', fontsize=16)

        # 5.1 速度云图 (u分量)
        scatter = axes[0, 0].scatter(x*1000, y*1e6, c=u, s=1, cmap='jet')
        axes[0, 0].set_xlabel('X (mm)')
        axes[0, 0].set_ylabel('Y (μm)')
        axes[0, 0].set_title('X方向速度 u (m/s)')
        plt.colorbar(scatter, ax=axes[0, 0])

        # 5.2 速度云图 (v分量)
        scatter = axes[0, 1].scatter(x*1000, y*1e6, c=v, s=1, cmap='jet')
        axes[0, 1].set_xlabel('X (mm)')
        axes[0, 1].set_ylabel('Y (μm)')
        axes[0, 1].set_title('Y方向速度 v (m/s)')
        plt.colorbar(scatter, ax=axes[0, 1])

        # 5.3 压力云图
        scatter = axes[0, 2].scatter(x*1000, y*1e6, c=p, s=1, cmap='viridis')
        axes[0, 2].set_xlabel('X (mm)')
        axes[0, 2].set_ylabel('Y (μm)')
        axes[0, 2].set_title('压力 p (Pa)')
        plt.colorbar(scatter, ax=axes[0, 2])

        # 5.4 速度大小分布
        speed = np.sqrt(u**2 + v**2)
        scatter = axes[1, 0].scatter(x*1000, y*1e6, c=speed, s=1, cmap='plasma')
        axes[1, 0].set_xlabel('X (mm)')
        axes[1, 0].set_ylabel('Y (μm)')
        axes[1, 0].set_title('速度大小 |U| (m/s)')
        plt.colorbar(scatter, ax=axes[1, 0])

        # 5.5 X方向速度剖面 (在通道中间位置)
        y_mid = (y.max() + y.min()) / 2
        mid_tol = (y.max() - y.min()) * 0.1
        mid_region = np.abs(y - y_mid) < mid_tol

        if np.sum(mid_region) > 0:
            x_mid = x[mid_region]
            u_mid = u[mid_region]
            # 按x排序
            sort_idx = np.argsort(x_mid)
            axes[1, 1].plot(x_mid[sort_idx]*1000, u_mid[sort_idx], 'b-', linewidth=2)
            axes[1, 1].set_xlabel('X (mm)')
            axes[1, 1].set_ylabel('u (m/s)')
            axes[1, 1].set_title('中心线X方向速度剖面')
            axes[1, 1].grid(True, alpha=0.3)

        # 5.6 速度直方图
        axes[1, 2].hist(u, bins=50, alpha=0.7, label='u', color='blue')
        axes[1, 2].set_xlabel('速度 (m/s)')
        axes[1, 2].set_ylabel('频数')
        axes[1, 2].set_title('X方向速度分布直方图')
        axes[1, 2].legend()
        axes[1, 2].grid(True, alpha=0.3)

        plt.tight_layout()

        # 保存图片
        if save_dir is None:
            save_dir = Path(__file__).parent.parent.parent / "logs"
        save_dir.mkdir(parents=True, exist_ok=True)

        img_path = save_dir / f"validation_{self.filepath.stem}.png"
        plt.savefig(img_path, dpi=150, bbox_inches='tight')
        print(f"  ✅ 可视化图已保存: {img_path}")

        plt.close()

    def generate_report(self):
        """生成验证报告"""
        print(f"\n{'='*60}")
        print("📋 验证报告汇总")
        print('='*60)

        results = {
            '完整性': self.check_completeness(),
            '物理一致性': self.check_physics_consistency(),
            '理论一致性': self.check_theoretical_consistency(),
            '数值特性': self.check_numerical_properties()
        }

        # 生成可视化
        self.visualize_data()

        # 总体评估
        all_passed = all(results.values())

        print(f"\n{'='*60}")
        print("✅ 验证完成")
        print('='*60)

        for category, passed in results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"  {status} - {category}")

        if all_passed:
            print(f"\n🎉 所有验证通过! 数据质量良好。")
        else:
            print(f"\n⚠️  部分验证未通过，请检查上述问题。")

        return all_passed


def main():
    """主函数"""
    import sys

    if len(sys.argv) > 1:
        # 指定文件
        filepath = sys.argv[1]
    else:
        # 默认验证最新的6个文件
        data_dir = Path(__file__).parent.parent.parent / "data"
        files = [
            "v0.4_w150.h5", "v0.4_w200.h5", "v0.4_w250.h5",
            "v1.2_w150.h5", "v1.2_w200.h5", "v1.2_w250.h5"
        ]

        print("🔍 COMSOL数据综合验证")
        print("="*60)
        print("验证文件:")
        for f in files:
            print(f"  - {f}")

        all_passed = True
        for filename in files:
            filepath = data_dir / filename
            if filepath.exists():
                validator = DataValidator(filepath)
                passed = validator.generate_report()
                all_passed = all_passed and passed
            else:
                print(f"\n❌ 文件不存在: {filename}")

        sys.exit(0 if all_passed else 1)

    # 验证单个文件
    validator = DataValidator(filepath)
    passed = validator.generate_report()
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
