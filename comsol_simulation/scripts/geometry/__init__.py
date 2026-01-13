"""
Microfluidic chip geometry generation module

Provides parametric geometry generation for microchannels:
- Straight channels
- T-junction channels
- Y-junction channels

All geometries explicitly mark boundary types (inlet, outlet, wall)
for correct boundary condition setup in COMSOL.
"""

from base_geometry import MicrochannelGeometry, BoundaryType
from tjunction import TJunctionGeometry, create_tjunction_standard
from yjunction import YJunctionGeometry, create_yjunction_standard

__all__ = [
    'MicrochannelGeometry',
    'BoundaryType',
    'TJunctionGeometry',
    'create_tjunction_standard',
    'YJunctionGeometry',
    'create_yjunction_standard',
]
