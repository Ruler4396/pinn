"""
测试COMSOL与Python连接脚本

此脚本验证COMSOL Multiphysics与Python API的连接是否正常工作。
如果成功，将显示COMSOL版本信息和创建一个简单的模型。

作者: PINNs项目组
创建时间: 2025-11-19
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
except ImportError as e:
    print(f"❌ mph模块导入失败: {e}")
    print("请确保已安装mph包: pip install mph")
    sys.exit(1)


def test_comsol_connection():
    """测试COMSOL连接的基本功能"""
    
    print("=" * 50)
    print("测试COMSOL Multiphysics与Python连接")
    print("=" * 50)
    
    try:
        # 1. 检查COMSOL可执行文件
        comsol_executable = r"E:\COMSOL63\Multiphysics\bin\win64\comsol.exe"
        if os.path.exists(comsol_executable):
            print(f"✅ COMSOL可执行文件找到: {comsol_executable}")
        else:
            print(f"❌ COMSOL可执行文件未找到: {comsol_executable}")
            return False
            
        # 2. 启动COMSOL服务器
        print("\n🚀 启动COMSOL服务器...")
        client = mph.start(cores=1)
        print("✅ COMSOL服务器启动成功")
        
        # 3. 获取COMSOL版本信息
        print("\n📋 COMSOL版本信息:")
        try:
            version = client.version()
            print(f"   版本: {version}")
            print(f"   Java版本: {client.java_version()}")
            print(f"   可用核心数: {client.cores()}")
        except Exception as e:
            print(f"   ⚠️  无法获取详细版本信息: {e}")
            print("   但COMSOL连接正常工作")
        
        # 4. 创建一个简单的2D模型测试
        print("\n🔧 创建测试模型...")
        model = client.create('test_model')
        print("✅ 模型创建成功")
        
        # 5. 创建几何
        print("   创建几何...")
        geometry = model.geometry()
        geometry.create('rect1', 'Rectangle')
        geometry.run()
        print("✅ 几何创建成功")
        
        # 6. 添加物理场
        print("   添加物理场...")
        physics = model.physics()
        physics.create('laminar_flow', 'LaminarFlow', 'geom1')
        print("✅ 物理场添加成功")
        
        # 7. 保存模型
        print("   保存模型...")
        temp_dir = tempfile.gettempdir()
        model_path = os.path.join(temp_dir, 'test_model.mph')
        model.save(model_path)
        print(f"✅ 模型已保存到: {model_path}")
        
        # 8. 清理
        model.remove()
        client.remove()
        print("✅ 测试完成，已清理资源")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 连接测试失败: {e}")
        print("\n💡 可能的解决方案:")
        print("   1. 检查COMSOL是否正确安装")
        print("   2. 确认COMSOL许可证有效")
        print("   3. 检查Windows防火墙设置")
        print("   4. 以管理员权限运行此脚本")
        return False


def check_environment():
    """检查系统环境配置"""
    
    print("\n🔍 系统环境检查:")
    
    # 检查Python版本
    python_version = sys.version
    print(f"   Python版本: {python_version}")
    
    # 检查操作系统
    import platform
    os_info = platform.system() + " " + platform.release()
    print(f"   操作系统: {os_info}")
    
    # 检查Java环境（COMSOL需要Java）
    try:
        import java
        print("   ✅ Java环境可用 (通过JPype)")
    except ImportError:
        print("   ⚠️  Java环境检查失败 (可能影响COMSOL API)")
    
    # 检查必要的Python包
    required_packages = ['numpy', 'scipy', 'matplotlib']
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package} 可用")
        except ImportError:
            print(f"   ❌ {package} 未安装")


if __name__ == "__main__":
    
    # 显示欢迎信息
    print("🧪 COMSOL Python API 测试脚本")
    print(f"📅 运行时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查环境
    check_environment()
    
    # 测试连接
    success = test_comsol_connection()
    
    # 显示结果
    print("\n" + "=" * 50)
    if success:
        print("🎉 测试成功！COMSOL Python API可以正常使用")
        print("🚀 现在可以开始创建你的微流控模型了")
    else:
        print("😞 测试失败，请检查COMSOL安装和配置")
        print("📞 如需帮助，请查看COMSOL文档或联系技术支持")
    print("=" * 50)
    
    # 退出码
    sys.exit(0 if success else 1)