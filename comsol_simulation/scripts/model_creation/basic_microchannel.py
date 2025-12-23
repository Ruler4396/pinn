"""
基础2D微通道创建脚本

创建最简单的2D微通道几何和基本设置
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


def create_basic_microchannel():
    """创建基础2D微通道几何"""
    
    print("=" * 50)
    print("🔧 创建基础2D微通道几何")
    print("=" * 50)
    
    try:
        # 启动COMSOL
        print("\n🚀 启动COMSOL...")
        client = mph.start()
        print("✅ COMSOL启动成功")
        
        # 创建模型
        print("\n📋 创建模型...")
        model = client.create("basic_microchannel")
        print(f"✅ 模型创建成功: {model.name()}")
        
        # 使用Java API
        java_model = model.java
        
        # 创建2D组件
        print("\n📐 创建2D组件...")
        comp1 = java_model.component().create("comp1", True)  # True = 2D
        print("✅ 2D组件创建成功")
        
        # 创建几何
        print("\n📏 创建几何...")
        geom1 = java_model.geom("comp1")
        
        # 创建矩形
        rect1 = geom1.create("r1", "Rectangle")
        rect1.set("size", [10.0, 0.2])  # 10mm长, 0.2mm宽
        rect1.set("pos", [0.0, 0.0])    # 原点位置
        
        # 运行几何
        print("🔄 运行几何...")
        geom1.run()
        print("✅ 几何创建完成")
        
        # 显示几何信息
        print("\n📊 几何信息:")
        print(f"   几何类型: 2D")
        print(f"   形状: 矩形")
        print(f"   尺寸: 10.0 mm × 0.2 mm")
        print(f"   位置: (0, 0) mm")
        
        # 保存模型（即使没有物理场设置）
        print("\n💾 保存基础几何模型...")
        save_path = r"D:\PINNs\comsol_simulation\models\basic_microchannel_geometry.mph"
        model.save(save_path)
        print(f"✅ 基础几何模型已保存: {save_path}")
        
        # 清理资源
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


def create_manual_comsol_script():
    """创建一个手动COMSOL脚本文本文件，可以后续在COMSOL中运行"""
    
    script_content = '''
# COMSOL Java脚本 - 2D微通道创建
# 可以在COMSOL中运行此脚本

import com.comsol.model.*
import com.comsol.model.util.*

model = ModelUtil.create("Model")

# 创建2D组件
model.component().create("comp1", true)
model.geom().create("geom1", 2)
model.geom("geom1").lengthUnit("mm")

# 创建矩形通道
rect1 = model.geom("geom1").create("r1", "Rectangle")
rect1.set("size", new double[]{10.0, 0.2})  # 10mm长, 0.2mm宽
rect1.set("pos", new double[]{0.0, 0.0})    # 位置

# 运行几何
model.geom("geom1").run()

# 添加层流物理场
model.physics().create("spf", "LaminarFlow", "geom1")

# 设置流体属性（水）
model.physics("spf").feature().create("defns", "DefaultNodeSettings")
model.physics("spf").feature("defns").selection().all()

# 入口边界条件
inlet = model.physics("spf").feature().create("in1", "InletVelocity", 2)
inlet.selection().set([1])
inlet.set("U0", "0.01")  # 0.01 m/s

# 出口边界条件
outlet = model.physics("spf").feature().create("out1", "OutletPressure", 2)
outlet.selection().set([2])
outlet.set("p0", "0")     # 0 Pa

# 壁面边界条件
wall = model.physics("spf").feature().create("wall1", "Wall", 2)
wall.selection().set([3, 4])

# 创建网格
model.mesh().create("mesh1", "geom1")
model.mesh("mesh1").automatic(true)
model.mesh("mesh1").run()

# 创建研究
study = model.study().create("std1")
study.feature().create("stat", "Stationary")

# 运行模拟
study.run()

# 保存模型
model.save("D:/PINNs/comsol_simulation/models/manual_microchannel.mph")

print("2D微通道模型创建完成！")
'''
    
    script_path = r"D:\PINNs\comsol_simulation\scripts\create_microchannel_comsol.java"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"📝 COMSOL Java脚本已创建: {script_path}")
    print("💡 可以在COMSOL中使用 File > Developer File > Run Java File 来运行此脚本")
    
    return script_path


if __name__ == "__main__":
    print("🌟 基础2D微通道创建器")
    print(f"📅 {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 尝试创建基础几何
    success = create_basic_microchannel()
    
    # 同时创建手动脚本作为备选方案
    print("\n" + "=" * 50)
    print("📝 创建手动COMSOL脚本...")
    script_path = create_manual_comsol_script()
    
    # 显示结果
    print("\n" + "=" * 50)
    if success:
        print("🎉 基础几何创建成功！")
        print("✅ 可以在COMSOL中打开模型文件继续设置")
    else:
        print("⚠️ 自动创建遇到问题")
        print("✅ 但已创建手动脚本，可以在COMSOL中运行")
    
    print(f"📁 所有文件保存在: D:\\PINNs\\comsol_simulation\\models\\")
    print("🚀 下一步：在COMSOL中打开模型文件，添加物理场设置")
    print("=" * 50)
    
    sys.exit(0)