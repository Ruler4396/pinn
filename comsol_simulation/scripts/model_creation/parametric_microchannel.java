// COMSOL Java脚本 - 参数化微通道模拟
// 在COMSOL中批量运行生成多组数据
// 适合在COMSOL GUI中直接运行

import com.comsol.model.*;
import com.comsol.model.util.*;
import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Date;

public class parametric_microchannel {
    public static void main(String[] args) {
        try {
            System.out.println("🚀 开始参数化微通道模拟");

            // 定义参数组合
            double[] inletVelocities = {0.001, 0.01, 0.03, 0.05, 0.1};  // m/s
            double[] channelWidths = {0.15, 0.20, 0.25};  // mm
            double[] fluidViscosities = {0.001, 0.01};    // Pa·s

            int totalCases = inletVelocities.length * channelWidths.length * fluidViscosities.length;
            System.out.println("📋 总计 " + totalCases + " 组参数");

            // 输出目录
            String outputDir = "D:/PINNs/comsol_simulation/data/";
            File dir = new File(outputDir);
            if (!dir.exists()) {
                dir.mkdirs();
            }

            int caseCount = 0;
            int successfulCases = 0;

            // 遍历所有参数组合
            for (int i = 0; i < inletVelocities.length; i++) {
                for (int j = 0; j < channelWidths.length; j++) {
                    for (int k = 0; k < fluidViscosities.length; k++) {
                        caseCount++;

                        double vInlet = inletVelocities[i];
                        double width = channelWidths[j];
                        double viscosity = fluidViscosities[k];

                        String caseId = String.format("case_%02d_%d_%d", i+1, j+1, k+1);

                        System.out.println("\n" + "=".repeat(60));
                        System.out.println("案例 " + caseCount + "/" + totalCases + ": " + caseId);
                        System.out.println("参数: v=" + vInlet + "m/s, w=" + (width*1000) + "μm, μ=" + viscosity + "Pa·s");

                        try {
                            // 创建新模型
                            Model model = ModelUtil.create("Microfluidic_" + caseId);

                            // 几何设置
                            model.geom().create("geom1", 2);
                            model.geom("geom1").lengthUnit("mm");

                            // 创建矩形通道
                            Rectangle rect = model.geom("geom1").create("r1", "Rectangle");
                            rect.set("size", new double[]{10.0, width});  // 10mm长，width mm宽
                            rect.set("pos", new double[]{0.0, 0.0});
                            model.geom("geom1").run();

                            // 物理场设置
                            model.physics().create("spf", "LaminarFlow", "geom1");

                            // 材料属性 (水)
                            model.physics("spf").feature().create("defns", "DefaultNodeSettings");
                            model.physics("spf").feature("defns").selection().all();
                            model.physics("spf").feature("defns").set("rho", "1000");  // kg/m³
                            model.physics("spf").feature("defns").set("mu", Double.toString(viscosity));

                            // 边界条件
                            // 入口 (左边界)
                            Inlet inlet = model.physics("spf").feature().create("in1", "InletVelocity", 2);
                            inlet.selection().set(new int[]{1});
                            inlet.set("U0", Double.toString(vInlet));

                            // 出口 (右边界)
                            Outlet outlet = model.physics("spf").feature().create("out1", "OutletPressure", 2);
                            outlet.selection().set(new int[]{2});
                            outlet.set("p0", "0");  // Pa

                            // 壁面 (上下边界)
                            Wall wall = model.physics("spf").feature().create("wall1", "Wall", 2);
                            wall.selection().set(new int[]{3, 4});

                            // 网格生成
                            model.mesh().create("mesh1", "geom1");
                            model.mesh("mesh1").automatic(true);

                            // 自适应网格设置
                            double elementSize = Math.max(width/8.0, width/15.0);
                            model.mesh("mesh1").set("maxsize", elementSize);
                            model.mesh("mesh1").set("minsize", elementSize/4.0);
                            model.mesh("mesh1").run();

                            // 创建研究
                            Study study = model.study().create("std1");
                            study.feature().create("stat", "Stationary");

                            // 运行求解
                            System.out.println("开始求解...");
                            long startTime = System.currentTimeMillis();
                            study.run();
                            long solveTime = System.currentTimeMillis() - startTime;
                            System.out.println("求解完成，用时: " + (solveTime/1000.0) + "秒");

                            // 导出数据
                            System.out.println("导出数据...");
                            exportModelData(model, caseId, outputDir, vInlet, width, viscosity);

                            // 计算雷诺数
                            double reynolds = 1000.0 * vInlet * (width * 1e-3) / viscosity;
                            System.out.println("雷诺数: Re = " + String.format("%.1f", reynolds));

                            // 清理模型
                            model.clear();
                            successfulCases++;

                            System.out.println("✅ 案例 " + caseId + " 完成");

                        } catch (Exception e) {
                            System.out.println("❌ 案例 " + caseId + " 失败: " + e.getMessage());
                        }
                    }
                }
            }

            System.out.println("\n" + "=".repeat(60));
            System.out.println("🎉 参数化扫描完成!");
            System.out.println("✅ 成功: " + successfulCases + "/" + totalCases + " 案例");
            System.out.println("📁 数据保存在: " + outputDir);

        } catch (Exception e) {
            System.out.println("❌ 程序执行错误: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private static void exportModelData(Model model, String caseId, String outputDir,
                                      double vInlet, double width, double viscosity) {
        try {
            // 创建结果评估
            model.result().numerical().create("eval1", "Eval");
            model.result().numerical("eval1").set("expr", new String[]{"u", "v", "p"});
            model.result().numerical("eval1").set("unit", new String[]{"m/s", "m/s", "Pa"});
            model.result().numerical("eval1").set("descr", new String[]{"x-velocity", "y-velocity", "pressure"});

            // 生成数据网格
            int gridSize = 25;  // 25x25 网格点
            String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date());

            // 导出数据表
            model.result().numerical().create("table1", "Table");
            model.result().numerical("table1").set("expr", new String[]{"x", "y", "u", "v", "p"});

            // 设置数据导出参数
            double[] xRange = {0.0, 10.0};  // x范围
            double[] yRange = {0.0, width}; // y范围
            int[] resolution = {gridSize, gridSize};

            // 创建表格数据
            model.result().table().create("tbl1", "Table");

            // 生成数据点
            for (int i = 0; i < gridSize; i++) {
                for (int j = 0; j < gridSize; j++) {
                    double x = xRange[0] + (xRange[1] - xRange[0]) * i / (gridSize - 1);
                    double y = yRange[0] + (yRange[1] - yRange[0]) * j / (gridSize - 1);

                    try {
                        model.result().numerical("eval1").set("p", new double[]{x, y});
                        double[] values = model.result().numerical("eval1").getReal();

                        if (values != null && values.length >= 3) {
                            // 添加到表格
                            // 注意：实际导出时需要使用COMSOL的表导出功能
                        }
                    } catch (Exception e) {
                        // 跳过无法计算的点
                    }
                }
            }

            // 导出为CSV文件（简化版本）
            String csvFilename = outputDir + "comsol_data_" + caseId + "_" + timestamp + ".csv";

            // 创建简单的数据导出
            model.result().numerical().create("export1", "Export");
            model.result().numerical("export1").set("expr", new String[]{"comp1(u)", "comp1(v)", "p"});
            model.result().numerical("export1").set("descr", "Velocity and Pressure");
            model.result().numerical("export1").set("unit", new String[]{"m/s", "m/s", "Pa"});
            model.result().numerical("export1").set("filename", csvFilename);

            try {
                model.result().numerical("export1").run();
                System.out.println("数据导出成功: " + csvFilename);
            } catch (Exception e) {
                // 如果自动导出失败，提示手动导出
                System.out.println("自动导出失败，请手动导出数据:");
                System.out.println("1. 在Results中右键点击Export");
                System.out.println("2. 选择要导出的表达式: u, v, p");
                System.out.println("3. 设置输出文件: " + csvFilename);
            }

        } catch (Exception e) {
            System.out.println("数据导出错误: " + e.getMessage());
        }
    }
}