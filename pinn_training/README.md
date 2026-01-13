# PINNs 微流道流场预测模型

## 设计目的

本项目的目标是开发一个基于物理信息神经网络（Physics-Informed Neural Networks, PINNs）的微流道流场快速预测工具，用于解决传统计算流体力学（CFD）方法在微流控芯片设计中面临的以下问题：

1. **计算成本高**：传统CFD方法（如COMSOL、FLUENT）求解Navier-Stokes方程需要数小时到数天
2. **参数化困难**：每次改变几何参数或边界条件都需要重新求解
3. **实时性差**：无法满足设计优化和实时控制的需求

PINNs通过将物理方程嵌入神经网络损失函数，实现了**无标签数据训练**，仅需物理方程即可学习流场分布，训练完成后可毫秒级预测任意点流场。

---

## 技术方案

### 1. 物理约束：Navier-Stokes方程

微通道内不可压缩流动的控制方程：

**连续性方程**：
```
∂u/∂x + ∂v/∂y = 0
```

**x方向动量方程**：
```
ρ(u·∂u/∂x + v·∂u/∂y) + ∂p/∂x - μ(∂²u/∂x² + ∂²u/∂y²) = 0
```

**y方向动量方程**：
```
ρ(u·∂v/∂x + v·∂v/∂y) + ∂p/∂y - μ(∂²v/∂x² + ∂²v/∂y²) = 0
```

其中：
- `u, v`：x、y方向速度
- `p`：压力
- `ρ = 1000 kg/m³`：流体密度（水）
- `μ = 0.001 Pa·s`：动力粘度

### 2. 网络架构

```
输入: (x, y) 位置坐标
  ↓
全连接层: [2, 64, 64, 64, 64, 3]
  ↓
输出: (u, v, p) 速度和压力
```

- **激活函数**：Tanh（保证物理量的平滑性）
- **损失函数**：物理方程残差 + 边界条件惩罚
- **优化器**：Adam（学习率 1e-3）

### 3. 边界条件

| 位置 | 条件 |
|-----|------|
| 入口 (x=0) | u = v_in, v = 0 |
| 出口 (x=L) | ∂u/∂x = 0, p = 0 |
| 下壁面 (y=0) | u = 0, v = 0 |
| 上壁面 (y=W) | u = 0, v = 0 |

### 4. 训练策略

**纯物理模式**：不需要任何COMSOL数据

- 在计算域内随机采样点（内部点 + 边界点）
- 计算Navier-Stokes方程残差
- 最小化物理损失函数

**数据融合模式**（可选）：结合COMSOL仿真数据提升精度

---

## 参考文献

### 期刊论文

1. **Raissi, M., Perdikaris, P., & Karniadakis, G. E.** (2019). Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations. *Journal of Computational Physics*, 378, 686-707.

2. **Cai, S., Mao, Z., Wang, Z., Yin, M., & Karniadakis, G. E.** (2021). Physics-informed neural networks (PINNs) for fluid mechanics: A review. *Acta Mechanica Sinica*, 1-22.

3. **Mao, Z., Jagtap, A. D., & Karniadakis, G. E.** (2020). Physics-informed neural networks for high-speed flows. *Computer Methods in Applied Mechanics and Engineering*, 360, 112789.

### 会议论文

4. **Raissi, M., & Karniadakis, G. E.** (2018). Hidden physics models: Machine learning of nonlinear partial differential equations. *arXiv preprint arXiv:1808.04829*.

### 学位论文

5. **Raissi, M.** (2018). *Deep hidden physics models: Deep learning of nonlinear differential equations* (Doctoral dissertation, Brown University).

---

## 使用方法

### 快速开始

**第1步**：训练模型（约20-30分钟）

在项目根目录下运行：

```bash
python pinn_training/inference/trained_model_template.py
```

或者从任意目录运行（脚本会自动定位项目路径）：

```bash
python /path/to/PINNs/pinn_training/inference/trained_model_template.py
```

**第2步**：等待训练完成，自动进入交互模式

训练完成后会显示：
```
======================================================================
训练完成！进入交互模式
======================================================================

现在你可以直接使用以下函数:
  predict_single_point(trained_model, x, y)
  predict_multiple_points(trained_model, points)
  predict_flow_field(trained_model, L, W, nx, ny)

示例:
  u, v, p = predict_single_point(trained_model, 0.005, 0.0001)

输入 exit() 或按 Ctrl+Z 退出

>>>
```

**第3步**：输入命令计算流场

---

### 命令示例

#### 1. 计算单个点的速度和压力

```python
# 格式: u, v, p = predict_single_point(trained_model, x=xxx, y=xxx)
# 注意: 坐标单位必须是米(m)

# 计算芯片中心点 (x=5mm, y=100μm)
>>> u, v, p = predict_single_point(trained_model, x=0.005, y=0.0001)
>>> print(f"u={u:.6e} m/s, v={v:.6e} m/s, p={p:.6e} Pa")

# 计算入口中心 (x=0, y=100μm)
>>> u, v, p = predict_single_point(trained_model, x=0, y=0.0001)

# 计算任意点 (x=3mm, y=50μm)
>>> u, v, p = predict_single_point(trained_model, x=0.003, y=0.00005)
```

#### 2. 批量计算多个点

```python
# 格式: results = predict_multiple_points(trained_model, points)

# 沿中心线分布的10个点
>>> import numpy as np
>>> x_coords = np.linspace(0, 0.01, 10)
>>> y_coords = np.full_like(x_coords, 0.0001)
>>> points = np.column_stack([x_coords, y_coords])
>>> results = predict_multiple_points(trained_model, points)

# 查看结果
>>> print(results['u'])  # 所有点的x方向速度
>>> print(results['p'])  # 所有点的压力

# 任意指定的多个点
>>> test_points = np.array([[0.002, 0.00005], [0.005, 0.00010], [0.008, 0.00015]])
>>> results = predict_multiple_points(trained_model, test_points)
>>> for i, pt in enumerate(test_points):
...     print(f"点{i+1}: u={results['u'][i]:.6e}, p={results['p'][i]:.6e}")
```

#### 3. 生成完整流场（用于可视化）

```python
# 格式: X, Y, U, V, P = predict_flow_field(trained_model, L, W, nx, ny)

>>> X, Y, U, V, P = predict_flow_field(trained_model, L=0.01, W=0.00020)

# 绘制速度幅值云图
>>> import matplotlib.pyplot as plt
>>> velocity = (U**2 + V**2)**0.5
>>> plt.contourf(X*1000, Y*1e6, velocity, levels=50, cmap='jet')
>>> plt.colorbar(label='Velocity (m/s)')
>>> plt.xlabel('x (mm)')
>>> plt.ylabel('y (μm)')
>>> plt.show()
```

---

### 退出程序

```python
>>> exit()
```

---

## 工况参数

| 参数 | 值 | 说明 |
|-----|---|------|
| 通道长度 L | 0.01 m | 10 mm |
| 通道宽度 W | 0.00020 m | 200 μm |
| 入口速度 v_in | 0.0077 m/s | 0.77 cm/s |
| 流体密度 ρ | 1000 kg/m³ | 水 |
| 动力粘度 μ | 0.001 Pa·s | 水 |

**坐标范围**：x ∈ [0, 0.01], y ∈ [0, 0.00020]

---

## 系统要求

- Python 3.8+
- 至少 4GB 内存
- 操作系统：Windows / Linux / macOS

## 依赖安装

```bash
pip install deepxde==1.9.2 tensorflow==2.14.0 numpy>=1.21.0 matplotlib>=3.5.0
```
