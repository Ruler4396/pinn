"""
简化版2D微通道创建脚本

使用更简单的方法创建2D微通道模型
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


def create_simple_microchannel():
    """创建简单的2D微通道模型"""
    
    print("=" * 50)
    print("🔧 创建简单2D微通道模型")
    print("=" * 50)
    
    try:
        # 启动COMSOL
        print("\n🚀 启动COMSOL...")
        client = mph.start()
        print("✅ COMSOL启动成功")
        
        # 创建模型
        print("\n📋 创建模型...")
        model = client.create("simple_microchannel")
        print(f"✅ 模型创建成功: {model.name()}")
        
        # 使用model.java访问Java API
        java_model = model.java
        
        # 创建2D组件
        print("\n📐 创建2D组件...")
        comp1 = java_model.component().create("comp1", True)  # True表示2D
        print("✅ 2D组件创建成功")
        
        # 创建几何组
        print("\n🔧 创建几何...")
        geom1 = java_model.geom().create("geom1", 2)  # 2D几何
        print("✅ 几何组创建成功")
        
        # 创建矩形
        print("\n📏 创建矩形通道...")
        rect1 = geom1.create("r1", "Rectangle")
        
        # 设置矩形尺寸 (单位: mm)
        rect1.set("size", [10.0, 0.2])  # [长度, 宽度]
        rect1.set("pos", [0, 0])        # 位置
        print("✅ 矩形创建成功")
        
        # 运行几何
        print("\n🔄 运行几何...")
        geom1.run()
        print("✅ 几何运行完成")
        
        # 创建物理场
        print("\n⚡ 添加层流物理场...")
        spf = java_model.physics().create("spf", "LaminarFlow", "geom1")
        print("✅ 层流物理场添加成功")
        
        # 设置流体属性（水）
        print("\n💧 设置流体属性...")
        fluid1 = spf.feature("fluid1")
        fluid1.set("density", "1000")      # kg/m³
        fluid1.set("dynamicviscosity", "0.001")  # Pa·s
        print("✅ 流体属性设置完成")
        
        # 设置边界条件
        print("\n🔗 设置边界条件...")
        
        # 入口边界条件 (左侧 - 边界1)
        inlet = spf.feature("inlet1")
        inlet.selection().set([1])
        inlet.set("Velocity", "0.01")  # m/s
        
        # 出口边界条件 (右侧 - 边界2)
        outlet = spf.feature("outlet1")
        outlet.selection().set([2])
        outlet.set("Pressure", "0")     # Pa
        
        # 壁面边界条件 (上下边界 - 边界3,4)
        wall = spf.feature("wall1")
        wall.selection().set([3, 4])    # 无滑移
        
        print("✅ 边界条件设置完成")
        
        # 创建网格
        print("\n🕸️ 创建网格...")
        mesh1 = java_model.mesh().create("mesh1", "geom1")
        
        # 设置物理场控制的网格
        mesh1.set("predo", "1")  # 预处理网格
        
        # 运行网格生成
        mesh1.run()
        print("✅ 网格创建完成")
        
        # 创建研究
        print("\n🔬 创建研究...")
        study1 = java_model.study().create("std1")
        stat = study1.feature().create("stat", "Stationary")
        print("✅ 研究创建成功")
        
        # 运行模拟
        print("\n🚀 运行模拟...")
        study1.run()
        print("✅ 模拟运行完成")
        
        # 保存模型
        print("\n💾 保存模型...")
        save_path = r"D:\PINNs\comsol_simulation\models\simple_microchannel.mph"
        model.save(save_path)
        print(f"✅ 模型已保存: {save_path}")
        
        # 显示模型信息
        print("\n📊 模型信息:")
        print(f"   模型名称: {model.name()}")
        print(f"   几何尺寸: 10mm × 0.2mm")
        print(f"   流体: 水 (ρ=1000 kg/m³, μ=0.001 Pa·s)")
        print(f"   入口速度: 0.01 m/s")
        print(f"   雷诺数: Re = ρvD/μ = 2.0 (层流)")
        
        # 清理
        print("\n🧹 清理资源...")
        model.remove()
        client.remove()
        print("✅ 清理完成")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🌟 简单2D微通道创建器")
    print(f"📅 {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = create_simple_microchannel()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 模型创建成功！")
        print("🚀 可以开始使用模型进行PINNs训练了")
    else:
        print("😞 模型创建失败")
        print("💡 请检查错误信息并重试")
    print("=" * 50)
    
    sys.exit(0 if success else 1)