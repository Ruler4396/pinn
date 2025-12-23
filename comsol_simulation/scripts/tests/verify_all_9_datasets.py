#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量验证9组COMSOL数据
"""

import numpy as np
from pathlib import Path

def verify_all_data():
    """验证所有数据文件"""
    print(f"\n{'='*70}")
    print(f"🔍 批量验证9组COMSOL数据")
    print(f"{'='*70}")

    data_dir = Path("D:/PINNs/comsol_simulation/data")

    # 所有CSV文件
    csv_files = [
        "v05_w150.csv",
        "2025_12_23-2.csv",
        "2025_12_23-3.csv",
        "2025_12_23-4.csv",
        "2025_12_23-5.csv",
        "2025_12_23-6.csv",
        "2025_12_23-7.csv",
        "2025_12_23-8.csv",
        "2025_12_23-9.csv"
    ]

    results = []

    for i, filename in enumerate(csv_files, 1):
        file_path = data_dir / filename

        if not file_path.exists():
            print(f"\n⚠️  文件不存在: {filename}")
            continue

        print(f"\n{'─'*70}")
        print(f"📂 [{i}/9] {filename}")
        print(f"{'─'*70}")

        # 读取数据
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 解析头部
        header = {}
        for line in lines[:10]:
            if line.startswith('%'):
                parts = line[1:].strip().split(',', 1)
                if len(parts) == 2:
                    header[parts[0].strip()] = parts[1].strip().strip('"')

        # 读取数值数据
        data_lines = []
        for line in lines[9:]:
            line = line.strip()
            if line and not line.startswith('%'):
                try:
                    parts = line.split(',')
                    if len(parts) >= 5:
                        data_lines.append([float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])])
                except:
                    continue

        data = np.array(data_lines)
        if len(data) == 0:
            print(f"   ❌ 无数据")
            continue

        x, y, u, v, p = data[:, 0], data[:, 1], data[:, 2], data[:, 3], data[:, 4]

        # 几何尺寸
        x_max = x.max()
        y_max = y.max()
        x_length_mm = x_max * 1000
        y_width_um = y_max * 1e6

        # 速度
        u_max = np.abs(u).max()
        v_max = np.abs(v).max()

        # 压力
        p_min, p_max = p.min(), p.max()

        # 推断参数
        v_inlet_cm = u_max * 100
        width_um = y_width_um

        # 分类
        if 140 < width_um < 160:
            w_str = "w150"
        elif 190 < width_um < 210:
            w_str = "w200"
        elif 240 < width_um < 260:
            w_str = "w250"
        else:
            w_str = f"w{int(width_um)}"

        if 0.08 < v_inlet_cm < 0.12:
            v_str = "v01"
        elif 0.45 < v_inlet_cm < 0.55:
            v_str = "v05"
        elif 0.95 < v_inlet_cm < 1.05:
            v_str = "v10"
        else:
            v_str = f"v{v_inlet_cm:.1f}"

        case_id = f"{v_str}_{w_str}"

        # Reynolds数
        Re = 1000 * u_max * (width_um * 1e-6) / 0.001

        # 检查
        issues = []
        if not (9.9 < x_length_mm < 10.1):
            issues.append(f"长度异常({x_length_mm:.2f}mm)")
        if not (100 < y_width_um < 300):
            issues.append(f"宽度异常({y_width_um:.0f}μm)")
        if not (0 < u_max < 0.02):
            issues.append(f"速度异常({u_max*100:.2f}cm/s)")

        status = "✅" if len(issues) == 0 else "⚠️"

        print(f"\n   📐 几何: L={x_length_mm:.2f}mm, W={y_width_um:.0f}μm")
        print(f"   📊 参数: {v_str}_{w_str} ({v_inlet_cm:.2f}cm/s, {width_um:.0f}μm)")
        print(f"   🧮 Re={Re:.2f}")
        print(f"   📈 数据点: {len(data):,}")
        print(f"   {status} 状态: {'通过' if len(issues) == 0 else ' '.join(issues)}")

        results.append({
            'filename': filename,
            'case_id': case_id,
            'v_inlet_cm': v_inlet_cm,
            'width_um': width_um,
            'Re': Re,
            'points': len(data),
            'valid': len(issues) == 0,
            'issues': issues
        })

    # 总结
    print(f"\n{'='*70}")
    print(f"📋 验证总结")
    print(f"{'='*70}")

    print(f"\n数据清单:")
    print(f"{'文件名':<25} {'类型':<12} {'速度':<10} {'宽度':<10} {'Re':<8} {'数据点':<12} {'状态'}")
    print(f"{'-'*70}")

    valid_count = 0
    for r in results:
        status = "✅" if r['valid'] else "❌"
        if r['valid']:
            valid_count += 1

        print(f"{r['filename']:<25} {r['case_id']:<12} {r['v_inlet_cm']:<10.2f} {r['width_um']:<10.0f} {r['Re']:<8.2f} {r['points']:<12,} {status}")

    print(f"\n{'='*70}")
    print(f"✅ 完成: {valid_count}/9 组数据通过验证")

    if valid_count == 9:
        print(f"🎉 所有数据验证通过！可以转换为HDF5格式")
    else:
        print(f"⚠️  有 {9-valid_count} 组数据存在问题")

    return results


if __name__ == "__main__":
    results = verify_all_data()

    print(f"\n💡 建议的重命名方案:")
    for r in results:
        if r['valid']:
            old_name = r['filename']
            new_name = f"{r['case_id']}.csv"
            if old_name != new_name:
                print(f"   {old_name} → {new_name}")
