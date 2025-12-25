#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断parametric_base.mph的物理场特征
"""

import mph
from pathlib import Path

def main():
    print("=" * 60)
    print("🔍 诊断parametric_base.mph物理场特征")
    print("=" * 60)

    base_model_path = Path(__file__).parent.parent.parent / "models" / "parametric_base.mph"

    print(f"\n📂 模型: {base_model_path.name}")

    # 启动COMSOL
    print("\n🚀 启动COMSOL...")
    client = mph.Client()

    try:
        model = client.load(str(base_model_path))
        java_model = model.java

        # 获取物理场
        physics_list = java_model.physics()
        physics_iter = physics_list.iterator()

        while physics_iter.hasNext():
            phys = physics_iter.next()
            tag = str(phys.tag())
            label = str(phys.label())
            print(f"\n{'='*50}")
            print(f"物理场: {label} (tag: {tag})")
            print('='*50)

            # 获取所有特征
            features = phys.feature()
            feat_iter = features.iterator()

            while feat_iter.hasNext():
                feat = feat_iter.next()
                feat_tag = str(feat.tag())
                feat_label = str(feat.label())
                feat_type = str(feat.getType())

                print(f"  - {feat_label}")
                print(f"      tag: {feat_tag}")
                print(f"      type: {feat_type}")

                # 尝试获取属性
                try:
                    props = feat.properties()
                    if props:
                        print(f"      属性: {props}")
                except:
                    pass

        # 也检查全局参数
        print(f"\n{'='*50}")
        print("全局参数:")
        print('='*50)
        params = java_model.param()
        param_iter = params.entrySet().iterator()
        while param_iter.hasNext():
            entry = param_iter.next()
            name = entry.key
            value = entry.value
            print(f"  {name} = {value}")

    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
