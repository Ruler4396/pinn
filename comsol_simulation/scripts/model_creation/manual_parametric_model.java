// COMSOL Java脚本 - 参数化微通道模型 (手动运行版本)
// 在COMSOL GUI中运行：File > New > Java > 粘贴此代码 > Run

import com.comsol.model.*;
import com.comsol.model.util.*;

model = ModelUtil.create("Parametric_Microfluidic_Channel");

// 创建2D组件
model.component().create("comp1", true);
model.geom().create("geom1", 2);
model.geom("geom1").lengthUnit("mm");

// ============ 参数定义 ============
// 基本几何参数 (mm)
model.param().set("L_ch", "10[mm]", "Channel length");
model.param().set("W_ch", "0.2[mm]", "Channel width");

// 流体参数
model.param().set("rho_fluid", "1000[kg/m^3]", "Fluid density (water)");
model.param().set("mu_fluid", "0.001[Pa*s]", "Dynamic viscosity (water)");

// 流动参数
model.param().set("U_inlet", "0.01[m/s]", "Inlet velocity");
model.param().set("P_outlet", "0[Pa]", "Outlet pressure");

// 网格参数
model.param().set("mesh_size", "W_ch/10", "Maximum element size");

print("参数设置完成");
print("通道长度: " + model.param().evaluate("L_ch"));
print("通道宽度: " + model.param().evaluate("W_ch"));
print("入口速度: " + model.param().evaluate("U_inlet"));
print("流体粘度: " + model.param().evaluate("mu_fluid"));

// ============ 几何创建 ============
// 创建矩形通道
rect1 = model.geom("geom1").create("r1", "Rectangle");
rect1.set("size", new String[]{"L_ch", "W_ch"});
rect1.set("pos", new String[]{"0", "0"});

// 运行几何
model.geom("geom1").run();

print("几何创建完成");

// ============ 物理场设置 ============
// 添加层流物理场
model.physics().create("spf", "LaminarFlow", "geom1");

// 设置流体属性
model.physics("spf").feature().create("defns", "DefaultNodeSettings");
model.physics("spf").feature("defns").selection().all();
model.physics("spf").feature("defns").set("rho", "rho_fluid");
model.physics("spf").feature("defns").set("mu", "mu_fluid");

// 入口边界条件 (左边界)
inlet = model.physics("spf").feature().create("in1", "InletVelocity", 2);
inlet.selection().set([1]);
inlet.set("U0", "U_inlet");

// 出口边界条件 (右边界)
outlet = model.physics("spf").feature().create("out1", "OutletPressure", 2);
outlet.selection().set([2]);
outlet.set("p0", "P_outlet");

// 壁面边界条件 (上下边界)
wall = model.physics("spf").feature().create("wall1", "Wall", 2);
wall.selection().set([3, 4]);

print("物理场设置完成");

// ============ 网格生成 ============
model.mesh().create("mesh1", "geom1");

// 自定义网格设置
model.mesh("mesh1").set("maxsize", "mesh_size");
model.mesh("mesh1").set("minsize", "mesh_size/4");
model.mesh("mesh1").automatic(true);

// 运行网格生成
model.mesh("mesh1").run();

print("网格生成完成");

// ============ 求解设置 ============
// 创建研究
study = model.study().create("std1");
study.feature().create("stat", "Stationary");

// 设置求解器参数
study.feature().stat().set("solnum", "auto");
study.feature().stat().set("funclist", "all");

print("求解设置完成");

// ============ 运行求解 ============
print("开始求解...");
study.run();
print("求解完成！");

// ============ 后处理设置 ============
// 计算雷诺数
Re_val = model.param().evaluate("rho_fluid * U_inlet * W_ch / mu_fluid");
print("雷诺数 Re = " + Re_val);

// 创建速度场图
model.result().numeric().create("int1", "Interpolation");
model.result().numeric("int1").set("expr", "comp1(u)");
model.result().numeric("int1").set("unit", "m/s");
model.result().numeric("int1").set("descr", "X-velocity");

model.result().numeric().create("int2", "Interpolation");
model.result().numeric("int2").set("expr", "comp1(v)");
model.result().numeric("int2").set("unit", "m/s");
model.result().numeric("int2").set("descr", "Y-velocity");

model.result().numeric().create("int3", "Interpolation");
model.result().numeric("int3").set("expr", "p");
model.result().numeric("int3").set("unit", "Pa");
model.result().numeric("int3").set("descr", "Pressure");

// 创建速度大小
model.result().numeric().create("int4", "Interpolation");
model.result().numeric("int4").set("expr", "sqrt(comp1(u)^2 + comp1(v)^2)");
model.result().numeric("int4").set("unit", "m/s");
model.result().numeric("int4").set("descr", "Velocity magnitude");

print("后处理设置完成");

// ============ 数据导出 ============
// 导出数据表 (可以右键运行或在Table中查看)
model.result().table().create("tbl1", "Table");
model.result().table("tbl1").set("expr", new String[]{"x", "y", "comp1(u)", "comp1(v)", "p"});
model.result().table("tbl1").set("descr", "Export data for PINNs training");

// 创建CSV导出
model.result().table().create("tbl2", "Table");
model.result().table("tbl2").set("expr", new String[]{"x", "y", "comp1(u)", "comp1(v)", "p"});
model.result().table("tbl2").set("descr", "Export to CSV");

// 设置导出参数
model.result().numerical().create("export1", "Export");
model.result().numerical("export1").set("expr", new String[]{"x", "y", "comp1(u)", "comp1(v)", "p"});
model.result().numerical("export1").set("descr", "Complete field data");
model.result().numerical("export1").set("unit", new String[]{"mm", "mm", "m/s", "m/s", "Pa"});

print("数据导出设置完成");

// ============ 保存模型 ============
String timestamp = java.time.LocalDateTime.now().toString().replace(":", "-");
String filename = "D:/PINNs/comsol_simulation/models/parametric_microchannel_" + timestamp + ".mph";
model.save(filename);

print("模型保存完成: " + filename);
print("");
print("========== 使用说明 ==========");
print("1. 修改参数: 在Parameters面板修改 L_ch, W_ch, U_inlet, mu_fluid");
print("2. 重新求解: 右键Study > Compute");
print("3. 查看结果: Results > Plot Groups");
print("4. 导出数据: Results > Export > 选择表达式并运行");
print("5. 批量运行: 使用Parameters中的Scan功能");
print("");
print("推荐参数组合:");
print("- 低速: U_inlet = 0.001[m/s]");
print("- 中速: U_inlet = 0.01[m/s]");
print("- 高速: U_inlet = 0.05[m/s]");
print("- 窄通道: W_ch = 0.15[mm]");
print("- 宽通道: W_ch = 0.25[mm]");
print("- 高粘度: mu_fluid = 0.01[Pa*s]");