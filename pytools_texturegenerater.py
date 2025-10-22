import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
import numpy as np
from PIL import Image, ImageDraw, ImageTk
import random
import math


class TextureGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("纹理贴图生成器")
        self.root.geometry("1200x800")

        # 默认参数
        self.width = 512
        self.height = 512
        self.bg_color = (255, 255, 255)
        self.fg_color = (0, 0, 0)
        self.current_image = None

        self.setup_ui()
        self.generate_texture()

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧控制面板
        control_frame = ttk.Frame(main_frame, width=300)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)

        # 右侧预览区域
        preview_frame = ttk.Frame(main_frame)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # === 控制面板内容 ===

        # 画布尺寸设置
        size_frame = ttk.LabelFrame(control_frame, text="画布尺寸", padding=10)
        size_frame.pack(fill=tk.X, pady=5)

        ttk.Label(size_frame, text="尺寸(像素):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.size_var_canvas = tk.IntVar(value=512)
        size_spinbox = ttk.Spinbox(size_frame, from_=64, to=2048,
                                   textvariable=self.size_var_canvas, width=15)
        size_spinbox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        size_frame.columnconfigure(1, weight=1)

        # 颜色设置
        color_frame = ttk.LabelFrame(control_frame, text="颜色设置", padding=10)
        color_frame.pack(fill=tk.X, pady=5)

        self.bg_color_btn = tk.Button(color_frame, text="背景色",
                                      command=self.choose_bg_color, width=15,
                                      bg='white')
        self.bg_color_btn.pack(pady=2)

        self.fg_color_btn = tk.Button(color_frame, text="前景色",
                                      command=self.choose_fg_color, width=15,
                                      bg='black', fg='white')
        self.fg_color_btn.pack(pady=2)

        # 图案类型选择
        pattern_frame = ttk.LabelFrame(control_frame, text="图案类型", padding=10)
        pattern_frame.pack(fill=tk.X, pady=5)

        self.pattern_var = tk.StringVar(value="横线阵列")
        patterns = ["横线阵列", "竖线阵列", "圆形阵列", "矩形阵列",
                    "随机圆点", "棋盘格", "波浪纹", "六边形",
                    "三角形阵列", "星形阵列", "噪声纹理", "渐变"]

        for pattern in patterns:
            ttk.Radiobutton(pattern_frame, text=pattern, variable=self.pattern_var,
                            value=pattern).pack(anchor=tk.W)

        # 参数设置
        param_frame = ttk.LabelFrame(control_frame, text="参数设置", padding=10)
        param_frame.pack(fill=tk.X, pady=5)

        # 密度/间距
        ttk.Label(param_frame, text="密度/间距:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.density_var = tk.IntVar(value=20)
        density_entry = ttk.Entry(param_frame, textvariable=self.density_var, width=8)
        density_entry.grid(row=0, column=1, padx=5, pady=5)
        density_scale = ttk.Scale(param_frame, from_=5, to=100, variable=self.density_var,
                                  orient=tk.HORIZONTAL)
        density_scale.grid(row=0, column=2, sticky=tk.EW, padx=5, pady=5)

        # 大小/粗细
        ttk.Label(param_frame, text="大小/粗细:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.size_var = tk.IntVar(value=5)
        size_entry = ttk.Entry(param_frame, textvariable=self.size_var, width=8)
        size_entry.grid(row=1, column=1, padx=5, pady=5)
        size_scale = ttk.Scale(param_frame, from_=1, to=50, variable=self.size_var,
                               orient=tk.HORIZONTAL)
        size_scale.grid(row=1, column=2, sticky=tk.EW, padx=5, pady=5)

        # 随机度
        ttk.Label(param_frame, text="随机度(%):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.random_var = tk.IntVar(value=0)
        random_entry = ttk.Entry(param_frame, textvariable=self.random_var, width=8)
        random_entry.grid(row=2, column=1, padx=5, pady=5)
        random_scale = ttk.Scale(param_frame, from_=0, to=100, variable=self.random_var,
                                 orient=tk.HORIZONTAL)
        random_scale.grid(row=2, column=2, sticky=tk.EW, padx=5, pady=5)

        # 旋转角度
        ttk.Label(param_frame, text="旋转角度(°):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.rotation_var = tk.IntVar(value=0)
        rotation_entry = ttk.Entry(param_frame, textvariable=self.rotation_var, width=8)
        rotation_entry.grid(row=3, column=1, padx=5, pady=5)
        rotation_scale = ttk.Scale(param_frame, from_=0, to=360, variable=self.rotation_var,
                                   orient=tk.HORIZONTAL)
        rotation_scale.grid(row=3, column=2, sticky=tk.EW, padx=5, pady=5)

        param_frame.columnconfigure(2, weight=1)

        # 按钮区域
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="生成纹理",
                   command=self.generate_texture).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="保存图片",
                   command=self.save_image).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="随机生成",
                   command=self.random_generate).pack(fill=tk.X, pady=2)

        # === 预览区域 ===
        preview_label = ttk.Label(preview_frame, text="纹理预览", font=('Arial', 12, 'bold'))
        preview_label.pack(pady=5)

        # 画布
        self.canvas = tk.Canvas(preview_frame, bg='gray', width=600, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def choose_bg_color(self):
        color = colorchooser.askcolor(title="选择背景色", initialcolor=self.bg_color)
        if color[0]:
            self.bg_color = tuple(int(c) for c in color[0])
            self.bg_color_btn.config(bg=color[1])

    def choose_fg_color(self):
        color = colorchooser.askcolor(title="选择前景色", initialcolor=self.fg_color)
        if color[0]:
            self.fg_color = tuple(int(c) for c in color[0])
            self.fg_color_btn.config(bg=color[1])
            # 根据颜色亮度调整文字颜色
            brightness = sum(self.fg_color) / 3
            text_color = 'white' if brightness < 128 else 'black'
            self.fg_color_btn.config(fg=text_color)

    def generate_texture(self):
        self.width = self.size_var_canvas.get()
        self.height = self.size_var_canvas.get()
        pattern = self.pattern_var.get()

        # 创建图像
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)

        density = self.density_var.get()
        size = self.size_var.get()
        randomness = self.random_var.get() / 100.0
        rotation = self.rotation_var.get()

        # 根据选择的图案生成纹理
        if pattern == "横线阵列":
            self.draw_horizontal_lines(draw, density, size, randomness)
        elif pattern == "竖线阵列":
            self.draw_vertical_lines(draw, density, size, randomness)
        elif pattern == "圆形阵列":
            self.draw_circle_array(draw, density, size, randomness)
        elif pattern == "矩形阵列":
            self.draw_rectangle_array(draw, density, size, randomness)
        elif pattern == "随机圆点":
            self.draw_random_dots(draw, density, size)
        elif pattern == "棋盘格":
            self.draw_checkerboard(draw, density)
        elif pattern == "波浪纹":
            self.draw_waves(draw, density, size)
        elif pattern == "六边形":
            self.draw_hexagons(draw, density, size)
        elif pattern == "三角形阵列":
            self.draw_triangles(draw, density, size, randomness)
        elif pattern == "星形阵列":
            self.draw_stars(draw, density, size, randomness)
        elif pattern == "噪声纹理":
            img = self.draw_noise(randomness)
        elif pattern == "渐变":
            img = self.draw_gradient(rotation)

        self.current_image = img
        self.display_image(img)

    def draw_horizontal_lines(self, draw, density, size, randomness):
        spacing = max(5, density)
        y = 0
        while y < self.height:
            offset = int(random.uniform(-spacing * randomness, spacing * randomness))
            actual_y = y + offset
            thickness = max(1, size + int(random.uniform(-size * randomness, size * randomness)))
            draw.line([(0, actual_y), (self.width, actual_y)],
                      fill=self.fg_color, width=thickness)
            y += spacing

    def draw_vertical_lines(self, draw, density, size, randomness):
        spacing = max(5, density)
        x = 0
        while x < self.width:
            offset = int(random.uniform(-spacing * randomness, spacing * randomness))
            actual_x = x + offset
            thickness = max(1, size + int(random.uniform(-size * randomness, size * randomness)))
            draw.line([(actual_x, 0), (actual_x, self.height)],
                      fill=self.fg_color, width=thickness)
            x += spacing

    def draw_circle_array(self, draw, density, size, randomness):
        spacing = max(10, density)
        radius = max(1, size)

        for y in range(0, self.height, spacing):
            for x in range(0, self.width, spacing):
                offset_x = int(random.uniform(-spacing * randomness, spacing * randomness))
                offset_y = int(random.uniform(-spacing * randomness, spacing * randomness))
                actual_x = x + offset_x
                actual_y = y + offset_y
                actual_radius = max(1, radius + int(random.uniform(-radius * randomness,
                                                                   radius * randomness)))

                draw.ellipse([actual_x - actual_radius, actual_y - actual_radius,
                              actual_x + actual_radius, actual_y + actual_radius],
                             fill=self.fg_color)

    def draw_rectangle_array(self, draw, density, size, randomness):
        spacing = max(10, density)
        rect_size = max(1, size)

        for y in range(0, self.height, spacing):
            for x in range(0, self.width, spacing):
                offset_x = int(random.uniform(-spacing * randomness, spacing * randomness))
                offset_y = int(random.uniform(-spacing * randomness, spacing * randomness))
                actual_x = x + offset_x
                actual_y = y + offset_y
                actual_size = max(1, rect_size + int(random.uniform(-rect_size * randomness,
                                                                    rect_size * randomness)))

                draw.rectangle([actual_x - actual_size, actual_y - actual_size,
                                actual_x + actual_size, actual_y + actual_size],
                               fill=self.fg_color)

    def draw_random_dots(self, draw, density, size):
        num_dots = int((self.width * self.height) / (density * density) * 10)
        radius = max(1, size)

        for _ in range(num_dots):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            r = random.randint(1, radius)
            draw.ellipse([x - r, y - r, x + r, y + r], fill=self.fg_color)

    def draw_checkerboard(self, draw, density):
        square_size = max(5, density)

        for y in range(0, self.height, square_size):
            for x in range(0, self.width, square_size):
                if (x // square_size + y // square_size) % 2 == 0:
                    draw.rectangle([x, y, x + square_size, y + square_size],
                                   fill=self.fg_color)

    def draw_waves(self, draw, density, size):
        wavelength = max(10, density)
        amplitude = max(1, size)

        for y in range(self.height):
            x_offset = int(amplitude * math.sin(2 * math.pi * y / wavelength))
            for x in range(0, self.width, 2):
                if 0 <= x + x_offset < self.width:
                    draw.point((x + x_offset, y), fill=self.fg_color)

    def draw_hexagons(self, draw, density, size):
        spacing = max(15, density)
        hex_size = max(5, size)

        for row in range(0, self.height, int(spacing * 1.5)):
            for col in range(0, self.width, spacing):
                x = col + (spacing // 2 if (row // int(spacing * 1.5)) % 2 else 0)
                y = row
                self.draw_hexagon(draw, x, y, hex_size)

    def draw_hexagon(self, draw, x, y, size):
        points = []
        for i in range(6):
            angle = math.pi / 3 * i
            px = x + size * math.cos(angle)
            py = y + size * math.sin(angle)
            points.append((px, py))
        draw.polygon(points, outline=self.fg_color, fill=None)

    def draw_triangles(self, draw, density, size, randomness):
        spacing = max(15, density)
        tri_size = max(5, size)

        for y in range(0, self.height, spacing):
            for x in range(0, self.width, spacing):
                offset_x = int(random.uniform(-spacing * randomness, spacing * randomness))
                offset_y = int(random.uniform(-spacing * randomness, spacing * randomness))
                cx = x + offset_x
                cy = y + offset_y

                points = [
                    (cx, cy - tri_size),
                    (cx - tri_size, cy + tri_size),
                    (cx + tri_size, cy + tri_size)
                ]
                draw.polygon(points, fill=self.fg_color)

    def draw_stars(self, draw, density, size, randomness):
        spacing = max(20, density)
        star_size = max(5, size)

        for y in range(0, self.height, spacing):
            for x in range(0, self.width, spacing):
                offset_x = int(random.uniform(-spacing * randomness, spacing * randomness))
                offset_y = int(random.uniform(-spacing * randomness, spacing * randomness))
                cx = x + offset_x
                cy = y + offset_y
                self.draw_star(draw, cx, cy, star_size)

    def draw_star(self, draw, x, y, size):
        points = []
        for i in range(10):
            angle = math.pi / 5 * i - math.pi / 2
            radius = size if i % 2 == 0 else size / 2
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append((px, py))
        draw.polygon(points, fill=self.fg_color)

    def draw_noise(self, intensity):
        arr = np.random.rand(self.height, self.width, 3) * 255 * intensity
        base = np.array(self.bg_color)
        arr = base + (arr - 128) * intensity
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(arr, 'RGB')

    def draw_gradient(self, angle):
        arr = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        angle_rad = math.radians(angle)
        for y in range(self.height):
            for x in range(self.width):
                # 计算梯度值
                t = (x * math.cos(angle_rad) + y * math.sin(angle_rad)) / \
                    (self.width * abs(math.cos(angle_rad)) + self.height * abs(math.sin(angle_rad)))
                t = max(0, min(1, t))

                # 插值颜色
                color = tuple(int(self.bg_color[i] * (1 - t) + self.fg_color[i] * t)
                              for i in range(3))
                arr[y, x] = color

        return Image.fromarray(arr, 'RGB')

    def display_image(self, img):
        # 缩放图像以适应画布
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 600
            canvas_height = 600

        img_ratio = img.width / img.height
        canvas_ratio = canvas_width / canvas_height

        if img_ratio > canvas_ratio:
            new_width = canvas_width
            new_height = int(canvas_width / img_ratio)
        else:
            new_height = canvas_height
            new_width = int(canvas_height * img_ratio)

        display_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(display_img)

        self.canvas.delete("all")
        self.canvas.create_image(canvas_width // 2, canvas_height // 2,
                                 image=self.photo, anchor=tk.CENTER)

    def save_image(self):
        if self.current_image is None:
            messagebox.showwarning("警告", "没有可保存的图像!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"),
                       ("All files", "*.*")]
        )

        if filename:
            self.current_image.save(filename)
            messagebox.showinfo("成功", f"图像已保存到: {filename}")

    def random_generate(self):
        # 随机选择参数
        patterns = ["横线阵列", "竖线阵列", "圆形阵列", "矩形阵列",
                    "随机圆点", "棋盘格", "波浪纹", "六边形",
                    "三角形阵列", "星形阵列", "噪声纹理", "渐变"]
        self.pattern_var.set(random.choice(patterns))

        self.density_var.set(random.randint(10, 80))
        self.size_var.set(random.randint(2, 30))
        self.random_var.set(random.randint(0, 80))
        self.rotation_var.set(random.randint(0, 360))

        # 随机颜色
        self.bg_color = (random.randint(0, 255), random.randint(0, 255),
                         random.randint(0, 255))
        self.fg_color = (random.randint(0, 255), random.randint(0, 255),
                         random.randint(0, 255))

        self.bg_color_btn.config(bg='#%02x%02x%02x' % self.bg_color)
        self.fg_color_btn.config(bg='#%02x%02x%02x' % self.fg_color)

        brightness = sum(self.fg_color) / 3
        text_color = 'white' if brightness < 128 else 'black'
        self.fg_color_btn.config(fg=text_color)

        self.generate_texture()


if __name__ == "__main__":
    root = tk.Tk()
    app = TextureGenerator(root)
    root.mainloop()