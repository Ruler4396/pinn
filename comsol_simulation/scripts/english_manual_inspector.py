"""
English Manual Data Inspector

Provides a simple way to manually check the quality and authenticity of generated datasets
with English labels to avoid font display issues

Author: PINNs Project Team
Created: 2025-11-19
"""

import os
import sys
import numpy as np
import h5py
import matplotlib.pyplot as plt
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Set matplotlib font to avoid Chinese font issues
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


def load_and_inspect_dataset(filename):
    """Load and inspect a single dataset"""
    data_dir = project_root / "comsol_simulation" / "data"
    file_path = data_dir / filename

    print(f"\n{'='*60}")
    print(f"Manual Dataset Inspection: {filename}")
    print(f"{'='*60}")

    if not file_path.exists():
        print(f"ERROR: File does not exist: {file_path}")
        return

    # Show file size
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"File Size: {file_size_mb:.2f} MB")

    try:
        with h5py.File(file_path, 'r') as h5file:
            print(f"File Format: HDF5")

            # 1. Basic information
            print(f"\nBasic Information:")
            if 'info' in h5file:
                info_attrs = dict(h5file['info'].attrs)
                for key, value in info_attrs.items():
                    print(f"   {key}: {value}")

            # 2. Data structure
            print(f"\nData Structure:")
            for key in h5file.keys():
                group = h5file[key]
                if isinstance(group, h5py.Group):
                    print(f"   Group: {key}/")
                    for subkey in group.keys():
                        if isinstance(group[subkey], h5py.Dataset):
                            shape = group[subkey].shape
                            dtype = group[subkey].dtype
                            print(f"      Dataset: {subkey}: {shape} {dtype}")
                        else:
                            print(f"      Sub-group: {subkey}/")
                else:
                    print(f"   Dataset: {key}: {group.shape} {group.dtype}")

            # 3. Load key data
            print(f"\nData Content Analysis:")

            # Mesh data
            if 'mesh' in h5file:
                mesh_group = h5file['mesh']
                x = mesh_group['x'][:]
                y = mesh_group['y'][:]
                n_points = len(x)

                print(f"   Grid Points: {n_points}")
                print(f"   X Range: {np.min(x):.3f} ~ {np.max(x):.3f} mm")
                print(f"   Y Range: {np.min(y):.3f} ~ {np.max(y):.3f} mm")

            # Solution data
            if 'solution' in h5file:
                sol = h5file['solution']

                # Clean data
                u_clean = sol['u_clean'][:]
                v_clean = sol['v_clean'][:]
                p_clean = sol['p_clean'][:]

                # Noisy data
                u_noisy = sol['u'][:]
                v_noisy = sol['v'][:]
                p_noisy = sol['p'][:]

                # Calculate speed magnitude
                speed_clean = np.sqrt(u_clean**2 + v_clean**2)
                speed_noisy = np.sqrt(u_noisy**2 + v_noisy**2)

                print(f"\n   Flow Field Data:")
                print(f"      U-velocity (clean): {np.min(u_clean):.6f} ~ {np.max(u_clean):.6f} m/s")
                print(f"      V-velocity (clean): {np.min(v_clean):.6f} ~ {np.max(v_clean):.6f} m/s")
                print(f"      Speed magnitude (clean): {np.min(speed_clean):.6f} ~ {np.max(speed_clean):.6f} m/s")
                print(f"      Pressure (clean): {np.min(p_clean):.1f} ~ {np.max(p_clean):.1f} Pa")

                print(f"\n      U-velocity (noisy): {np.min(u_noisy):.6f} ~ {np.max(u_noisy):.6f} m/s")
                print(f"      V-velocity (noisy): {np.min(v_noisy):.6f} ~ {np.max(v_noisy):.6f} m/s")
                print(f"      Speed magnitude (noisy): {np.min(speed_noisy):.6f} ~ {np.max(speed_noisy):.6f} m/s")
                print(f"      Pressure (noisy): {np.min(p_noisy):.1f} ~ {np.max(p_noisy):.1f} Pa")

                # Missing data
                if 'missing_mask' in sol:
                    missing_mask = sol['missing_mask'][:]
                    missing_count = np.sum(missing_mask)
                    missing_ratio = missing_count / len(missing_mask) * 100
                    print(f"      Missing Data: {missing_count}/{len(missing_mask)} ({missing_ratio:.1f}%)")

            # 4. Noise analysis
            if 'noise_analysis' in h5file:
                print(f"\nNoise Analysis:")
                noise_group = h5file['noise_analysis']
                for field in noise_group.keys():
                    field_attrs = dict(noise_group[field].attrs)
                    print(f"      {field} field:")
                    for attr_name, attr_value in field_attrs.items():
                        if attr_name == 'snr_db':
                            print(f"         Signal-to-Noise Ratio: {attr_value:.1f} dB")
                        elif attr_name == 'noise_std':
                            print(f"         Noise Std Dev: {attr_value:.2e}")
                        else:
                            print(f"         {attr_name}: {attr_value}")

            # 5. Physical reasonableness check
            print(f"\nPhysical Reasonableness Check:")

            # Velocity check
            if 'solution' in h5file:
                max_speed = np.max(speed_clean)
                avg_speed = np.mean(speed_clean)

                print(f"   Velocity Characteristics:")
                print(f"      Maximum Speed: {max_speed:.6f} m/s")
                print(f"      Average Speed: {avg_speed:.6f} m/s")

                if max_speed < 0.1:
                    print(f"      PASS: Velocity range reasonable (microfluidics typically < 0.1 m/s)")
                else:
                    print(f"      WARNING: Velocity possibly too high (microfluidics typically < 0.1 m/s)")

                # Pressure check
                pressure_range = np.max(p_clean) - np.min(p_clean)
                print(f"   Pressure Characteristics:")
                print(f"      Pressure Drop: {pressure_range:.1f} Pa")

                if pressure_range < 50000:
                    print(f"      PASS: Pressure drop reasonable (microfluidics typically < 50 kPa)")
                else:
                    print(f"      WARNING: Pressure drop possibly too high")

                # Reynolds number estimation
                channel_width = 0.2e-3  # Assume 0.2mm channel width
                kinematic_viscosity = 1e-6  # Water kinematic viscosity
                reynolds_number = avg_speed * channel_width / kinematic_viscosity

                print(f"   Flow Characteristics:")
                print(f"      Estimated Reynolds Number: {reynolds_number:.1f}")

                if reynolds_number < 2300:
                    print(f"      PASS: Laminar flow (suitable for PINNs training)")
                else:
                    print(f"      WARNING: Possibly not laminar flow")

            # 6. Show some raw data
            print(f"\nRaw Data Samples (First 10 points):")
            print(f"{'No':<4} {'X(mm)':<8} {'Y(mm)':<8} {'U(m/s)':<12} {'V(m/s)':<12} {'P(Pa)':<10}")
            print("-" * 70)

            n_show = min(10, len(x))
            for i in range(n_show):
                print(f"{i+1:<4} "
                      f"{x[i]:<8.3f} "
                      f"{y[i]:<8.3f} "
                      f"{u_noisy[i]:<12.6f} "
                      f"{v_noisy[i]:<12.6f} "
                      f"{p_noisy[i]:<10.1f}")

            # 7. Generate visualization
            if 'solution' in h5file:
                print(f"\nGenerating data visualization...")
                create_english_visualization(x, y, u_noisy, v_noisy, p_noisy,
                                          filename.replace('.h5', '_english_check.png'))

    except Exception as e:
        print(f"ERROR reading file: {e}")
        import traceback
        traceback.print_exc()


def create_english_visualization(x, y, u, v, p, save_name):
    """Create English language data visualization"""
    try:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Manual Data Inspection - Visualization', fontsize=16)

        # 1. Data point distribution
        ax1 = axes[0, 0]
        speed = np.sqrt(u**2 + v**2)
        scatter = ax1.scatter(x, y, c=speed, s=10, cmap='viridis', alpha=0.7)
        ax1.set_xlabel('X (mm)')
        ax1.set_ylabel('Y (mm)')
        ax1.set_title('Data Point Distribution (Color = Speed)')
        ax1.set_aspect('equal')
        plt.colorbar(scatter, ax=ax1, label='Speed (m/s)')

        # 2. Velocity field vector plot
        ax2 = axes[0, 1]
        # For clarity, draw arrows every few points
        skip = max(1, len(x) // 50)
        ax2.quiver(x[::skip], y[::skip], u[::skip], v[::skip],
                  speed[::skip], cmap='viridis', alpha=0.7)
        ax2.set_xlabel('X (mm)')
        ax2.set_ylabel('Y (mm)')
        ax2.set_title('Velocity Field Vector Plot')
        ax2.set_aspect('equal')

        # 3. Pressure distribution
        ax3 = axes[1, 0]
        scatter = ax3.scatter(x, y, c=p, s=10, cmap='coolwarm', alpha=0.7)
        ax3.set_xlabel('X (mm)')
        ax3.set_ylabel('Y (mm)')
        ax3.set_title('Pressure Distribution')
        ax3.set_aspect('equal')
        plt.colorbar(scatter, ax=ax3, label='Pressure (Pa)')

        # 4. Data statistics
        ax4 = axes[1, 1]
        ax4.axis('off')

        # Statistical information
        stats_text = f"""Data Statistics Information:

Total Data Points: {len(x)}
X Range: {np.min(x):.3f} ~ {np.max(x):.3f} mm
Y Range: {np.min(y):.3f} ~ {np.max(y):.3f} mm

Velocity Statistics:
  U: {np.min(u):.6f} ~ {np.max(u):.6f} m/s
  V: {np.min(v):.6f} ~ {np.max(v):.6f} m/s
  Speed Mag: {np.min(speed):.6f} ~ {np.max(speed):.6f} m/s

Pressure Statistics:
  P: {np.min(p):.1f} ~ {np.max(p):.1f} Pa
  Pressure Drop: {np.max(p) - np.min(p):.1f} Pa

Avg Reynolds Number ≈ {np.mean(speed) * 0.2e-3 / 1e-6:.1f} (Laminar)
"""
        ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes,
                fontsize=10, verticalalignment='top', fontfamily='monospace')

        plt.tight_layout()

        # Save image
        output_dir = project_root / "comsol_simulation" / "data"
        save_path = output_dir / save_name
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"Visualization saved: {save_path}")

    except Exception as e:
        print(f"ERROR generating visualization: {e}")


def main():
    """Main function"""
    print("English Manual Data Inspection Tool")

    # Find all realistic datasets
    data_dir = project_root / "comsol_simulation" / "data"
    h5_files = list(data_dir.glob("*.h5"))
    realistic_files = [f for f in h5_files if "realistic" in f.name]

    if not realistic_files:
        print("ERROR: No realistic dataset files found")
        return

    print(f"Found {len(realistic_files)} realistic datasets")

    # Check each dataset
    for i, file_path in enumerate(realistic_files, 1):
        load_and_inspect_dataset(file_path.name)

        if i < len(realistic_files):
            print(f"\nCompleted {i}/{len(realistic_files)} datasets")

    print(f"\nAll dataset inspections completed!")
    print(f"Visualizations saved in: {data_dir}")


if __name__ == "__main__":
    main()