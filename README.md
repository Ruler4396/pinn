# 微流控芯片PINNs项目

基于COMSOL模拟数据训练物理信息神经网络(PINNs)，实现微流控芯片流场可视化软件。

## 项目结构

```
PINNs/
├── comsol_simulation/          # COMSOL模拟相关
├── pinn_training/              # PINNs训练相关
├── visualization/              # 可视化软件
├── deployment/                 # 部署相关
├── tests/                      # 测试用例
├── project_plan.md             # 详细项目规划
└── README.md                   # 项目说明
```

## 快速开始

### 环境要求
- Python 3.8+
- COMSOL Multiphysics 6.0+
- CUDA Toolkit (可选，用于GPU加速)

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行示例
```bash
# COMSOL模拟
python comsol_simulation/scripts/run_simulation.py

# PINNs训练
python pinn_training/training/train_pinn.py

# 可视化软件
python visualization/app.py
```

## 项目进展

- [x] 项目规划
- [x] 目录结构创建
- [ ] COMSOL模型开发
- [ ] PINNs训练框架
- [ ] 可视化软件开发
- [ ] 软件打包部署

详细规划请参见 [project_plan.md](./project_plan.md)