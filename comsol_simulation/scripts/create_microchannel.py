"""
创建2D微通道COMSOL模型

此脚本创建一个简单的二维直通微通道模型，用于微流控芯片的流动模拟。
模型包含：
- 矩形微通道几何
- 层流物理场设置
- 入口速度边界条件
- 出口压力边界条件
- 壁面无滑移边界条件

作者: PINNs项目组
创建时间: 2025-11-19
"""

import sys
import numpy as np
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


class MicrochannelModel:
    """2D微通道COMSOL模型类"""
    
    def __init__(self):
        self.client = None
        self.model = None
        
        # 微通道几何参数 (单位: mm)
        self.channel_length = 10.0    # 通道长度 10mm
        self.channel_width = 0.2     # 通道宽度 200μm = 0.2mm
        
        # 流体参数 (水)
        self.density = 1000.0        # 密度 kg/m³
        self.viscosity = 0.001       # 动力粘度 Pa·s
        
        # 流动参数
        self.inlet_velocity = 0.01   # 入口速度 0.01 m/s
        self.outlet_pressure = 0     # 出口压力 Pa (相对压力)
        
    def start_comsol(self):
        """启动COMSOL客户端"""
        print("🚀 启动COMSOL...")
        try:
            self.client = mph.start()
            print("✅ COMSOL启动成功")
            return True
        except Exception as e:
            print(f"❌ COMSOL启动失败: {e}")
            return False
    
    def create_model(self):
        """创建新模型"""
        print("🔧 创建新模型...")
        try:
            self.model = self.client.create('microchannel_2d')
            print(f"✅ 模型创建成功: {self.model.name()}")
            return True
        except Exception as e:
            print(f"❌ 模型创建失败: {e}")
            return False
    
    def create_geometry(self):
        """创建2D微通道几何"""
        print("📐 创建2D微通道几何...")
        
        try:
            # 获取模型对象
            model = self.model
            
            # 创建2D几何
            # 使用MPH API命令创建矩形
            model.java.component().create("comp1", True)  # 创建2D组件
            
            # 创建矩形几何
            rect_tag = model.java.geom("comp1").create("r1", "Rectangle")
            model.java.geom("comp1").feature(rect_tag).set("size", 
                [self.channel_length, self.channel_width])
            model.java.geom("comp1").feature(rect_tag).set("pos", [0, 0])
            
            # 运行几何
            model.java.geom("comp1").run()
            
            print(f"✅ 几何创建成功")
            print(f"   通道长度: {self.channel_length} mm")
            print(f"   通道宽度: {self.channel_width} mm")
            
            return True
            
        except Exception as e:
            print(f"❌ 几何创建失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def add_physics(self):
        """添加层流物理场"""
        print("⚡ 添加层流物理场...")
        
        try:
            model = self.model
            
            # 添加层流物理场接口
            physics = model.java.physics().create("laminar_flow", "LaminarFlow", "geom1")
            
            # 设置流体属性
            model.java.physics("laminar_flow").feature("fluid1").set("density", str(self.density))
            model.java.physics("laminar_flow").feature("fluid1").set("dynamicviscosity", str(self.viscosity))
            
            print(f"✅ 层流物理场添加成功")
            print(f"   流体密度: {self.density} kg/m³")
            print(f"   动力粘度: {self.viscosity} Pa·s")
            
            return True
            
        except Exception as e:
            print(f"❌ 物理场添加失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def set_boundary_conditions(self):
        """设置边界条件"""
        print("🔗 设置边界条件...")
        
        try:
            model = self.model
            
            # 入口边界条件 (左边界) - 速度入口
            model.java.physics("laminar_flow").feature("inlet1").selection().set([1])  # 左边界
            model.java.physics("laminar_flow").feature("inlet1").set("Velocity", str(self.inlet_velocity))
            
            # 出口边界条件 (右边界) - 压力出口
            model.java.physics("laminar_flow").feature("outlet1").selection().set([2])  # 右边界
            model.java.physics("laminar_flow").feature("outlet1").set("Pressure", str(self.outlet_pressure))
            
            # 壁面边界条件 (上下边界) - 无滑移
            model.java.physics("laminar_flow").feature("wall1").selection().set([3, 4])  # 上下边界
            
            print(f"✅ 边界条件设置成功")
            print(f"   入口速度: {self.inlet_velocity} m/s")
            print(f"   出口压力: {self.outlet_pressure} Pa")
            print(f"   壁面条件: 无滑移")
            
            return True
            
        except Exception as e:
            print(f"❌ 边界条件设置失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_mesh(self):
        """创建网格"""
        print("🕸️ 创建网格...")
        
        try:
            model = self.model
            
            # 创建物理场控制的网格
            model.java.mesh().create("mesh1", "geom1")
            
            # 设置网格尺寸
            model.java.mesh("mesh1").feature("ftri1").set("hmax", "0.1")  # 最大单元尺寸
            model.java.mesh("mesh1").feature("ftri1").set("hmin", "0.01") # 最小单元尺寸
            
            # 运行网格生成
            model.java.mesh("mesh1").run()
            
            # 获取网格统计信息
            mesh_stats = model.java.mesh("mesh1").getstat()
            print(f"✅ 网格创建成功")
            print(f"   网格统计: {mesh_stats}")
            
            return True
            
        except Exception as e:
            print(f"❌ 网格创建失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def setup_study(self):
        """设置研究"""
        print("🔬 设置研究...")
        
        try:
            model = self.model
            
            # 创建稳态研究
            model.java.study().create("std1")
            model.java.study("std1").feature().create("stat", "Stationary")
            
            # 添加物理场接口到研究
            model.java.study("std1").feature("stat").set("activate", ["laminar_flow"])
            
            print("✅ 稳态研究设置成功")
            
            return True
            
        except Exception as e:
            print(f"❌ 研究设置失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_simulation(self):
        """运行模拟"""
        print("🚀 运行模拟...")
        
        try:
            model = self.model
            
            # 运行计算
            model.java.study("std1").run()
            
            print("✅ 模拟计算完成")
            
            return True
            
        except Exception as e:
            print(f"❌ 模拟运行失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_model(self, save_path=None):
        """保存模型"""
        print("💾 保存模型...")
        
        try:
            if save_path is None:
                save_path = r"D:\PINNs\comsol_simulation\models\microchannel_2d_v1.mph"
            
            self.model.save(save_path)
            print(f"✅ 模型已保存到: {save_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ 模型保存失败: {e}")
            return False
    
    def calculate_reynolds_number(self):
        """计算雷诺数"""
        # Re = ρ * v * D_h / μ
        # D_h = 4 * A / P = 4 * (w * h) / (2 * (w + h)) = 2 * w * h / (w + h)
        # 对于矩形通道，假设高度与宽度相同
        
        hydraulic_diameter = 2 * self.channel_width * self.channel_width / (self.channel_width + self.channel_width) * 1e-3  # 转换为m
        reynolds = (self.density * self.inlet_velocity * hydraulic_diameter) / self.viscosity
        
        print(f"📊 流动参数:")
        print(f"   水力直径: {hydraulic_diameter*1000:.3f} mm")
        print(f"   雷诺数: {reynolds:.2f}")
        
        if reynolds < 2300:
            print("   流态: 层流 ✓")
        else:
            print("   流态: 湍流 ⚠️")
        
        return reynolds
    
    def create_complete_model(self):
        """创建完整模型的工作流程"""
        print("=" * 60)
        print("🧪 创建2D微通道COMSOL模型")
        print("=" * 60)
        
        # 显示设计参数
        print(f"\n📋 设计参数:")
        print(f"   通道长度: {self.channel_length} mm")
        print(f"   通道宽度: {self.channel_width} mm")
        print(f"   入口速度: {self.inlet_velocity} m/s")
        print(f"   流体密度: {self.density} kg/m³")
        print(f"   流体粘度: {self.viscosity} Pa·s")
        
        # 计算雷诺数
        self.calculate_reynolds_number()
        
        # 执行建模步骤
        steps = [
            ("启动COMSOL", self.start_comsol),
            ("创建模型", self.create_model),
            ("创建几何", self.create_geometry),
            ("添加物理场", self.add_physics),
            ("设置边界条件", self.set_boundary_conditions),
            ("创建网格", self.create_mesh),
            ("设置研究", self.setup_study),
            ("运行模拟", self.run_simulation),
            ("保存模型", self.save_model)
        ]
        
        for step_name, step_func in steps:
            print(f"\n🔄 {step_name}...")
            if not step_func():
                print(f"❌ {step_name}失败，停止建模过程")
                return False
        
        print("\n" + "=" * 60)
        print("🎉 2D微通道模型创建成功！")
        print("✅ 所有步骤完成")
        print("=" * 60)
        
        return True


def main():
    """主函数"""
    print("🌟 PINNs项目 - 2D微通道模型生成器")
    print(f"📅 运行时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建微通道模型实例
    model_builder = MicrochannelModel()
    
    # 创建完整模型
    success = model_builder.create_complete_model()
    
    # 清理资源
    if model_builder.model:
        try:
            model_builder.model.remove()
        except:
            pass
    
    if model_builder.client:
        try:
            model_builder.client.remove()
        except:
            pass
    
    # 显示结果
    if success:
        print("\n🚀 模型创建完成，可以开始进行PINNs训练了！")
        return 0
    else:
        print("\n😞 模型创建失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())