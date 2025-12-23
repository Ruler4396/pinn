"""
数据预处理脚本 - 将COMSOL数据转换为PINNs训练格式

功能:
1. 加载9组HDF5数据
2. 数据归一化
3. 数据集划分 (训练/验证/测试)
4. 保存预处理结果
"""

import os
import h5py
import numpy as np
from pathlib import Path
from typing import Tuple, Dict
import pickle


class DataPreprocessor:
    """COMSOL数据预处理器"""

    def __init__(self, data_dir: str, output_dir: str = None):
        """
        初始化预处理器

        Args:
            data_dir: COMSOL数据目录
            output_dir: 预处理结果输出目录
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir) if output_dir else self.data_dir / "../processed"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 归一化统计量
        self.stats = {}

        # 数据文件列表
        self.data_files = [
            "v0.2_w150.h5", "v0.8_w150.h5", "v1.5_w150.h5",
            "v0.2_w200.h5", "v0.8_w200.h5", "v1.5_w200.h5",
            "v0.2_w250.h5", "v0.8_w250.h5", "v1.5_w250.h5",
        ]

    def load_single_data(self, filepath: str) -> Dict[str, np.ndarray]:
        """加载单个HDF5文件"""
        with h5py.File(filepath, 'r') as f:
            return {
                'coordinates': f['coordinates'][:],
                'velocity_u': f['velocity_u'][:],
                'velocity_v': f['velocity_v'][:],
                'pressure': f['pressure'][:],
            }

    def load_all_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        加载所有数据并合并

        Returns:
            X: 坐标数据 (N, 2)
            y: 物理量数据 (N, 3) - [u, v, p]
        """
        all_coords = []
        all_velocity_u = []
        all_velocity_v = []
        all_pressure = []

        for filename in self.data_files:
            filepath = self.data_dir / filename
            if not filepath.exists():
                print(f"警告: 文件不存在 {filepath}")
                continue

            data = self.load_single_data(str(filepath))
            all_coords.append(data['coordinates'])
            all_velocity_u.append(data['velocity_u'].reshape(-1, 1))
            all_velocity_v.append(data['velocity_v'].reshape(-1, 1))
            all_pressure.append(data['pressure'].reshape(-1, 1))

            print(f"已加载: {filename}, 数据点: {len(data['coordinates'])}")

        # 合并所有数据
        X = np.vstack(all_coords)
        u = np.vstack(all_velocity_u)
        v = np.vstack(all_velocity_v)
        p = np.vstack(all_pressure)

        y = np.hstack([u, v, p])

        print(f"\n总数据量: {X.shape[0]} 数据点")
        return X, y

    def compute_normalization_stats(self, X: np.ndarray, y: np.ndarray):
        """计算归一化统计量"""
        # 坐标归一化 (Min-Max)
        self.stats['x_min'] = X[:, 0].min()
        self.stats['x_max'] = X[:, 0].max()
        self.stats['y_min'] = X[:, 1].min()
        self.stats['y_max'] = X[:, 1].max()

        # 物理量归一化 (Standardization)
        self.stats['u_mean'] = y[:, 0].mean()
        self.stats['u_std'] = y[:, 0].std()
        self.stats['v_mean'] = y[:, 1].mean()
        self.stats['v_std'] = y[:, 1].std()
        self.stats['p_mean'] = y[:, 2].mean()
        self.stats['p_std'] = y[:, 2].std()

        print("\n归一化统计量:")
        for key, value in self.stats.items():
            print(f"  {key}: {value:.6e}")

    def normalize(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        数据归一化

        Args:
            X: 坐标 (N, 2)
            y: 物理量 (N, 3)

        Returns:
            X_norm: 归一化后的坐标
            y_norm: 归一化后的物理量
        """
        X_norm = X.copy()
        y_norm = y.copy()

        # 坐标 Min-Max 归一化到 [0, 1]
        X_norm[:, 0] = (X[:, 0] - self.stats['x_min']) / (self.stats['x_max'] - self.stats['x_min'])
        X_norm[:, 1] = (X[:, 1] - self.stats['y_min']) / (self.stats['y_max'] - self.stats['y_min'])

        # 物理量 标准化
        y_norm[:, 0] = (y[:, 0] - self.stats['u_mean']) / self.stats['u_std']
        y_norm[:, 1] = (y[:, 1] - self.stats['v_mean']) / self.stats['v_std']
        y_norm[:, 2] = (y[:, 2] - self.stats['p_mean']) / self.stats['p_std']

        return X_norm, y_norm

    def split_data(self, X: np.ndarray, y: np.ndarray,
                   train_ratio: float = 0.7,
                   val_ratio: float = 0.15,
                   test_ratio: float = 0.15,
                   random_seed: int = 42) -> Tuple:
        """
        数据集划分

        Args:
            X: 特征数据
            y: 标签数据
            train_ratio: 训练集比例
            val_ratio: 验证集比例
            test_ratio: 测试集比例
            random_seed: 随机种子

        Returns:
            (X_train, y_train), (X_val, y_val), (X_test, y_test)
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6

        np.random.seed(random_seed)
        N = len(X)
        indices = np.random.permutation(N)

        train_end = int(N * train_ratio)
        val_end = train_end + int(N * val_ratio)

        train_indices = indices[:train_end]
        val_indices = indices[train_end:val_end]
        test_indices = indices[val_end:]

        return (
            (X[train_indices], y[train_indices]),
            (X[val_indices], y[val_indices]),
            (X[test_indices], y[test_indices])
        )

    def save_processed_data(self, train_data, val_data, test_data):
        """保存预处理后的数据"""
        output_file = self.output_dir / "processed_data.npz"
        np.savez(
            output_file,
            X_train=train_data[0], y_train=train_data[1],
            X_val=val_data[0], y_val=val_data[1],
            X_test=test_data[0], y_test=test_data[1]
        )
        print(f"\n数据已保存至: {output_file}")

        # 保存归一化统计量
        stats_file = self.output_dir / "normalization_stats.pkl"
        with open(stats_file, 'wb') as f:
            pickle.dump(self.stats, f)
        print(f"归一化统计量已保存至: {stats_file}")

    def run(self):
        """执行完整预处理流程"""
        print("=" * 50)
        print("开始数据预处理")
        print("=" * 50)

        # 1. 加载数据
        print("\n[1/5] 加载数据...")
        X, y = self.load_all_data()

        # 2. 计算归一化统计量
        print("\n[2/5] 计算归一化统计量...")
        self.compute_normalization_stats(X, y)

        # 3. 归一化
        print("\n[3/5] 归一化数据...")
        X_norm, y_norm = self.normalize(X, y)

        # 4. 数据集划分
        print("\n[4/5] 划分数据集...")
        train_data, val_data, test_data = self.split_data(X_norm, y_norm)
        print(f"  训练集: {train_data[0].shape[0]} 数据点 ({train_data[0].shape[0]/X.shape[0]*100:.1f}%)")
        print(f"  验证集: {val_data[0].shape[0]} 数据点 ({val_data[0].shape[0]/X.shape[0]*100:.1f}%)")
        print(f"  测试集: {test_data[0].shape[0]} 数据点 ({test_data[0].shape[0]/X.shape[0]*100:.1f}%)")

        # 5. 保存结果
        print("\n[5/5] 保存预处理结果...")
        self.save_processed_data(train_data, val_data, test_data)

        print("\n" + "=" * 50)
        print("数据预处理完成!")
        print("=" * 50)


def main():
    """主函数"""
    # 数据目录
    data_dir = Path(__file__).parent.parent.parent / "comsol_simulation" / "data"
    output_dir = Path(__file__).parent.parent / "data_preprocessing" / "output"

    # 创建预处理器并运行
    preprocessor = DataPreprocessor(str(data_dir), str(output_dir))
    preprocessor.run()


if __name__ == "__main__":
    main()
