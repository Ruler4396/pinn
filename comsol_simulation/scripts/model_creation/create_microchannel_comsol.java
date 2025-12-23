
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
