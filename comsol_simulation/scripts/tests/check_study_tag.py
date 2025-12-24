#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查模型的研究标记"""

import mph
from pathlib import Path

base_path = Path("D:/PINNs/comsol_simulation/models/parametric_base.mph")

client = mph.Client()
model = client.load(str(base_path))
java_model = model.java

print("研究列表:")
studies = java_model.study()
iter = studies.iterator()
while iter.hasNext():
    study = iter.next()
    print(f"  tag: {study.tag()}, label: {study.label()}")

client.disconnect()
