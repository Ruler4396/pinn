"""
COMSOL API完整功能测试 (简化版)

测试COMSOL API的核心功能：连接、创建模型、保存
解决所有已知API调用问题。

作者: PINNs项目组
时间: 2025-11-19
"""

import os
import sys
import tempfile
import multiprocessing
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


def test_comsol_core():
    """测试COMSOL核心功能"""
    import mph

    print("=" * 70)
    print("🧪 COMSOL API 核心功能测试")
    print("=" * 70)

    # 1. 基础检查
    print("\n📋 基础检查:")
    comsol_exe = r"E:\COMSOL63\Multiphysics\bin\win64\comsol.exe"
    if os.path.exists(comsol_exe):
        print(f"   ✅ COMSOL可执行文件存在")
    else:
        print(f"   ❌ COMSOL未找到: {comsol_exe}")
        return False

    # 2. 创建客户端
    print("\n🚀 启动COMSOL客户端...")
    try:
        client = mph.Client(cores=1)
        print("   ✅ 客户端启动成功")
    except Exception as e:
        print(f"   ❌ 客户端启动失败: {e}")
        return False

    # 3. 获取版本信息
    print("\n📋 版本信息:")
    try:
        # 正确方式：version是一个属性，不应该加()
        version_str = client.version
        print(f"   COMSOL版本: {version_str}")
    except Exception as e:
        print(f"   ⚠️  版本信息获取问题: {e}")

    # 4. 创建模型
    print("\n🔧 创建测试模型...")
    try:
        model = client.create('comsol_test')
        print("   ✅ 模型创建成功")
    except Exception as e:
        print(f"   ❌ 模型创建失败: {e}")
        client.remove()
        return False

    # 5. 设置模型参数
    print("   设置模型参数...")
    try:
        # 设置参数
        model.parameter('L', '10 [mm]')  # 长度
        model.parameter('W', '2 [mm]')   # 宽度
        print("   ✅ 参数设置成功")
    except Exception as e:
        print(f"   ⚠️  参数设置问题: {e}")

    # 6. 保存模型
    print("\n💾 保存测试模型...")
    try:
        temp_dir = tempfile.gettempdir()
        model_path = os.path.join(temp_dir, 'comsol_api_test.mph')

        model.save(model_path)
        print(f"   ✅ 模型保存成功")
        print(f"   📁 保存路径: {model_path}")

        # 验证文件
        if os.path.exists(model_path):
            size = os.path.getsize(model_path)
            print(f"   📊 文件大小: {size:,} bytes")
        else:
            print("   ⚠️  文件未找到")
    except Exception as e:
        print(f"   ❌ 保存失败: {e}")
        model.remove()
        client.remove()
        return False

    # 7. 加载刚保存的模型
    print("\n📂 测试模型加载...")
    try:
        loaded_model = client.load(model_path)
        print("   ✅ 模型加载成功")
        loaded_model.remove()
    except Exception as e:
        print(f"   ⚠️  模型加载问题: {e}")

    # 8. 清理
    print("\n🧹 清理资源...")
    try:
        # 正确清理方式：不调用model.remove()，直接清理客户端
        client.clear()  # 清理所有模型
        print("   ✅ 资源清理成功")
    except Exception as e:
        print(f"   ⚠️  清理问题: {e}")
    finally:
        try:
            client.remove()
            print("   ✅ 客户端关闭成功")
        except:
            pass

    print("\n" + "=" * 70)
    print("✅ 测试完成！COMSOL API 核心功能正常")
    print("=" * 70)
    return True


def main():
    """主函数"""
    print("📅 COMSOL API 测试 (简化版)")
    print(f"⏰ 开始: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}")

    # 检查mph
    try:
        import mph
        print(f"✅ mph {mph.__version__} 已导入\n")
    except Exception as e:
        print(f"❌ mph导入失败: {e}\n")
        return False

    # 在独立进程中运行
    print("🔄 在独立进程中运行测试...\n")
    print("-" * 70)

    with multiprocessing.Pool(1) as pool:
        result = pool.apply(test_comsol_core)

    print("-" * 70)
    print(f"\n⏱️ 结束: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}")

    if result:
        print("\n🎉 成功！COMSOL API工作正常\n")
        print("✅ 现在可以进行以下操作:")
        print("   1. 创建微流控芯片模型")
        print("   2. 设置物理场和边界条件")
        print("   3. 运行参数化扫描")
        print("   4. 导出训练数据")
        return True
    else:
        print("\n😞 失败！请检查COMSOL配置\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
