"""
验证导出的COMSOL数据

检查HDF5文件中的数据完整性和格式正确性
"""

import sys
import numpy as np
import h5py
import matplotlib.pyplot as plt
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


def load_and_validate_hdf5(file_path):
    """
    加载并验证HDF5数据文件
    
    Args:
        file_path: HDF5文件路径
        
    Returns:
        dict: 验证结果
    """
    print(f"🔍 验证数据文件: {file_path}")
    
    try:
        with h5py.File(file_path, 'r') as h5file:
            validation_results = {}
            
            # 检查文件结构
            print("\n📋 文件结构:")
            def print_structure(name, obj):
                print(f"   {name}: {type(obj).__name__}")
            h5file.visititems(print_structure)
            
            # 验证基本信息
            print("\nℹ️ 基本信息:")
            info_group = h5file.get('info')
            if info_group:
                for key, value in info_group.attrs.items():
                    print(f"   {key}: {value}")
                    validation_results[key] = value
            
            # 验证网格数据
            print("\n📐 网格数据验证:")
            mesh_group = h5file.get('mesh')
            if mesh_group:
                x_data = mesh_group['x'][:]
                y_data = mesh_group['y'][:]
                
                print(f"   X坐标范围: {np.min(x_data):.3f} ~ {np.max(x_data):.3f} mm")
                print(f"   Y坐标范围: {np.min(y_data):.3f} ~ {np.max(y_data):.3f} mm")
                print(f"   数据点数: {len(x_data)}")
                
                validation_results['mesh'] = {
                    'x_range': (float(np.min(x_data)), float(np.max(x_data))),
                    'y_range': (float(np.min(y_data)), float(np.max(y_data))),
                    'num_points': int(len(x_data))
                }
            
            # 验证求解数据
            print("\n📊 求解数据验证:")
            solution_group = h5file.get('solution')
            if solution_group:
                u_data = solution_group['u'][:]
                v_data = solution_group['v'][:]
                p_data = solution_group['p'][:]
                
                print(f"   速度u范围: {np.min(u_data):.6f} ~ {np.max(u_data):.6f} m/s")
                print(f"   速度v范围: {np.min(v_data):.6f} ~ {np.max(v_data):.6f} m/s")
                print(f"   压力范围: {np.min(p_data):.2f} ~ {np.max(p_data):.2f} Pa")
                
                validation_results['solution'] = {
                    'u_stats': {
                        'min': float(np.min(u_data)),
                        'max': float(np.max(u_data)),
                        'mean': float(np.mean(u_data)),
                        'std': float(np.std(u_data))
                    },
                    'v_stats': {
                        'min': float(np.min(v_data)),
                        'max': float(np.max(v_data)),
                        'mean': float(np.mean(v_data)),
                        'std': float(np.std(v_data))
                    },
                    'p_stats': {
                        'min': float(np.min(p_data)),
                        'max': float(np.max(p_data)),
                        'mean': float(np.mean(p_data)),
                        'std': float(np.std(p_data))
                    }
                }
            
            # 验证统计信息
            print("\n📈 统计信息:")
            stats_group = h5file.get('statistics')
            if stats_group:
                for field in ['u', 'v', 'p']:
                    if field in stats_group:
                        field_stats = stats_group[field]
                        print(f"   {field}统计:")
                        for stat_name, stat_value in field_stats.attrs.items():
                            print(f"     {stat_name}: {stat_value}")
            
            return validation_results
            
    except Exception as e:
        print(f"❌ 数据验证失败: {e}")
        return None


def create_visualization_plots(file_path):
    """
    创建数据可视化图表
    
    Args:
        file_path: HDF5文件路径
    """
    try:
        print("\n📈 创建可视化图表...")
        
        with h5py.File(file_path, 'r') as h5file:
            # 提取数据
            mesh_group = h5file.get('mesh')
            solution_group = h5file.get('solution')
            
            if mesh_group and solution_group:
                x_data = mesh_group['x'][:]
                y_data = mesh_group['y'][:]
                u_data = solution_group['u'][:]
                v_data = solution_group['v'][:]
                p_data = solution_group['p'][:]
                
                # 创建2D网格用于可视化
                # 假设数据是规则的网格
                x_unique = np.unique(x_data)
                y_unique = np.unique(y_data)
                
                if len(x_unique) * len(y_unique) == len(x_data):
                    # 规则网格
                    X, Y = np.meshgrid(x_unique, y_unique)
                    U = u_data.reshape(len(y_unique), len(x_unique))
                    V = v_data.reshape(len(y_unique), len(x_unique))
                    P = p_data.reshape(len(y_unique), len(x_unique))
                else:
                    # 不规则网格，使用散点图
                    X, Y = x_data, y_data
                    U, V, P = u_data, v_data, p_data
                
                # 创建图表
                fig, axes = plt.subplots(2, 2, figsize=(12, 8))
                fig.suptitle('微通道流场数据验证', fontsize=16)
                
                # 速度幅值
                speed = np.sqrt(U**2 + V**2)
                if len(U.shape) == 2:  # 规则网格
                    im1 = axes[0, 0].contourf(X, Y, speed, levels=20, cmap='viridis')
                    axes[0, 0].set_title('速度幅值 (m/s)')
                    plt.colorbar(im1, ax=axes[0, 0])
                else:  # 散点数据
                    scatter = axes[0, 0].scatter(X, Y, c=speed, cmap='viridis', s=1)
                    axes[0, 0].set_title('速度幅值 (m/s)')
                    plt.colorbar(scatter, ax=axes[0, 0])
                axes[0, 0].set_xlabel('X (mm)')
                axes[0, 0].set_ylabel('Y (mm)')
                
                # X方向速度
                if len(U.shape) == 2:
                    im2 = axes[0, 1].contourf(X, Y, U, levels=20, cmap='RdBu_r')
                    axes[0, 1].set_title('X方向速度 (m/s)')
                    plt.colorbar(im2, ax=axes[0, 1])
                else:
                    scatter2 = axes[0, 1].scatter(X, Y, c=U, cmap='RdBu_r', s=1)
                    axes[0, 1].set_title('X方向速度 (m/s)')
                    plt.colorbar(scatter2, ax=axes[0, 1])
                axes[0, 1].set_xlabel('X (mm)')
                axes[0, 1].set_ylabel('Y (mm)')
                
                # 压力
                if len(P.shape) == 2:
                    im3 = axes[1, 0].contourf(X, Y, P, levels=20, cmap='coolwarm')
                    axes[1, 0].set_title('压力 (Pa)')
                    plt.colorbar(im3, ax=axes[1, 0])
                else:
                    scatter3 = axes[1, 0].scatter(X, Y, c=P, cmap='coolwarm', s=1)
                    axes[1, 0].set_title('压力 (Pa)')
                    plt.colorbar(scatter3, ax=axes[1, 0])
                axes[1, 0].set_xlabel('X (mm)')
                axes[1, 0].set_ylabel('Y (mm)')
                
                # 速度矢量图
                if len(U.shape) == 2:
                    # 稀疏采样以避免箭头过密
                    skip = max(1, len(X[0]) // 20)
                    axes[1, 1].quiver(X[::skip, ::skip], Y[::skip, ::skip], 
                                   U[::skip, ::skip], V[::skip, ::skip])
                    axes[1, 1].set_title('速度矢量')
                else:
                    # 散点图的矢量
                    skip = max(1, len(X) // 500)
                    axes[1, 1].quiver(X[::skip], Y[::skip], 
                                   U[::skip], V[::skip], scale=0.1)
                    axes[1, 1].set_title('速度矢量')
                axes[1, 1].set_xlabel('X (mm)')
                axes[1, 1].set_ylabel('Y (mm)')
                axes[1, 1].set_aspect('equal')
                
                plt.tight_layout()
                
                # 保存图表
                output_dir = Path(file_path).parent
                plot_path = output_dir / "data_validation_plots.png"
                plt.savefig(plot_path, dpi=150, bbox_inches='tight')
                print(f"✅ 可视化图表已保存: {plot_path}")
                
                # 显示图表（如果在交互环境中）
                # plt.show()
                
                return str(plot_path)
        
    except Exception as e:
        print(f"❌ 可视化创建失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    print("🔬 COMSOL数据验证工具")
    
    # 查找数据文件
    data_dir = Path("comsol_simulation/data")
    h5_files = list(data_dir.glob("*.h5")) if data_dir.exists() else []
    
    if not h5_files:
        print("❌ 未找到HDF5数据文件")
        sys.exit(1)
    
    # 使用最新的数据文件
    latest_file = max(h5_files, key=lambda f: f.stat().st_mtime)
    print(f"📁 使用数据文件: {latest_file.name}")
    
    # 验证数据
    validation_results = load_and_validate_hdf5(latest_file)
    
    # 创建可视化
    plot_path = create_visualization_plots(str(latest_file))
    
    # 显示总结
    print("\n" + "=" * 50)
    if validation_results:
        print("🎉 数据验证通过！")
        print("✅ 数据格式正确，可以用于PINNs训练")
        
        if 'mesh' in validation_results:
            mesh_info = validation_results['mesh']
            print(f"\n📐 几何信息:")
            print(f"   数据点数: {mesh_info['num_points']}")
            print(f"   X范围: {mesh_info['x_range'][0]:.1f} ~ {mesh_info['x_range'][1]:.1f} mm")
            print(f"   Y范围: {mesh_info['y_range'][0]:.3f} ~ {mesh_info['y_range'][1]:.3f} mm")
        
        if 'solution' in validation_results:
            sol_info = validation_results['solution']
            print(f"\n📊 流场信息:")
            print(f"   最大速度: {sol_info['u_stats']['max']:.6f} m/s")
            print(f"   压力降: {sol_info['p_stats']['min'] - sol_info['p_stats']['max']:.2f} Pa")
        
        if plot_path:
            print(f"\n📈 可视化图表: {plot_path}")
    else:
        print("😞 数据验证失败")
        print("💡 请检查数据文件完整性")
    
    print("=" * 50)
    sys.exit(0 if validation_results else 1)


if __name__ == "__main__":
    main()