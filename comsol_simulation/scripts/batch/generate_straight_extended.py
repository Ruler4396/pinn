#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直通道参数加密数据生成脚本 (6组)

新增速度: 0.4 cm/s, 1.2 cm/s
通道宽度: 150, 200, 250 μm

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
    """主函数 - 只生成直通道加密数据"""
    print("🚀 直通道参数加密数据生成器")
    print("=" * 50)
    print("\n生成内容:")
    print("  - 速度: 0.4, 1.2 cm/s (2档)")
    print("  - 宽度: 150, 200, 250 μm (3档)")
    print("  - 总计: 6 组数据\n")

    try:
        generator = ExtendedDataGenerator()
        generator.start_comsol()

        try:
            count = generator.generate_straight_extended()
            print(f"\n🎉 完成! 成功生成 {count}/6 组数据")
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
