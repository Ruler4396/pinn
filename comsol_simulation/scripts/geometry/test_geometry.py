"""
Microfluidic geometry test script

Tests T-junction and Y-junction geometries with standard microfluidic chip dimensions.
"""
import sys
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print("Testing geometry module...")
print("=" * 60)

# Test 1: Import base module
print("\n[Test 1] Importing base_geometry module...")
try:
    from base_geometry import BoundaryType, MicrochannelGeometry
    print("  [OK] base_geometry imported successfully")
    print(f"  - BoundaryType enum: {list(BoundaryType)}")
    print(f"  - MicrochannelGeometry class: available")
except Exception as e:
    print(f"  [ERROR] Failed to import: {e}")
    sys.exit(1)

# Test 2: Import T-junction module
print("\n[Test 2] Importing T-junction module...")
try:
    from tjunction import TJunctionGeometry, create_tjunction_standard
    print("  [OK] T-junction module imported successfully")
    print("  - TJunctionGeometry class: available")
    print("  - create_tjunction_standard function: available")
except Exception as e:
    print(f"  [ERROR] Failed to import: {e}")
    sys.exit(1)

# Test 3: Import Y-junction module
print("\n[Test 3] Importing Y-junction module...")
try:
    from yjunction import YJunctionGeometry, create_yjunction_standard
    print("  [OK] Y-junction module imported successfully")
    print("  - YJunctionGeometry class: available")
    print("  - create_yjunction_standard function: available")
except Exception as e:
    print(f"  [ERROR] Failed to import: {e}")
    sys.exit(1)

# Test 4: Create T-junction geometry
print("\n[Test 4] Creating T-junction geometry...")
try:
    t_geom = create_tjunction_standard()
    data = t_geom.generate()
    print("  [OK] T-junction geometry created successfully")
    print(f"  - Type: {t_geom.geometry_params['type']}")
    print(f"  - Main channel: {t_geom.geometry_params['L_main']} x {t_geom.geometry_params['W']} mm")
    print(f"  - Branch channel: {t_geom.geometry_params['L_branch']} x {t_geom.geometry_params['W_branch']} mm")
    print(f"  - Junction angle: {t_geom.geometry_params['junction_angle']}°")
except Exception as e:
    print(f"  [ERROR] Failed to create T-junction: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Create Y-junction geometry
print("\n[Test 5] Creating Y-junction geometry...")
try:
    y_geom = create_yjunction_standard()
    data = y_geom.generate()
    print("  [OK] Y-junction geometry created successfully")
    print(f"  - Type: {y_geom.geometry_params['type']}")
    print(f"  - Main channel: {y_geom.geometry_params['L_main']} x {y_geom.geometry_params['W']} mm")
    print(f"  - Branch channel: {y_geom.geometry_params['L_branch']} x {y_geom.geometry_params['W']} mm")
    print(f"  - Branch angle: {y_geom.geometry_params['branch_angle']}° per side")
except Exception as e:
    print(f"  [ERROR] Failed to create Y-junction: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Validate boundaries
print("\n[Test 6] Validating boundary conditions...")
try:
    # T-junction validation
    is_valid, errors = t_geom.validate_boundaries()
    if is_valid:
        print("  [OK] T-junction boundaries validated")
    else:
        print(f"  [ERROR] T-junction boundary errors: {errors}")
        sys.exit(1)

    # Y-junction validation
    is_valid, errors = y_geom.validate_boundaries()
    if is_valid:
        print("  [OK] Y-junction boundaries validated")
    else:
        print(f"  [ERROR] Y-junction boundary errors: {errors}")
        sys.exit(1)
except Exception as e:
    print(f"  [ERROR] Validation failed: {e}")
    sys.exit(1)

# Test 7: Export for COMSOL
print("\n[Test 7] Exporting geometries for COMSOL...")
try:
    t_comsol = t_geom.export_for_comsol()
    y_comsol = y_geom.export_for_comsol()
    print("  [OK] Both geometries exported successfully")
    print(f"  - T-junction: {len(t_comsol['polygons'])} polygons, {len(t_comsol['boundaries'])} boundaries")
    print(f"  - Y-junction: {len(y_comsol['polygons'])} polygons, {len(y_comsol['boundaries'])} boundaries")
except Exception as e:
    print(f"  [ERROR] Export failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("All geometry tests passed successfully!")
print("=" * 60)
