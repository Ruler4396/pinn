#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整T型分岔道模型测试"""

import mph

client = mph.Client()

try:
    # 创建模型
    model = client.create('test_tj_full')
    java_model = model.java

    # 创建几何 (毫米单位)
    geom = java_model.geom().create('geom1', 2)
    geom.lengthUnit('mm')

    L_main = 10
    L_side = 5
    W = 0.2

    # 左半段
    rect_left = geom.feature().create('rect_left', 'Rectangle')
    rect_left.set('size', [f'{L_main/2}', f'{W}'])
    rect_left.set('pos', ['0', '0'])

    # 右半段
    rect_right = geom.feature().create('rect_right', 'Rectangle')
    rect_right.set('size', [f'{L_main/2}', f'{W}'])
    rect_right.set('pos', [f'{L_main/2}', '0'])

    # 侧通道
    rect_side = geom.feature().create('rect_side', 'Rectangle')
    rect_side.set('size', [f'{W}', f'{L_side}'])
    rect_side.set('pos', [f'{L_main/2 - W/2}', f'{W}'])

    # 运行几何并合并
    geom.run('rect_left')
    geom.run('rect_right')
    geom.run('rect_side')

    union = geom.feature().create('union1', 'Union')
    union.selection('input').all()
    geom.run()
    print('✅ 几何创建成功')

    # 添加物理场
    physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')
    print('✅ 物理场创建成功')

    # 设置材料
    mat = java_model.material().create('mat1')
    mat.label("Water")
    pg = mat.propertyGroup('def')
    pg.set('materialtype', '1')
    pg.set('mu', '0.001 [Pa*s]')
    pg.set('rho', '1000 [kg/m^3]')
    mat.selection().all()
    print('✅ 材料设置成功')

    # 验证材料设置
    mu_val = pg.getString('mu')
    rho_val = pg.getString('rho')
    print(f'   mu = {mu_val}')
    print(f'   rho = {rho_val}')

    # 入口
    inlet = physics.feature().create('in1', 'Inlet')
    inlet.selection().set([1])
    inlet.set('U0in', '0.005')
    print('✅ 入口边界条件设置成功')

    # 出口1
    outlet1 = physics.feature().create('out1', 'Outlet')
    outlet1.selection().set([2])
    outlet1.set('p0', '0')
    print('✅ 出口1边界条件设置成功')

    # 出口2
    outlet2 = physics.feature().create('out2', 'Outlet')
    outlet2.selection().set([3])
    outlet2.set('p0', '0')
    print('✅ 出口2边界条件设置成功')

    # 网格
    mesh = java_model.mesh().create('mesh1', 'geom1')
    mesh.autoMeshSize(5)
    mesh.run()
    print('✅ 网格生成成功')

    # 求解
    print('🔄 正在求解...')
    study = java_model.study().create('std1')
    study.feature().create('stat', 'Stationary')
    study.run()
    print('✅ 求解成功!')

except Exception as e:
    print(f'❌ 失败: {e}')
    import traceback
    traceback.print_exc()
finally:
    client.clear()
