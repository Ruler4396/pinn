#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量转换所有CSV文件为HDF5格式
"""

import numpy as np
import h5py
from pathlib import Path

def convert_all_csv_to_hdf5():
    """批量转换所有CSV"""
    print(f"\n{'='*70}")
    print(f"🔄 批量转换CSV → HDF5")
    print(f"{'='*70}")

    data_dir = Path("D:/PINNs/comsol_simulation/data")

    # 数据参数配置
    datasets = [
        {
            'csv': 'v0.2_w150.csv',
            'h5': 'v0.2_w150.h5',
            'v_in': 0.0015,  # m/s (0.15 cm/s)
            'W': 150e-6,    # m
            'Re': 0.23
        },
        {
            'csv': 'v0.8_w150.csv',
            'h5': 'v0.8_w150.h5',
            'v_in': 0.0077,  # m/s (0.77 cm/s)
            'W': 150e-6,
            'Re': 1.15
        },
        {
            'csv': 'v1.5_w150.csv',
            'h5': 'v1.5_w150.h5',
            'v_in': 0.0154,  # m/s (1.54 cm/s)
            'W': 150e-6,
            'Re': 2.31
        },
        {
            'csv': 'v0.2_w200.csv',
            'h5': 'v0.2_w200.h5',
            'v_in': 0.0015,
            'W': 200e-6,
            'Re': 0.31
        },
        {
            'csv': 'v0.8_w200.csv',
            'h5': 'v0.8_w200.h5',
            'v_in': 0.0077,
            'W': 200e-6,
            'Re': 1.54
        },
        {
            'csv': 'v1.5_w200.csv',
            'h5': 'v1.5_w200.h5',
            'v_in': 0.0154,
            'W': 200e-6,
            'Re': 3.08
        },
        {
            'csv': 'v0.2_w250.csv',
            'h5': 'v0.2_w250.h5',
            'v_in': 0.0015,
            'W': 250e-6,
            'Re': 0.39
        },
        {
            'csv': 'v0.8_w250.csv',
            'h5': 'v0.8_w250.h5',
            'v_in': 0.0077,
            'W': 250e-6,
            'Re': 1.92
        },
        {
            'csv': 'v1.5_w250.csv',
            'h5': 'v1.5_w250.h5',
            'v_in': 0.0154,
            'W': 250e-6,
            'Re': 3.84
        }
    ]

    success_count = 0

    for ds in datasets:
        csv_path = data_dir / ds['csv']
        h5_path = data_dir / ds['h5']

        if not csv_path.exists():
            print(f"\n⚠️  跳过: {ds['csv']} (不存在)")
            continue

        print(f"\n🔄 {ds['csv']} → {ds['h5']}")

        # 读取CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

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

        # 创建HDF5
        with h5py.File(h5_path, 'w') as f:
            f.create_dataset('x', data=data[:, 0])
            f.create_dataset('y', data=data[:, 1])
            f.create_dataset('u', data=data[:, 2])
            f.create_dataset('v', data=data[:, 3])
            f.create_dataset('p', data=data[:, 4])

            f.attrs['case_id'] = ds['h5'].replace('.h5', '')
            f.attrs['description'] = f'COMSOL microfluidic simulation - {ds["h5"].replace(".h5", "")}'
            f.attrs['total_points'] = len(data)

            f.attrs['inlet_velocity'] = ds['v_in']
            f.attrs['channel_width'] = ds['W']
            f.attrs['channel_length'] = 10e-3
            f.attrs['fluid_density'] = 1000.0
            f.attrs['fluid_viscosity'] = 0.001
            f.attrs['reynolds_number'] = ds['Re']

        size_mb = h5_path.stat().st_size / (1024*1024)
        print(f"   ✅ {len(data):,} 数据点, {size_mb:.2f} MB")
        success_count += 1

    print(f"\n{'='*70}")
    print(f"✅ 转换完成: {success_count}/9 个文件")
    print(f"{'='*70}")

    # 列出所有HDF5文件
    h5_files = list(data_dir.glob("*.h5"))
    total_size = sum(f.stat().st_size for f in h5_files) / (1024**2)

    print(f"\n📁 HDF5文件:")
    for h5 in sorted(h5_files):
        size_mb = h5.stat().st_size / (1024*1024)
        print(f"   {h5.name:<20} {size_mb:>6.2f} MB")

    print(f"\n   总计: {len(h5_files)} 个文件, {total_size:.2f} MB")


if __name__ == "__main__":
    convert_all_csv_to_hdf5()
