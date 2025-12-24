#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于现有模型生成数据集

使用现有的 parametric_base.mph 和 tjunction_base.mph 模型
通过修改参数来生成多组数据，避免复杂的API调用

作者: PINNs项目组
日期: 2025-12-24
"""

import mph
import h5py
import numpy as np
from datetime import datetime
from pathlib import Path


class ModelBasedGenerator:
    """基于现有模型的数据生成器"""

    def __init__(self):
        self.models_dir = Path(__file__).parent.parent.parent / "models"
        self.output_dir = Path(__file__).parent.parent.parent / "data"
        self.client = None

    def start_comsol(self):
        """启动COMSOL客户端"""
        if self.client is None:
            print("🚀 启动COMSOL客户端...")
            self.client = mph.Client(cores=1)
            print("   ✅ 客户端启动成功")

    def stop_comsol(self):
        """停止COMSOL客户端"""
        if self.client is not None:
            try:
                self.client.disconnect()
                self.client = None
                print("   ✅ COMSOL客户端已关闭")
            except:
                pass

    def generate_from_parametric_base(self, case_name, v_cm_s, width_um):
        """基于parametric_base.mph生成直通道数据"""
        base_path = self.models_dir / "parametric_base.mph"

        if not base_path.exists():
            print(f"   ❌ 模型不存在: {base_path}")
            return False

        try:
            print(f"\n📐 生成: {case_name}")
            print(f"   参数: v={v_cm_s:.2f} cm/s, w={width_um} μm")

            # 加载模型
            model = self.client.load(str(base_path))
            java_model = model.java

            # 设置参数
            v_in = v_cm_s / 100  # m/s
            width_mm = width_um / 1000  # mm

            # 修改模型参数
            params = java_model.param()
            params.set("v_in", f"{v_in} [m/s]")
            params.set("W", f"{width_um} [um]")

            # 修改几何
            geom = java_model.geom("geom1")
            rect = geom.feature("r1")
            rect.set("size", ["10", f"{width_mm}"])

            geom.run("r1")

            # 修改入口速度
            physics = java_model.physics("spf")
            inlet = physics.feature("inlet")
            inlet.set("U0in", f"{v_in}")

            # 求解
            print("   🔄 正在求解...")
            study = java_model.study("steady")
            study.run()

            # 导出数据
            self.export_data(model, case_name, v_in, width_um*1e-6, 'straight')

            # 清理
            model.clear()
            return True

        except Exception as e:
            print(f"   ❌ 失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def generate_from_tjunction_base(self, case_name, v_cm_s, width_um):
        """基于tjunction_base.mph生成T型分岔道数据"""
        base_path = self.models_dir / "tjunction_base.mph"

        if not base_path.exists():
            print(f"   ❌ 模型不存在: {base_path}")
            return False

        try:
            print(f"\n📐 生成: {case_name}")
            print(f"   参数: v={v_cm_s:.2f} cm/s, w={width_um} μm")

            # 加载模型
            model = self.client.load(str(base_path))
            java_model = model.java

            # 设置参数
            v_in = v_cm_s / 100  # m/s

            # 修改入口速度
            physics = java_model.physics("spf")
            inlet = physics.feature("inlet")
            inlet.set("U0in", f"{v_in}")

            # 求解
            print("   🔄 正在求解...")
            studies = java_model.study()
            study_iter = studies.iterator()
            if study_iter.hasNext():
                study = study_iter.next()
                study.run()

            # 导出数据
            self.export_data(model, case_name, v_in, width_um*1e-6, 'tjunction')

            # 清理
            model.clear()
            return True

        except Exception as e:
            print(f"   ❌ 失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def export_data(self, model, case_name, v_in, width, geometry_type):
        """导出数据到HDF5 - 使用COMSOL Export功能"""
        java_model = model.java

        try:
            print("   📊 正在提取数据...")

            # 使用COMSOL的Export功能导出到临时文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = self.output_dir / f"temp_{case_name}_{timestamp}.csv"

            # 创建Export特征
            export = java_model.result().export().create("export1", "Data")
            export.set("expr", ["u", "v", "p", "x", "y"])
            export.set("filename", str(temp_file))

            # 执行导出
            export.run()

            # 读取CSV文件
            data_lines = []
            with open(temp_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('%'):
                        parts = line.split(',')
                        if len(parts) >= 5:
                            try:
                                data_lines.append([float(parts[3]), float(parts[4]),  # x, y
                                                   float(parts[0]), float(parts[1]),  # u, v
                                                   float(parts[2])])  # p
                            except:
                                continue

            # 删除临时文件
            try:
                temp_file.unlink()
            except:
                pass

            if len(data_lines) == 0:
                raise ValueError("未获取到有效数据")

            results = np.array(data_lines)
            x = results[:, 0]
            y = results[:, 1]
            u = results[:, 2]
            v = results[:, 3]
            p = results[:, 4]

            if u.max() == 0:
                raise ValueError("速度数据全为零")

            print(f"   📊 获取到 {len(x)} 个数据点")
            print(f"   📊 U范围: [{u.min():.6f}, {u.max():.6f}] m/s")

        except Exception as e:
            print(f"   ⚠️ Export方法失败: {e}")
            raise

        # 保存HDF5文件
        filepath = self.output_dir / f"{case_name}.h5"

        # 计算Reynolds数
        rho = 1000.0
        mu = 0.001
        reynolds = rho * v_in * width / mu

        with h5py.File(filepath, 'w') as f:
            f.create_dataset('x', data=x)
            f.create_dataset('y', data=y)
            f.create_dataset('u', data=u)
            f.create_dataset('v', data=v)
            f.create_dataset('p', data=p)

            # 元数据
            f.attrs['case_id'] = case_name
            f.attrs['inlet_velocity'] = v_in
            f.attrs['channel_width'] = width
            f.attrs['channel_length'] = 0.01
            f.attrs['fluid_density'] = rho
            f.attrs['fluid_viscosity'] = mu
            f.attrs['reynolds_number'] = reynolds
            f.attrs['total_points'] = len(x)
            f.attrs['generation_method'] = 'COMSOL_simulation'
            f.attrs['geometry_type'] = geometry_type

        print(f"   ✅ 数据已保存: {filepath.name} ({len(x)} 点, Re={reynolds:.2f})")

    def generate_tjunction_dataset(self):
        """生成T型分岔道数据集"""
        print("\n" + "=" * 60)
        print("🔄 生成T型分岔道数据 (9组)")
        print("=" * 60)

        velocities = [0.15, 0.77, 1.54]  # cm/s
        widths = [150, 200, 250]  # μm

        success_count = 0
        case_num = 0

        for v in velocities:
            for w in widths:
                case_num += 1
                case_name = f"tj_v{v:.2f}_w{w}"

                print(f"\n[{case_num}/9] ", end="")

                if self.generate_from_tjunction_base(case_name, v, w):
                    success_count += 1

        print(f"\n✅ T型分岔道数据完成: {success_count}/9")
        return success_count

    def generate_viscosity_variants(self):
        """生成不同粘度数据 (3组)"""
        print("\n" + "=" * 60)
        print("🔄 生成不同粘度数据 (3组)")
        print("=" * 60)

        base_path = self.models_dir / "parametric_base.mph"

        if not base_path.exists():
            print("   ❌ parametric_base.mph 不存在")
            return 0

        # 基准工况
        v_cm_s = 0.77
        width_um = 200
        v_in = v_cm_s / 100
        width = width_um * 1e-6

        viscosities = [0.0005, 0.002, 0.004]  # Pa·s

        success_count = 0

        for i, viscosity in enumerate(viscosities, 1):
            case_name = f"v{v_cm_s:.2f}_w{width_um}_mu{viscosity*1000:.0f}"

            try:
                print(f"\n[{i}/3] 📐 生成: {case_name}")
                print(f"   粘度: {viscosity} Pa·s")

                # 加载模型
                model = self.client.load(str(base_path))
                java_model = model.java

                # 设置参数
                params = java_model.param()
                params.set("v_in", f"{v_in} [m/s]")
                params.set("W", f"{width_um} [um]")

                # 修改材料粘度
                mat = java_model.material("fluid")
                mat.propertyGroup("def").set("mu", f"{viscosity} [Pa*s]")

                # 修改入口速度
                physics = java_model.physics("spf")
                inlet = physics.feature("inlet")
                inlet.set("U0in", f"{v_in}")

                # 求解
                print("   🔄 正在求解...")
                study = java_model.study("steady")
                study.run()

                # 导出数据
                self.export_data_with_viscosity(model, case_name, v_in, width, viscosity)

                # 清理
                model.clear()
                success_count += 1

            except Exception as e:
                print(f"   ❌ 失败: {e}")

        print(f"\n✅ 不同粘度数据完成: {success_count}/3")
        return success_count

    def export_data_with_viscosity(self, model, case_name, v_in, width, viscosity):
        """导出不同粘度数据"""
        java_model = model.java

        # 使用mph的evaluate方法
        x = np.array(model.evaluate('x')).flatten()
        y = np.array(model.evaluate('y')).flatten()
        u = np.array(model.evaluate('u')).flatten()
        v = np.array(model.evaluate('v')).flatten()
        p = np.array(model.evaluate('p')).flatten()

        # 计算Reynolds数
        rho = 1000.0
        mu = viscosity
        reynolds = rho * v_in * width / mu

        filepath = self.output_dir / f"{case_name}.h5"

        with h5py.File(filepath, 'w') as f:
            f.create_dataset('x', data=x)
            f.create_dataset('y', data=y)
            f.create_dataset('u', data=u)
            f.create_dataset('v', data=v)
            f.create_dataset('p', data=p)

            f.attrs['case_id'] = case_name
            f.attrs['inlet_velocity'] = v_in
            f.attrs['channel_width'] = width
            f.attrs['fluid_viscosity'] = viscosity
            f.attrs['reynolds_number'] = reynolds
            f.attrs['total_points'] = len(x)

        print(f"   ✅ 数据已保存: {filepath.name} ({len(x)} 点, Re={reynolds:.2f})")


def main():
    """主函数"""
    import sys

    print("=" * 60)
    print("🚀 基于现有模型的数据生成器")
    print("=" * 60)

    # 解析命令行参数
    task = sys.argv[1] if len(sys.argv) > 1 else 'tjunction'

    generator = ModelBasedGenerator()

    try:
        generator.start_comsol()

        if task == 'tjunction':
            generator.generate_tjunction_dataset()
        elif task == 'viscosity':
            generator.generate_viscosity_variants()
        elif task == 'all':
            generator.generate_tjunction_dataset()
            generator.generate_viscosity_variants()
        else:
            print(f"❌ 未知任务: {task}")
            print("   可用任务: tjunction, viscosity, all")

    finally:
        generator.stop_comsol()

    print("\n🎉 所有任务完成!")


if __name__ == "__main__":
    main()
