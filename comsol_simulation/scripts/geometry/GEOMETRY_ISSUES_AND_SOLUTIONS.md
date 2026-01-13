# 微流控几何生成 - 问题与解决方案

## 概述

本文档记录了在开发微流控几何生成模块时遇到的常见问题及其解决方案，避免重复犯错。

---

## 问题1：多边形顶点连接顺序错误

### 问题描述
在生成Y型分岔道几何时，多边形顶点的连接顺序错误导致图形异常。

**错误表现：**
- 图形不完整，部分区域缺失
- 点连接顺序错乱（如应该是1234，实际变成了132）
- 线段交叉或重叠

**错误示例：**
```python
# 错误：直接按数学计算的端点构建多边形，顺序混乱
outer_boundary = np.array([
    inlet_bottom,
    main_end_bottom,
    lower_outlet_left,
    lower_outlet_right,
    upper_outlet_right,
    upper_outlet_left,
    main_end_top,
    inlet_top,
])
```

### 根本原因
按照数学计算出的端点位置直接构建多边形，但未考虑实际的拓扑连接顺序。对于复杂的分岔结构，数学方法计算出的端点顺序与实际的边界遍历顺序不一致。

### 正确解决方案
**直接使用用户绘制的线段，保持原有的连接顺序：**

```python
# 正确：按照实际边界遍历顺序构建
# 1. 入口 → 2. 主通道下 → 3. 下分支外壁 → 4. 下分支端口
# → 5. 下分支内壁 → 6. 上分支内壁 → 7. 上分支端口
# → 8. 上分支外壁 → 9. 主通道上 → 10. 回到入口

vertices = [
    inlet_bottom,           # 入口底部
    main_end_bottom,        # 主通道右下
    lower_branch_outer_end, # 下分支外壁终点
    lower_outlet_end,       # 下分支端口
    lower_branch_inner_end, # 下分支内壁终点
    upper_branch_inner_end, # 上分支内壁终点
    upper_outlet_end,       # 上分支端口
    upper_branch_outer_end, # 上分支外壁终点
    main_end_top,           # 主通道右上
    inlet_top,              # 入口顶部
    # 闭合回到起点
]
```

### 关键原则
1. **按边界遍历顺序**：想象沿着边界走一圈的顺序
2. **使用绘制的线段**：直接使用用户绘制的线段，而不是重新计算
3. **逆时针方向**：外边界多边形顶点按逆时针方向排列

---

## 问题2：中心线位置偏移

### 问题描述
从交互式绘图板绘制的数据，中心线不在y=0位置，导致几何位置不标准。

**表现：**
- 主通道中心线在 y≈3.83 而不是 y=0
- 所有点的y坐标都需要平移

### 解决方案
计算需要平移的距离，然后对所有点进行平移：

```python
# 计算中心线y坐标
y_center = (y_top + y_bottom) / 2
y_offset = y_center

def shift_point(x, y):
    """将点平移，使中心线在y=0"""
    return np.array([x, y - y_offset])

# 使用平移后的点
shifted_point = shift_point(original_x, original_y)
```

---

## 问题3：分支不对称

### 问题描述
手绘的图形由于人为原因，上下分支角度不一致。

**表现：**
- 上分支角度约45°，下分支角度约35°
- 导致几何不对称

### 处理方案
根据需求选择处理方式：

**方案A：保持原样（推荐用于完全复现用户绘图）**
```python
# 直接使用用户绘制的线段，不做修正
self.raw_lines = [...]  # 用户绘制的原始线段
```

**方案B：强制对称（推荐用于标准几何模型）**
```python
# 取平均值作为对称角度
avg_angle = (upper_angle + lower_angle) / 2
upper_dir = np.array([np.cos(avg_angle), np.sin(avg_angle)])
lower_dir = np.array([np.cos(avg_angle), -np.sin(avg_angle)])
```

---

## 问题4：绘图板导出格式问题

### 问题描述
最初绘图板只导出图片，无法转换为可用的几何模型代码。

### 解决方案
增强绘图板，添加几何代码导出功能：

```python
def export_geometry(self):
    """导出几何数据"""
    # 1. 保存原始数据（TXT格式）
    # 2. 生成可运行的Python代码
    # 3. 显示代码预览
```

**导出的代码应包含：**
- 完整的类定义
- 所有绘制的线段/矩形数据
- 边界类型标注（INLET, OUTLET, WALL）
- 可直接运行的测试代码

---

## 问题5：边界段定义与多边形顶点不一致

### 问题描述
通过`add_boundary`定义的边界段与多边形顶点顺序不匹配。

### 解决方案
**保持一致性：**
```python
# 方式1：先定义边界段，多边形顶点按边界段的连接点提取
self.add_boundary(p1, p2, type, label)  # 边界段1
self.add_boundary(p2, p3, type, label)  # 边界段2
# ...
vertices = [p1, p2, p3, ...]  # 按相同顺序

# 方式2：直接从绘制的线段构建
# 每条线段对应一个边界段
for line in user_lines:
    p1 = shift_point(line[0], line[1])
    p2 = shift_point(line[2], line[3])
    self.add_boundary([p1, p2], type, label)
```

---

## 最佳实践总结

### 1. 优先使用用户绘制的线段
```python
# ✅ 推荐
def from_user_lines(self, raw_lines):
    """直接使用用户绘制的线段"""
    self.raw_lines = raw_lines
    # 按原始顺序构建
```

### 2. 保持连接顺序
```python
# ✅ 正确：按实际边界遍历顺序
vertices = [start, ...end]  # 逆时针一圈

# ❌ 错误：随意排序
vertices = [random_points]  # 顺序混乱
```

### 3. 坐标标准化
```python
# ✅ 正确：统一坐标系
def normalize_coords(self, points):
    center = calculate_center(points)
    return [p - center for p in points]

# ❌ 错误：直接使用原始坐标
points = raw_points  # 可能在任意位置
```

### 4. 边界标注清晰
```python
# ✅ 正确：明确标注每个边界段
self.add_boundary(inlet, BoundaryType.INLET, "INLET")
self.add_boundary(outlet1, BoundaryType.OUTLET_1, "OUTLET1")
self.add_boundary(wall1, BoundaryType.WALL, "WALL-top")

# ❌ 错误：混淆边界类型
self.add_boundary(wall, BoundaryType.INLET, "WALL")  # 类型错误
```

---

## 调试技巧

### 1. 可视化顶点编号
```python
for i, point in enumerate(vertices):
    ax.plot(point[0], point[1], 'ro')
    ax.text(point[0], point[1], str(i), fontsize=12)
```

### 2. 检查多边形闭合
```python
# 检查首尾点是否相同或非常接近
if np.linalg.norm(vertices[0] - vertices[-1]) > 1e-6:
    print("警告：多边形未闭合！")
```

### 3. 打印边界摘要
```python
geom.print_boundary_summary()
# 查看所有边界段的详细信息
```

---

## 文件组织建议

```
geometry/
├── base_geometry.py          # 基类
├── tjunction.py              # T型（参数化生成）
├── yjunction.py              # Y型（参数化生成，可能有问题）
├── yjunction_from_lines.py   # Y型（基于绘制线段，✅推荐）
├── yjunction_corrected.py    # Y型（修正版）
└── interactive_drawing_board.py  # 交互式绘图板
```

---

## 快速检查清单

开发新的几何类时，确认以下事项：

- [ ] 多边形顶点按逆时针顺序排列
- [ ] 多边形首尾相接，形成封闭区域
- [ ] 边界段与多边形顶点顺序一致
- [ ] 入口/出口正确标注
- [ ] 坐标已标准化（中心线在y=0）
- [ ] 可视化结果正确
- [ ] 所有壁面都标注为WALL
- [ ] 文档说明清晰

---

## 参考资源

- **成功案例**：`yjunction_from_lines.py` - 直接基于用户绘制线段的实现
- **问题案例**：`yjunction.py` - 纯数学计算方法，存在顶点顺序问题
- **工具**：`interactive_drawing_board.py` - 交互式绘图板，可用于测试几何形状

---

*文档创建日期：2026-01-13*
*最后更新：2026-01-13*
