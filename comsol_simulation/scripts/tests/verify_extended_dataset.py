#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证扩展数据集 (36组)

检查项:
1. 文件完整性
2. 数据点数量
3. 物理量范围
4. Reynolds数验证
5. 数据质量评分

作者: PINNs项目组
日期: 2025-12-24
"""

import h5py
import numpy as np
from pathlib import Path
from datetime import datetime


class ExtendedDataVerifier:
    """扩展数据集验证器"""

    def __init__(self, data_dir: str):
        """初始化验证器"""
        self.data_dir = Path(data_dir)
        self.results = []

    def get_expected_files(self) -> dict:
        """获取预期文件列表"""
        expected = {
            # 原有9组
            'v0.2_w150.h5': {'v': 0.0015, 'w': 0.00015, 'mu': 0.001, 'type': 'straight'},
            'v0.8_w150.h5': {'v': 0.0077, 'w': 0.00015, 'mu': 0.001, 'type': 'straight'},
            'v1.5_w150.h5': {'v': 0.0154, 'w': 0.00015, 'mu': 0.001, 'type': 'straight'},
            'v0.2_w200.h5': {'v': 0.0015, 'w': 0.00020, 'mu': 0.001, 'type': 'straight'},
            'v0.8_w200.h5': {'v': 0.0077, 'w': 0.00020, 'mu': 0.001, 'type': 'straight'},
            'v1.5_w200.h5': {'v': 0.0154, 'w': 0.00020, 'mu': 0.001, 'type': 'straight'},
            'v0.2_w250.h5': {'v': 0.0015, 'w': 0.00025, 'mu': 0.001, 'type': 'straight'},
            'v0.8_w250.h5': {'v': 0.0077, 'w': 0.00025, 'mu': 0.001, 'type': 'straight'},
            'v1.5_w250.h5': {'v': 0.0154, 'w': 0.00025, 'mu': 0.001, 'type': 'straight'},

            # 直通道加密 (6组)
            'v0.4_w150.h5': {'v': 0.004, 'w': 0.00015, 'mu': 0.001, 'type': 'straight_extended'},
            'v0.4_w200.h5': {'v': 0.004, 'w': 0.00020, 'mu': 0.001, 'type': 'straight_extended'},
            'v0.4_w250.h5': {'v': 0.004, 'w': 0.00025, 'mu': 0.001, 'type': 'straight_extended'},
            'v1.2_w150.h5': {'v': 0.012, 'w': 0.00015, 'mu': 0.001, 'type': 'straight_extended'},
            'v1.2_w200.h5': {'v': 0.012, 'w': 0.00020, 'mu': 0.001, 'type': 'straight_extended'},
            'v1.2_w250.h5': {'v': 0.012, 'w': 0.00025, 'mu': 0.001, 'type': 'straight_extended'},

            # T型分岔道 (9组)
            'tj_v0.2_w150.h5': {'v': 0.0015, 'w': 0.00015, 'mu': 0.001, 'type': 'tjunction'},
            'tj_v0.8_w150.h5': {'v': 0.0077, 'w': 0.00015, 'mu': 0.001, 'type': 'tjunction'},
            'tj_v1.5_w150.h5': {'v': 0.0154, 'w': 0.00015, 'mu': 0.001, 'type': 'tjunction'},
            'tj_v0.2_w200.h5': {'v': 0.0015, 'w': 0.00020, 'mu': 0.001, 'type': 'tjunction'},
            'tj_v0.8_w200.h5': {'v': 0.0077, 'w': 0.00020, 'mu': 0.001, 'type': 'tjunction'},
            'tj_v1.5_w200.h5': {'v': 0.0154, 'w': 0.00020, 'mu': 0.001, 'type': 'tjunction'},
            'tj_v0.2_w250.h5': {'v': 0.0015, 'w': 0.00025, 'mu': 0.001, 'type': 'tjunction'},
            'tj_v0.8_w250.h5': {'v': 0.0077, 'w': 0.00025, 'mu': 0.001, 'type': 'tjunction'},
            'tj_v1.5_w250.h5': {'v': 0.0154, 'w': 0.00025, 'mu': 0.001, 'type': 'tjunction'},

            # Y型分岔道 (9组)
            'yj_v0.2_w150.h5': {'v': 0.0015, 'w': 0.00015, 'mu': 0.001, 'type': 'yjunction'},
            'yj_v0.8_w150.h5': {'v': 0.0077, 'w': 0.00015, 'mu': 0.001, 'type': 'yjunction'},
            'yj_v1.5_w150.h5': {'v': 0.0154, 'w': 0.00015, 'mu': 0.001, 'type': 'yjunction'},
            'yj_v0.2_w200.h5': {'v': 0.0015, 'w': 0.00020, 'mu': 0.001, 'type': 'yjunction'},
            'yj_v0.8_w200.h5': {'v': 0.0077, 'w': 0.00020, 'mu': 0.001, 'type': 'yjunction'},
            'yj_v1.5_w200.h5': {'v': 0.0154, 'w': 0.00020, 'mu': 0.001, 'type': 'yjunction'},
            'yj_v0.2_w250.h5': {'v': 0.0015, 'w': 0.00025, 'mu': 0.001, 'type': 'yjunction'},
            'yj_v0.8_w250.h5': {'v': 0.0077, 'w': 0.00025, 'mu': 0.001, 'type': 'yjunction'},
            'yj_v1.5_w250.h5': {'v': 0.0154, 'w': 0.00025, 'mu': 0.001, 'type': 'yjunction'},

            # 不同粘度 (3组)
            'v0.8_w200_mu0.5.h5': {'v': 0.0077, 'w': 0.00020, 'mu': 0.0005, 'type': 'viscosity'},
            'v0.8_w200_mu2.0.h5': {'v': 0.0077, 'w': 0.00020, 'mu': 0.002, 'type': 'viscosity'},
            'v0.8_w200_mu4.0.h5': {'v': 0.0077, 'w': 0.00020, 'mu': 0.004, 'type': 'viscosity'},
        }
        return expected

    def verify_file(self, filename: str, expected_params: dict) -> dict:
        """验证单个文件"""
        filepath = self.data_dir / filename

        result = {
            'filename': filename,
            'exists': False,
            'valid': False,
            'points': 0,
            'issues': []
        }

        if not filepath.exists():
            result['issues'].append('文件不存在')
            return result

        result['exists'] = True

        try:
            with h5py.File(filepath, 'r') as f:
                # 检查数据集
                required_datasets = ['coordinates', 'velocity_u', 'velocity_v', 'pressure']
                for ds in required_datasets:
                    if ds not in f:
                        result['issues'].append(f'缺少数据集: {ds}')

                # 获取数据点数
                if 'coordinates' in f:
                    result['points'] = len(f['coordinates'])

                # 读取数据
                coords = f['coordinates'][:]
                u = f['velocity_u'][:]
                v = f['velocity_v'][:]
                p = f['pressure'][:]

                # 计算Reynolds数
                rho = 1000.0
                v_in = expected_params['v']
                width = expected_params['w']
                mu = expected_params['mu']
                re_expected = rho * v_in * width / mu

                # 检查数据范围
                u_max = np.abs(u).max()
                v_max = np.abs(v).max()
                p_range = p.max() - p.min()

                # 验证速度
                if u_max < v_in * 0.5:
                    result['issues'].append(f'最大速度过低: {u_max:.6f} < {v_in*0.5:.6f}')
                if u_max > v_in * 2.0:
                    result['issues'].append(f'最大速度过高: {u_max:.6f} > {v_in*2.0:.6f}')

                # 验证压力
                if p_range < 0:
                    result['issues'].append('压力范围异常')

                # 验证Reynolds数
                if re_expected > 100:
                    result['issues'].append(f'Reynolds数过高: {re_expected:.1f} > 100')

                # 检查数据完整性
                if np.any(np.isnan(u)) or np.any(np.isnan(v)) or np.any(np.isnan(p)):
                    result['issues'].append('数据包含NaN值')

                if result['points'] < 10000:
                    result['issues'].append(f'数据点过少: {result["points"]} < 10000')

            result['valid'] = len(result['issues']) == 0

        except Exception as e:
            result['issues'].append(f'读取失败: {str(e)}')

        return result

    def run_verification(self):
        """运行完整验证"""
        print("=" * 70)
        print("🔍 扩展数据集验证")
        print("=" * 70)
        print(f"数据目录: {self.data_dir}")
        print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        expected_files = self.get_expected_files()
        total = len(expected_files)

        # 按类型分类
        by_type = {}
        for filename, params in expected_files.items():
            geom_type = params['type']
            if geom_type not in by_type:
                by_type[geom_type] = []
            by_type[geom_type].append((filename, params))

        # 验证各类
        all_results = []
        for geom_type, files in by_type.items():
            print(f"\n{'='*50}")
            print(f"📋 {geom_type.upper()}: {len(files)} 个文件")
            print('='*50)

            for filename, params in files:
                result = self.verify_file(filename, params)
                all_results.append(result)

                # 显示结果
                status = "✅" if result['valid'] else ("⚠️" if result['exists'] else "❌")
                print(f"{status} {filename}", end='')

                if result['exists']:
                    print(f" ({result['points']} 点)", end='')
                    if result['issues']:
                        print(f" - {', '.join(result['issues'][:2])}")
                    else:
                        print()
                else:
                    print()

        # 汇总统计
        self.print_summary(all_results, total)

    def print_summary(self, results: list, total: int):
        """打印汇总报告"""
        print("\n" + "=" * 70)
        print("📊 验证汇总")
        print("=" * 70)

        valid = sum(1 for r in results if r['valid'])
        exists = sum(1 for r in results if r['exists'])
        missing = total - exists
        invalid = exists - valid

        total_points = sum(r['points'] for r in results if r['exists'])

        print(f"\n文件状态:")
        print(f"  ✅ 有效: {valid}/{total}")
        print(f"  ⚠️ 存在缺陷: {invalid}/{total}")
        print(f"  ❌ 缺失: {missing}/{total}")

        print(f"\n数据统计:")
        print(f"  总数据点: {total_points:,}")
        print(f"  平均点/文件: {total_points//exists if exists > 0 else 0:,}")

        print(f"\n数据类型分布:")
        type_counts = {}
        for r in results:
            if r['exists']:
                # 从文件名推断类型
                fn = r['filename']
                if fn.startswith('tj_'):
                    t = 'tjunction'
                elif fn.startswith('yj_'):
                    t = 'yjunction'
                elif 'mu' in fn:
                    t = 'viscosity'
                elif fn.startswith('v1.2') or fn.startswith('v0.4'):
                    t = 'straight_extended'
                else:
                    t = 'straight'
                type_counts[t] = type_counts.get(t, 0) + 1

        for t, count in sorted(type_counts.items()):
            print(f"  {t}: {count} 文件")

        # 保存报告
        report_file = self.data_dir.parent / "logs" / f"verify_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("扩展数据集验证报告\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总文件数: {total}\n")
            f.write(f"有效文件: {valid}\n")
            f.write(f"缺失文件: {missing}\n")
            f.write(f"有缺陷文件: {invalid}\n")
            f.write(f"总数据点: {total_points:,}\n\n")

            f.write("详细结果:\n")
            for r in results:
                f.write(f"\n{r['filename']}: ")
                if not r['exists']:
                    f.write("缺失\n")
                elif r['valid']:
                    f.write(f"✅ 有效 ({r['points']} 点)\n")
                else:
                    f.write(f"⚠️ {', '.join(r['issues'])}\n")

        print(f"\n📋 报告已保存: {report_file}")


def main():
    """主函数"""
    data_dir = Path(__file__).parent.parent.parent / "comsol_simulation" / "data"

    verifier = ExtendedDataVerifier(str(data_dir))
    verifier.run_verification()


if __name__ == "__main__":
    main()
