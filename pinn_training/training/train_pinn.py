"""
PINN模型训练脚本

用法:
    python train_pinn.py --case v0.8_w150 --epochs 10000
"""

import os
import sys
import argparse
import numpy as np
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# DeepXDE配置
os.environ['DDE_BACKEND'] = 'tensorflow'
import deepxde as dde
# 配置使用float64
dde.config.set_default_float("float64")
from pinn_training.models.navier_stokes import create_microchannel_pinn


class PINNTrainer:
    """PINN模型训练器"""

    # 工况参数配置
    CASES = {
        'v0.2_w150': {'v_in': 0.0015, 'W': 0.00015, 'L': 0.01},  # 0.15 cm/s, 150μm
        'v0.8_w150': {'v_in': 0.0077, 'W': 0.00015, 'L': 0.01},  # 0.77 cm/s, 150μm
        'v1.5_w150': {'v_in': 0.0154, 'W': 0.00015, 'L': 0.01},  # 1.54 cm/s, 150μm
        'v0.2_w200': {'v_in': 0.0015, 'W': 0.00020, 'L': 0.01},  # 0.15 cm/s, 200μm
        'v0.8_w200': {'v_in': 0.0077, 'W': 0.00020, 'L': 0.01},  # 0.77 cm/s, 200μm
        'v1.5_w200': {'v_in': 0.0154, 'W': 0.00020, 'L': 0.01},  # 1.54 cm/s, 200μm
        'v0.2_w250': {'v_in': 0.0015, 'W': 0.00025, 'L': 0.01},  # 0.15 cm/s, 250μm
        'v0.8_w250': {'v_in': 0.0077, 'W': 0.00025, 'L': 0.01},  # 0.77 cm/s, 250μm
        'v1.5_w250': {'v_in': 0.0154, 'W': 0.00025, 'L': 0.01},  # 1.54 cm/s, 250μm
    }

    def __init__(self, case: str = 'v0.8_w200',
                 epochs: int = 10000,
                 lr: float = 1e-3,
                 num_domain: int = 2000,
                 num_boundary: int = 200,
                 checkpoint_dir: str = None):
        """
        初始化训练器

        Args:
            case: 工况名称 (如 v0.8_w200)
            epochs: 训练轮数
            lr: 学习率
            num_domain: 域内采样点数
            num_boundary: 边界采样点数
            checkpoint_dir: 检查点保存目录
        """
        self.case = case
        self.epochs = epochs
        self.lr = lr
        self.num_domain = num_domain
        self.num_boundary = num_boundary

        # 设置检查点目录
        if checkpoint_dir is None:
            checkpoint_dir = Path(__file__).parent.parent / "checkpoints" / case
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # 获取工况参数
        if case not in self.CASES:
            raise ValueError(f"未知工况: {case}. 可选: {list(self.CASES.keys())}")
        self.params = self.CASES[case]

        print(f"工况: {case}")
        print(f"  入口速度: {self.params['v_in']*100:.2f} cm/s")
        print(f"  通道宽度: {self.params['W']*1e6:.0f} μm")
        print(f"  通道长度: {self.params['L']*1000:.1f} mm")

    def create_model(self):
        """创建PINN模型"""
        model, pinn = create_microchannel_pinn(
            x_range=(0, self.params['L']),
            y_range=(0, self.params['W']),
            v_in=self.params['v_in']
        )

        # 编译模型
        model.compile(
            "adam",
            lr=self.lr
        )

        return model, pinn

    def train(self):
        """执行训练"""
        print("\n" + "=" * 50)
        print("开始PINN模型训练")
        print("=" * 50)

        # 创建模型
        print("\n[1/3] 创建模型...")
        model, pinn = self.create_model()
        print(f"  网络结构: {pinn.layers}")
        print(f"  域内采样点: {self.num_domain}")
        print(f"  边界采样点: {self.num_boundary}")

        # 设置检查点
        checkpoint_path = str(self.checkpoint_dir / f"{self.case}_model")
        print(f"\n[2/3] 开始训练 (迭代次数: {self.epochs})...")

        # 训练模型
        losshistory, train_state = model.train(
            iterations=self.epochs,
            display_every=100
        )

        # 保存模型
        print(f"\n[3/3] 保存模型...")
        model.save(f"{checkpoint_path}.model")

        print(f"\n模型已保存至: {checkpoint_path}.model")

        # 打印最终损失
        print(f"\n训练完成! 训练了 {self.epochs} 次迭代")

        print("\n" + "=" * 50)
        print("训练完成!")
        print("=" * 50)

        return model, losshistory, train_state

    def evaluate(self, model):
        """评估模型"""
        print("\n模型评估:")

        # 在域内随机点进行预测
        geom = model.data.geom
        X_test = geom.random_points(1000)
        y_pred = model.predict(X_test)

        u_pred = y_pred[:, 0]
        v_pred = y_pred[:, 1]
        p_pred = y_pred[:, 2]

        print(f"  速度 u 范围: [{u_pred.min():.6e}, {u_pred.max():.6e}] m/s")
        print(f"  速度 v 范围: [{v_pred.min():.6e}, {v_pred.max():.6e}] m/s")
        print(f"  压力 p 范围: [{p_pred.min():.6e}, {p_pred.max():.6e}] Pa")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PINN模型训练')
    parser.add_argument('--case', type=str, default='v0.8_w200',
                       choices=list(PINNTrainer.CASES.keys()),
                       help='工况名称')
    parser.add_argument('--epochs', type=int, default=10000,
                       help='训练轮数')
    parser.add_argument('--lr', type=float, default=1e-3,
                       help='学习率')
    parser.add_argument('--num-domain', type=int, default=2000,
                       help='域内采样点数')
    parser.add_argument('--num-boundary', type=int, default=200,
                       help='边界采样点数')

    args = parser.parse_args()

    # 创建训练器并训练
    trainer = PINNTrainer(
        case=args.case,
        epochs=args.epochs,
        lr=args.lr,
        num_domain=args.num_domain,
        num_boundary=args.num_boundary
    )

    model, losshistory, train_state = trainer.train()
    trainer.evaluate(model)


if __name__ == "__main__":
    main()
