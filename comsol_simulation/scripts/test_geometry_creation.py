"""
测试COMSOL几何创建的脚本

逐步验证几何创建的API调用方式

作者: PINNs项目组
时间: 2025-11-19
"""

import os
import sys
import tempfile
import multiprocessing
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


def test_step_by_step():
    """逐步测试API调用"""
    import mph

    print("=" * 70)
    print("🔍 逐步测试几何创建API")
    print("=" * 70)

    client = mph.Client(cores=1)
    model = client.create('step_test')

    print("\n1️⃣ 检查基础属性:")
    print(f"   model: {model}")
    print(f"   geometries类型: {type(model.geometries())}")
    print(f"   geometries值: {model.geometries()}")

    print("\n2️⃣ 尝试通过Java接口创建几何:")
    try:
        # 使用Java接口直接操作
        java_model = model.java
        print(f"   Java模型对象: {java_model}")

        # 获取几何器
        geom = java_model.geom().create('geom1', 2)  # 2D
        print(f"   ✅ Java几何器创建成功")

        # 创建矩形特征
        rect = geom.feature().create('rect1', 'Rectangle')
        print(f"   ✅ 矩形特征创建成功")

        # 设置参数
        rect.set('size', ['10', '0.2'])  # 10mm x 0.2mm
        print(f"   ✅ 参数设置成功")

        # 运行几何
        geom.run()
        print(f"   ✅ 几何运行成功")

        # 检查几何结果
        geoms = model.geometries()
        print(f"   📊 Python中geometries: {geoms}")
        print(f"   📊 几何数量: {len(geoms)}")

    except Exception as e:
        print(f"   ❌ Java接口失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n3️⃣ 尝试使用mph的高级API:")
    try:
        # 这可能不是正确方式，但试试
        if hasattr(model, 'geometry'):
            print("   找到geometry方法")
        if hasattr(model, 'geometries'):
            print("   找到geometries属性")
    except Exception as e:
        print(f"   ⚠️  高级API测试失败: {e}")

    # 保存模型
    print("\n4️⃣ 保存模型:")
    try:
        temp_dir = tempfile.gettempdir()
        model_path = os.path.join(temp_dir, 'step_test.mph')
        model.save(model_path)
        print(f"   ✅ 保存成功: {model_path}")

        if os.path.exists(model_path):
            size = os.path.getsize(model_path)
            print(f"   📊 文件大小: {size:,} bytes")
    except Exception as e:
        print(f"   ❌ 保存失败: {e}")

    # 清理
    print("\n🧹 清理:")
    client.clear()
    client.remove()

    print("\n" + "=" * 70)
    print("✅ 步骤测试完成")
    print("=" * 70)
    return True


def main():
    """主函数"""
    print("📅 COMSOL几何API测试")
    print(f"⏰ 开始: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}")

    with multiprocessing.Pool(1) as pool:
        result = pool.apply(test_step_by_step)

    print(f"\n⏱️ 结束: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}")
    return result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
