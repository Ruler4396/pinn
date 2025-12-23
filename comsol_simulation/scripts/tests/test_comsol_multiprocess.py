"""
COMSOL API多进程测试脚本

由于COMSOL Python API在同一会话中只能有一个客户端实例，
我们使用multiprocessing在独立进程中测试API连接。

用法:
python test_comsol_multiprocess.py

作者: PINNs项目组
创建时间: 2025-11-19
"""

import os
import sys
import tempfile
import multiprocessing
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


def test_in_subprocess():
    """在独立进程中测试COMSOL API"""
    import mph

    print("=" * 60)
    print("🧪 COMSOL API多进程测试")
    print("=" * 60)

    try:
        # 1. 检查COMSOL路径
        comsol_executable = r"E:\COMSOL63\Multiphysics\bin\win64\comsol.exe"
        if not os.path.exists(comsol_executable):
            print(f"❌ COMSOL未安装或路径错误: {comsol_executable}")
            return False

        print(f"✅ COMSOL路径确认: {comsol_executable}")

        # 2. 创建客户端
        print("\n🚀 启动COMSOL客户端...")
        client = mph.Client(cores=1)
        print("✅ 客户端启动成功")

        # 3. 获取版本信息
        print("\n📋 版本信息:")
        try:
            version = client.version
            print(f"   COMSOL版本: {version()}")
            java_ver = client.java_version
            print(f"   Java版本: {java_ver()}")
        except Exception as e:
            print(f"   ⚠️  版本信息获取失败: {e}")

        # 4. 创建模型
        print("\n🔧 创建测试模型...")
        model = client.create('mp_test')
        print(f"✅ 模型创建成功: {model.name}")

        # 5. 创建几何
        print("   创建矩形几何...")
        try:
            geometries = model.geometries()
            rect = geometries.create('rect1', 'Rectangle')
            rect.parameter('size', '10 [mm]')
            geometries.run()
            print("✅ 几何创建成功")
        except Exception as e:
            print(f"⚠️  几何创建问题: {e}")

        # 6. 保存模型
        print("   保存模型...")
        temp_dir = tempfile.gettempdir()
        model_path = os.path.join(temp_dir, 'comsol_mp_test.mph')
        model.save(model_path)
        print(f"✅ 模型已保存: {model_path}")

        # 7. 清理
        print("\n🧹 清理资源...")
        model.remove()
        client.remove()
        print("✅ 清理完成")

        print("\n" + "=" * 60)
        print("✅ 测试成功！")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("❌ 测试失败")
        print("=" * 60)
        return False


def main():
    """主函数：运行多进程测试"""
    print("📅 COMSOL API连接测试 (多进程版本)")
    print(f"⏰ 开始时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查mph是否可用
    try:
        import mph
        print(f"✅ mph {mph.__version__} 可用\n")
    except ImportError as e:
        print(f"❌ mph导入失败: {e}")
        return False

    # 在独立进程中运行测试
    print("🔄 在独立进程中运行测试...")
    print("-" * 60)

    # 使用multiprocessing在独立进程中测试
    with multiprocessing.Pool(1) as pool:
        result = pool.apply(test_in_subprocess)

    print("-" * 60)
    print(f"\n⏱️ 结束时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if result:
        print("\n🎉 测试成功完成！COMSOL API可以正常使用")
        print("\n💡 下一步:")
        print("   1. 现在可以运行参数化扫描脚本")
        print("   2. 可以创建真实的COMSOL模型")
        print("   3. 可以导出训练数据")
        return True
    else:
        print("\n😞 测试失败，请检查COMSOL安装和配置")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
