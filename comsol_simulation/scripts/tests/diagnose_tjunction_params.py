#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断tjunction_base.mph模型的参数设置"""

import mph
from pathlib import Path

client = mph.Client()
model = client.load(str(Path("D:/PINNs/comsol_simulation/models/tjunction_base.mph")))
java_model = model.java

# 检查参数
print("模型参数:")
params = java_model.param()
entries = params.entrySet()
if entries:
    iter = entries.iterator()
    while iter.hasNext():
        entry = iter.next()
        print(f"  {entry.key} = {entry.value}")

# 检查入口边界条件
print("\n入口边界条件:")
physics = java_model.physics("spf")
inlet = physics.feature("inlet")
print(f"  tag: {inlet.tag()}")
print(f"  label: {inlet.label()}")

# 尝试获取U0in的当前值
try:
    props = inlet.properties()
    for prop in props:
        if 'U0in' in prop or 'u0' in prop:
            try:
                val = inlet.get(prop)
                print(f"  {prop} = {val}")
            except:
                pass
except Exception as e:
    print(f"  获取属性失败: {e}")

client.disconnect()
