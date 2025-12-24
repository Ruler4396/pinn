#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证新生成的数据集

验证:
- T型分岔道数据 (9组)
- 不同粘度数据 (3组)
"""

import h5py
import numpy as np
from pathlib import Path

def verify_file(filepath):
    """验证单个数据文件"""
    try:
        with h5py.File(filepath, 'r') as f:
            x = f['x'][:]
            y = f['y'][:]
            u = f['u'][:]
            v = f['v'][:]
            p = f['p'][:]

            # 获取元数据
            case_id = f.attrs.get('case_id', 'N/A')
            reynolds = f.attrs.get('reynolds_number', -1)

            # 基本检查
            issues = []

            # 1. 数据完整性
            if np.isnan(u).sum() > 0 or np.isnan(v).sum() > 0 or np.isnan(p).sum() > 0:
                issues.append("存在NaN值")

            # 2. 数据非零
            if np.abs(u).max() < 1e-10:
                issues.append("速度为零")

            # 3. 压力范围
            p_range = p.max() - p.min()
            if p_range < 1e-5:
                issues.append("压力无变化")

            # 4. Reynolds数合理性
            if not (0 < reynolds < 10):
                issues.append(f"Reynolds数异常: {reynolds:.2f}")

            # 5. 几何范围
            x_range_mm = (x.max() - x.min()) * 1000
            y_range_um = (y.max() - y.min()) * 1e6

            status = "✅" if len(issues) == 0 else "⚠️"

            return {
                'file': filepath.name,
                'case_id': case_id,
                'points': len(x),
                'x_range_mm': x_range_mm,
                'y_range_um': y_range_um,
                'u_max': u.max(),
                'p_range': p_range,
                'reynolds': reynolds,
                'status': status,
                'issues': issues
            }
    except Exception as e:
        return {
            'file': filepath.name,
            'status': '❌',
            'issues': [f"读取失败: {e}"]
        }

def main():
    print("=" * 70)
    print("🔍 验证新生成的数据集")
    print("=" * 70)

    data_dir = Path("D:/PINNs/comsol_simulation/data")

    # T型分岔道数据
    tj_files = [
        "tj_v0.15_w150.h5", "tj_v0.15_w200.h5", "tj_v0.15_w250.h5",
        "tj_v0.77_w150.h5", "tj_v0.77_w200.h5", "tj_v0.77_w250.h5",
        "tj_v1.54_w150.h5", "tj_v1.54_w200.h5", "tj_v1.54_w250.h5"
    ]

    # 粘度数据
    visc_files = [
        "v0.77_w200_mu0.h5", "v0.77_w200_mu2.h5", "v0.77_w200_mu4.h5"
    ]

    all_files = [('T型分岔道', tj_files), ('不同粘度', visc_files)]

    total_passed = 0
    total_files = 0

    for category, files in all_files:
        print(f"\n{'='*70}")
        print(f"📂 {category}数据")
        print('='*70)

        results = []
        for filename in files:
            filepath = data_dir / filename
            total_files += 1
            result = verify_file(filepath)
            results.append(result)

            if result['status'] in ['✅']:
                total_passed += 1

            # 打印结果
            issues_str = "; ".join(result['issues']) if result['issues'] else "通过"
            print(f"{result['status']:3} {result['file']:<25} {result['points']:>6}点  Re={result.get('reynolds', 0):.2f}  {issues_str}")

    # 总结
    print(f"\n{'='*70}")
    print("📋 验证总结")
    print('='*70)
    print(f"✅ 通过: {total_passed}/{total_files}")
    print(f"⚠️ 问题: {total_files - total_passed}/{total_files}")

    if total_passed == total_files:
        print("\n🎉 所有数据验证通过!")
        return True
    else:
        print(f"\n⚠️ 有 {total_files - total_passed} 个文件存在问题")
        return False


if __name__ == "__main__":
    success = main()
