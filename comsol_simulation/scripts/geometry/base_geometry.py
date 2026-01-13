"""
微流控芯片几何生成基类

定义基础的几何生成接口和边界类型枚举。
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Tuple, Dict, Optional
import numpy as np


class BoundaryType(Enum):
    """边界类型枚举"""
    INLET = "inlet"           # 入口边界
    OUTLET_1 = "outlet1"      # 出口1
    OUTLET_2 = "outlet2"      # 出口2（用于分岔道）
    WALL = "wall"             # 壁面（无滑移边界）


class BoundarySegment:
    """边界线段描述"""
    def __init__(self, points: np.ndarray, boundary_type: BoundaryType, label: str = ""):
        """
        Args:
            points: (N, 2)数组，边界线的顶点坐标
            boundary_type: 边界类型
            label: 边界标签
        """
        self.points = points
        self.boundary_type = boundary_type
        self.label = label

    def __repr__(self):
        return f"BoundarySegment(type={self.boundary_type.value}, label='{self.label}', points={len(self.points)})"


class MicrochannelGeometry(ABC):
    """
    微流控芯片几何生成基类

    所有几何生成都需要：
    1. 明确标记所有边界类型
    2. 提供边界验证功能
    3. 生成可用于COMSOL的几何数据
    """

    def __init__(self, units: str = 'mm'):
        """
        Args:
            units: 长度单位 ('mm', 'm')
        """
        self.units = units
        self.unit_scale = 0.001 if units == 'mm' else 1.0  # 转换为米
        self.boundaries: List[BoundarySegment] = []
        self.geometry_params: Dict = {}

    @abstractmethod
    def generate(self) -> Dict:
        """
        生成几何数据

        Returns:
            包含以下键的字典:
            - 'polygons': List of polygon definitions
            - 'boundaries': List of boundary segments
            - 'params': Geometry parameters
        """
        # 清空现有边界，避免重复添加
        self.boundaries = []
        pass

    def add_boundary(self, points: np.ndarray, boundary_type: BoundaryType, label: str = ""):
        """添加边界定义"""
        segment = BoundarySegment(points, boundary_type, label)
        self.boundaries.append(segment)

    def get_boundaries_by_type(self, boundary_type: BoundaryType) -> List[BoundarySegment]:
        """获取指定类型的所有边界"""
        return [b for b in self.boundaries if b.boundary_type == boundary_type]

    def validate_boundaries(self) -> Tuple[bool, List[str]]:
        """
        验证边界条件设置是否完整

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # 检查是否有入口
        inlets = self.get_boundaries_by_type(BoundaryType.INLET)
        if len(inlets) != 1:
            errors.append(f"入口边界数量错误: 应为1个，实际{len(inlets)}个")

        # 检查是否有至少一个出口
        outlets = (self.get_boundaries_by_type(BoundaryType.OUTLET_1) +
                   self.get_boundaries_by_type(BoundaryType.OUTLET_2))
        if len(outlets) < 1:
            errors.append(f"出口边界数量不足: 至少需要1个，实际{len(outlets)}个")

        # 检查是否有壁面
        walls = self.get_boundaries_by_type(BoundaryType.WALL)
        if len(walls) == 0:
            errors.append("缺少壁面边界定义")

        # 检查边界是否闭合（可选，根据几何类型）

        is_valid = len(errors) == 0
        return is_valid, errors

    def print_boundary_summary(self):
        """打印边界摘要信息"""
        print("\n" + "="*60)
        print("边界条件摘要")
        print()

        for btype in [BoundaryType.INLET, BoundaryType.OUTLET_1,
                      BoundaryType.OUTLET_2, BoundaryType.WALL]:
            segments = self.get_boundaries_by_type(btype)
            if segments:
                print(f"\n{btype.value.upper()}:")
                for i, seg in enumerate(segments, 1):
                    print(f"  {i}. {seg.label}")
                    print(f"     顶点数: {len(seg.points)}")
                    print(f"     长度: {self._calculate_length(seg.points):.4f} {self.units}")

        # 验证
        is_valid, errors = self.validate_boundaries()
        print("\n" + "-"*60)
        if is_valid:
            print("[OK] 边界条件验证通过")
        else:
            print("[ERROR] 边界条件验证失败:")
            for err in errors:
                print(f"   - {err}")
        print("="*60 + "\n")

    def _calculate_length(self, points: np.ndarray) -> float:
        """计算边界线段长度"""
        if len(points) < 2:
            return 0.0
        diffs = np.diff(points, axis=0)
        lengths = np.sqrt(np.sum(diffs**2, axis=1))
        return np.sum(lengths)

    def export_for_comsol(self) -> Dict:
        """
        导出为COMSOL可用的格式

        Returns:
            包含COMSOL Polygon创建所需数据的字典
        """
        data = self.generate()

        # 转换为COMSOL单位（米）
        comsol_data = {
            'units': 'm',
            'polygons': [],
            'boundaries': []
        }

        for poly in data['polygons']:
            points = np.array(poly['points']) * self.unit_scale
            comsol_data['polygons'].append({
                'label': poly['label'],
                'x': points[:, 0].tolist(),
                'y': points[:, 1].tolist()
            })

        for boundary in self.boundaries:
            points = boundary.points * self.unit_scale
            comsol_data['boundaries'].append({
                'type': boundary.boundary_type.value,
                'label': boundary.label,
                'x': points[:, 0].tolist(),
                'y': points[:, 1].tolist()
            })

        comsol_data['params'] = data['params']
        return comsol_data
