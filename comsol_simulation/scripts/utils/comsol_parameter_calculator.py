"""
COMSOL微流控参数计算器

计算合适的微流控参数，包括速度、压力、雷诺数等。

作者: PINNs项目组
时间: 2025-11-19
"""

import numpy as np

def calculate_reynolds(density, velocity, width, viscosity):
    """计算雷诺数"""
    re = density * velocity * width / viscosity
    return re

def calculate_pressure_drop(length, velocity, viscosity, density, width):
    """
    计算通道内的压力降
    基于Hagen-Poiseuille方程（层流）
    """
    # 流量
    Q = velocity * width  # 对于矩形通道的简化

    # 压力降 (简化公式)
    # 对于矩形通道，压力降与速度成正比
    delta_p = (12 * viscosity * velocity * length) / (width**2)

    return delta_p

def analyze_parameters(inlet_velocity, channel_length, channel_width,
                      fluid_viscosity=1e-3, fluid_density=1000):
    """分析参数是否合理"""
    print("=" * 70)
    print("🔬 微流控参数分析")
    print("=" * 70)

    print(f"\n📋 当前参数:")
    print(f"   入口速度: {inlet_velocity*100:.1f} cm/s = {inlet_velocity:.4f} m/s")
    print(f"   通道长度: {channel_length*1000:.1f} mm")
    print(f"   通道宽度: {channel_width*1e6:.0f} μm")
    print(f"   流体粘度: {fluid_viscosity:.4f} Pa·s")
    print(f"   流体密度: {fluid_density} kg/m³")

    # 计算雷诺数
    re = calculate_reynolds(fluid_density, inlet_velocity, channel_width, fluid_viscosity)
    print(f"\n📊 雷诺数: {re:.2f}")

    if re < 2300:
        print(f"   ✅ 层流 (Re < 2300)")
    elif re < 4000:
        print(f"   ⚠️  过渡流 (2300 < Re < 4000)")
    else:
        print(f"   ❌ 湍流 (Re > 4000)")

    # 计算压力降
    delta_p = calculate_pressure_drop(channel_length, inlet_velocity,
                                   fluid_viscosity, fluid_density, channel_width)
    print(f"\n💨 预期压力降: {delta_p:.1f} Pa")
    print(f"   (从入口到出口)")

    # 检查速度是否合理
    print(f"\n🔍 速度合理性检查:")
    if inlet_velocity > 0.005:
        print(f"   ⚠️  速度 {inlet_velocity:.4f} m/s 较快")
        print(f"      建议: < 0.005 m/s")
    elif inlet_velocity < 0.0001:
        print(f"   ⚠️  速度 {inlet_velocity:.6f} m/s 较慢")
        print(f"      建议: > 0.0001 m/s")
    else:
        print(f"   ✅ 速度在合理范围内")

    # 检查边界条件
    print(f"\n🔧 边界条件建议:")
    print(f"\n   方案1: 入口速度 + 出口压力 (推荐)")
    print(f"      入口: 速度 = {inlet_velocity:.4f} m/s")
    print(f"      出口: 压力 = 0 Pa (相对压力)")
    print(f"      壁面: 无滑移")

    print(f"\n   方案2: 压力驱动流")
    print(f"      入口: 压力 = {delta_p:.0f} Pa")
    print(f"      出口: 压力 = 0 Pa")
    print(f"      壁面: 无滑移")

    # 检查问题的可能原因
    print(f"\n❓ 为什么所有物理量为零？")
    print(f"\n   可能的原 因:")
    print(f"   1. 求解器没有收敛")
    print(f"   2. 边界条件组合不合适")
    print(f"   3. 参数设置导致数值问题")
    print(f"   4. 导出了错误的数据类型")

    return re, delta_p


def suggest_parameters():
    """推荐参数组合"""
    print("\n" + "=" * 70)
    print("💡 推荐参数组合")
    print("=" * 70)

    # 推荐的参数
    print("\n🎯 推荐设置1: 低速层流")
    re1, dp1 = analyze_parameters(
        inlet_velocity=0.001,  # 0.1 cm/s
        channel_length=10e-3,  # 10 mm
        channel_width=200e-6,  # 200 μm
    )

    print("\n" + "-" * 70)
    print("\n🎯 推荐设置2: 中速层流")
    re2, dp2 = analyze_parameters(
        inlet_velocity=0.005,  # 0.5 cm/s
        channel_length=10e-3,
        channel_width=200e-6,
    )

    print("\n" + "=" * 70)
    print("✅ 建议使用的参数")
    print("=" * 70)
    print(f"\n推荐使用 方案1 (低速层流):")
    print(f"   入口速度: 0.001 m/s (0.1 cm/s)")
    print(f"   出口压力: 0 Pa")
    print(f"   雷诺数: {re1:.1f} (层流)")
    print(f"   预期压力降: {dp1:.0f} Pa")


def debug_zero_results():
    """调试零结果问题"""
    print("\n" + "=" * 70)
    print("🔍 零结果问题诊断")
    print("=" * 70)

    print("\n💡 可能的原因和解决方案:")

    print("\n1️⃣  求解器问题")
    print("   现象: 所有物理量为零")
    print("   原因: 求解器未收敛或初始猜测不佳")
    print("   解决:")
    print("      ✅ 检查COMSOL日志中的收敛信息")
    print("      ✅ 尝试调整求解器设置")
    print("      ✅ 使用更保守的初始值")

    print("\n2️⃣  边界条件组合")
    print("   当前: 入口速度 + 出口压力")
    print("   问题: 可能不合适")
    print("   解决: 尝试以下组合:")
    print("      方案A: 入口速度 = 0.001 m/s, 出口压力 = 0 Pa")
    print("      方案B: 入口压力 = 10 Pa, 出口压力 = 0 Pa")

    print("\n3️⃣  导出设置")
    print("   当前: 选择了 '边界' 导出")
    print("   问题: 边界上速度垂直分量为零")
    print("   解决: 选择 '域' 重新导出")

    print("\n4️⃣  验证步骤")
    print("   ✅ 检查COMSOL模型树中的求解状态")
    print("   ✅ 查看结果 → 速度大小图形")
    print("   ✅ 查看结果 → 压力图形")
    print("   ✅ 确认图形中有非零数据显示")


def main():
    """主函数"""
    print("📅 微流控参数验证工具")
    print(f"⏰ 时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 分析当前参数（如果用户是0.01 m/s）
    print("\n🔍 分析您当前的参数 (0.01 m/s 入口速度):")
    re_current, dp_current = analyze_parameters(
        inlet_velocity=0.01,
        channel_length=10e-3,
        channel_width=200e-6,
    )

    # 推荐参数
    suggest_parameters()

    # 调试零结果
    debug_zero_results()

    print("\n" + "=" * 70)
    print("✅ 分析完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
