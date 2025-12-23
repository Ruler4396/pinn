"""
COMSOL数据验证和转换脚本

验证导出的COMSOL数据格式，提取速度场和压力场信息，
并转换为PINNs训练所需的格式。

用法:
python validate_comsol_data.py [CSV文件路径]

作者: PINNs项目组
时间: 2025-11-19
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


def parse_comsol_csv(file_path):
    """
    解析COMSOL导出的CSV文件

    参数:
        file_path: CSV文件路径

    返回:
        dict: 包含数据信息的字典
    """
    print("=" * 70)
    print("📊 COMSOL数据验证")
    print("=" * 70)

    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return None

    print(f"\n📁 文件: {file_path}")
    file_size = os.path.getsize(file_path)
    print(f"📊 文件大小: {file_size / (1024*1024):.2f} MB")

    # 读取CSV文件
    df = pd.read_csv(file_path, comment='%')
    print(f"\n📋 数据信息:")
    print(f"   行数: {len(df):,}")
    print(f"   列数: {df.shape[1]}")
    print(f"   列名: {list(df.columns)}")

    # 检查列名
    columns = df.columns.tolist()
    print(f"\n🔍 列分析:")
    if 'x' in columns and 'y' in columns:
        print(f"   ✅ 坐标列: x, y")
    else:
        print(f"   ❌ 缺少坐标列")

    if 'u' in columns or 'spf.Ux' in columns:
        print(f"   ✅ 速度u列")
    else:
        print(f"   ❌ 缺少速度u列")

    if 'v' in columns or 'spf.Uy' in columns:
        print(f"   ✅ 速度v列")
    else:
        print(f"   ❌ 缺少速度v列")

    if 'p' in columns or 'spf.p' in columns:
        print(f"   ✅ 压力p列")
    else:
        print(f"   ❌ 缺少压力p列")

    # 统计信息
    print(f"\n📈 数值统计:")
    for col in df.columns:
        if col in ['x', 'y']:
            continue
        print(f"   {col}:")
        print(f"      最小值: {df[col].min():.6e}")
        print(f"      最大值: {df[col].max():.6e}")
        print(f"      平均值: {df[col].mean():.6e}")

    # 检查边界值
    if 'x' in df.columns and 'y' in df.columns:
        print(f"\n📍 几何范围:")
        print(f"   x: [{df['x'].min():.6f}, {df['x'].max():.6f}]")
        print(f"   y: [{df['y'].min():.6f}, {df['y'].max():.6f}]")

    return df


def extract_velocity_pressure(df):
    """
    提取速度和压力数据
    """
    print("\n" + "=" * 70)
    print("⚡ 提取速度和压力数据")
    print("=" * 70)

    # 检查必要的列
    if 'x' not in df.columns or 'y' not in df.columns:
        print("❌ 缺少坐标列")
        return None

    # 提取坐标
    x = df['x'].values
    y = df['y'].values

    # 提取速度u
    if 'u' in df.columns:
        u = df['u'].values
    elif 'spf.Ux' in df.columns:
        u = df['spf.Ux'].values
    else:
        print("⚠️  未找到速度u列")
        u = None

    # 提取速度v
    if 'v' in df.columns:
        v = df['v'].values
    elif 'spf.Uy' in df.columns:
        v = df['spf.Uy'].values
    else:
        print("⚠️  未找到速度v列")
        v = None

    # 提取压力p
    if 'p' in df.columns:
        p = df['p'].values
    elif 'spf.p' in df.columns:
        p = df['spf.p'].values
    else:
        print("⚠️  未找到压力p列")
        p = None

    # 显示提取结果
    print(f"\n✅ 提取结果:")
    print(f"   坐标点: {len(x):,} 个")
    if u is not None:
        print(f"   速度u: [{u.min():.6f}, {u.max():.6f}] m/s")
    if v is not None:
        print(f"   速度v: [{v.min():.6f}, {v.max():.6f}] m/s")
    if p is not None:
        print(f"   压力p: [{p.min():.6f}, {p.max():.6f}] Pa")

    # 验证物理量
    if u is not None and v is not None:
        speed = np.sqrt(u**2 + v**2)
        print(f"   速度大小: [{speed.min():.6f}, {speed.max():.6f}] m/s")

    return {'x': x, 'y': y, 'u': u, 'v': v, 'p': p}


def check_quality(data):
    """检查数据质量"""
    print("\n" + "=" * 70)
    print("🔍 数据质量检查")
    print("=" * 70)

    x, y, u, v, p = data['x'], data['y'], data['u'], data['v'], data['p']

    # 检查NaN
    for key, arr in data.items():
        if arr is not None:
            nan_count = np.isnan(arr).sum()
            print(f"   {key} NaN数量: {nan_count}")
            if nan_count > 0:
                print(f"      ⚠️  数据中存在NaN值")

    # 检查无穷值
    for key, arr in data.items():
        if arr is not None:
            inf_count = np.isinf(arr).sum()
            if inf_count > 0:
                print(f"   {key} 无穷值: {inf_count}")
                print(f"      ⚠️  数据中存在无穷值")

    # 检查速度范围
    if u is not None and v is not None:
        speed = np.sqrt(u**2 + v**2)
        if speed.max() > 1.0:  # 微流控通常 < 1 m/s
            print(f"   ⚠️  最大速度 {speed.max():.3f} m/s 超出典型微流控范围")

    print("\n✅ 质量检查完成")


def save_for_pinns(data, output_dir):
    """
    将数据保存为PINNs训练格式
    """
    print("\n" + "=" * 70)
    print("💾 保存PINNs训练数据")
    print("=" * 70)

    os.makedirs(output_dir, exist_ok=True)

    # 保存原始数据
    output_file = os.path.join(output_dir, 'comsol_data_processed.h5')
    import h5py

    with h5py.File(output_file, 'w') as f:
        f.create_dataset('x', data=data['x'])
        f.create_dataset('y', data=data['y'])
        if data['u'] is not None:
            f.create_dataset('u', data=data['u'])
        if data['v'] is not None:
            f.create_dataset('v', data=data['v'])
        if data['p'] is not None:
            f.create_dataset('p', data=data['p'])

    print(f"✅ 已保存到: {output_file}")

    return output_file


def main():
    """主函数"""
    print("📅 COMSOL数据验证工具")
    print(f"⏰ 时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 获取文件路径
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        # 默认文件
        csv_file = 'comsol_simulation/data/2025_11_19-1.csv'

    # 解析文件
    df = parse_comsol_csv(csv_file)
    if df is None:
        return False

    # 提取数据
    data = extract_velocity_pressure(df)
    if data is None:
        return False

    # 检查质量
    check_quality(data)

    # 保存
    if data['u'] is not None and data['v'] is not None:
        output_file = save_for_pinns(data, 'comsol_simulation/data')
        print(f"\n✅ 处理完成！")
        return True
    else:
        print(f"\n❌ 缺少必要的物理量，无法保存")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
