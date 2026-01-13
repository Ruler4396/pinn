# -*- coding: utf-8 -*-
"""
Create COMSOL model files from geometry definitions

This script generates .mph model files for T-junction and Y-junction microchannels
using the geometry generation modules. The models are saved with basic settings
that need to be configured in COMSOL GUI.

Note: Full COMSOL model generation requires COMSOL with Python API (mph library).
This script generates the geometry data and creates the models if COMSOL is available.
"""

import sys
from pathlib import Path
import numpy as np
import json

# 添加项目路径
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

# 添加geometry目录
geometry_dir = Path(__file__).parent
sys.path.insert(0, str(geometry_dir))

# 尝试导入COMSOL (可选依赖)
try:
    import mph
    COMSOL_AVAILABLE = True
    print("[OK] COMSOL (mph) library available")
except ImportError:
    COMSOL_AVAILABLE = False
    print("[INFO] COMSOL (mph) not available - will generate geometry data only")


def create_comsol_model(geometry, model_name: str, output_dir: Path):
    """
    Create COMSOL model file from geometry

    Args:
        geometry: Geometry object (T-junction or Y-junction)
        model_name: Name of the model
        output_dir: Output directory for model files

    Returns:
        Path to created model file or data file
    """
    output_dir.mkdir(exist_ok=True)

    # 生成几何数据
    data = geometry.generate()
    comsol_data = geometry.export_for_comsol()

    # 保存几何数据为JSON（可被COMSOL读取）
    json_path = output_dir / f"{model_name}_geometry.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(comsol_data, f, indent=2, ensure_ascii=False)
    print(f"  [OK] Geometry data saved: {json_path}")

    # 保存参数
    params_path = output_dir / f"{model_name}_params.json"
    with open(params_path, 'w', encoding='utf-8') as f:
        json.dump(geometry.geometry_params, f, indent=2, ensure_ascii=False)
    print(f"  [OK] Parameters saved: {params_path}")

    # 如果COMSOL可用，创建模型
    if COMSOL_AVAILABLE:
        try:
            return create_mph_model(geometry, model_name, output_dir)
        except Exception as e:
            print(f"  [WARN] Could not create .mph model: {e}")
            return json_path
    else:
        print(f"  [INFO] To create .mph model, install COMSOL and mph: pip install mph")
        return json_path


def create_mph_model(geometry, model_name: str, output_dir: Path) -> Path:
    """
    Create COMSOL .mph model using mph library

    Args:
        geometry: Geometry object
        model_name: Name of the model
        output_dir: Output directory

    Returns:
        Path to .mph file
    """
    # 创建新模型
    model = mph.Model(model_name)

    # 添加几何参数
    params = geometry.geometry_params
    for key, value in params.items():
        if isinstance(value, (int, float)):
            model.parameter(key, str(value))

    # 创建几何
    comsol_data = geometry.export_for_comsol()

    # 创建多边形
    for i, poly in enumerate(comsol_data['polygons']):
        x = poly['x']
        y = poly['y']

        # 创建COMSOL多边形
        poly_entity = model.java().geom('geom1').create(
            f'poly{i+1}',
            'Polygon'
        )
        poly_entity.set('x', x)
        poly_entity.set('y', y)

    # 创建所有边界
    boundaries = comsol_data['boundaries']
    boundary_groups = {
        'inlet': [],
        'outlet1': [],
        'outlet2': [],
        'wall': []
    }

    for i, b in enumerate(boundaries):
        btype = b['type']
        x = b['x']
        y = b['y']

        # 创建边界线
        line_entity = model.java().geom('geom1').create(
            f'line{i+1}',
            'Line'
        )
        line_entity.set('x', x)
        line_entity.set('y', y)

        boundary_groups.get(btype, []).append(f'line{i+1}')

    # 构建联合体
    model.java().geom('geom1').create('uni1', 'Union')
    model.java().geom('geom1').feature('uni1').set('input', ['fin1'])

    # 保存模型
    mph_path = output_dir / f"{model_name}.mph"
    model.save(str(mph_path))
    print(f"  [OK] COMSOL model saved: {mph_path}")

    return mph_path


def create_tjunction_model():
    """Create T-junction COMSOL model"""
    print("\n" + "=" * 60)
    print("Creating T-Junction Model")
    print("=" * 60)

    from tjunction import TJunctionGeometry

    # 创建标准尺寸T型分岔道
    t_geom = TJunctionGeometry(
        L_main=10.0,      # 10 mm
        L_branch=5.0,     # 5 mm
        W=0.2,            # 200 μm
        units='mm'
    )

    # 输出目录
    output_dir = Path(__file__).parent.parent.parent / 'models'
    output_dir.mkdir(exist_ok=True)

    # 创建模型
    model_path = create_comsol_model(t_geom, 'tjunction_base', output_dir)

    # 打印边界条件摘要
    t_geom.print_boundary_summary()

    return model_path


def create_yjunction_model():
    """Create Y-junction COMSOL model"""
    print("\n" + "=" * 60)
    print("Creating Y-Junction Model")
    print("=" * 60)

    from yjunction import YJunctionGeometry

    # 创建标准尺寸Y型分岔道
    y_geom = YJunctionGeometry(
        L_main=10.0,       # 10 mm
        L_branch=5.0,      # 5 mm
        W=0.2,             # 200 μm
        branch_angle=45.0, # 每侧45度
        units='mm'
    )

    # 输出目录
    output_dir = Path(__file__).parent.parent.parent / 'models'
    output_dir.mkdir(exist_ok=True)

    # 创建模型
    model_path = create_comsol_model(y_geom, 'yjunction_base', output_dir)

    # 打印边界条件摘要
    y_geom.print_boundary_summary()

    return model_path


def create_all_models():
    """Create all COMSOL models"""
    print("\n" + "=" * 70)
    print("Creating All Microfluidic Channel Models")
    print("=" * 70)

    # 创建输出目录
    output_dir = Path(__file__).parent.parent.parent / 'models'
    output_dir.mkdir(exist_ok=True)

    models_created = []

    # T型分岔道
    print("\n[1/2] Creating T-junction model...")
    t_path = create_tjunction_model()
    models_created.append(('T-junction', t_path))

    # Y型分岔道
    print("\n[2/2] Creating Y-junction model...")
    y_path = create_yjunction_model()
    models_created.append(('Y-junction', y_path))

    # 摘要
    print("\n" + "=" * 70)
    print("Models Created Successfully")
    print("=" * 70)
    for name, path in models_created:
        print(f"  - {name}: {path}")

    print("\n[INFO] Next steps:")
    print("  1. Open the generated models in COMSOL GUI")
    print("  2. Add Physics: Laminar Flow (spf)")
    print("  3. Set boundary conditions according to the marked boundaries")
    print("  4. Add Mesh and Study (Stationary)")
    print("  5. Configure Export for solution data")
    print("  6. Run simulation and export results")

    return models_created


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create COMSOL models for microfluidic channels')
    parser.add_argument('--t-junction', action='store_true', help='Create T-junction model only')
    parser.add_argument('--y-junction', action='store_true', help='Create Y-junction model only')
    parser.add_argument('--all', action='store_true', help='Create all models')

    args = parser.parse_args()

    if args.t_junction:
        create_tjunction_model()
    elif args.y_junction:
        create_yjunction_model()
    elif args.all:
        create_all_models()
    else:
        print("[INFO] Use --all to create all models, or --t-junction / --y-junction for specific models")
        print("\nAvailable options:")
        print("  --t-junction  : Create T-junction model")
        print("  --y-junction  : Create Y-junction model")
        print("  --all         : Create all models")
        print("\nNote: COMSOL with mph library is required to create .mph files.")
        print("      Without mph, only geometry JSON files will be generated.")
