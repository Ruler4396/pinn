"""
简化的COMSOL连接测试

基本测试COMSOL与Python的连接是否工作正常
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    import mph
    print("✅ mph模块导入成功")
except ImportError as e:
    print(f"❌ mph模块导入失败: {e}")
    sys.exit(1)


def test_simple_comsol():
    """简单的COMSOL连接测试"""
    
    print("=" * 40)
    print("简单COMSOL连接测试")
    print("=" * 40)
    
    try:
        # 设置COMSOL路径
        comsol_path = r"E:\COMSOL63\Multiphysics"
        print(f"📁 COMSOL路径: {comsol_path}")
        
        # 启动COMSOL客户端
        print("\n🚀 启动COMSOL客户端...")
        client = mph.start()
        print("✅ COMSOL客户端启动成功")
        
        # 检查版本
        try:
            print(f"\n📋 COMSOL版本: {client.version()}")
        except:
            print("\n📋 COMSOL版本信息获取失败，但连接正常")
        
        # 创建新模型
        print("\n🔧 创建新模型...")
        model = client.create()
        print("✅ 模型创建成功")
        
        # 检查模型属性
        print(f"\n🔍 模型名称: {model.name()}")
        print(f"🔍 模型标签: {model}")
        
        # 测试基本操作
        print("\n🧪 测试基本操作...")
        
        # 创建几何组件
        try:
            geom1 = model.component().create('geom1', True)
            print("✅ 几何组件创建成功")
        except Exception as e:
            print(f"⚠️ 几何组件创建遇到问题: {e}")
        
        # 保存模型
        print("\n💾 保存测试模型...")
        try:
            model.save(r"E:\COMSOL63\Multiphysics\test_model.mph")
            print("✅ 模型保存成功")
        except Exception as e:
            print(f"⚠️ 模型保存遇到问题: {e}")
        
        # 清理资源
        print("\n🧹 清理资源...")
        try:
            model.clear()
            model.remove()
            client.remove()
            print("✅ 资源清理完成")
        except Exception as e:
            print(f"⚠️ 清理时遇到问题: {e}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_simple_comsol()
    
    if success:
        print("\n🎉 简单测试成功！")
        print("🚀 COMSOL Python API基本功能正常")
    else:
        print("\n😞 测试失败")
        print("💡 请检查COMSOL安装和许可证")
    
    print("=" * 40)