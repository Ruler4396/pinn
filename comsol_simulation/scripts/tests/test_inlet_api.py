#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Inlet边界条件API调用
"""

import mph

def test_inlet_api():
    """测试Inlet边界条件的正确API调用"""
    print("=" * 60)
    print("🔍 测试Inlet边界条件API")
    print("=" * 60)

    client = mph.Client(cores=1)

    try:
        # 创建简单模型
        model = client.create("test_inlet")
        java_model = model.java

        # 创建几何
        geom = java_model.geom().create('geom1', 2)
        geom.lengthUnit('mm')

        rect1 = geom.feature().create('rect1', 'Rectangle')
        rect1.set('size', ['10', '0.15'])
        rect1.set('pos', ['0', '0'])
        geom.run()

        # 添加层流物理场
        physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')

        # 创建Inlet边界条件
        inlet = physics.feature().create('in1', 'Inlet')
        inlet.selection().set([1])

        print("\n📋 Inlet边界条件属性:")
        print("=" * 50)

        # 尝试获取所有属性
        try:
            props = inlet.properties()
            print(f"属性列表: {props}")
        except Exception as e:
            print(f"获取属性失败: {e}")

        # 尝试不同的设置方法
        print("\n🔧 测试不同的API调用:")
        print("=" * 50)

        test_methods = [
            ("方法1: inlet.property('U0in', value)", lambda: inlet.property('U0in', '0.005')),
            ("方法2: inlet.set('U0in', value)", lambda: inlet.set('U0in', '0.005')),
            ("方法3: 设置u0/v0", lambda: test_u0_v0(inlet)),
        ]

        for name, method in test_methods:
            try:
                print(f"\n{name}")
                method()
                print("  ✅ 成功!")
                break
            except Exception as e:
                print(f"  ❌ 失败: {e}")

        print("\n✅ 测试完成")

    finally:
        client.clear()
        client.disconnect()


def test_u0_v0(inlet):
    """测试设置u0和v0"""
    # 从诊断脚本中看到的属性名
    inlet.property('u0', '0.005')
    inlet.property('v0', '0')


if __name__ == "__main__":
    test_inlet_api()
