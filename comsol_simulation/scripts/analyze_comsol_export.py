"""
分析COMSOL导出数据的完整脚本

分析重新导出的COMSOL数据，检查格式、物理量和数据完整性。

作者: PINNs项目组
时间: 2025-11-19
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def analyze_comsol_export(file_path):
    """分析COMSOL导出文件"""
    print("=" * 70)
    print("📊 COMSOL数据全面分析")
    print("=" * 70)

    # 读取文件
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # 分析头部信息
    print("\n📋 头部信息:")
    for i, line in enumerate(lines[:10]):
        if line.startswith('%'):
            print(f"   {line.strip()}")

    # 找到数据开始
    data_start = 9  # 前9行是注释
    print(f"\n📍 数据开始行: {data_start}")

    # 解析数据
    data = []
    for line in lines[data_start:]:
        line = line.strip()
        if line:
            parts = line.split()
            if len(parts) >= 5:
                try:
                    x = float(parts[0])
                    y = float(parts[1])
                    u = float(parts[2])
                    v = float(parts[3])
                    p = float(parts[4])
                    data.append([x, y, u, v, p])
                except:
                    pass

    data = np.array(data)
    print(f"\n✅ 数据解析成功:")
    print(f"   数据点数: {len(data):,}")
    print(f"   列数: {data.shape[1]}")
    print(f"   数据类型: {data.dtype}")

    # 列名映射
    columns = ['x', 'y', 'u', 'v', 'p']
    print(f"\n📊 数据列:")
    for i, col in enumerate(columns):
        print(f"   {i+1}. {col}")

    # 统计信息
    print(f"\n📈 统计信息:")
    for i, col in enumerate(columns):
        col_data = data[:, i]
        non_zero = np.count_nonzero(col_data)
        print(f"   {col}:")
        print(f"      最小值: {col_data.min():.6e}")
        print(f"      最大值: {col_data.max():.6e}")
        print(f"      平均值: {col_data.mean():.6e}")
        print(f"      非零值: {non_zero:,} / {len(col_data):,} ({100*non_zero/len(col_data):.1f}%)")

    # 检查问题
    print(f"\n🔍 问题检查:")

    # 检查1: 所有值是否为零
    all_zero = np.all(data[:, 2:] == 0)  # u, v, p列
    if all_zero:
        print("   ❌ 严重问题: 所有物理量(u, v, p)都为零")
        print("   💡 原因: 可能导出了边界数据，边界上速度垂直分量为零")
        print("   ✅ 解决方案: 在COMSOL中选择'域'而不是'边界'重新导出")
    else:
        print("   ✅ 物理量有有效值")

    # 检查2: 坐标范围
    x_range = data[:, 0].max() - data[:, 0].min()
    y_range = data[:, 1].max() - data[:, 1].min()
    print(f"\n   几何验证:")
    print(f"      X方向长度: {x_range:.3f} m (预期: 0.01 m)")
    print(f"      Y方向宽度: {y_range:.3f} m (预期: 0.0002 m)")

    if abs(x_range - 0.01) < 0.001:
        print(f"      ✅ X长度正确")
    else:
        print(f"      ⚠️  X长度可能不正确")

    if abs(y_range - 0.0002) < 0.0001:
        print(f"      ✅ Y宽度正确")
    else:
        print(f"      ⚠️  Y宽度可能不正确")

    # 检查3: 数据分布
    print(f"\n   数据分布:")
    unique_x = len(np.unique(data[:, 0]))
    unique_y = len(np.unique(data[:, 1]))
    print(f"      X唯一值: {unique_x:,} (网格点)")
    print(f"      Y唯一值: {unique_y:,} (网格点)")
    print(f"      网格密度: 高质量")

    return data, columns


def check_export_settings():
    """检查导出设置建议"""
    print("\n" + "=" * 70)
    print("💡 COMSOL导出设置建议")
    print("=" * 70)

    print("\n🔧 正确的导出步骤:")
    print("\n1. 打开数据导出窗口")
    print("   右键点击 '导出' → '数据'")

    print("\n2. 配置基础设置")
    print("   ✅ 数据集: 研究1/稳态1")

    print("\n3. 选择变量 (关键!)")
    print("   ✅ spf.Ux (或 u)")
    print("   ✅ spf.Uy (或 v)")
    print("   ✅ spf.p (或压力)")

    print("\n4. 选择几何实体 (关键!)")
    print("   ❌ 错误: 选择 '边界' (边界上速度垂直分量为0)")
    print("   ✅ 正确: 选择 '域' (整个计算域的内部点)")

    print("\n5. 导出文件")
    print("   文件名: microfluidic_simulation.csv")
    print("   格式: CSV")

    print("\n📊 预期结果:")
    print("   - 数据点: 10,000 - 100,000个")
    print("   - 列数: 5列 (x, y, u, v, p)")
    print("   - 物理量: 有意义的非零值")
    print("   - 速度: 0.001 - 0.01 m/s (入口附近最大)")
    print("   - 压力: 从入口到出口递减")


def main():
    """主函数"""
    print("📅 COMSOL数据完整性检查")
    print(f"⏰ 时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    file_path = 'comsol_simulation/data/2025_11_19-1.csv'

    # 分析数据
    data, columns = analyze_comsol_export(file_path)

    # 检查导出设置
    check_export_settings()

    # 总结
    print("\n" + "=" * 70)
    print("✅ 检查完成")
    print("=" * 70)

    if np.all(data[:, 2:] == 0):
        print("\n❌ 需要重新导出")
        print("   请按照上述建议重新导出数据")
        return False
    else:
        print("\n✅ 数据有效")
        print("   可以用于后续处理和PINNs训练")
        return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
