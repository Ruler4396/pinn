"""
COMSOL数据加载器

为PINNs训练提供数据加载和预处理功能
支持从HDF5文件加载COMSOL模拟数据

作者: PINNs项目组
创建时间: 2025-11-19
"""

import os
import sys
import numpy as np
import h5py
from pathlib import Path
from typing import Dict, Tuple, Optional
import matplotlib.pyplot as plt

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


class COMSOLDataLoader:
    """COMSOL模拟数据加载器"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化数据加载器
        
        Args:
            data_dir: 数据目录路径，默认为 comsol_simulation/data
        """
        if data_dir is None:
            data_dir = project_root / "comsol_simulation" / "data"
        
        self.data_dir = Path(data_dir)
        self.current_data = None
        
    def load_hdf5_data(self, filename: str) -> Dict:
        """
        从HDF5文件加载COMSOL数据
        
        Args:
            filename: HDF5文件名
            
        Returns:
            dict: 包含所有数据的字典
        """
        file_path = self.data_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {file_path}")
        
        print(f"📁 加载数据文件: {filename}")
        
        try:
            with h5py.File(file_path, 'r') as h5file:
                data = {}
                
                # 加载基本信息
                info_group = h5file.get('info')
                if info_group:
                    data['info'] = dict(info_group.attrs)
                
                # 加载网格数据
                mesh_group = h5file.get('mesh')
                if mesh_group:
                    data['mesh'] = {
                        'x': mesh_group['x'][:],
                        'y': mesh_group['y'][:],
                        'num_nodes': mesh_group.attrs['num_nodes']
                    }
                
                # 加载求解数据
                solution_group = h5file.get('solution')
                if solution_group:
                    data['solution'] = {
                        'u': solution_group['u'][:],
                        'v': solution_group['v'][:],
                        'p': solution_group['p'][:]
                    }
                
                # 加载统计信息
                stats_group = h5file.get('statistics')
                if stats_group:
                    data['statistics'] = {}
                    for field in ['u', 'v', 'p']:
                        if field in stats_group:
                            data['statistics'][field] = dict(stats_group[field].attrs)
                
                self.current_data = data
                print(f"✅ 数据加载成功")
                return data
                
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            raise
    
    def get_training_data(self, data: Optional[Dict] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取PINNs训练所需的数据格式
        
        Args:
            data: 数据字典，如果为None则使用当前加载的数据
            
        Returns:
            tuple: (输入数据, 输出数据)
        """
        if data is None:
            if self.current_data is None:
                raise ValueError("没有加载的数据，请先调用load_hdf5_data")
            data = self.current_data
        
        # 提取坐标
        x = data['mesh']['x'].reshape(-1, 1)  # (N, 1)
        y = data['mesh']['y'].reshape(-1, 1)  # (N, 1)
        
        # 提取流场数据
        u = data['solution']['u'].reshape(-1, 1)  # (N, 1)
        v = data['solution']['v'].reshape(-1, 1)  # (N, 1)
        p = data['solution']['p'].reshape(-1, 1)  # (N, 1)
        
        # 组合输入 (x, y坐标)
        X_train = np.hstack([x, y])  # (N, 2)
        
        # 组合输出 (u, v, p)
        Y_train = np.hstack([u, v, p])  # (N, 3)
        
        print(f"📊 训练数据格式:")
        print(f"   输入形状: {X_train.shape} (x, y)")
        print(f"   输出形状: {Y_train.shape} (u, v, p)")
        
        return X_train, Y_train
    
    def normalize_data(self, X: np.ndarray, Y: np.ndarray, 
                      method: str = 'minmax') -> Tuple[np.ndarray, np.ndarray, Dict]:
        """
        数据归一化
        
        Args:
            X: 输入数据 (N, 2)
            Y: 输出数据 (N, 3)
            method: 归一化方法 ('minmax' 或 'standard')
            
        Returns:
            tuple: (归一化X, 归一化Y, 归一化参数)
        """
        print(f"🔧 数据归一化 (方法: {method})")
        
        normalization_params = {}
        
        if method == 'minmax':
            # Min-Max归一化到[0, 1]
            x_min, x_max = X.min(axis=0), X.max(axis=0)
            y_min, y_max = Y.min(axis=0), Y.max(axis=0)
            
            X_norm = (X - x_min) / (x_max - x_min)
            Y_norm = (Y - y_min) / (y_max - y_min)
            
            normalization_params = {
                'method': 'minmax',
                'x_min': x_min,
                'x_max': x_max,
                'y_min': y_min,
                'y_max': y_max
            }
            
        elif method == 'standard':
            # 标准化 (均值0, 标准差1)
            x_mean, x_std = X.mean(axis=0), X.std(axis=0)
            y_mean, y_std = Y.mean(axis=0), Y.std(axis=0)
            
            X_norm = (X - x_mean) / x_std
            Y_norm = (Y - y_mean) / y_std
            
            normalization_params = {
                'method': 'standard',
                'x_mean': x_mean,
                'x_std': x_std,
                'y_mean': y_mean,
                'y_std': y_std
            }
        else:
            raise ValueError(f"不支持的归一化方法: {method}")
        
        print(f"✅ 归一化完成")
        return X_norm, Y_norm, normalization_params
    
    def denormalize_data(self, X_norm: np.ndarray, Y_norm: np.ndarray, 
                        params: Dict) -> Tuple[np.ndarray, np.ndarray]:
        """
        反归一化数据
        
        Args:
            X_norm: 归一化的输入数据
            Y_norm: 归一化的输出数据
            params: 归一化参数
            
        Returns:
            tuple: (原始X, 原始Y)
        """
        method = params['method']
        
        if method == 'minmax':
            X = X_norm * (params['x_max'] - params['x_min']) + params['x_min']
            Y = Y_norm * (params['y_max'] - params['y_min']) + params['y_min']
        elif method == 'standard':
            X = X_norm * params['x_std'] + params['x_mean']
            Y = Y_norm * params['y_std'] + params['y_mean']
        else:
            raise ValueError(f"不支持的归一化方法: {method}")
        
        return X, Y
    
    def split_data(self, X: np.ndarray, Y: np.ndarray, 
                  train_ratio: float = 0.7, val_ratio: float = 0.15,
                  random_seed: int = 42) -> Dict[str, np.ndarray]:
        """
        数据集分割
        
        Args:
            X: 输入数据
            Y: 输出数据
            train_ratio: 训练集比例
            val_ratio: 验证集比例
            random_seed: 随机种子
            
        Returns:
            dict: 包含训练、验证、测试数据的字典
        """
        np.random.seed(random_seed)
        
        N = len(X)
        indices = np.random.permutation(N)
        
        train_end = int(N * train_ratio)
        val_end = int(N * (train_ratio + val_ratio))
        
        train_indices = indices[:train_end]
        val_indices = indices[train_end:val_end]
        test_indices = indices[val_end:]
        
        data_split = {
            'X_train': X[train_indices],
            'Y_train': Y[train_indices],
            'X_val': X[val_indices],
            'Y_val': Y[val_indices],
            'X_test': X[test_indices],
            'Y_test': Y[test_indices]
        }
        
        print(f"📊 数据分割完成:")
        print(f"   训练集: {len(train_indices)} 样本 ({train_ratio*100:.1f}%)")
        print(f"   验证集: {len(val_indices)} 样本 ({val_ratio*100:.1f}%)")
        print(f"   测试集: {len(test_indices)} 样本 ({(1-train_ratio-val_ratio)*100:.1f}%)")
        
        return data_split
    
    def save_processed_data(self, data_split: Dict[str, np.ndarray], 
                          filename: str, normalization_params: Dict):
        """
        保存处理后的数据
        
        Args:
            data_split: 分割后的数据字典
            filename: 保存文件名
            normalization_params: 归一化参数
        """
        output_path = self.data_dir / f"processed_{filename}"
        
        print(f"💾 保存处理后的数据到: {output_path}")
        
        try:
            with h5py.File(output_path, 'w') as h5file:
                # 保存归一化参数
                norm_group = h5file.create_group('normalization')
                for key, value in normalization_params.items():
                    if isinstance(value, np.ndarray):
                        norm_group.create_dataset(key, data=value)
                    else:
                        norm_group.attrs[key] = value
                
                # 保存数据集
                for key, value in data_split.items():
                    h5file.create_dataset(key, data=value)
                
                # 添加元数据
                h5file.attrs['creation_time'] = str(np.datetime64('now'))
                h5file.attrs['description'] = 'Processed data for PINN training'
            
            print(f"✅ 数据保存成功")
            
        except Exception as e:
            print(f"❌ 数据保存失败: {e}")
            raise
    
    def create_batch_generator(self, X: np.ndarray, Y: np.ndarray, 
                             batch_size: int = 32, shuffle: bool = True):
        """
        创建批量数据生成器
        
        Args:
            X: 输入数据
            Y: 输出数据
            batch_size: 批次大小
            shuffle: 是否打乱数据
            
        Yields:
            tuple: (batch_X, batch_Y)
        """
        N = len(X)
        indices = np.arange(N)
        
        if shuffle:
            np.random.shuffle(indices)
        
        for start_idx in range(0, N, batch_size):
            end_idx = min(start_idx + batch_size, N)
            batch_indices = indices[start_idx:end_idx]
            
            yield X[batch_indices], Y[batch_indices]
    
    def visualize_data_distribution(self, X: np.ndarray, Y: np.ndarray, 
                                  save_path: Optional[str] = None):
        """
        可视化数据分布
        
        Args:
            X: 输入数据
            Y: 输出数据
            save_path: 保存路径
        """
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        fig.suptitle('COMSOL数据分布', fontsize=16)
        
        # 坐标分布
        axes[0, 0].scatter(X[:, 0], X[:, 1], s=1, alpha=0.6)
        axes[0, 0].set_xlabel('X (mm)')
        axes[0, 0].set_ylabel('Y (mm)')
        axes[0, 0].set_title('坐标分布')
        axes[0, 0].set_aspect('equal')
        
        # 速度分量分布
        axes[0, 1].hist(Y[:, 0], bins=50, alpha=0.7, label='u')
        axes[0, 1].set_xlabel('u (m/s)')
        axes[0, 1].set_ylabel('频次')
        axes[0, 1].set_title('X方向速度分布')
        axes[0, 1].legend()
        
        axes[0, 2].hist(Y[:, 1], bins=50, alpha=0.7, label='v', color='orange')
        axes[0, 2].set_xlabel('v (m/s)')
        axes[0, 2].set_ylabel('频次')
        axes[0, 2].set_title('Y方向速度分布')
        axes[0, 2].legend()
        
        # 压力分布
        axes[1, 0].hist(Y[:, 2], bins=50, alpha=0.7, label='p', color='red')
        axes[1, 0].set_xlabel('p (Pa)')
        axes[1, 0].set_ylabel('频次')
        axes[1, 0].set_title('压力分布')
        axes[1, 0].legend()
        
        # 速度场
        speed = np.sqrt(Y[:, 0]**2 + Y[:, 1]**2)
        scatter = axes[1, 1].scatter(X[:, 0], X[:, 1], c=speed, s=1, cmap='viridis')
        axes[1, 1].set_xlabel('X (mm)')
        axes[1, 1].set_ylabel('Y (mm)')
        axes[1, 1].set_title('速度幅值')
        axes[1, 1].set_aspect('equal')
        plt.colorbar(scatter, ax=axes[1, 1])
        
        # 压力场
        scatter2 = axes[1, 2].scatter(X[:, 0], X[:, 1], c=Y[:, 2], s=1, cmap='coolwarm')
        axes[1, 2].set_xlabel('X (mm)')
        axes[1, 2].set_ylabel('Y (mm)')
        axes[1, 2].set_title('压力场')
        axes[1, 2].set_aspect('equal')
        plt.colorbar(scatter2, ax=axes[1, 2])
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"📈 数据分布图已保存: {save_path}")
        else:
            plt.show()


def main():
    """主函数 - 演示数据加载和处理流程"""
    print("🌟 COMSOL数据加载器演示")
    
    # 创建数据加载器
    loader = COMSOLDataLoader()
    
    # 查找数据文件
    h5_files = list(loader.data_dir.glob("*.h5"))
    
    if not h5_files:
        print("❌ 未找到HDF5数据文件")
        return
    
    # 使用最新的数据文件
    data_file = h5_files[-1].name
    print(f"📁 使用数据文件: {data_file}")
    
    try:
        # 1. 加载数据
        data = loader.load_hdf5_data(data_file)
        
        # 2. 获取训练数据
        X, Y = loader.get_training_data()
        
        # 3. 数据归一化
        X_norm, Y_norm, norm_params = loader.normalize_data(X, Y, method='minmax')
        
        # 4. 数据分割
        data_split = loader.split_data(X_norm, Y_norm)
        
        # 5. 保存处理后的数据
        output_filename = f"processed_{data_file}"
        loader.save_processed_data(data_split, output_filename, norm_params)
        
        # 6. 可视化数据分布
        plot_path = loader.data_dir / "data_distribution.png"
        loader.visualize_data_distribution(X, Y, save_path=str(plot_path))
        
        # 7. 测试批量生成器
        print("\n🧪 测试批量生成器:")
        for i, (batch_X, batch_Y) in enumerate(loader.create_batch_generator(
                data_split['X_train'], data_split['Y_train'], batch_size=16)):
            print(f"   批次 {i+1}: X shape={batch_X.shape}, Y shape={batch_Y.shape}")
            if i >= 2:  # 只测试前几个批次
                break
        
        print("\n✅ 数据处理演示完成！")
        print("🚀 数据已准备好用于PINNs训练")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()