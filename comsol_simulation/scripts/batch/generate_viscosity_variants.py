#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
不同粘度数据生成脚本 (3组)

参数配置:
- 基准工况: v=0.77 cm/s, w=200 μm
- 粘度变化: 0.0005, 0.002, 0.004 Pa·s (50%, 200%, 400%水)

作者: PINNs项目组
日期: 2025-12-24
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from generate_extended_dataset import ExtendedDataGenerator


def main():
    """主函数 - 只生成不同粘度数据"""
    print("🚀 不同粘度数据生成器")
    print("=" * 50)
    print("\n生成内容:")
    print("  - 基准: v=0.77 cm/s, w=200 μm")
    print("  - 粘度: 0.0005, 0.002, 0.004 Pa·s (3档)")
    print("  - 总计: 3 组数据\n")

    try:
        generator = ExtendedDataGenerator()
        generator.start_comsol()

        try:
            count = generator.generate_viscosity_variants()
            print(f"\n🎉 完成! 成功生成 {count}/3 组数据")
        finally:
            generator.stop_comsol()

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 执行错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
