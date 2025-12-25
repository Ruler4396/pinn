#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断parametric_base.mph的材料设置
"""

import mph
from pathlib import Path

def main():
    print("=" * 60)
    print("🔍 诊断parametric_base.mph材料设置")
    print("=" * 60)

    base_model_path = Path(__file__).parent.parent.parent / "models" / "parametric_base.mph"

    print(f"\n📂 模型: {base_model_path.name}")

    if not base_model_path.exists():
        print(f"❌ 文件不存在: {base_model_path}")
        return

    # 启动COMSOL
    print("\n🚀 启动COMSOL...")
    client = mph.Client()

    try:
        model = client.load(str(base_model_path))
        java_model = model.java

        # 获取材料
        materials = java_model.material()
        mat_iter = materials.iterator()

        print("\n" + "=" * 50)
        print("材料列表:")
        print('=' * 50)

        while mat_iter.hasNext():
            mat = mat_iter.next()
            label = str(mat.label())
            tag = str(mat.tag())
            print(f"\n{label} (tag: {tag})")

            # 获取材料属性组
            prop_groups = mat.propertyGroup()
            if prop_groups:
                group_iter = prop_groups.iterator()
                while group_iter.hasNext():
                    group = group_iter.next()
                    group_name = str(group.name())
                    print(f"\n  属性组: {group_name}")

                    # 获取属性
                    try:
                        props = group.properties()
                        for prop in props:
                            prop_name = str(prop)
                            try:
                                prop_value = group.get(prop_name)
                                print(f"    {prop_name} = {prop_value}")
                            except:
                                print(f"    {prop_name} = (无法读取)")
                    except Exception as e:
                        print(f"  获取属性失败: {e}")

    finally:
        try:
            client.disconnect()
        except:
            pass


if __name__ == "__main__":
    main()
