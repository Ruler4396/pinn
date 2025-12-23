# COMSOL微通道模型手动创建指南

## 📋 操作步骤

### 1. 启动COMSOL
1. 打开COMSOL Multiphysics 6.3
2. 选择 `Blank Model` (空白模型)

### 2. 运行Java脚本
1. 在COMSOL中: `File` > `New` > `Java`
2. 复制 `manual_parametric_model.java` 中的代码
3. 粘贴到Java编辑器中
4. 点击 `Run` 按钮执行

或者:
1. `File` > `Open` > 选择 `manual_parametric_model.java`
2. COMSOL会自动运行脚本

### 3. 验证模型创建
脚本运行完成后，应该看到:
- ✅ 几何模型 (10mm × 0.2mm 矩形)
- ✅ 层流物理场设置
- ✅ 网格生成 (约1000-2000个单元)
- ✅ 求解完成
- ✅ 结果显示

### 4. 查看结果
1. 在 `Results` 节点下:
   - `Velocity (spf)` - 速度场
   - `Pressure (spf)` - 压力场
   - `Velocity magnitude` - 速度大小

2. 典型结果应该显示:
   - 入口速度: 0.01 m/s
   - 最大速度: ~0.015 m/s (抛物线分布)
   - 压力降: ~10,000 Pa

### 5. 修改参数运行
1. 在 `Parameters` 节点修改参数:
   ```
   L_ch = 10[mm]     # 通道长度
   W_ch = 0.2[mm]    # 通道宽度
   U_inlet = 0.01[m/s]  # 入口速度
   mu_fluid = 0.001[Pa*s]  # 流体粘度
   ```

2. 重新求解:
   - 右键 `Study 1` > `Compute`

### 6. 批量参数扫描
1. 在 `Parameters` 节点添加参数表格:
   ```
   Name       | Value
   ------------------------------
   U_inlet_1  | 0.001[m/s]
   U_inlet_2  | 0.01[m/s]
   U_inlet_3  | 0.05[m/s]
   ```

2. 在 `Study` 节点:
   - 右键 `Study 1` > `Add Sweep`
   - 选择要扫描的参数
   - 运行批量求解

### 7. 数据导出
#### 方法1: 表格导出
1. `Results` > `Derived Values` > `Table`
2. 设置表达式: `x, y, comp1(u), comp1(v), p`
3. 右键 `Table` > `Evaluate`

#### 方法2: CSV导出
1. `Results` > `Export`
2. 设置表达式: `x, y, comp1(u), comp1(v), p`
3. 选择输出位置和格式
4. 点击 `Export`

#### 方法3: 数据探针
1. `Results` > `Evaluation Group` > `Point Probe`
2. 在模型上点击选择点
3. 查看该点的(u,v,p)值

## 🎯 推荐测试参数

### 基础验证 (默认参数)
```
L_ch = 10[mm]
W_ch = 0.2[mm]
U_inlet = 0.01[m/s]
mu_fluid = 0.001[Pa*s]
```

### 速度变化测试
1. 低速: `U_inlet = 0.001[m/s]` (Re ≈ 0.2)
2. 中速: `U_inlet = 0.01[m/s]` (Re ≈ 2.0)
3. 高速: `U_inlet = 0.05[m/s]` (Re ≈ 10.0)

### 几何变化测试
1. 窄通道: `W_ch = 0.15[mm]`
2. 标准通道: `W_ch = 0.2[mm]`
3. 宽通道: `W_ch = 0.25[mm]`

### 流体属性测试
1. 水: `mu_fluid = 0.001[Pa*s]`
2. 甘油溶液: `mu_fluid = 0.01[Pa*s]`

## 🔍 验证要点

### 物理合理性检查
1. **速度场**:
   - 呈抛物线分布
   - 中心速度最大，壁面速度为0
   - 最大速度 ≈ 1.5 × 入口速度

2. **压力场**:
   - 从入口到出口线性下降
   - 压力降与粘度成正比
   - 典型值: 1,000-50,000 Pa

3. **雷诺数**:
   - Re = ρVD/μ < 2300 (层流)
   - 微流控典型范围: 0.1-100

### 数值收敛检查
1. **求解器状态**:
   - 应显示 "Solution converged"
   - 残差应 < 1e-6

2. **网格质量**:
   - 最小角度 > 10°
   - 最大纵横比 < 20

## 📊 预期结果

### 速度分布 (抛物线)
```
u(y) = 1.5 * U_inlet * (1 - (2y/W_ch)^2)
最大速度 = 1.5 * U_inlet
平均速度 = U_inlet
```

### 压力降
```
ΔP = 12 * μ * U_inlet * L_ch / W_ch^2
```

### 典型数值 (默认参数)
- 最大速度: 0.015 m/s
- 压力降: 15,000 Pa
- 雷诺数: 2.0
- 网格数: ~1,500

## ⚠️ 常见问题

### 1. 求解不收敛
- 检查边界条件设置
- 减小入口速度
- 细化网格

### 2. 奇异的网格
- 检查几何尺寸
- 重新生成网格
- 减小最大单元尺寸

### 3. 物理场设置错误
- 确认选择了正确的物理场接口
- 检查边界选择 (1=入口, 2=出口, 3,4=壁面)

### 4. 数据导出失败
- 检查表达式语法
- 确认模型已求解
- 检查文件写入权限

## 📁 输出文件位置

默认保存位置:
```
D:/PINNs/comsol_simulation/models/
D:/PINNs/comsol_simulation/data/
```

建议命名格式:
```
parametric_microchannel_YYYY-MM-DD.mph
export_data_U0.001_W0.15.csv
```

完成模型验证后，即可开始批量数据生成！