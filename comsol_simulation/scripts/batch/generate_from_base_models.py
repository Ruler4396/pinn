#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于预设基准模型生成分岔道数据集

使用方法:
1. 在COMSOL GUI中打开并设置好 tjunction_base.mph 和 yjunction_base.mph
2. 运行此脚本批量生成数据

依赖: 需要先完成GUI中的边界设置
"""

import os
import sys
import time
import h5py
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

# 添加项目路径
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

try:
    import mph
    print("✅ mph模块导入成功")
except ImportError:
    print("❌ mph模块未安装")
    sys.exit(1)


class BaseModelDataGenerator:
    """基于预设基准模型生成数据"""

    # 参数配置
    VELOCITIES = [0.0015, 0.0077, 0.0154]  # 0.15, 0.77, 1.54 cm/s
    WIDTHS = [0.00015, 0.00020, 0.00025]    # 150, 200, 250 μm
    VISCOSITIES = [0.0005, 0.002, 0.004]    # 不同粘度

    def __init__(self, comsol_path=None):
        self.comsol_path = comsol_path or r"E:\COMSOL63\Multiphysics\bin\win64\comsol.exe"

        # 目录设置
        self.output_dir = project_root / "comsol_simulation" / "data"
        self.models_dir = project_root / "comsol_simulation" / "models"
        self.logs_dir = project_root / "comsol_simulation" / "comsol_simulation" / "logs"

        # 创建目录
        for directory in [self.output_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        self.results = {
            'tjunction': [],
            'yjunction': [],
            'viscosity': []
        }

        self.client = None

        print(f"🚀 基准模型数据生成器初始化完成")
        print(f"   - 输出目录: {self.output_dir}")
        print(f"   - 模型目录: {self.models_dir}")

    def start_comsol(self):
        """启动COMSOL客户端"""
        print(f"\n🚀 启动COMSOL客户端...")
        self.client = mph.start(self.comsol_path)
        print(f"   ✅ 客户端启动成功")

    def generate_case_name(self, geometry_type: str, v_in: float, width: float,
                          viscosity: float = 0.001) -> str:
        """生成文件名"""
        v_str = f"v{v_in*100:.1f}"  # cm/s
        w_str = f"w{width*1e6:.0f}"  # μm

        if geometry_type == 'tjunction':
            prefix = "tj"
        elif geometry_type == 'yjunction':
            prefix = "yj"
        elif geometry_type == 'viscosity':
            prefix = "v0.8_w200"
            # 添加粘度标识
            if viscosity == 0.0005:
                v_str = "mu0"
            elif viscosity == 0.002:
                v_str = "mu2"
            elif viscosity == 0.004:
                v_str = "mu4"
            return f"{prefix}_{v_str}"
        else:
            prefix = "v"

        return f"{prefix}_{v_str}_{w_str}"

    def export_data_from_model(self, model, case_name: str, metadata: Dict) -> Dict:
        """从模型导出数据到HDF5"""
        try:
            java_model = model.java

            # 检查模型是否有Export节点
            export_nodes = java_model.result().export()
            export_count = len(list(export_nodes))
            print(f"   📤 现有Export节点: {export_count}个")

            # 创建新的Export节点
            export = export_nodes.create(f'export_{case_name}', 'Data')
            export.set('expr', ['x', 'y', 'u', 'v', 'p'])

            # 生成临时文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = self.logs_dir / f"temp_{case_name}_{timestamp}.txt"
            export.set('filename', str(temp_file))

            # 执行导出
            print(f"   📤 正在导出数据...")
            export.run()

            # 读取导出的数据
            try:
                with open(temp_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # 解析数据
                data_lines = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('%'):
                        try:
                            parts = line.split()
                            if len(parts) >= 5:
                                x_val = float(parts[0])
                                y_val = float(parts[1])
                                u_val = float(parts[2])
                                v_val = float(parts[3])
                                p_val = float(parts[4])

                                # 单位转换（如果是mm）
                                x_val /= 1000  # mm -> m
                                y_val /= 1000  # mm -> m

                                data_lines.append([x_val, y_val, u_val, v_val, p_val])
                        except:
                            continue

                results = np.array(data_lines)

                # 删除临时文件
                try:
                    temp_file.unlink()
                except:
                    pass

            except Exception as e:
                print(f"   ⚠️ 导出文件读取失败: {e}")
                raise

            if len(results) == 0:
                raise ValueError("无有效数据")

            # 保存HDF5文件
            filename = f"{case_name}.h5"
            filepath = self.output_dir / filename

            with h5py.File(filepath, 'w') as f:
                f.create_dataset('x', data=results[:, 0])
                f.create_dataset('y', data=results[:, 1])
                f.create_dataset('u', data=results[:, 2])
                f.create_dataset('v', data=results[:, 3])
                f.create_dataset('p', data=results[:, 4])

                # 元数据
                f.attrs['case_id'] = case_name
                f.attrs['inlet_velocity'] = metadata.get('v_in', 0.005)
                f.attrs['channel_width'] = metadata.get('width', 0.00015)
                f.attrs['fluid_viscosity'] = metadata.get('viscosity', 0.001)
                f.attrs['fluid_density'] = metadata.get('density', 1000.0)
                f.attrs['reynolds_number'] = metadata.get('reynolds', 1.0)
                f.attrs['total_points'] = len(results)
                f.attrs['generation_method'] = 'COMSOL_simulation'

            print(f"   ✅ 数据导出成功: {filename} ({len(results)} 点)")
            print(f"      U范围: {results[:, 2].min():.6f} - {results[:, 2].max():.6f} m/s")
            print(f"      P范围: {results[:, 4].min():.6f} - {results[:, 4].max():.6f} Pa")

            return {
                'case_name': case_name,
                'filename': filename,
                'points': len(results),
                'filepath': filepath
            }

        except Exception as e:
            print(f"   ❌ 数据导出失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    def generate_from_base_model(self, geometry_type: str, v_in: float,
                                 width: float, viscosity: float = 0.001) -> Tuple[bool, Dict]:
        """从基准模型生成一个案例"""
        case_name = self.generate_case_name(geometry_type, v_in, width, viscosity)

        print(f"\n📐 生成案例: {case_name}")
        print(f"   参数: v={v_in*100:.2f} cm/s, w={width*1e6:.0f} μm")

        try:
            # 确定基准模型路径
            if geometry_type == 'tjunction':
                base_model_path = self.models_dir / 'tjunction_base.mph'
            elif geometry_type == 'yjunction':
                base_model_path = self.models_dir / 'yjunction_base.mph'
            elif geometry_type == 'viscosity':
                base_model_path = self.models_dir / 'tjunction_base.mph'  # 使用直通道或T型
                # 对于粘度变化，使用直通道模型更合适
                # 需要检查是否有专门的粘度基准模型
            else:
                raise ValueError(f"未知几何类型: {geometry_type}")

            # 检查基准模型是否存在
            if not base_model_path.exists():
                print(f"   ⚠️ 基准模型不存在: {base_model_path}")
                print(f"   请先运行 create_base_models.py 并在GUI中设置边界")
                return False, None

            # 加载基准模型
            print(f"   📂 加载基准模型: {base_model_path.name}")
            model = self.client.load(str(base_model_path))
            java_model = model.java

            # 修改参数
            params = java_model.param()
            params.set('v_in', f'{v_in} [m/s]')
            params.set('width', f'{width} [m]')
            params.set('viscosity', f'{viscosity} [Pa*s]')

            print(f"   ✅ 参数已更新")

            # 注意：几何需要根据新参数重新生成
            # 这需要在基准模型中设置参数化几何

            # 运行求解
            print(f"   🔄 正在求解...")
            java_model.study().run()
            print(f"   ✅ 求解完成")

            # 导出数据
            data = self.export_data_from_model(model, case_name, {
                'geometry': geometry_type,
                'v_in': v_in,
                'width': width,
                'viscosity': viscosity,
                'density': 1000.0,
                'reynolds': 1000 * v_in * width / viscosity
            })

            return True, data

        except Exception as e:
            print(f"   ❌ 失败: {e}")
            import traceback
            traceback.print_exc()
            return False, None

    def generate_tjunction_dataset(self):
        """生成T型分岔道数据集"""
        print("\n" + "=" * 60)
        print("🔄 任务: 生成T型分岔道数据集 (9组)")
        print("=" * 60)

        cases = []
        for v_in in self.VELOCITIES:
            for width in self.WIDTHS:
                success, data = self.generate_from_base_model('tjunction', v_in, width)
                if success:
                    cases.append(data)
                time.sleep(1)  # 短暂暂停

        self.results['tjunction'] = cases
        print(f"\n✅ T型分岔道数据完成: {len(cases)}/9")

    def generate_yjunction_dataset(self):
        """生成Y型分岔道数据集"""
        print("\n" + "=" * 60)
        print("🔄 任务: 生成Y型分岔道数据集 (9组)")
        print("=" * 60)

        cases = []
        for v_in in self.VELOCITIES:
            for width in self.WIDTHS:
                success, data = self.generate_from_base_model('yjunction', v_in, width)
                if success:
                    cases.append(data)
                time.sleep(1)

        self.results['yjunction'] = cases
        print(f"\n✅ Y型分岔道数据完成: {len(cases)}/9")

    def generate_viscosity_dataset(self):
        """生成不同粘度数据集"""
        print("\n" + "=" * 60)
        print("🔄 任务: 生成不同粘度数据集 (3组)")
        print("=" * 60)

        cases = []
        v_in = 0.0077  # 使用0.77 cm/s
        width = 0.0002  # 使用200μm

        for viscosity in self.VISCOSITIES:
            success, data = self.generate_from_base_model('viscosity', v_in, width, viscosity)
            if success:
                cases.append(data)
            time.sleep(1)

        self.results['viscosity'] = cases
        print(f"\n✅ 不同粘度数据完成: {len(cases)}/3")

    def generate_all(self):
        """生成所有数据"""
        start_time = time.time()

        print("=" * 60)
        print("🚀 开始批量生成分岔道数据集")
        print("=" * 60)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"任务列表: tjunction, yjunction, viscosity")

        self.start_comsol()

        try:
            # T型分岔道
            self.generate_tjunction_dataset()

            # Y型分岔道
            self.generate_yjunction_dataset()

            # 不同粘度
            self.generate_viscosity_dataset()

            # 总结报告
            elapsed = time.time() - start_time
            self.print_summary(elapsed)

        finally:
            if self.client:
                self.client.disconnect()

    def print_summary(self, elapsed_time: float):
        """打印总结报告"""
        print("\n" + "=" * 60)
        print("📊 生成总结报告")
        print("=" * 60)

        for geom_type, cases in self.results.items():
            if cases:
                print(f"\n{geom_type.upper()}: {len(cases)} 个文件")
                for case in cases:
                    print(f"  - {case['filename']} ({case['points']} 点)")

        total_files = sum(len(cases) for cases in self.results.values())
        print(f"\n总生成文件: {total_files}")
        print(f"总用时: {elapsed_time/60:.1f} 分钟")
        print(f"\n📁 数据保存在: {self.output_dir}")

        # 保存报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.logs_dir / f"generation_report_{timestamp}.txt"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("COMSOL分岔道数据集生成报告\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总文件数: {total_files}\n")
            f.write(f"总用时: {elapsed_time/60:.1f} 分钟\n\n")

            for geom_type, cases in self.results.items():
                if cases:
                    f.write(f"{geom_type.upper()}:\n")
                    for case in cases:
                        f.write(f"  - {case['filename']} ({case['points']} 点)\n")
                    f.write("\n")

        print(f"📋 报告文件: {report_path}")
        print("\n🎉 所有任务完成!")


if __name__ == '__main__':
    print("=" * 60)
    print("基于预设基准模型的数据生成工具")
    print("=" * 60)
    print()
    print("⚠️  使用前请确保:")
    print("   1. 已运行 create_base_models.py 生成基准模型")
    print("   2. 已在COMSOL GUI中设置好边界条件")
    print("   3. 基准模型已保存")
    print()
    print("=" * 60)

    generator = BaseModelDataGenerator()
    generator.generate_all()
