#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断基准模型结构

查看parametric_base.mph模型中:
1. 有哪些研究(study)
2. 有哪些参数(parameters)
3. 有哪些几何(geometries)
4. 研究的标签(name/tag)

作者: PINNs项目组
日期: 2025-12-24
"""

import mph
from pathlib import Path


def diagnose_model():
    """诊断模型结构"""
    print("=" * 60)
    print("🔍 基准模型结构诊断")
    print("=" * 60)

    # 模型路径
    base_model_path = Path(__file__).parent.parent.parent / "models" / "parametric_base.mph"

    if not base_model_path.exists():
        print(f"❌ 模型不存在: {base_model_path}")
        return

    print(f"\n📂 模型路径: {base_model_path}")

    # 启动COMSOL客户端
    print("\n🚀 启动COMSOL客户端...")
    client = mph.Client()
    print("   ✅ 客户端启动成功\n")

    try:
        # 加载模型
        print("📂 加载模型...")
        model = client.load(str(base_model_path))
        java_model = model.java
        print("   ✅ 模型加载成功\n")

        # 1. 列出所有参数
        print("=" * 60)
        print("📋 全局参数 (Global Parameters)")
        print("=" * 60)
        try:
            params = java_model.param()
            if params is not None:
                # 获取参数条目
                param_entries = params.entrySet()
                count = 0
                for entry in param_entries:
                    name = entry.key
                    value = entry.value
                    print(f"  {name} = {value}")
                    count += 1
                if count == 0:
                    print("  (无全局参数)")
            else:
                print("  (无全局参数)")
        except Exception as e:
            print(f"  ❌ 错误: {e}")

        # 2. 列出所有研究
        print("\n" + "=" * 60)
        print("📋 研究列表 (Studies)")
        print("=" * 60)
        try:
            study_list = java_model.study()
            if study_list is not None:
                # 使用Java迭代器获取研究
                studies_iterator = study_list.iterator()
                studies = []
                while studies_iterator.hasNext():
                    study = studies_iterator.next()
                    tag = study.tag()
                    name = study.label()
                    studies.append((tag, name))
                    print(f"  标签: {tag}, 名称: {name}")

                if len(studies) == 0:
                    print("  (无研究)")
            else:
                print("  (无研究)")
        except Exception as e:
            print(f"  ❌ 错误: {e}")

        # 3. 列出所有几何
        print("\n" + "=" * 60)
        print("📋 几何列表 (Geometries)")
        print("=" * 60)
        try:
            geom_list = java_model.geom()
            if geom_list is not None:
                geom_iterator = geom_list.iterator()
                geoms = []
                while geom_iterator.hasNext():
                    geom = geom_iterator.next()
                    tag = geom.tag()
                    dim = geom.dim()
                    geoms.append((tag, dim))
                    print(f"  标签: {tag}, 维度: {dim}D")

                if len(geoms) == 0:
                    print("  (无几何)")
            else:
                print("  (无几何)")
        except Exception as e:
            print(f"  ❌ 错误: {e}")

        # 4. 列出物理场
        print("\n" + "=" * 60)
        print("📋 物理场 (Physics)")
        print("=" * 60)
        try:
            physics_list = java_model.physics()
            if physics_list is not None:
                physics_iterator = physics_list.iterator()
                physics = []
                while physics_iterator.hasNext():
                    phys = physics_iterator.next()
                    tag = phys.tag()
                    label = phys.label()
                    physics.append((tag, label))
                    print(f"  标签: {tag}, 名称: {label}")

                if len(physics) == 0:
                    print("  (无物理场)")
            else:
                print("  (无物理场)")
        except Exception as e:
            print(f"  ❌ 错误: {e}")

        # 5. 列出材料
        print("\n" + "=" * 60)
        print("📋 材料 (Materials)")
        print("=" * 60)
        try:
            mat_list = java_model.material()
            if mat_list is not None:
                mat_iterator = mat_list.iterator()
                materials = []
                while mat_iterator.hasNext():
                    mat = mat_iterator.next()
                    tag = mat.tag()
                    label = mat.label()
                    materials.append((tag, label))
                    print(f"  标签: {tag}, 名称: {label}")

                if len(materials) == 0:
                    print("  (无材料)")
            else:
                print("  (无材料)")
        except Exception as e:
            print(f"  ❌ 错误: {e}")

        # 6. 模型文件信息
        print("\n" + "=" * 60)
        print("📋 模型文件信息")
        print("=" * 60)
        print(f"  文件名: {base_model_path.name}")
        print(f"  文件大小: {base_model_path.stat().st_size / 1024:.1f} KB")

    finally:
        # 清理
        try:
            client.disconnect()
        except:
            pass
        print("\n✅ 诊断完成")


if __name__ == "__main__":
    diagnose_model()
