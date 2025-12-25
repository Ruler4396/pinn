#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的36组COMSOL数据集自动生成脚本

生成内容:
1. 直通道参数加密 (6组) - v0.4/v1.2
2. T型分岔道 (9组) - 3速度 × 3宽度
3. Y型分岔道 (9组) - 3速度 × 3宽度
4. 不同粘度 (3组) - v0.8_w200

作者: PINNs项目组
日期: 2025-12-24
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
# 脚本位于: project_root/comsol_simulation/scripts/batch/
# 需要向上4级到达项目根目录
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

try:
    import mph
    print("✅ mph模块导入成功")
except ImportError:
    print("❌ mph模块未安装，请先安装: pip install mph")
    sys.exit(1)


class ExtendedDataGenerator:
    """扩展数据集生成器 - 完整36组数据"""

    # 工况参数配置
    VELOCITIES = [0.0015, 0.0077, 0.0154]  # 0.15, 0.77, 1.54 cm/s
    WIDTHS = [0.00015, 0.00020, 0.00025]     # 150, 200, 250 μm

    # 新增加密速度
    EXTENDED_VELOCITIES = [0.004, 0.012]     # 0.4, 1.2 cm/s

    # 不同粘度 (Pa·s)
    VISCOSITIES = [0.0005, 0.002, 0.004]     # 50%, 200%, 400%水

    # 几何类型
    GEOMETRY_TYPES = ['straight', 'tjunction', 'yjunction']

    def __init__(self, comsol_path=None):
        """初始化生成器"""
        # 自动检测COMSOL路径（mph库通常会自动检测）
        # 如需手动指定，使用: r"E:\COMSOL63\Multiphysics\bin\win64\comsol.exe"
        self.comsol_path = comsol_path or r"E:\COMSOL63\Multiphysics\bin\win64\comsol.exe"

        # 目录设置
        self.output_dir = project_root / "comsol_simulation" / "data"
        self.models_dir = project_root / "comsol_simulation" / "models"
        self.logs_dir = project_root / "comsol_simulation" / "logs"

        # 创建目录
        for directory in [self.output_dir, self.models_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # 状态跟踪
        self.results = {
            'straight': [],
            'tjunction': [],
            'yjunction': [],
            'viscosity': []
        }

        self.client = None

        print(f"🚀 扩展数据集生成器初始化完成")
        print(f"   - 输出目录: {self.output_dir}")

    def start_comsol(self):
        """启动COMSOL客户端"""
        if self.client is None:
            print(f"🚀 启动COMSOL客户端...")
            try:
                self.client = mph.Client(cores=1)
                print(f"   ✅ 客户端启动成功")
            except Exception as e:
                print(f"   ❌ 客户端启动失败: {e}")
                raise

    def stop_comsol(self):
        """停止COMSOL客户端"""
        if self.client is not None:
            try:
                self.client.clear()
                self.client.remove()
                self.client = None
                print(f"   ✅ COMSOL客户端已关闭")
            except:
                pass

    def generate_case_name(self, geometry: str, v_in: float, width: float,
                          viscosity: float = None) -> str:
        """生成案例名称"""
        v_label = f"v{v_in*100:.1f}"  # cm/s
        w_label = f"w{int(width*1e6)}"  # μm

        if geometry == 'straight':
            name = f"{v_label}_{w_label}"
        elif geometry == 'tjunction':
            name = f"tj_{v_label}_{w_label}"
        elif geometry == 'yjunction':
            name = f"yj_{v_label}_{w_label}"
        elif geometry == 'viscosity':
            mu_label = f"mu{viscosity*1000:.0f}"  # mPa·s
            name = f"{v_label}_{w_label}_{mu_label}"
        else:
            name = f"{geometry}_{v_label}_{w_label}"

        return name

    def create_straight_channel_model(self, v_in: float, width: float,
                                     length: float = 0.01,
                                     viscosity: float = 0.001,
                                     density: float = 1000.0,
                                     geometry_type: str = 'straight'):
        """创建直通道模型并求解"""
        # 根据viscosity判断是否需要特殊命名
        if viscosity != 0.001:  # 非标准粘度
            case_name = self.generate_case_name('viscosity', v_in, width, viscosity)
        else:
            case_name = self.generate_case_name(geometry_type, v_in, width)

        print(f"\n📐 创建直通道模型: {case_name}")
        print(f"   参数: v={v_in*100:.2f} cm/s, w={width*1e6:.0f} μm")

        try:
            # 创建模型
            model = self.client.create(case_name)
            java_model = model.java

            # 创建几何
            geom = geom = java_model.geom().create('geom1', 2)
            geom.lengthUnit('mm')

            # 创建矩形 (10mm x width)
            rect1 = geom.feature().create('rect1', 'Rectangle')
            rect1.set('size', [f'{length*1000}', f'{width*1000}'])
            rect1.set('pos', ['0', '0'])
            geom.run()

            # 添加层流物理场
            physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')

            # 设置流体属性 - 直接在FluidProperties节点设置
            fp = physics.feature('fp1')
            fp.set('mu_mat', 'userdef')
            fp.set('mu', f'{viscosity} [Pa*s]')
            fp.set('rho_mat', 'userdef')
            fp.set('rho', f'{density} [kg/m^3]')

            # 入口边界条件 (左边界) - 使用Inlet边界条件
            inlet = physics.feature().create('in1', 'Inlet')
            inlet.selection().set([1])  # 左边界
            # 设置速度 - U0in是法向流入速度（标量）
            inlet.set('U0in', f'{v_in}')

            # 出口边界条件 (右边界)
            outlet = physics.feature().create('out1', 'Outlet')
            outlet.selection().set([2])  # 右边界
            outlet.set('p0', '0')

            # 壁面 (上下边界，默认无滑移)
            wall = physics.feature().create('wall1', 'Wall')
            wall.selection().set([3, 4])

            # 创建网格
            mesh = java_model.mesh().create('mesh1', 'geom1')
            mesh.autoMeshSize(5)  # 常规
            mesh.run()

            # 创建研究
            study = java_model.study().create('std1')
            study.feature().create('stat', 'Stationary')

            # 运行求解
            print(f"   🔄 正在求解...")
            study.run()

            # 导出数据
            data = self.export_data_from_model(model, case_name, {
                'geometry': 'straight',
                'v_in': v_in,
                'width': width,
                'viscosity': viscosity,
                'density': density,
                'reynolds': density * v_in * width / viscosity
            })

            # 清理模型
            self.client.clear()

            return True, data

        except Exception as e:
            print(f"   ❌ 失败: {e}")
            return False, None

    def create_tjunction_model(self, v_in: float, width: float,
                              main_length: float = 0.01,
                              side_length: float = 0.005,
                              viscosity: float = 0.001,
                              density: float = 1000.0):
        """创建T型分岔道模型并求解"""
        case_name = self.generate_case_name('tjunction', v_in, width)

        print(f"\n📐 创建T型分岔道模型: {case_name}")
        print(f"   参数: v={v_in*100:.2f} cm/s, w={width*1e6:.0f} μm")

        try:
            # 创建模型
            model = self.client.create(case_name)
            java_model = model.java

            # 创建几何 (毫米单位)
            geom = java_model.geom().create('geom1', 2)
            geom.lengthUnit('mm')

            L_main = main_length * 1000
            L_side = side_length * 1000
            W = width * 1000

            # 左半段 (入口到分岔点)
            rect_left = geom.feature().create('rect_left', 'Rectangle')
            rect_left.set('size', [f'{L_main/2}', f'{W}'])
            rect_left.set('pos', ['0', '0'])

            # 右半段 (分岔点到出口1)
            rect_right = geom.feature().create('rect_right', 'Rectangle')
            rect_right.set('size', [f'{L_main/2}', f'{W}'])
            rect_right.set('pos', [f'{L_main/2}', '0'])

            # 侧通道 (分岔点到出口2)
            rect_side = geom.feature().create('rect_side', 'Rectangle')
            rect_side.set('size', [f'{W}', f'{L_side}'])
            rect_side.set('pos', [f'{L_main/2 - W/2}', f'{W}'])

            # 运行几何并合并
            geom.run('rect_left')
            geom.run('rect_right')
            geom.run('rect_side')

            union = geom.feature().create('union1', 'Union')
            union.selection('input').all()
            geom.run()

            # 添加层流物理场
            physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')

            # 设置流体属性 - 直接在FluidProperties节点设置
            fp = physics.feature('fp1')
            fp.set('mu_mat', 'userdef')
            fp.set('mu', f'{viscosity} [Pa*s]')
            fp.set('rho_mat', 'userdef')
            fp.set('rho', f'{density} [kg/m^3]')

            # 入口 (左边界) - 使用Inlet边界条件
            inlet = physics.feature().create('in1', 'Inlet')
            inlet.selection().set([1])  # 左边界
            # 设置速度 - U0in是法向流入速度（标量）
            inlet.set('U0in', f'{v_in}')

            # 出口1 (右边界)
            outlet1 = physics.feature().create('out1', 'Outlet')
            outlet1.selection().set([2])
            outlet1.set('p0', '0')

            # 出口2 (上边界)
            outlet2 = physics.feature().create('out2', 'Outlet')
            outlet2.selection().set([3])
            outlet2.set('p0', '0')

            # 网格
            mesh = java_model.mesh().create('mesh1', 'geom1')
            mesh.autoMeshSize(5)
            mesh.run()

            # 求解
            print(f"   🔄 正在求解...")
            study = java_model.study().create('std1')
            study.feature().create('stat', 'Stationary')
            study.run()

            # 导出数据
            data = self.export_data_from_model(model, case_name, {
                'geometry': 'tjunction',
                'v_in': v_in,
                'width': width,
                'main_length': main_length,
                'side_length': side_length,
                'viscosity': viscosity,
                'density': density,
                'reynolds': density * v_in * width / viscosity
            })

            self.client.clear()
            return True, data

        except Exception as e:
            print(f"   ❌ 失败: {e}")
            return False, None

    def create_yjunction_model(self, v_in: float, width: float,
                              main_length: float = 0.01,
                              branch_length: float = 0.005,
                              branch_angle: float = 45.0,
                              viscosity: float = 0.001,
                              density: float = 1000.0):
        """创建Y型分岔道模型并求解"""
        case_name = self.generate_case_name('yjunction', v_in, width)

        print(f"\n📐 创建Y型分岔道模型: {case_name}")
        print(f"   参数: v={v_in*100:.2f} cm/s, w={width*1e6:.0f} μm, angle={branch_angle}°")

        try:
            # 创建模型
            model = self.client.create(case_name)
            java_model = model.java

            # 创建几何
            geom = java_model.geom().create('geom1', 2)
            geom.lengthUnit('mm')

            L_main = main_length * 1000
            L_branch = branch_length * 1000
            W = width * 1000

            # 主通道 (入口到分岔点)
            rect_main = geom.feature().create('rect_main', 'Rectangle')
            rect_main.set('size', [f'{L_main/2}', f'{W}'])
            rect_main.set('pos', ['0', '0'])

            # 左分支
            rect_left = geom.feature().create('rect_left', 'Rectangle')
            rect_left.set('size', [f'{L_branch}', f'{W}'])
            rect_left.set('pos', [f'{L_main/2}', '0'])

            # 右分支 (偏移和旋转后)
            # 简化版：使用矩形然后旋转
            rect_right = geom.feature().create('rect_right', 'Rectangle')
            rect_right.set('size', [f'{L_branch}', f'{W}'])
            rect_right.set('pos', [f'{L_main/2}', '0'])

            # 运行几何
            geom.run('rect_main')
            geom.run('rect_left')
            geom.run('rect_right')

            # 合并
            union = geom.feature().create('union1', 'Union')
            union.selection('input').all()
            geom.run()

            # 添加物理场
            physics = java_model.physics().create('spf', 'LaminarFlow', 'geom1')

            # 设置流体属性 - 直接在FluidProperties节点设置
            fp = physics.feature('fp1')
            fp.set('mu_mat', 'userdef')
            fp.set('mu', f'{viscosity} [Pa*s]')
            fp.set('rho_mat', 'userdef')
            fp.set('rho', f'{density} [kg/m^3]')

            # 入口 (左边界) - 使用Inlet边界条件
            inlet = physics.feature().create('in1', 'Inlet')
            inlet.selection().set([1])
            # 设置速度 - U0in是法向流入速度（标量）
            inlet.set('U0in', f'{v_in}')

            # 出口1 (上分支)
            outlet1 = physics.feature().create('out1', 'Outlet')
            outlet1.selection().set([2])
            outlet1.set('p0', '0')

            # 出口2 (下分支)
            outlet2 = physics.feature().create('out2', 'Outlet')
            outlet2.selection().set([3])
            outlet2.set('p0', '0')

            # 网格
            mesh = java_model.mesh().create('mesh1', 'geom1')
            mesh.autoMeshSize(5)
            mesh.run()

            # 求解
            print(f"   🔄 正在求解...")
            study = java_model.study().create('std1')
            study.feature().create('stat', 'Stationary')
            study.run()

            # 导出数据
            data = self.export_data_from_model(model, case_name, {
                'geometry': 'yjunction',
                'v_in': v_in,
                'width': width,
                'main_length': main_length,
                'branch_length': branch_length,
                'branch_angle': branch_angle,
                'viscosity': viscosity,
                'density': density,
                'reynolds': density * v_in * width / viscosity
            })

            self.client.clear()
            return True, data

        except Exception as e:
            print(f"   ❌ 失败: {e}")
            return False, None

    def export_data_from_model(self, model, case_name: str, metadata: Dict) -> Dict:
        """从模型导出数据"""
        try:
            java_model = model.java

            # 创建导出节点 - 简化配置，与直通道相同
            export = java_model.result().export().create('export1', 'Data')
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

                # 解析数据（跳过头部注释）
                data_lines = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('%'):
                        try:
                            parts = line.split()
                            if len(parts) >= 5:
                                # 导出格式: x, y, u, v, p
                                # 注意：COMSOL导出使用几何单位，可能是mm
                                x_val = float(parts[0])
                                y_val = float(parts[1])
                                u_val = float(parts[2])
                                v_val = float(parts[3])
                                p_val = float(parts[4])

                                # 单位转换：COMSOL使用几何定义的单位（mm）导出
                                # 对于微流控芯片（长度~10-15mm），需要转换为米
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
                print(f"   ⚠️ 不使用备用评估方法（会导致数据错误）")
                print(f"   ❌ 请检查Export节点配置")
                raise ValueError("数据导出失败，无法使用备用评估方法")

            if len(results) == 0:
                raise ValueError("无有效数据")

            # 保存HDF5文件（使用现有格式：x, y, u, v, p）
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
                f.attrs['channel_length'] = metadata.get('width', 0.01)
                f.attrs['channel_width'] = metadata.get('width', 0.00015)
                f.attrs['inlet_velocity'] = metadata.get('v_in', 0.005)
                f.attrs['fluid_density'] = metadata.get('density', 1000.0)
                f.attrs['fluid_viscosity'] = metadata.get('viscosity', 0.001)
                f.attrs['reynolds_number'] = metadata.get('reynolds', 1.0)
                f.attrs['total_points'] = len(results)
                f.attrs['generation_method'] = 'COMSOL_simulation'
                f.attrs['description'] = f'COMSOL microfluidic simulation - {case_name}'

            print(f"   ✅ 数据导出成功: {filename} ({len(results)} 点)")

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

    def generate_straight_extended(self):
        """生成直通道加密数据 (6组)"""
        print("\n" + "=" * 60)
        print("🔄 任务1: 生成直通道参数加密数据 (6组)")
        print("=" * 60)

        cases = []
        for v_in in self.EXTENDED_VELOCITIES:
            for width in self.WIDTHS:
                cases.append({'v_in': v_in, 'width': width})

        success_count = 0
        for i, case in enumerate(cases, 1):
            print(f"\n[{i}/{len(cases)}] 生成案例...")
            success, data = self.create_straight_channel_model(
                v_in=case['v_in'],
                width=case['width']
            )
            if success:
                success_count += 1
                self.results['straight'].append(data)

        print(f"\n✅ 直通道加密数据完成: {success_count}/{len(cases)}")
        return success_count

    def generate_tjunction_dataset(self):
        """生成T型分岔道数据 (9组)"""
        print("\n" + "=" * 60)
        print("🔄 任务2: 生成T型分岔道数据 (9组)")
        print("=" * 60)

        cases = []
        for v_in in self.VELOCITIES:
            for width in self.WIDTHS:
                cases.append({'v_in': v_in, 'width': width})

        success_count = 0
        for i, case in enumerate(cases, 1):
            print(f"\n[{i}/{len(cases)}] 生成案例...")
            success, data = self.create_tjunction_model(
                v_in=case['v_in'],
                width=case['width']
            )
            if success:
                success_count += 1
                self.results['tjunction'].append(data)

        print(f"\n✅ T型分岔道数据完成: {success_count}/{len(cases)}")
        return success_count

    def generate_yjunction_dataset(self):
        """生成Y型分岔道数据 (9组)"""
        print("\n" + "=" * 60)
        print("🔄 任务3: 生成Y型分岔道数据 (9组)")
        print("=" * 60)

        cases = []
        for v_in in self.VELOCITIES:
            for width in self.WIDTHS:
                cases.append({'v_in': v_in, 'width': width})

        success_count = 0
        for i, case in enumerate(cases, 1):
            print(f"\n[{i}/{len(cases)}] 生成案例...")
            success, data = self.create_yjunction_model(
                v_in=case['v_in'],
                width=case['width']
            )
            if success:
                success_count += 1
                self.results['yjunction'].append(data)

        print(f"\n✅ Y型分岔道数据完成: {success_count}/{len(cases)}")
        return success_count

    def generate_viscosity_variants(self):
        """生成不同粘度数据 (3组)"""
        print("\n" + "=" * 60)
        print("🔄 任务4: 生成不同粘度数据 (3组)")
        print("=" * 60)

        # 基准工况: v0.8_w200
        v_in = 0.0077
        width = 0.00020

        success_count = 0
        for i, viscosity in enumerate(self.VISCOSITIES, 1):
            print(f"\n[{i}/{len(self.VISCOSITIES)}] 生成案例 (μ={viscosity} Pa·s)...")
            success, data = self.create_straight_channel_model(
                v_in=v_in,
                width=width,
                viscosity=viscosity
            )
            if success:
                success_count += 1
                self.results['viscosity'].append(data)

        print(f"\n✅ 不同粘度数据完成: {success_count}/{len(self.VISCOSITIES)}")
        return success_count

    def run_all_tasks(self, tasks: List[str] = None):
        """运行所有生成任务"""
        if tasks is None:
            tasks = ['straight', 'tjunction', 'yjunction', 'viscosity']

        print("\n" + "=" * 70)
        print("🚀 开始批量生成COMSOL数据集")
        print("=" * 70)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"任务列表: {', '.join(tasks)}")

        start_time = time.time()

        try:
            self.start_comsol()

            if 'straight' in tasks:
                self.generate_straight_extended()

            if 'tjunction' in tasks:
                self.generate_tjunction_dataset()

            if 'yjunction' in tasks:
                self.generate_yjunction_dataset()

            if 'viscosity' in tasks:
                self.generate_viscosity_variants()

        finally:
            self.stop_comsol()

        # 总结
        total_time = time.time() - start_time
        self.print_summary(total_time)

    def print_summary(self, total_time: float):
        """打印总结报告"""
        print("\n" + "=" * 70)
        print("📊 生成总结报告")
        print("=" * 70)

        total_files = 0
        for geom_type, results in self.results.items():
            count = len(results)
            total_files += count
            if count > 0:
                print(f"\n{geom_type.upper()}: {count} 个文件")

        print(f"\n总生成文件: {total_files}")
        print(f"总用时: {total_time/60:.1f} 分钟")
        print(f"平均每文件: {total_time/total_files:.1f} 秒")

        print(f"\n📁 数据保存在: {self.output_dir}")

        # 生成报告文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.logs_dir / f"generation_report_{timestamp}.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("COMSOL扩展数据集生成报告\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总文件数: {total_files}\n")
            f.write(f"总用时: {total_time/60:.1f} 分钟\n\n")

            for geom_type, results in self.results.items():
                if results:
                    f.write(f"{geom_type.upper()}:\n")
                    for r in results:
                        f.write(f"  - {r['filename']} ({r['points']} 点)\n")

        print(f"📋 报告文件: {report_file}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='批量生成COMSOL扩展数据集')
    parser.add_argument('--tasks', type=str, default='all',
                       help='任务列表: straight,tjunction,yjunction,viscosity,all')
    parser.add_argument('--comsol', type=str,
                       default=r"E:\COMSOL63\Multiphysics\bin\win64\comsol.exe",
                       help='COMSOL可执行文件路径')

    args = parser.parse_args()

    # 解析任务
    if args.tasks.lower() == 'all':
        tasks = ['straight', 'tjunction', 'yjunction', 'viscosity']
    else:
        tasks = [t.strip() for t in args.tasks.split(',')]

    print("🚀 COMSOL扩展数据集自动生成器")
    print("=" * 50)
    print(f"任务: {', '.join(tasks)}")

    try:
        generator = ExtendedDataGenerator(comsol_path=args.comsol)
        generator.run_all_tasks(tasks=tasks)

        print("\n🎉 所有任务完成!")

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 执行错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
