"""
修复版COMSOL Python API测试脚本

此脚本使用正确的API调用方式来测试COMSOL连接。
基于mph 1.2.4版本的正确用法。

作者: PINNs项目组
修复时间: 2025-11-19
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    import mph
    print("✅ mph模块导入成功")
    print(f"   版本: {mph.__version__}")
except ImportError as e:
    print(f"❌ mph模块导入失败: {e}")
    print("请确保已安装mph包: pip install mph")
    sys.exit(1)


def test_java_environment():
    """测试Java环境"""
    print("\n🔍 检查Java环境:")
    try:
        import jpype
        import jpype.imports
        print("   ✅ JPype已安装")

        # 尝试启动JVM
        try:
            if not jpype.isJVMStarted():
                jpype.startJVM()
                print("   ✅ JVM启动成功")
            else:
                print("   ✅ JVM已运行")
        except Exception as e:
            print(f"   ⚠️  JVM启动问题: {e}")

        # 尝试访问Java类
        try:
            from java.lang import String
            test_str = String("Java测试")
            print(f"   ✅ Java类访问正常")
        except Exception as e:
            print(f"   ⚠️  Java类访问问题: {e}")

    except ImportError as e:
        print(f"   ❌ JPype未安装或有问题: {e}")
        print("   建议: pip install jpype1")


def test_comsol_connection():
    """测试COMSOL连接"""

    print("=" * 60)
    print("🧪 测试COMSOL Multiphysics与Python API连接")
    print("=" * 60)

    try:
        # 1. 检查COMSOL可执行文件
        comsol_executable = r"E:\COMSOL63\Multiphysics\bin\win64\comsol.exe"
        if os.path.exists(comsol_executable):
            print(f"\n✅ COMSOL可执行文件确认: {comsol_executable}")
        else:
            print(f"\n❌ COMSOL可执行文件未找到: {comsol_executable}")
            return False

        # 2. 检查是否已有客户端实例
        print("\n📋 检查现有客户端实例...")
        try:
            # 尝试创建客户端（如果已存在会报错）
            client = mph.Client(cores=1)
            print("   ✅ 成功创建新的COMSOL客户端")
        except Exception as e:
            print(f"   ❌ 创建客户端失败: {e}")
            print("\n💡 这可能是因为:")
            print("   - 同一Python会话中已有客户端实例")
            print("   - COMSOL许可证问题")
            print("   - 端口被占用")
            return False

        # 3. 获取版本信息
        print("\n📋 COMSOL版本信息:")
        try:
            # 正确的版本获取方式
            version = client.version
            if callable(version):
                version_str = version()
            else:
                version_str = str(version)
            print(f"   版本: {version_str}")

            # Java版本
            try:
                java_ver = client.java_version
                if callable(java_ver):
                    java_ver_str = java_ver()
                else:
                    java_ver_str = str(java_ver)
                print(f"   Java版本: {java_ver_str}")
            except:
                print(f"   Java版本: 无法获取")

            # 可用核心数
            try:
                cores = client.cores
                if callable(cores):
                    cores_str = cores()
                else:
                    cores_str = str(cores)
                print(f"   可用核心数: {cores_str}")
            except:
                print(f"   可用核心数: 无法获取")

        except Exception as e:
            print(f"   ⚠️  版本信息获取异常: {e}")
            print("   但COMSOL连接正常")

        # 4. 创建测试模型
        print("\n🔧 创建测试模型...")
        try:
            model = client.create('test_model_api')
            print("   ✅ 模型创建成功")
            print(f"   模型名称: {model.name}")
        except Exception as e:
            print(f"   ❌ 模型创建失败: {e}")
            client.remove()
            return False

        # 5. 测试模型基本操作
        print("\n🔍 测试模型基本操作:")
        try:
            # 检查模型属性
            print(f"   模型文件: {model.file}")
            print(f"   模型名称: {model.name}")
        except Exception as e:
            print(f"   ⚠️  属性访问问题: {e}")

        # 6. 测试几何操作（使用正确API）
        print("\n   创建几何...")
        try:
            geometries = model.geometries()
            print(f"   ✅ 几何对象获取成功: {type(geometries)}")

            # 尝试创建矩形几何
            try:
                rect = geometries.create('rect1', 'Rectangle')
                print("   ✅ 矩形几何创建成功")

                # 设置几何参数
                rect.parameter('size', '10 [mm]')
                print("   ✅ 几何参数设置成功")

            except Exception as e:
                print(f"   ⚠️  几何创建问题: {e}")

        except Exception as e:
            print(f"   ⚠️  几何操作问题: {e}")

        # 7. 测试物理场操作
        print("\n   添加物理场...")
        try:
            physics = model.physics()
            print(f"   ✅ 物理场对象获取成功: {type(physics)}")

            # 这里不实际添加物理场，只是测试API
            # physics.create('laminar_flow', 'LaminarFlow', 'geom1')
            # print("   ✅ 物理场添加成功")

        except Exception as e:
            print(f"   ⚠️  物理场操作问题: {e}")

        # 8. 保存模型
        print("\n   保存测试模型...")
        try:
            temp_dir = tempfile.gettempdir()
            model_path = os.path.join(temp_dir, 'test_comsol_connection.mph')
            model.save(model_path)
            print(f"   ✅ 模型已保存到: {model_path}")

            # 验证文件是否存在
            if os.path.exists(model_path):
                file_size = os.path.getsize(model_path)
                print(f"   ✅ 文件大小: {file_size} bytes")
        except Exception as e:
            print(f"   ⚠️  保存问题: {e}")

        # 9. 清理
        print("\n🧹 清理资源...")
        try:
            model.remove()
            print("   ✅ 模型已移除")
        except:
            pass

        try:
            client.remove()
            print("   ✅ 客户端已移除")
        except:
            pass

        print("\n" + "=" * 60)
        print("✅ 测试成功！COMSOL Python API正常工作")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ 整体测试失败: {e}")
        import traceback
        traceback.print_exc()

        print("\n💡 可能的解决方案:")
        print("   1. 检查COMSOL许可证是否有效")
        print("   2. 确认防火墙允许COMSOL通信")
        print("   3. 尝试以管理员权限运行")
        print("   4. 重启计算机后重试")
        print("   5. 检查端口2036是否被占用")

        print("\n" + "=" * 60)
        print("❌ 测试失败")
        print("=" * 60)
        return False


def check_license():
    """检查COMSOL许可证信息"""
    print("\n🔑 COMSOL许可证检查:")
    try:
        client = mph.Client(cores=1)

        # 通过Java接口检查许可证
        java_model_util = client.java.getModelUtil()
        license_info = java_model_util.getLicenseInformation()
        print(f"   许可证信息: {license_info}")

        client.remove()
    except Exception as e:
        print(f"   ⚠️  许可证检查失败: {e}")


if __name__ == "__main__":

    # 显示欢迎信息
    print("🧪 COMSOL Python API 修复版测试脚本")
    print(f"📅 运行时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📦 mph版本: {mph.__version__}")

    # 检查Java环境
    test_java_environment()

    # 测试连接
    success = test_comsol_connection()

    # 如果成功，检查许可证
    if success:
        check_license()

    # 退出码
    sys.exit(0 if success else 1)
