#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T型分岔道数据生成脚本 (9组)

参数配置:
- 入口速度: 0.15, 0.77, 1.54 cm/s (3档)
- 通道宽度: 150, 200, 250 μm (3档)

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
    """主函数 - 只生成T型分岔道数据"""
    print("🚀 T型分岔道数据生成器")
    print("=" * 50)
    print("\n生成内容:")
    print("  - 速度: 0.15, 0.77, 1.54 cm/s (3档)")
    print("  - 宽度: 150, 200, 250 μm (3档)")
    print("  - 总计: 9 组数据\n")

    try:
        generator = ExtendedDataGenerator()
        generator.start_comsol()

        try:
            count = generator.generate_tjunction_dataset()
            print(f"\n🎉 完成! 成功生成 {count}/9 组数据")
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
