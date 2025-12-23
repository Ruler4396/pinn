#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将CSV格式的COMSOL数据转换为HDF5格式

用于PINNs训练的标准数据格式
"""

import numpy as np
import h5py
from pathlib import Path
import argparse


def convert_csv_to_hdf5(csv_path, hdf5_path, case_id, params):
    """
    将COMSOL导出的CSV文件转换为HDF5格式

    Args:
        csv_path: CSV文件路径
        hdf5_path: 输出HDF5文件路径
        case_id: 案例标识 (如 "v01_w200")
        params: 参数字典
    """
    print(f"\n{'='*60}")
    print(f"🔄 转换: {Path(csv_path).name} → {Path(hdf5_path).name}")
    print(f"{'='*60}")

    # 读取CSV文件
    print(f"\n📂 读取CSV文件...")
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 解析头部信息
    header_info = {}
    for line in lines[:10]:
        if line.startswith('%'):
            parts = line[1:].strip().split(',', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip().strip('"')
                header_info[key] = value

    # 读取数据
    data_lines = []
    for line in lines[9:]:
        line = line.strip()
        if line and not line.startswith('%'):
            try:
                parts = line.split(',')
                if len(parts) >= 5:
                    x = float(parts[0])
                    y = float(parts[1])
                    u = float(parts[2])
                    v = float(parts[3])
                    p = float(parts[4])
                    data_lines.append([x, y, u, v, p])
            except:
                continue

    data = np.array(data_lines)
    x, y, u, v, p = data[:, 0], data[:, 1], data[:, 2], data[:, 3], data[:, 4]

    print(f"   数据点数: {len(data):,}")

    # 创建HDF5文件
    print(f"\n💾 创建HDF5文件...")
    with h5py.File(hdf5_path, 'w') as f:
        # 保存数据
        f.create_dataset('x', data=x)
        f.create_dataset('y', data=y)
        f.create_dataset('u', data=u)
        f.create_dataset('v', data=v)
        f.create_dataset('p', data=p)

        # 保存元数据
        f.attrs['case_id'] = case_id
        f.attrs['description'] = f'COMSOL microfluidic simulation - {case_id}'
        f.attrs['total_points'] = len(data)
        f.attrs['source_file'] = Path(csv_path).name

        # 保存物理参数
        for key, value in params.items():
            if isinstance(value, (int, float)):
                f.attrs[key] = value
            else:
                f.attrs[key] = str(value)

    # 统计信息
    speed = np.sqrt(u**2 + v**2)
    reynolds = params.get('reynolds_number', 0)

    print(f"\n📊 数据统计:")
    print(f"   入口速度: {params['inlet_velocity']*100:.2f} cm/s")
    print(f"   通道宽度: {params['channel_width']*1e6:.0f} μm")
    print(f"   Reynolds数: {reynolds:.2f}")
    print(f"   速度范围: [{speed.min():.6f}, {speed.max():.6f}] m/s")
    print(f"   压力范围: [{p.min():.6f}, {p.max():.6f}] Pa")

    # 文件大小
    size_mb = Path(hdf5_path).stat().st_size / (1024*1024)
    print(f"\n✅ 转换完成!")
    print(f"   文件大小: {size_mb:.2f} MB")
    print(f"   保存位置: {hdf5_path}")

    return True


def main():
    """主函数"""
    data_dir = Path("D:/PINNs/comsol_simulation/data")

    # 定义要转换的文件
    conversions = [
        {
            'csv': data_dir / 'v01_w200.csv',
            'h5': data_dir / 'v01_w200.h5',
            'case_id': 'v01_w200',
            'params': {
                'inlet_velocity': 0.001,  # m/s (0.1 cm/s)
                'channel_width': 200e-6,   # m (200 μm)
                'channel_length': 10e-3,   # m (10 mm)
                'fluid_density': 1000.0,   # kg/m³
                'fluid_viscosity': 0.001,  # Pa·s
                'reynolds_number': 0.20
            }
        },
        {
            'csv': data_dir / 'v05_w200.csv',
            'h5': data_dir / 'v05_w200.h5',
            'case_id': 'v05_w200',
            'params': {
                'inlet_velocity': 0.005,  # m/s (0.5 cm/s)
                'channel_width': 200e-6,   # m (200 μm)
                'channel_length': 10e-3,   # m (10 mm)
                'fluid_density': 1000.0,   # kg/m³
                'fluid_viscosity': 0.001,  # Pa·s
                'reynolds_number': 0.99
            }
        }
    ]

    print("🚀 COMSOL数据转换为HDF5格式")
    print("="*60)

    success_count = 0
    for conv in conversions:
        if not conv['csv'].exists():
            print(f"\n⚠️  文件不存在: {conv['csv']}")
            continue

        if convert_csv_to_hdf5(
            conv['csv'],
            conv['h5'],
            conv['case_id'],
            conv['params']
        ):
            success_count += 1

    print(f"\n{'='*60}")
    print(f"✅ 转换完成: {success_count}/{len(conversions)} 个文件")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
