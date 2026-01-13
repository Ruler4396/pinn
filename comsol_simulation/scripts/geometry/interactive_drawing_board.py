# -*- coding: utf-8 -*-
"""
交互式几何绘图板

允许用户通过鼠标绘制流道几何形状，然后转换为COMSOL几何模型

功能：
- 矩形工具：绘制矩形通道
- 直线工具：绘制流道边界
- 橡皮擦：删除已绘制的内容
- 撤销：撤销上一步操作
- 导出：将绘制的几何导出为模型数据
"""

import sys
from pathlib import Path
import numpy as np

# 添加geometry目录到路径
geometry_dir = Path(__file__).parent
sys.path.insert(0, str(geometry_dir))

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Polygon
    from matplotlib.lines import Line2D
    print("[OK] matplotlib imported successfully")
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    print("Please run: pip install matplotlib numpy")
    sys.exit(1)


class DrawingBoard:
    """交互式绘图板类"""

    def __init__(self, figsize=(14, 10), xlim=(0, 15), ylim=(-8, 8)):
        """
        初始化绘图板

        Args:
            figsize: 图形大小
            xlim: X轴范围 (min, max)，单位mm
            ylim: Y轴范围 (min, max)，单位mm
        """
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.fig.canvas.manager.set_window_title('微流控几何交互式绘图板')

        # 设置坐标范围
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.set_xlabel('X (mm)', fontsize=12)
        self.ax.set_ylabel('Y (mm)', fontsize=12)
        self.ax.set_title('交互式几何绘图板 - 绘制流道形状', fontsize=14, fontweight='bold')

        # 绘图状态
        self.current_tool = 'rectangle'  # 当前工具: rectangle, line, erase
        self.is_drawing = False
        self.start_point = None
        self.current_shape = None  # 当前正在绘制的形状

        # 存储所有绘制的形状
        self.rectangles = []  # 矩形列表 [(x1, y1, x2, y2), ...]
        self.lines = []       # 线段列表 [(x1, y1, x2, y2), ...]
        self.shapes_drawn = []  # 已绘制的图形对象（用于撤销）

        # 鼠标位置指示器
        self.cursor_indicator = self.ax.plot([], [], 'r+', markersize=15, alpha=0.5)[0]

        # 连接事件
        self.fig.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)

        # 添加工具说明
        self.add_instructions()

        print("\n" + "="*60)
        print("交互式绘图板已启动")
        print("="*60)
        self.print_instructions()

    def add_instructions(self):
        """在图形上添加操作说明"""
        instructions = (
            "快捷键:\n"
            "1 - 矩形工具\n"
            "2 - 直线工具\n"
            "3 - 橡皮擦\n"
            "Z - 撤销\n"
            "C - 清空画布\n"
            "E - 导出几何\n"
            "Q - 退出"
        )
        self.ax.text(0.02, 0.02, instructions, transform=self.ax.transAxes,
                    fontsize=9, verticalalignment='bottom',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    def print_instructions(self):
        """打印操作说明"""
        print("\n操作说明:")
        print("  鼠标左键拖动 - 绘制形状")
        print("  键盘快捷键:")
        print("    1 - 切换到矩形工具")
        print("    2 - 切换到直线工具")
        print("    3 - 切换到橡皮擦")
        print("    Z - 撤销上一步")
        print("    C - 清空画布")
        print("    E - 导出几何数据")
        print("    Q - 退出程序")
        print(f"\n当前工具: {self.get_tool_name()}")
        print("="*60)

    def get_tool_name(self):
        """获取当前工具名称"""
        tool_names = {
            'rectangle': '矩形工具',
            'line': '直线工具',
            'erase': '橡皮擦'
        }
        return tool_names.get(self.current_tool, self.current_tool)

    def update_title(self):
        """更新标题显示当前工具"""
        self.ax.set_title(f'交互式几何绘图板 - 当前工具: {self.get_tool_name()}',
                        fontsize=14, fontweight='bold')
        self.fig.canvas.draw()

    def on_mouse_press(self, event):
        """鼠标按下事件"""
        if event.inaxes != self.ax:
            return

        self.is_drawing = True
        self.start_point = (event.xdata, event.ydata)

        if self.current_tool == 'rectangle':
            # 创建临时矩形
            self.current_shape = Rectangle(
                self.start_point, 0, 0,
                fill=False, edgecolor='blue', linewidth=2
            )
            self.ax.add_patch(self.current_shape)
        elif self.current_tool == 'line':
            # 创建临时线段
            self.current_shape = Line2D(
                [self.start_point[0]], [self.start_point[1]],
                color='green', linewidth=2
            )
            self.ax.add_line(self.current_shape)
        elif self.current_tool == 'erase':
            # 橡皮擦：删除点击位置附近的形状
            self.erase_at(event.xdata, event.ydata)

    def on_mouse_release(self, event):
        """鼠标释放事件"""
        if not self.is_drawing:
            return

        self.is_drawing = False

        if event.inaxes != self.ax:
            # 鼠标移出画布，取消绘制
            if self.current_shape:
                self.current_shape.remove()
                self.current_shape = None
            return

        end_point = (event.xdata, event.ydata)

        if self.current_tool == 'rectangle' and self.current_shape:
            # 完成矩形绘制
            x1, y1 = self.start_point
            x2, y2 = end_point
            width = x2 - x1
            height = y2 - y1

            # 标准化矩形数据（确保width和height为正）
            if width < 0:
                x1, x2 = x2, x1
                width = abs(width)
            if height < 0:
                y1, y2 = y2, y1
                height = abs(height)

            self.current_shape.set_width(width)
            self.current_shape.set_height(height)
            self.current_shape.set_xy((x1, y1))

            # 保存矩形数据
            self.rectangles.append((x1, y1, x2, y2))
            self.shapes_drawn.append(('rectangle', self.current_shape, (x1, y1, x2, y2)))
            print(f"[OK] 添加矩形: ({x1:.2f}, {y1:.2f}) -> ({x2:.2f}, {y2:.2f})")

        elif self.current_tool == 'line' and self.current_shape:
            # 完成线段绘制
            self.current_shape.set_data(
                [self.start_point[0], end_point[0]],
                [self.start_point[1], end_point[1]]
            )

            # 保存线段数据
            self.lines.append((self.start_point[0], self.start_point[1],
                             end_point[0], end_point[1]))
            self.shapes_drawn.append(('line', self.current_shape,
                                    (self.start_point[0], self.start_point[1],
                                     end_point[0], end_point[1])))
            print(f"[OK] 添加线段: ({self.start_point[0]:.2f}, {self.start_point[1]:.2f}) -> "
                  f"({end_point[0]:.2f}, {end_point[1]:.2f})")

        self.current_shape = None
        self.fig.canvas.draw()

    def on_mouse_move(self, event):
        """鼠标移动事件"""
        if event.inaxes == self.ax:
            # 更新光标指示器
            self.cursor_indicator.set_data([event.xdata], [event.ydata])

            if self.is_drawing and self.current_shape:
                if self.current_tool == 'rectangle':
                    # 更新矩形大小
                    x1, y1 = self.start_point
                    x2, y2 = event.xdata, event.ydata
                    width = x2 - x1
                    height = y2 - y1
                    self.current_shape.set_width(width)
                    self.current_shape.set_height(height)
                elif self.current_tool == 'line':
                    # 更新线段终点
                    self.current_shape.set_data(
                        [self.start_point[0], event.xdata],
                        [self.start_point[1], event.ydata]
                    )

                self.fig.canvas.draw()

    def on_key_press(self, event):
        """键盘按键事件"""
        key = event.key.upper()

        if key == '1':
            self.current_tool = 'rectangle'
            print(f"\n[INFO] 切换工具: {self.get_tool_name()}")
            self.update_title()
        elif key == '2':
            self.current_tool = 'line'
            print(f"\n[INFO] 切换工具: {self.get_tool_name()}")
            self.update_title()
        elif key == '3':
            self.current_tool = 'erase'
            print(f"\n[INFO] 切换工具: {self.get_tool_name()}")
            self.update_title()
        elif key == 'Z':
            self.undo()
        elif key == 'C':
            self.clear_all()
        elif key == 'E':
            self.export_geometry()
        elif key == 'Q':
            print("\n[INFO] 退出绘图板")
            plt.close(self.fig)

    def erase_at(self, x, y, threshold=0.5):
        """在指定位置擦除形状"""
        erased = False

        # 从后往前检查（后绘制的在上面）
        for i in range(len(self.shapes_drawn) - 1, -1, -1):
            shape_type, shape_obj, shape_data = self.shapes_drawn[i]

            if shape_type == 'rectangle':
                x1, y1, x2, y2 = shape_data
                if x1 - threshold <= x <= x2 + threshold and y1 - threshold <= y <= y2 + threshold:
                    shape_obj.remove()
                    self.shapes_drawn.pop(i)
                    self.rectangles.pop(i)
                    erased = True
                    print(f"[OK] 删除矩形: ({x1:.2f}, {y1:.2f}) -> ({x2:.2f}, {y2:.2f})")
                    break

            elif shape_type == 'line':
                x1, y1, x2, y2 = shape_data
                # 计算点到线段的距离
                dist = self.point_to_line_distance(x, y, x1, y1, x2, y2)
                if dist < threshold:
                    shape_obj.remove()
                    # 找到对应的线段索引
                    for j, line_data in enumerate(self.lines):
                        if line_data == shape_data:
                            self.lines.pop(j)
                            break
                    self.shapes_drawn.pop(i)
                    erased = True
                    print(f"[OK] 删除线段: ({x1:.2f}, {y1:.2f}) -> ({x2:.2f}, {y2:.2f})")
                    break

        if erased:
            self.fig.canvas.draw()

    def point_to_line_distance(self, px, py, x1, y1, x2, y2):
        """计算点到线段的距离"""
        # 线段长度平方
        line_length_sq = (x2 - x1)**2 + (y2 - y1)**2
        if line_length_sq == 0:
            return np.sqrt((px - x1)**2 + (py - y1)**2)

        # 计算投影参数
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq))

        # 投影点
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)

        return np.sqrt((px - proj_x)**2 + (py - proj_y)**2)

    def undo(self):
        """撤销上一步操作"""
        if not self.shapes_drawn:
            print("[INFO] 没有可撤销的操作")
            return

        shape_type, shape_obj, shape_data = self.shapes_drawn.pop()
        shape_obj.remove()

        if shape_type == 'rectangle':
            if self.rectangles and self.rectangles[-1] == shape_data:
                self.rectangles.pop()
        elif shape_type == 'line':
            if self.lines and self.lines[-1] == shape_data:
                self.lines.pop()

        print("[OK] 撤销上一步操作")
        self.fig.canvas.draw()

    def clear_all(self):
        """清空画布"""
        for _, shape_obj, _ in self.shapes_drawn:
            shape_obj.remove()

        self.rectangles.clear()
        self.lines.clear()
        self.shapes_drawn.clear()

        print("[OK] 画布已清空")
        self.fig.canvas.draw()

    def export_geometry(self):
        """导出几何数据"""
        print("\n" + "="*60)
        print("导出几何数据")
        print("="*60)

        print(f"\n矩形数量: {len(self.rectangles)}")
        print(f"线段数量: {len(self.lines)}")

        if self.rectangles:
            print("\n矩形列表:")
            for i, (x1, y1, x2, y2) in enumerate(self.rectangles, 1):
                width = x2 - x1
                height = y2 - y1
                print(f"  {i}. 位置: ({x1:.2f}, {y1:.2f}), "
                      f"尺寸: {width:.2f} x {height:.2f} mm")

        if self.lines:
            print("\n线段列表:")
            for i, (x1, y1, x2, y2) in enumerate(self.lines, 1):
                length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                print(f"  {i}. ({x1:.2f}, {y1:.2f}) -> ({x2:.2f}, {y2:.2f}), "
                      f"长度: {length:.2f} mm, 角度: {angle:.1f}°")

        # 保存原始数据到文件
        output_file = geometry_dir / 'output' / 'drawn_geometry.txt'
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 交互式绘图板导出的几何数据\n")
            f.write("# 单位: mm\n\n")
            f.write(f"# 矩形数量: {len(self.rectangles)}\n")
            f.write("RECTANGLES:\n")
            for i, (x1, y1, x2, y2) in enumerate(self.rectangles, 1):
                f.write(f"  {i}. x1={x1:.4f}, y1={y1:.4f}, x2={x2:.4f}, y2={y2:.4f}\n")

            f.write(f"\n# 线段数量: {len(self.lines)}\n")
            f.write("LINES:\n")
            for i, (x1, y1, x2, y2) in enumerate(self.lines, 1):
                f.write(f"  {i}. x1={x1:.4f}, y1={y1:.4f}, x2={x2:.4f}, y2={y2:.4f}\n")

        print(f"\n[OK] 数据已保存到: {output_file}")

        # 生成几何模型代码
        model_file = geometry_dir / 'output' / 'custom_geometry.py'
        self.generate_geometry_model(model_file)
        print(f"[OK] 几何模型代码已保存到: {model_file}")

        print("\n" + "="*60)

    def generate_geometry_model(self, output_file):
        """生成可运行的几何模型代码"""
        code = '''# -*- coding: utf-8 -*-
"""
自定义几何模型 - 从交互式绘图板生成

此文件由 interactive_drawing_board.py 自动生成
包含所有绘制的矩形和线段定义
"""

import numpy as np
from base_geometry import MicrochannelGeometry, BoundaryType


class CustomGeometry(MicrochannelGeometry):
    """
    自定义几何类 - 基于用户绘制的图形
    """

    def __init__(self, units='mm'):
        super().__init__(units)
        self.geometry_params = {
            'type': 'custom_from_drawing',
            'source': 'interactive_drawing_board',
            'units': units
        }

    def generate(self):
        """生成几何数据"""

'''

        # 添加矩形定义
        if self.rectangles:
            code += "        # 定义矩形区域\n"
            code += "        self.rectangles = [\n"
            for i, (x1, y1, x2, y2) in enumerate(self.rectangles):
                code += f"            ({x1:.6f}, {y1:.6f}, {x2:.6f}, {y2:.6f}),  # 矩形{i+1}\n"
            code += "        ]\n\n"

        # 添加线段定义
        if self.lines:
            code += "        # 定义线段\n"
            code += "        self.lines = [\n"
            for i, (x1, y1, x2, y2) in enumerate(self.lines):
                length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                code += f"            ({x1:.6f}, {y1:.6f}, {x2:.6f}, {y2:.6f}),  # 线段{i+1} L={length:.2f}mm, θ={angle:.1f}°\n"
            code += "        ]\n\n"

        # 继续生成代码
        code += '''        # 从绘制的线段构建多边形边界
        # 将所有线段的端点提取出来，构成外边界
        points = []

'''
        # 添加所有线段的端点
        if self.lines:
            code += "        # 按顺序添加线段端点\n"
            for i, (x1, y1, x2, y2) in enumerate(self.lines):
                code += f"        points.append(np.array([{x1:.6f}, {y1:.6f}]))  # 线段{i+1}起点\n"
                code += f"        points.append(np.array([{x2:.6f}, {y2:.6f}]))  # 线段{i+1}终点\n"

        code += '''
        # 定义外边界多边形
        outer_boundary = np.array(points)

        # 定义边界段
        # 注意：这里简化处理，将所有线段都作为壁面
        # 你需要根据实际情况指定入口和出口

'''

        # 添加线段作为边界
        if self.lines:
            code += "        # 添加所有线段作为边界（默认为壁面）\n"
            code += "        # 请根据实际情况修改边界类型\n"
            for i, (x1, y1, x2, y2) in enumerate(self.lines):
                if i == 0:
                    btype = "BoundaryType.INLET"
                    label = "INLET"
                elif i == len(self.lines) - 1:
                    btype = "BoundaryType.OUTLET_1"
                    label = "OUTLET1"
                else:
                    btype = "BoundaryType.WALL"
                    label = f"WALL_{i}"
                code += f"        self.add_boundary(np.array([{x1:.6f}, {y1:.6f}]), np.array([{x2:.6f}, {y2:.6f}]), {btype}, \"{label}\")  # 线段{i+1}\n"

        code += '''
        return {
            'polygons': [
                {
                    'label': 'custom_geometry_domain',
                    'points': outer_boundary.tolist(),
                    'type': 'outer_boundary'
                }
            ],
            'params': self.geometry_params
        }


def create_custom_geometry():
    """创建自定义几何对象"""
    return CustomGeometry()


if __name__ == '__main__':
    print("=" * 60)
    print("自定义几何模型测试")
    print("=" * 60)

    geom = create_custom_geometry()
    data = geom.generate()

    print(f"\\n几何参数:")
    for key, value in geom.geometry_params.items():
        print(f"  {key}: {value}")

    geom.print_boundary_summary()

    print("\\n" + "=" * 60)
'''

        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)

        print("\n# 生成的几何模型代码预览:")
        print("-" * 60)
        # 显示前30行
        lines = code.split('\n')
        for line in lines[:40]:
            print(line)
        if len(lines) > 40:
            print(f"\n... (省略 {len(lines) - 40} 行)")
        print("-" * 60)

    def show(self):
        """显示绘图板"""
        plt.show()


def main():
    """主函数"""
    print("\n" + "="*60)
    print("微流控几何交互式绘图板")
    print("="*60)
    print("\n正在启动绘图板...")

    # 创建绘图板
    board = DrawingBoard(
        figsize=(14, 10),
        xlim=(0, 15),   # X轴范围 0-15mm
        ylim=(-8, 8)    # Y轴范围 -8到8mm
    )

    # 显示绘图板
    board.show()


if __name__ == '__main__':
    main()
