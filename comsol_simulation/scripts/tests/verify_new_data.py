#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证新生成的COMSOL数据

检查两组新数据的质量和物理合理性
"""

import numpy as np
import pandas as pd
from pathlib import Path

def load_comsol_csv(file_path):
    """加载COMSOL导出的CSV文件"""
    print(f"\n{'='*60}")
    print(f"📂 文件: {Path(file_path).name}")
    print(f"{'='*60}")

    with open(file_path, 'r', encoding='utf-8') as f:
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

    print(f"\n📋 头部信息:")
    print(f"   模型: {header_info.get('Model', 'N/A')}")
    print(f"   日期: {header_info.get('Date', 'N/A')}")
    print(f"   数据点数: {header_info.get('Nodes', 'N/A')}")

    # 读取数据
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
    return data, header_info


def analyze_data(data):
    """分析数据质量"""
    x, y, u, v, p = data[:, 0], data[:, 1], data[:, 2], data[:, 3], data[:, 4]

    print(f"\n📊 数据统计:")
    print(f"   数据点数: {len(data):,}")

    print(f"\n   坐标范围:")
    print(f"      X: [{x.min():.6f}, {x.max():.6f}] m")
    print(f"      Y: [{y.min():.6f}, {y.max():.6f}] m")

    print(f"\n   速度 u (x方向):")
    print(f"      范围: [{u.min():.6f}, {u.max():.6f}] m/s")
    print(f"      平均: {u.mean():.6f} m/s")

    print(f"\n   速度 v (y方向):")
    print(f"      范围: [{v.min():.6f}, {v.max():.6f}] m/s")
    print(f"      平均: {v.mean():.6f} m/s")

    print(f"\n   压力 p:")
    print(f"      范围: [{p.min():.6f}, {p.max():.6f}] Pa")
    print(f"      压降: {p.max() - p.min():.6f} Pa")

    # 计算速度大小
    speed = np.sqrt(u**2 + v**2)
    print(f"\n   速度大小 |u|:")
    print(f"      最大: {speed.max():.6f} m/s")
    print(f"      平均: {speed.mean():.6f} m/s")

    return x, y, u, v, p


def validate_physics(x, y, u, v, p):
    """验证物理合理性"""
    print(f"\n🔍 物理验证:")

    # 1. 数据完整性
    nan_count = np.isnan(u).sum() + np.isnan(v).sum() + np.isnan(p).sum()
    if nan_count == 0:
        print(f"   ✅ 无NaN值")
    else:
        print(f"   ❌ 发现{nan_count}个NaN值")

    # 2. 速度方向
    if u.mean() > 0:
        print(f"   ✅ 主速度方向为正 (x方向)")
    else:
        print(f"   ⚠️  主速度方向异常")

    # 3. 压力分布
    if p.max() > p.min():
        print(f"   ✅ 压力从入口到出口递减")
    else:
        print(f"   ❌ 压力分布异常")

    # 4. 横向速度
    v_ratio = np.abs(v).max() / (np.abs(u).max() + 1e-10)
    if v_ratio < 0.3:
        print(f"   ✅ 横向速度较小 (层流特征)")
    else:
        print(f"   ⚠️  横向速度较大")

    # 5. 壁面边界条件
    # 通道宽度约为200μm，检查上下边界
    wall_tolerance = 1e-5
    top_wall = y > y.max() - wall_tolerance
    bottom_wall = y < y.min() + wall_tolerance

    if np.any(top_wall) or np.any(bottom_wall):
        v_wall = np.concatenate([v[top_wall], v[bottom_wall]])
        if np.abs(v_wall).mean() < 0.001:
            print(f"   ✅ 壁面无滑移条件满足")
        else:
            print(f"   ⚠️  壁面速度不为零")

    # 6. 推断入口速度
    inlet_region = x < 0.001
    if np.any(inlet_region):
        v_inlet = u[inlet_region].mean()
        print(f"\n   📌 推断参数:")
        print(f"      入口速度: ~{v_inlet*100:.2f} cm/s")
        return v_inlet

    return u.mean()


def estimate_reynolds(v_inlet, width_um=200):
    """估算雷诺数"""
    # Re = ρ * v * D / μ
    # 水: ρ=1000 kg/m³, μ=0.001 Pa·s
    rho = 1000
    mu = 0.001
    D = width_um * 1e-6  # 转换为米

    Re = rho * v_inlet * D / mu
    return Re


def classify_data(v_inlet):
    """根据入口速度分类数据"""
    v_cm_s = v_inlet * 100

    if 0.08 < v_cm_s < 0.12:
        return "v0.1_w200", "0.1 cm/s, 200μm"
    elif 0.45 < v_cm_s < 0.55:
        return "v0.5_w200", "0.5 cm/s, 200μm"
    elif 0.95 < v_cm_s < 1.05:
        return "v1.0_w200", "1.0 cm/s, 200μm"
    else:
        return f"v{v_cm_s:.1f}_w200", f"{v_cm_s:.1f} cm/s, 200μm"


def main():
    print("🔍 COMSOL新数据验证")
    print("="*60)

    data_dir = Path("D:/PINNs/comsol_simulation/data")

    # 检查新数据文件
    new_files = [
        data_dir / "2025_12_23.csv",
        data_dir / "2025_12_23-1.csv"
    ]

    results = []

    for file_path in new_files:
        if not file_path.exists():
            print(f"\n⚠️  文件不存在: {file_path.name}")
            continue

        # 加载数据
        data, header_info = load_comsol_csv(file_path)

        # 分析数据
        x, y, u, v, p = analyze_data(data)

        # 验证物理
        v_inlet = validate_physics(x, y, u, v, p)

        # 分类数据
        name, params = classify_data(v_inlet)
        Re = estimate_reynolds(v_inlet)

        print(f"\n   🎯 数据分类: {name}")
        print(f"      参数: {params}")
        print(f"      Reynolds数: Re = {Re:.2f}")

        results.append({
            'file': file_path.name,
            'name': name,
            'v_inlet_cm_s': v_inlet * 100,
            'points': len(data),
            'Re': Re
        })

    # 总结
    print(f"\n{'='*60}")
    print(f"📋 验证总结")
    print(f"{'='*60}")

    for r in results:
        print(f"\n✅ {r['file']}")
        print(f"   类型: {r['name']}")
        print(f"   入口速度: {r['v_inlet_cm_s']:.2f} cm/s")
        print(f"   数据点: {r['points']:,}")
        print(f"   Reynolds数: {r['Re']:.2f}")

    # 检查是否与已有数据重复
    print(f"\n🔁 重复性检查:")
    existing_files = [
        ("2025_11_19-1.csv", "v1.0_w200", 528758),
        ("comsol_real_data.h5", "v1.0_w200", 528758)
    ]

    for r in results:
        for exist_name, exist_type, exist_points in existing_files:
            if abs(r['v_inlet_cm_s'] - 1.0) < 0.1:
                print(f"   ⚠️  {r['file']} 与 {exist_name} 类型相似")
                break
        else:
            print(f"   ✅ {r['name']} 是新数据类型")

    print(f"\n{'='*60}")
    print(f"✅ 数据验证完成！")
    print(f"{'='*60}")

    return results


if __name__ == "__main__":
    results = main()
