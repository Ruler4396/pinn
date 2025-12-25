#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建T型和Y型分岔道的基准MPH模型文件

这些模型文件预先配置好所有物理场、边界、网格设置。
后续通过API修改参数（入口速度、通道宽度等）即可生成数据。

使用方法:
1. 运行此脚本生成基准模型文件
2. (可选) 在COMSOL GUI中打开验证
3. 使用参数化脚本批量生成数据
"""

import sys
import numpy as np
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

try:
    import mph
    print("✅ mph模块导入成功")
except ImportError:
    print("❌ mph模块未安装")
    sys.exit(1)


def create_tjunction_base_model():
    """创建T型分岔道基准模型"""
    print("\n=== 创建T型分岔道基准模型 ===")

    client = mph.start()
    model = client.create('tjunction_base')
    java_model = model.java

    # 创建几何 (毫米单位)
    geom = java_model.geom().create('geom1', 2)
    geom.lengthUnit('mm')

    # 尺寸参数 (可后续修改)
    L_main = 10  # mm - 主通道长度
    L_side = 5   # mm - 侧通道长度
    W = 0.2      # mm - 通道宽度 (200μm)

    print(f"   几何尺寸: {L_main}×{L_side} mm, 宽度={W} mm")

    # 左半段 (入口到分岔点)
    rect_left = geom.feature().create('rect_left', 'Rectangle')
    rect_left.set('size', [f'{L_main/2}', f'{W}'])
    rect_left.set('pos', ['0', '0'])
    rect_left.label('入口通道')

    # 右半段 (分岔点到出口1)
    rect_right = geom.feature().create('rect_right', 'Rectangle')
    rect_right.set('size', [f'{L_main/2}', f'{W}'])
    rect_right.set('pos', [f'{L_main/2}', '0'])
    rect_right.label('出口通道1')

    # 侧通道 (分岔点到出口2)
    rect_side = geom.feature().create('rect_side', 'Rectangle')
    rect_side.set('size', [f'{W}', f'{L_side}'])
    rect_side.set('pos', [f'{L_main/2 - W/2}', f'{W}'])
    rect_side.label('出口通道2')

    # 运行几何并合并
    geom.run('rect_left')
    geom.run('rect_right')
    geom.run('rect_side')

    union = geom.feature().create('union1', 'Union')
    union.selection('input').all()
    geom.run()

    print("   ✅ 几何创建完成")

    # === 物理场设置 ===
    physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')

    # 流体属性
    fp = physics.feature('fp1')
    fp.set('mu_mat', 'userdef')
    fp.set('mu', '0.001 [Pa*s]')      # 水的粘度
    fp.set('rho_mat', 'userdef')
    fp.set('rho', '1000 [kg/m^3]')     # 水的密度

    print("   ✅ 物理场设置完成")

    # === 边界条件 ===
    # 注意：Union后边界编号会改变，需要根据实际情况调整
    # 建议在GUI中验证并设置正确的边界编号

    # 入口 - 左边界 (假设为边界1)
    inlet = physics.feature().create('in1', 'Inlet')
    inlet.set('U0in', '0.0077')  # 0.77 cm/s = 0.0077 m/s (可修改)
    inlet.label('入口边界')
    # 入口边界编号需要在GUI中验证后设置
    # inlet.selection().set([正确的边界编号])

    # 出口1 - 右边界
    outlet1 = physics.feature().create('out1', 'Outlet')
    outlet1.set('p0', '0')
    outlet1.label('出口1边界')
    # outlet1.selection().set([正确的边界编号])

    # 出口2 - 上边界
    outlet2 = physics.feature().create('out2', 'Outlet')
    outlet2.set('p0', '0')
    outlet2.label('出口2边界')
    # outlet2.selection().set([正确的边界编号])

    # 壁面 - 其余边界
    wall = physics.feature().create('wall1', 'Wall')
    wall.label('壁面边界')
    # wall.selection().all()  # 选择所有边界，然后在GUI中取消入口/出口

    print("   ⚠️  边界条件节点已创建，请在GUI中验证并设置正确的边界编号")

    # === 网格 ===
    mesh = java_model.mesh().create('mesh1', 'geom1')
    mesh.autoMeshSize(5)  # 常规网格
    print("   ✅ 网格设置完成")

    # === 研究 ===
    study = java_model.study().create('std1')
    study.feature().create('stat', 'Stationary')
    print("   ✅ 研究步骤创建完成")

    # === 参数定义 (方便后续修改) ===
    params = java_model.param()
    params.set('v_in', '0.0077 [m/s]')     # 入口速度
    params.set('width', '0.0002 [m]')       # 通道宽度 (200μm)
    params.set('L_main', '0.01 [m]')        # 主通道长度
    params.set('L_side', '0.005 [m]')       # 侧通道长度
    params.set('viscosity', '0.001 [Pa*s]') # 粘度
    params.set('density', '1000 [kg/m^3]')  # 密度
    print("   ✅ 参数定义完成")

    # 保存模型
    output_path = project_root / 'comsol_simulation' / 'models' / 'tjunction_base.mph'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(output_path))
    print(f"   ✅ 模型已保存: {output_path}")

    client.clear()
    return output_path


def create_yjunction_base_model():
    """创建Y型分岔道基准模型（正确的Y形）"""
    print("\n=== 创建Y型分岔道基准模型 ===")

    client = mph.start()
    model = client.create('yjunction_base')
    java_model = model.java

    # 创建几何
    geom = java_model.geom().create('geom1', 2)
    geom.lengthUnit('mm')

    L_main = 10    # mm - 主通道长度（入口到分岔点）
    L_branch = 5   # mm - 分支长度
    W = 0.2        # mm (200μm)
    angle = 45     # 分支角度

    print(f"   几何尺寸: 主通道={L_main}mm, 分支={L_branch}mm, 宽度={W}mm, 角度={angle}°")

    # 主通道 (水平，入口在左侧，分岔点在右侧)
    rect_main = geom.feature().create('rect_main', 'Rectangle')
    rect_main.set('size', [f'{L_main}', f'{W}'])
    rect_main.set('pos', ['0', f'{-W/2}'])  # 居中在y=0
    rect_main.label('主通道')

    geom.run('rect_main')

    # 上分支 - 使用Polygon创建倾斜通道
    # 分支起点在主通道末端 (L_main, 0)，向上延伸
    poly_upper = geom.feature().create('poly_upper', 'Polygon')
    # 定义上分支的4个顶点（按顺时针）
    x_start = L_main
    y_start = 0
    x_end = x_start + L_branch * np.cos(np.radians(angle))
    y_end = y_start + L_branch * np.sin(np.radians(angle))

    # 上分支顶点：左下、左上、右上、右下
    upper_points = [
        [f'{x_start}', f'{y_start}'],                           # 起点（下）
        [f'{x_start}', f'{y_start + W}'],                       # 起点（上）
        [f'{x_end}', f'{y_end + W}'],                           # 终点（上）
        [f'{x_end}', f'{y_end}']                                # 终点（下）
    ]
    poly_upper.set('x', [p[0] for p in upper_points])
    poly_upper.set('y', [p[1] for p in upper_points])
    poly_upper.label('上分支')

    geom.run('poly_upper')

    # 下分支 - 向下延伸
    poly_lower = geom.feature().create('poly_lower', 'Polygon')
    x_end_lower = x_start + L_branch * np.cos(np.radians(angle))
    y_end_lower = y_start - L_branch * np.sin(np.radians(angle))

    # 下分支顶点：左上、左下、右下、右上
    lower_points = [
        [f'{x_start}', f'{y_start}'],                           # 起点（上）
        [f'{x_start}', f'{y_start - W}'],                       # 起点（下）
        [f'{x_end_lower}', f'{y_end_lower - W}'],               # 终点（下）
        [f'{x_end_lower}', f'{y_end_lower}']                    # 终点（上）
    ]
    poly_lower.set('x', [p[0] for p in lower_points])
    poly_lower.set('y', [p[1] for p in lower_points])
    poly_lower.label('下分支')

    geom.run('poly_lower')

    # 合并所有部分
    union = geom.feature().create('union1', 'Union')
    union.selection('input').all()
    geom.run()

    print("   ✅ Y型几何创建完成")
    print(f"      主通道: (0, {-W/2}) 到 ({L_main}, {W/2})")
    print(f"      上分支: ({L_main}, 0) 到 ({x_end:.1f}, {y_end:.1f})")
    print(f"      下分支: ({L_main}, 0) 到 ({x_end_lower:.1f}, {y_end_lower:.1f})")

    # 物理场
    physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')

    fp = physics.feature('fp1')
    fp.set('mu_mat', 'userdef')
    fp.set('mu', '0.001 [Pa*s]')
    fp.set('rho_mat', 'userdef')
    fp.set('rho', '1000 [kg/m^3]')

    # 边界条件 (需要在GUI中设置正确的边界编号)
    inlet = physics.feature().create('in1', 'Inlet')
    inlet.set('U0in', '0.0077')
    inlet.label('入口 - 主通道左端')

    outlet1 = physics.feature().create('out1', 'Outlet')
    outlet1.set('p0', '0')
    outlet1.label('出口1 - 上分支末端')

    outlet2 = physics.feature().create('out2', 'Outlet')
    outlet2.set('p0', '0')
    outlet2.label('出口2 - 下分支末端')

    wall = physics.feature().create('wall1', 'Wall')
    wall.label('壁面 - 所有其余边界')

    print("   ✅ 物理场设置完成")
    print("   ⚠️  边界条件需要在GUI中验证")

    # 网格
    mesh = java_model.mesh().create('mesh1', 'geom1')
    mesh.autoMeshSize(5)

    # 研究
    study = java_model.study().create('std1')
    study.feature().create('stat', 'Stationary')

    # 参数
    params = java_model.param()
    params.set('v_in', '0.0077 [m/s]')
    params.set('width', '0.0002 [m]')
    params.set('L_main', '0.01 [m]')
    params.set('L_branch', '0.005 [m]')
    params.set('branch_angle', '45 [deg]')
    params.set('viscosity', '0.001 [Pa*s]')
    params.set('density', '1000 [kg/m^3]')

    print("   ✅ 参数定义完成")

    # 保存
    output_path = project_root / 'comsol_simulation' / 'models' / 'yjunction_base.mph'
    model.save(str(output_path))
    print(f"   ✅ 模型已保存: {output_path}")

    client.clear()
    return output_path


if __name__ == '__main__':
    print("=" * 60)
    print("COMSOL分岔道基准模型生成工具")
    print("=" * 60)

    try:
        # 创建T型分岔道基准模型
        tj_path = create_tjunction_base_model()

        # 创建Y型分岔道基准模型
        yj_path = create_yjunction_base_model()

        print("\n" + "=" * 60)
        print("📋 下一步操作:")
        print("=" * 60)
        print("1. 在COMSOL GUI中打开生成的基准模型:")
        print(f"   - {tj_path}")
        print(f"   - {yj_path}")
        print()
        print("2. 验证并设置正确的边界编号:")
        print("   - 选择 Inlet 节点，指定入口边界")
        print("   - 选择 Outlet1/Outlet2 节点，指定出口边界")
        print("   - 选择 Wall 节点，选择所有剩余边界")
        print()
        print("3. 运行一次求解验证模型正确性")
        print()
        print("4. 保存模型，然后使用参数化脚本批量生成数据")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
