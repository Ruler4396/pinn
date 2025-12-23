#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
转换单个CSV文件为HDF5格式
"""

import numpy as np
import h5py
from pathlib import Path

def convert_single_file(csv_path, hdf5_path, case_id, params):
    """转换单个CSV文件"""
    print(f"\n{'='*60}")
    print(f"🔄 转换: {Path(csv_path).name} → {Path(hdf5_path).name}")
    print(f"{'='*60}")

    # 读取CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 解析数据
    data_lines = []
    for line in lines[9:]:
        line = line.strip()
        if line and not line.startswith('%'):
            try:
                parts = line.split(',')
                if len(parts) >= 5:
                    x, y, u, v, p = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                    data_lines.append([x, y, u, v, p])
            except:
                continue

    data = np.array(data_lines)
    x, y, u, v, p = data[:, 0], data[:, 1], data[:, 2], data[:, 3], data[:, 4]

    # 创建HDF5
    with h5py.File(hdf5_path, 'w') as f:
        f.create_dataset('x', data=x)
        f.create_dataset('y', data=y)
        f.create_dataset('u', data=u)
        f.create_dataset('v', data=v)
        f.create_dataset('p', data=p)

        f.attrs['case_id'] = case_id
        f.attrs['description'] = f'COMSOL microfluidic simulation - {case_id}'
        f.attrs['total_points'] = len(data)

        for key, value in params.items():
            if isinstance(value, (int, float)):
                f.attrs[key] = value
            else:
                f.attrs[key] = str(value)

    size_mb = Path(hdf5_path).stat().st_size / (1024*1024)
    print(f"✅ 转换完成!")
    print(f"   数据点: {len(data):,}")
    print(f"   文件大小: {size_mb:.2f} MB")
    print(f"   保存位置: {hdf5_path}")


if __name__ == "__main__":
    csv_file = Path("D:/PINNs/comsol_simulation/data/v05_w150.csv")
    h5_file = Path("D:/PINNs/comsol_simulation/data/v05_w150.h5")

    params = {
        'inlet_velocity': 0.005,  # m/s (0.5 cm/s)
        'channel_width': 150e-6,   # m (150 μm)
        'channel_length': 10e-3,   # m (10 mm)
        'fluid_density': 1000.0,    # kg/m³
        'fluid_viscosity': 0.001,  # Pa·s
        'reynolds_number': 1.15
    }

    convert_single_file(csv_file, h5_file, 'v05_w150', params)

    print(f"\n{'='*60}")
    print(f"✅ 准备就绪！可以使用 v05_w150.h5 进行PINNs训练")
    print(f"{'='*60}")
