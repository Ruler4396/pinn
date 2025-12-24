# COMSOL数据真实性检验指南

## 1. 综合验证脚本

### 快速验证所有数据
```bash
python comsol_simulation/scripts/tests/comprehensive_data_validation.py
```

该脚本会自动执行5大维度的验证：
- ✅ 数据完整性 (NaN、无穷值、零值)
- ✅ 物理一致性 (速度方向、壁面条件、压力分布)
- ✅ 理论一致性 (Reynolds数、压降、泊肃叶流)
- ✅ 数值特性 (数据密度、异常值)
- ✅ 可视化检查 (云图、剖面图、直方图)

### 验证单个文件
```bash
python comsol_simulation/scripts/tests/comprehensive_data_validation.py path/to/file.h5
```

---

## 2. 人工验证清单

### 2.1 数据完整性检查

#### ✅ 无NaN/无穷值
```python
import h5py
import numpy as np

with h5py.File('data.h5', 'r') as f:
    u = f['u'][:]
    v = f['v'][:]
    p = f['p'][:]

print(f"NaN值: u={np.isnan(u).sum()}, v={np.isnan(v).sum()}, p={np.isnan(p).sum()}")
print(f"无穷值: u={np.isinf(u).sum()}, v={np.isinf(v).sum()}, p={np.isinf(p).sum()}")
```

**期望结果**: 全部为0

#### ✅ 数据非零
```python
print(f"速度范围: u=[{u.min():.6f}, {u.max():.6f}]")
print(f"压力范围: p=[{p.min():.2f}, {p.max():.2f}]")
```

**期望结果**: 速度和压力都有合理的数值范围

---

### 2.2 物理一致性检查

#### ✅ 层流特征验证

1. **速度方向**: 主速度应为x方向
```python
u_ratio = np.abs(u).mean() / np.sqrt(u**2 + v**2).mean()
print(f"u_ratio = {u_ratio:.3f}")  # 应该接近1.0
```

2. **壁面无滑移**: 壁面速度应接近0
```python
y = f['y'][:]
y_max = y.max()
wall_points = y > y_max * 0.99
wall_velocity = np.sqrt(u[wall_points]**2 + v[wall_points]**2).mean()
print(f"壁面速度: {wall_velocity:.6f} m/s")  # 应该 < 0.001 m/s
```

3. **压力分布**: 入口压力 > 出口压力
```python
x = f['x'][:]
p_inlet = p[x < x.max() * 0.1].mean()
p_outlet = p[x > x.max() * 0.9].mean()
print(f"入口压力: {p_inlet:.2f} Pa")
print(f"出口压力: {p_outlet:.2f} Pa")
print(f"压降: {p_inlet - p_outlet:.2f} Pa")
```

---

### 2.3 理论一致性检查

#### ✅ Reynolds数验证
```python
# 从元数据获取参数
v_in_cm_s = 0.4  # cm/s
width_um = 150  # μm

# 物理参数
rho = 1000.0  # kg/m³
mu = 0.001    # Pa·s

# 计算Reynolds数: Re = ρvD/μ
Re = rho * (v_in_cm_s/100) * (width_um * 1e-6) / mu
print(f"Reynolds数: {Re:.2f}")

# 判断流态
if Re < 2000:
    print("✅ 层流")
elif Re < 4000:
    print("⚠️ 过渡区")
else:
    print("❌ 湍流 (超出层流假设)")
```

#### ✅ 速度分布验证 (泊肃叶流)

对于充分发展的层流，理论最大速度约为平均速度的1.5-2.0倍：
```python
u_max = np.sqrt(u**2 + v**2).max()
u_avg = np.sqrt(u**2 + v**2).mean()
ratio = u_max / u_avg
print(f"u_max/u_avg = {ratio:.2f}")  # 应该在 1.3-2.5 之间
```

---

### 2.4 可视化检查

#### 快速可视化脚本
```python
import h5py
import matplotlib.pyplot as plt
import numpy as np

with h5py.File('data.h5', 'r') as f:
    x = f['x'][:] * 1000  # mm
    y = f['y'][:] * 1e6   # μm
    u = f['u'][:]
    p = f['p'][:]

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# 速度云图
scatter1 = axes[0].scatter(x, y, c=u, s=1, cmap='jet')
axes[0].set_xlabel('X (mm)')
axes[0].set_ylabel('Y (μm)')
axes[0].set_title('X方向速度')
plt.colorbar(scatter1, ax=axes[0])

# 压力云图
scatter2 = axes[1].scatter(x, y, c=p, s=1, cmap='viridis')
axes[1].set_xlabel('X (mm)')
axes[1].set_ylabel('Y (μm)')
axes[1].set_title('压力')
plt.colorbar(scatter2, ax=axes[1])

plt.tight_layout()
plt.show()
```

---

### 2.5 与现有数据对比

#### 对比相同参数的数据
```python
def compare_datasets(file1, file2):
    """对比两个数据文件"""
    with h5py.File(file1, 'r') as f1, h5py.File(file2, 'r') as f2:
        u1, p1 = f1['u'][:], f1['p'][:]
        u2, p2 = f2['u'][:], f2['p'][:]

    print(f"{file1}: U_max={u1.max():.6f}, P_range={p1.max()-p1.min():.2f}")
    print(f"{file2}: U_max={u2.max():.6f}, P_range={p2.max()-p2.min():.2f}")

# 示例: 对比新旧数据
compare_datasets('data/v0.8_w150.h5', 'data/v0.4_w150.h5')
```

---

## 3. 常见问题排查

### 问题1: 数据全为零
**症状**: `u.max() ≈ 0`, `p.max() ≈ 0`

**可能原因**:
- COMSOL求解未完成
- 边界条件未设置
- 使用了错误的dataset

**解决方案**:
- 检查COMSOL模型是否求解成功
- 验证入口速度边界条件
- 确认使用正确的数据集进行导出

### 问题2: 速度方向异常
**症状**: `u_ratio << 1.0`

**可能原因**:
- 坐标系定义错误
- 边界条件设置错误

**解决方案**:
- 检查COMSOL几何方向定义
- 验证入口/出口边界选择

### 问题3: 压力分布异常
**症状**: 出口压力 > 入口压力

**可能原因**:
- 边界条件设置反向
- 出口条件不是大气压

**解决方案**:
- 确认入口是速度边界、出口是压力边界
- 设置出口压力为0 (表压)

---

## 4. 验证标准参考

| 检查项 | 合格标准 |
|--------|----------|
| **完整性** | NaN=0, Inf=0, 数据点>10000 |
| **Reynolds数** | < 2000 (层流) |
| **速度方向** | u_ratio > 0.8 |
| **壁面速度** | < 0.001 m/s |
| **压力梯度** | 入口 > 出口 |
| **速度分布** | 1.3 < u_max/u_avg < 2.5 |
| **异常值比例** | < 1% |
| **压降偏差** | 0.5 < 实际/理论 < 2.0 |

---

## 5. 自动化验证命令

### 验证所有新生成的数据
```bash
python comsol_simulation/scripts/tests/comprehensive_data_validation.py
```

### 验证特定文件
```bash
python comsol_simulation/scripts/tests/comprehensive_data_validation.py data/v0.4_w150.h5
```

### 查看验证报告和可视化图
验证脚本会自动保存图片到: `comsol_simulation/logs/validation_*.png`

---

## 6. 质量评分标准

| 等级 | 条件 |
|------|------|
| **优秀** | 所有检查项通过，理论值偏差<20% |
| **良好** | 核心检查项通过，理论值偏差<50% |
| **可用** | 完整性检查通过，部分物理检查有偏差 |
| **不合格** | 完整性检查失败或严重违反物理规律 |

---

**参考资源**:
- 泊肃叶流理论: `ΔP = (128μLQ)/(πD⁴)` (圆形管道)
- 达西-韦史巴赫方程: `ΔP = f·(L/D)·(ρv²/2)`
- Reynolds数定义: `Re = ρvD/μ`

**作者**: PINNs项目组
**更新日期**: 2025-12-24
