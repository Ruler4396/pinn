#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据导出方法 - 使用正确的COMSOL API

问题分析：
1. Export功能的数据格式不稳定
2. 坐标数据可能为0

解决方案：
直接使用Java API获取网格数据和结果数据
"""

import mph
import h5py
import numpy as np
from pathlib import Path

def export_data_from_mesh(model, case_name, v_in, width, viscosity, density):
    """
    使用网格数据导出 - 更可靠的方法

    直接从COMSOL模型获取：
    1. 网格坐标 (x, y)
    2. 结果数据 (u, v, p)
    """
    java_model = model.java

    # 获取网格
    mesh = java_model.mesh('mesh1')
    print(f"   获取网格信息...")

    # 使用Result对象获取网格上的解
    # 创建一个Result Evaluation Feature
    eval_result = java_model.result().numerical().create('eval1', 'Eval')
    eval_result.set('expr', ['u', 'v', 'p', 'x', 'y'])

    # 获取网格节点
    # 使用mesh.getNodes()或其他方法获取网格节点坐标
    try:
        # 方法1: 使用Quality命令获取数据
        quality = java_model.result().numerical().create('qual1', 'GlobalEvaluation')
        quality.set('expr', 'u')
        quality.set('unit', 'm/s')

        # 获取网格数据
        mesh_data = mesh.getMeshNodes()
        print(f"   网格节点数: {len(mesh_data)}")

    except Exception as e:
        print(f"   ⚠️ 网格数据获取失败: {e}")

    # 方法2: 使用Export但正确解析
    export = java_model.result().export().create('export1', 'Data')
    export.set('expr', ['x', 'y', 'u', 'v', 'p'])
    export.set('unit', ['m', 'm', 'm/s', 'm/s', 'Pa'])

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_file = Path(f"temp_export_{timestamp}.txt")

    export.set('filename', str(temp_file.absolute()))
    export.run()

    # 读取数据
    results = []
    with open(temp_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('%'):
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        x = float(parts[0])
                        y = float(parts[1])
                        u = float(parts[2])
                        v = float(parts[3])
                        p = float(parts[4])
                        results.append([x, y, u, v, p])
                    except:
                        continue

    temp_file.unlink()

    if len(results) == 0:
        raise ValueError("未获取到有效数据")

    results = np.array(results)

    print(f"   📊 获取到 {len(results)} 个数据点")
    print(f"   📊 X范围: [{results[:,0].min():.6f}, {results[:,0].max():.6f}] m")
    print(f"   📊 Y范围: [{results[:,1].min():.6f}, {results[:,1].max():.6f}] m")
    print(f"   📊 U范围: [{results[:,2].min():.6f}, {results[:,2].max():.6f}] m/s")

    return results

def main():
    """测试正确的导出方法"""
    client = mph.Client()

    try:
        print("🧪 测试正确的数据导出方法")
        print("="*60)

        # 创建简单模型测试
        model = client.create('test_export')
        java_model = model.java

        # 创建几何
        geom = java_model.geom().create('geom1', 2)
        geom.lengthUnit('mm')
        rect = geom.feature().create('rect1', 'Rectangle')
        rect.set('size', ['10', '0.2'])
        rect.set('pos', ['0', '0'])
        geom.run()

        # 物理场
        physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')

        # 流体属性
        fp = physics.feature('fp1')
        fp.set('mu_mat', 'userdef')
        fp.set('mu', '0.001 [Pa*s]')
        fp.set('rho_mat', 'userdef')
        fp.set('rho', '1000 [kg/m^3]')

        # 边界条件
        inlet = physics.feature().create('in1', 'Inlet')
        inlet.selection().set([1])
        inlet.set('U0in', '0.005')

        outlet = physics.feature().create('out1', 'Outlet')
        outlet.selection().set([2])
        outlet.set('p0', '0')

        wall = physics.feature().create('wall1', 'Wall')
        wall.selection().set([3, 4])

        # 网格和求解
        mesh = java_model.mesh().create('mesh1', 'geom1')
        mesh.autoMeshSize(5)
        mesh.run()

        study = java_model.study().create('std1')
        study.feature().create('stat', 'Stationary')
        study.run()

        print("✅ 模型求解完成")

        # 导出数据
        results = export_data_from_mesh(model, 'test', 0.005, 0.0002, 0.001, 1000)

        # 保存测试文件
        with h5py.File('test_export.h5', 'w') as f:
            f.create_dataset('x', data=results[:, 0])
            f.create_dataset('y', data=results[:, 1])
            f.create_dataset('u', data=results[:, 2])
            f.create_dataset('v', data=results[:, 3])
            f.create_dataset('p', data=results[:, 4])

        print("✅ 测试数据已保存: test_export.h5")

    finally:
        client.clear()

if __name__ == "__main__":
    main()
