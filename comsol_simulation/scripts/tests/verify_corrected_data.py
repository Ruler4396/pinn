#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证修正后的COMSOL数据

检查几何尺寸、物理参数是否正确
"""

import numpy as np
from pathlib import Path

def verify_corrected_data(file_path):
    """验证修正后的数据"""
    print(f"\n{'='*70}")
    print(f"🔍 修正后的COMSOL数据验证")
    print(f"{'='*70}")

    # 读取数据
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 解析头部
    header = {}
    for line in lines[:10]:
        if line.startswith('%'):
            parts = line[1:].strip().split(',', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip().strip('"')
                header[key] = value

    print(f"\n📋 文件信息:")
    print(f"   模型: {header.get('Model', 'N/A')}")
    print(f"   日期: {header.get('Date', 'N/A')}")
    print(f"   数据点: {header.get('Nodes', 'N/A')}")

    # 读取数值数据
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

    print(f"\n📐 几何尺寸验证:")

    # X坐标（通道长度）
    x_min, x_max = x.min(), x.max()
    x_length_mm = x_max * 1000

    print(f"   X坐标范围:")
    print(f"      [{x_min:.6f}, {x_max:.6f}] m")
    print(f"      通道长度: {x_length_mm:.2f} mm")

    if 9.9 < x_length_mm < 10.1:
        print(f"      ✅ 长度正确 (~10 mm)")
    else:
        print(f"      ❌ 长度异常！预期10mm")

    # Y坐标（通道宽度）
    y_min, y_max = y.min(), y.max()
    y_width_um = y_max * 1e6  # 转换为微米

    print(f"\n   Y坐标范围:")
    print(f"      [{y_min:.6e}, {y_max:.6e}] m")
    print(f"      通道宽度: {y_width_um:.1f} μm")

    if 140 < y_width_um < 160:
        print(f"      ✅ 宽度正确 (~150 μm)")
    elif 190 < y_width_um < 210:
        print(f"      ✅ 宽度正确 (~200 μm)")
    elif 240 < y_width_um < 260:
        print(f"      ✅ 宽度正确 (~250 μm)")
    else:
        print(f"      ❌ 宽度异常！预期150/200/250 μm")

    print(f"\n📊 物理场验证:")

    # 速度场
    speed = np.sqrt(u**2 + v**2)
    u_max = np.abs(u).max()

    print(f"   速度 u (主流方向):")
    print(f"      范围: [{u.min():.6f}, {u.max():.6f}] m/s")
    print(f"      最大: {u_max:.6f} m/s = {u_max*100:.2f} cm/s")

    # 推断入口速度
    inlet_region = x < 0.001
    if np.any(inlet_region):
        v_inlet = u[inlet_region].mean()
        print(f"      推断入口速度: ~{v_inlet*100:.2f} cm/s")

    print(f"\n   速度 v (横向):")
    print(f"      范围: [{v.min():.6e}, {v.max():.6e}] m/s")
    v_ratio = np.abs(v).max() / (u_max + 1e-10)
    print(f"      横向/纵向比: {v_ratio:.3f}")
    if v_ratio < 0.1:
        print(f"      ✅ 横向速度小（层流特征）")

    # 压力场
    print(f"\n   压力 p:")
    print(f"      范围: [{p.min():.2f}, {p.max():.2f}] Pa")
    print(f"      压降: {p.max() - p.min():.2f} Pa")
    if p.max() > p.min():
        print(f"      ✅ 压力从入口到出口递减")

    # Reynolds数计算
    print(f"\n🧮 Reynolds数:")
    v_inlet_cm = u_max * 100
    width_um = y_width_um
    rho = 1000  # kg/m³
    mu = 0.001  # Pa·s
    Re = rho * u_max * (width_um * 1e-6) / mu

    print(f"   Re = {Re:.2f}")
    if Re < 2300:
        print(f"      ✅ 层流状态 (Re < 2300)")
    else:
        print(f"      ⚠️  Re偏高，可能不是层流")

    # 数据完整性
    print(f"\n🔍 数据完整性:")
    nan_count = np.isnan(data).sum()
    inf_count = np.isinf(data).sum()
    print(f"   NaN值: {nan_count}")
    print(f"   无穷值: {inf_count}")
    if nan_count == 0 and inf_count == 0:
        print(f"      ✅ 无无效值")

    # 分类数据
    print(f"\n🎯 数据分类:")
    if 0.45 < v_inlet_cm < 0.55:
        if 140 < width_um < 160:
            case_id = "v05_w150"
            desc = "入口速度 0.5 cm/s, 通道宽度 150 μm"
        elif 190 < width_um < 210:
            case_id = "v05_w200"
            desc = "入口速度 0.5 cm/s, 通道宽度 200 μm"
        elif 240 < width_um < 260:
            case_id = "v05_w250"
            desc = "入口速度 0.5 cm/s, 通道宽度 250 μm"
        else:
            case_id = f"v05_w{int(width_um)}"
            desc = f"入口速度 0.5 cm/s, 通道宽度 {width_um:.0f} μm"
    elif 0.95 < v_inlet_cm < 1.05:
        if 140 < width_um < 160:
            case_id = "v10_w150"
            desc = "入口速度 1.0 cm/s, 通道宽度 150 μm"
        elif 190 < width_um < 210:
            case_id = "v10_w200"
            desc = "入口速度 1.0 cm/s, 通道宽度 200 μm"
        elif 240 < width_um < 260:
            case_id = "v10_w250"
            desc = "入口速度 1.0 cm/s, 通道宽度 250 μm"
        else:
            case_id = f"v10_w{int(width_um)}"
            desc = f"入口速度 1.0 cm/s, 通道宽度 {width_um:.0f} μm"
    elif 0.08 < v_inlet_cm < 0.12:
        if 140 < width_um < 160:
            case_id = "v01_w150"
            desc = "入口速度 0.1 cm/s, 通道宽度 150 μm"
        elif 190 < width_um < 210:
            case_id = "v01_w200"
            desc = "入口速度 0.1 cm/s, 通道宽度 200 μm"
        elif 240 < width_um < 260:
            case_id = "v01_w250"
            desc = "入口速度 0.1 cm/s, 通道宽度 250 μm"
        else:
            case_id = f"v01_w{int(width_um)}"
            desc = f"入口速度 0.1 cm/s, 通道宽度 {width_um:.0f} μm"
    else:
        case_id = f"v{v_inlet_cm:.1f}_w{int(width_um)}"
        desc = f"入口速度 {v_inlet_cm:.1f} cm/s, 通道宽度 {width_um:.0f} μm"

    print(f"   类型: {case_id}")
    print(f"   参数: {desc}")

    # 总结
    print(f"\n{'='*70}")
    print(f"📋 验证总结:")
    print(f"{'='*70}")

    all_ok = True

    # 检查几何尺寸
    if not (9.9 < x_length_mm < 10.1):
        print(f"❌ X坐标范围异常")
        all_ok = False
    if not (100 < y_width_um < 300):
        print(f"❌ Y坐标范围异常")
        all_ok = False

    # 检查物理场
    if not (0 < u_max < 0.1):
        print(f"❌ 速度范围异常")
        all_ok = False
    if not (p.max() > p.min()):
        print(f"❌ 压力分布异常")
        all_ok = False

    # 检查数据完整性
    if nan_count > 0 or inf_count > 0:
        print(f"❌ 数据含无效值")
        all_ok = False

    if all_ok:
        print(f"✅ 所有检查通过！")
        print(f"\n📁 建议重命名为: {case_id}.csv")
        return {
            'case_id': case_id,
            'v_inlet_cm': v_inlet_cm,
            'width_um': width_um,
            'Re': Re,
            'points': len(data),
            'valid': True
        }
    else:
        print(f"⚠️  发现问题，请检查")
        return {'valid': False}


if __name__ == "__main__":
    data_file = Path("D:/PINNs/comsol_simulation/data/2025_12_23-1.csv")

    if data_file.exists():
        result = verify_corrected_data(data_file)
    else:
        print(f"❌ 文件不存在: {data_file}")
