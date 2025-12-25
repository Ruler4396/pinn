#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证新生成的6组HDF5数据
"""

import h5py
import numpy as np
from pathlib import Path

def verify_file(filepath):
    """验证单个HDF5文件"""
    try:
        with h5py.File(filepath, 'r') as f:
            coords = f['coordinates'][:]
            u = f['velocity_u'][:]
            v = f['velocity_v'][:]
            p = f['pressure'][:]

            print(f"  ✅ {filepath.name}:")
            print(f"     数据点: {len(coords):,}")
            print(f"     X范围: [{coords[:, 0].min()*1000:.2f}, {coords[:, 0].max()*1000:.2f}] mm")
            print(f"     Y范围: [{coords[:, 1].min()*1e6:.1f}, {coords[:, 1].max()*1e6:.1f}] μm")
            print(f"     U范围: [{u.min():.6f}, {u.max():.6f}] m/s")
            print(f"     V范围: [{v.min():.6f}, {v.max():.6f}] m/s")
            print(f"     P范围: [{p.min():.2f}, {p.max():.2f}] Pa")

            # 检查数据完整性
            if np.any(np.isnan(u)) or np.any(np.isnan(v)) or np.any(np.isnan(p)):
                print(f"     ⚠️ 警告: 数据包含NaN值")
                return False

        return True
    except Exception as e:
        print(f"  ❌ {filepath.name}: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 验证新生成的6组数据")
    print("=" * 60)

    data_dir = Path(__file__).parent.parent.parent / "data"

    new_files = [
        "v0.4_w150.h5", "v0.4_w200.h5", "v0.4_w250.h5",
        "v1.2_w150.h5", "v1.2_w200.h5", "v1.2_w250.h5"
    ]

    total_points = 0
    valid_count = 0

    for filename in new_files:
        filepath = data_dir / filename
        if filepath.exists():
            if verify_file(filepath):
                valid_count += 1
                # 获取数据点数
                with h5py.File(filepath, 'r') as f:
                    total_points += len(f['coordinates'])
            print()
        else:
            print(f"  ❌ {filename}: 文件不存在\n")

    print("=" * 60)
    print("📊 汇总")
    print("=" * 60)
    print(f"有效文件: {valid_count}/6")
    print(f"总数据点: {total_points:,}")
    print(f"平均点/文件: {total_points//valid_count if valid_count > 0 else 0:,}")

    return valid_count == 6

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
