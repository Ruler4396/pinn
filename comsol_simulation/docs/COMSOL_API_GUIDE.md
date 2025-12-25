# COMSOL Python API 正确调用方式

## 问题总结

在使用COMSOL Python API（mph库）生成微流控芯片数据时，遇到了以下关键问题：

1. **材料属性设置** - 不能通过Material对象设置，必须通过Physics的FluidProperties节点
2. **坐标单位问题** - Export导出的坐标可能是mm单位，需要转换
3. **数据格式问题** - Export的expr顺序与输出顺序要一致

## 正确的API调用方式

### 1. 设置流体属性（关键）

```python
import mph

client = mph.Client()
model = client.create("model_name")
java_model = model.java

# 创建几何
geom = java_model.geom().create('geom1', 2)
geom.lengthUnit('mm')  # 使用mm单位
# ... 创建几何 ...

# 创建物理场
physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')

# ⚠️ 关键：通过FluidProperties节点设置流体属性
fp = physics.feature('fp1')
fp.set('mu_mat', 'userdef')      # 使用用户定义值
fp.set('mu', f'{viscosity} [Pa*s]')
fp.set('rho_mat', 'userdef')     # 使用用户定义值
fp.set('rho', f'{density} [kg/m^3]')

# ❌ 错误方式：不要使用Material对象
# mat = java_model.material().create('mat1')
# mat.propertyGroup('def').set('mu', ...)  # 这不会生效
```

### 2. 数据导出（关键）

```python
# 创建Export节点
export = java_model.result().export().create('export1', 'Data')
export.set('expr', ['x', 'y', 'u', 'v', 'p'])  # 顺序很重要
export.set('filename', 'output_file.txt')
export.run()

# 读取数据时注意单位转换
with open('output_file.txt', 'r') as f:
    for line in f:
        parts = line.split()
        x = float(parts[0])
        y = float(parts[1])
        u = float(parts[2])
        v = float(parts[3])
        p = float(parts[4])

        # ⚠️ 坐标可能需要单位转换
        if x > 1:  # 如果x>1，可能是mm单位
            x /= 1000
            y /= 1000
```

### 3. 完整示例

```python
import mph
import h5py
import numpy as np

def create_microchannel_model(client, v_in, width):
    """创建微通道模型"""
    model = client.create("microchannel")
    java_model = model.java

    # 1. 创建几何
    geom = java_model.geom().create('geom1', 2)
    geom.lengthUnit('mm')
    rect = geom.feature().create('rect1', 'Rectangle')
    rect.set('size', [f'{10}', f'{width*1000}'])  # mm
    rect.set('pos', ['0', '0'])
    geom.run()

    # 2. 创建物理场
    physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')

    # 3. 设置流体属性
    fp = physics.feature('fp1')
    fp.set('mu_mat', 'userdef')
    fp.set('mu', '0.001 [Pa*s]')
    fp.set('rho_mat', 'userdef')
    fp.set('rho', '1000 [kg/m^3]')

    # 4. 设置边界条件
    inlet = physics.feature().create('in1', 'Inlet')
    inlet.selection().set([1])
    inlet.set('U0in', f'{v_in}')

    outlet = physics.feature().create('out1', 'Outlet')
    outlet.selection().set([2])
    outlet.set('p0', '0')

    wall = physics.feature().create('wall1', 'Wall')
    wall.selection().set([3, 4])

    # 5. 网格和求解
    mesh = java_model.mesh().create('mesh1', 'geom1')
    mesh.autoMeshSize(5)
    mesh.run()

    study = java_model.study().create('std1')
    study.feature().create('stat', 'Stationary')
    study.run()

    return model

def export_data(model, output_file):
    """导出数据到HDF5"""
    java_model = model.java

    # 导出
    export = java_model.result().export().create('export1', 'Data')
    export.set('expr', ['x', 'y', 'u', 'v', 'p'])
    export.set('filename', str(output_file))
    export.run()

    # 读取并保存
    data = []
    with open(output_file, 'r') as f:
        for line in f:
            if not line.startswith('%'):
                parts = line.split()
                if len(parts) >= 5:
                    x, y, u, v, p = map(float, parts[:5])
                    # 单位转换
                    if x > 1:
                        x, y = x/1000, y/1000
                    data.append([x, y, u, v, p])

    results = np.array(data)

    # 保存HDF5
    with h5py.File('output.h5', 'w') as f:
        f.create_dataset('x', data=results[:, 0])
        f.create_dataset('y', data=results[:, 1])
        f.create_dataset('u', data=results[:, 2])
        f.create_dataset('v', data=results[:, 3])
        f.create_dataset('p', data=results[:, 4])
```

## 数据真实性验证

生成的数据应满足以下物理特征：

1. **泊肃叶流速度剖面** - 抛物线分布，中心速度最大，壁面为0
2. **压力梯度** - 沿流动方向线性下降
3. **无滑移边界** - 壁面速度接近0

验证代码：
```python
# 检查速度剖面
u_std = np.std(u)  # 应该>0
wall_u = u[np.abs(y - y.max()) < 1e-6].max()  # 应该接近0
center_u = u[np.abs(y - y.mean()) < 1e-6].max()  # 应该最大

# 检查压力梯度
p_corr = np.corrcoef(x, p)[0, 1]  # 应该接近-1
```
