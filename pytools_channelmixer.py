# ==== texture_channel_mixer/main.py ====
import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas
from PIL import Image, ImageTk
import numpy as np
from typing import Optional, Tuple, List
import os


class DragPreviewCanvas(Canvas):
    """拖拽预览画布（使用Canvas实现更好的兼容性）"""

    def __init__(self, parent):
        super().__init__(
            parent,
            width=80,
            height=90,
            highlightthickness=0,
            bg='SystemButtonFace'
        )
        self.preview_image = None
        self.image_id = None
        self.text_id = None

        # 设置透明度（在支持的平台上）
        try:
            self.attributes('-alpha', 0.9)
        except:
            pass

    def set_preview(self, channel_image: Image.Image, channel_name: str):
        """设置预览内容"""
        self.delete("all")

        # 绘制背景
        self.create_rectangle(0, 0, 80, 90, fill='#e0e0e0', outline='#808080', width=2)

        # 显示预览图
        preview_size = 60
        img_preview = channel_image.copy()
        img_preview.thumbnail((preview_size, preview_size), Image.Resampling.LANCZOS)

        # 转换为可显示的图像
        if img_preview.mode == 'L':
            display_img = img_preview.convert('RGB')
        else:
            display_img = img_preview

        self.preview_image = ImageTk.PhotoImage(display_img)
        self.image_id = self.create_image(40, 35, image=self.preview_image)

        # 显示文字
        self.text_id = self.create_text(
            40, 78,
            text=channel_name,
            font=('Arial', 9, 'bold'),
            fill='#333333'
        )


class ChannelSlot(ctk.CTkFrame):
    """表示一个可拖放的通道槽位"""

    def __init__(self, master, channel_name: str, **kwargs):
        super().__init__(master, **kwargs)
        self.channel_name = channel_name
        self.source_info = None  # (texture_index, channel)
        self.normal_fg_color = ("gray85", "gray25")
        self.hover_fg_color = ("#b3d9ff", "#1a5490")

        self.configure(fg_color=self.normal_fg_color, corner_radius=8)

        # 标签
        self.label = ctk.CTkLabel(
            self,
            text=f"{channel_name} 通道",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.label.pack(pady=(10, 5))

        # 内容区域
        self.content_label = ctk.CTkLabel(
            self,
            text="拖拽通道到此处",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.content_label.pack(pady=20, padx=20)

        # 清除按钮
        self.clear_btn = ctk.CTkButton(
            self,
            text="清除",
            width=60,
            height=25,
            command=self.clear_slot,
            fg_color="transparent",
            border_width=1
        )
        self.clear_btn.pack(pady=(0, 10))
        self.clear_btn.pack_forget()

    def set_channel(self, texture_index: int, channel: str, texture_name: str):
        """设置通道源"""
        self.source_info = (texture_index, channel)
        self.content_label.configure(
            text=f"纹理 {texture_index + 1}\n{channel} 通道",
            text_color=("gray10", "gray90")
        )
        self.clear_btn.pack(pady=(0, 10))

    def clear_slot(self):
        """清空槽位"""
        self.source_info = None
        self.content_label.configure(
            text="拖拽通道到此处",
            text_color="gray"
        )
        self.clear_btn.pack_forget()

    def highlight(self, enable: bool):
        """高亮显示槽位（拖拽悬停时）"""
        if enable:
            self.configure(
                border_width=3,
                border_color=("#0066cc", "#66b3ff"),
                fg_color=self.hover_fg_color
            )
        else:
            self.configure(
                border_width=0,
                fg_color=self.normal_fg_color
            )


class DraggableChannelButton(ctk.CTkButton):
    """可拖拽的通道按钮"""

    def __init__(self, master, channel: str, texture_index: int,
                 get_channel_preview, on_drag_start, on_drag_move, on_drag_end, **kwargs):
        super().__init__(master, **kwargs)
        self.channel = channel
        self.texture_index = texture_index
        self.get_channel_preview = get_channel_preview
        self.on_drag_start = on_drag_start
        self.on_drag_move = on_drag_move
        self.on_drag_end = on_drag_end
        self.is_dragging = False

        # 绑定拖拽事件
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.end_drag)

    def start_drag(self, event):
        """开始拖拽"""
        self.is_dragging = True

        # 获取通道预览图
        preview_img = self.get_channel_preview(self.texture_index, self.channel)
        self.on_drag_start(self.texture_index, self.channel, preview_img)

    def on_drag(self, event):
        """拖拽中"""
        if self.is_dragging:
            x = self.winfo_pointerx()
            y = self.winfo_pointery()
            self.on_drag_move(x, y)

    def end_drag(self, event):
        """结束拖拽"""
        if self.is_dragging:
            self.is_dragging = False
            x = self.winfo_pointerx()
            y = self.winfo_pointery()
            self.on_drag_end(self.texture_index, self.channel, x, y)


class TexturePanel(ctk.CTkFrame):
    """纹理贴图面板"""

    def __init__(self, master, index: int, get_channel_preview,
                 on_drag_start, on_drag_move, on_drag_end, **kwargs):
        super().__init__(master, **kwargs)
        self.index = index
        self.get_channel_preview = get_channel_preview
        self.on_drag_start = on_drag_start
        self.on_drag_move = on_drag_move
        self.on_drag_end = on_drag_end
        self.texture_path = None
        self.image_array = None
        self.image_channels = []
        self.preview_ctk_image = None

        self.configure(fg_color=("gray90", "gray20"), corner_radius=10)

        # 设置最小高度
        self.grid_propagate(True)

        # 标题
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            title_frame,
            text=f"纹理 {index + 1}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")

        # 清除按钮
        self.clear_btn = ctk.CTkButton(
            title_frame,
            text="清除",
            width=60,
            height=28,
            command=self.clear_texture,
            fg_color="transparent",
            border_width=1
        )
        self.clear_btn.pack(side="right")
        self.clear_btn.pack_forget()

        # 拖放区域容器
        self.drop_container = ctk.CTkFrame(self, fg_color="transparent")
        self.drop_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 预览区域
        self.preview_label = ctk.CTkLabel(
            self.drop_container,
            text="点击选择图片文件",
            width=150,
            height=150,
            fg_color=("gray80", "gray30"),
            corner_radius=8,
            cursor="hand2"
        )
        self.preview_label.pack()
        self.preview_label.bind("<Button-1>", lambda e: self.load_texture())

        # 文件名和信息
        self.filename_label = ctk.CTkLabel(
            self.drop_container,
            text="",
            font=ctk.CTkFont(size=9),
            text_color="gray",
            wraplength=140
        )
        self.filename_label.pack(pady=(5, 0))

        # 通道按钮框架
        self.channel_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.channel_frame.pack(fill="x", padx=10, pady=(5, 10))
        self.channel_frame.pack_propagate(False)

        self.channel_buttons = {}

    def create_channel_buttons(self, available_channels: List[str]):
        """根据实际通道创建按钮"""
        # 清除旧按钮
        for btn in self.channel_buttons.values():
            btn.destroy()
        self.channel_buttons.clear()

        # 创建新按钮
        for ch in available_channels:
            btn = DraggableChannelButton(
                self.channel_frame,
                channel=ch,
                texture_index=self.index,
                get_channel_preview=self.get_channel_preview,
                on_drag_start=self.on_drag_start,
                on_drag_move=self.on_drag_move,
                on_drag_end=self.on_drag_end,
                text=ch,
                width=45,
                height=28,
                state="normal",
                fg_color=("gray70", "gray40"),
                hover_color=("gray60", "gray50"),
                cursor="hand2"
            )
            btn.pack(side="left", padx=2)
            self.channel_buttons[ch] = btn

    def load_texture(self):
        """通过文件对话框加载纹理"""
        file_path = filedialog.askopenfilename(
            title="选择纹理文件",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.tga *.bmp *.tiff *.tif"),
                ("所有文件", "*.*")
            ]
        )

        if file_path:
            self.load_texture_from_path(file_path)

    def load_texture_from_path(self, file_path: str):
        """从指定路径加载纹理"""
        try:
            # 加载图片
            img = Image.open(file_path)
            self.texture_path = file_path

            # 转换为numpy数组并识别通道
            self.image_channels = []

            if img.mode == 'L':
                self.image_array = np.array(img)
                self.image_channels = ['Gray']
            elif img.mode == 'LA':
                self.image_array = np.array(img)
                self.image_channels = ['Gray', 'A']
            elif img.mode == 'RGB':
                self.image_array = np.array(img)
                self.image_channels = ['R', 'G', 'B']
            elif img.mode == 'RGBA':
                self.image_array = np.array(img)
                self.image_channels = ['R', 'G', 'B', 'A']
            elif img.mode in ('I', 'F'):
                img = img.convert('L')
                self.image_array = np.array(img)
                self.image_channels = ['Gray']
            else:
                img = img.convert('RGBA')
                self.image_array = np.array(img)
                self.image_channels = ['R', 'G', 'B', 'A']

            # 对于RGB或RGBA图像，添加灰度选项
            if 'R' in self.image_channels:
                self.image_channels.append('灰度')

            # 更新预览
            self.update_preview(img)

            # 更新文件名和信息
            filename = os.path.basename(file_path)
            if len(filename) > 22:
                filename = filename[:19] + "..."

            # 显示图像信息
            height, width = self.image_array.shape[:2]
            info_text = f"{filename}\n{width}×{height} | {img.mode}"
            self.filename_label.configure(text=info_text)

            # 显示清除按钮
            self.clear_btn.pack(side="right")

            # 创建对应的通道按钮
            self.create_channel_buttons(self.image_channels)

        except Exception as e:
            messagebox.showerror("错误", f"加载纹理失败：{str(e)}")

    def update_preview(self, img: Image.Image):
        """更新预览图（使用CTkImage）"""
        # 调整预览大小
        img_thumb = img.copy()
        img_thumb.thumbnail((140, 140), Image.Resampling.LANCZOS)

        # 创建背景
        bg = Image.new('RGB', (140, 140), (200, 200, 200))
        if img_thumb.mode in ('RGBA', 'LA'):
            # 创建棋盘格背景
            checker_size = 10
            for y in range(0, 140, checker_size):
                for x in range(0, 140, checker_size):
                    color = (220, 220, 220) if (x // checker_size + y // checker_size) % 2 == 0 else (180, 180, 180)
                    for py in range(y, min(y + checker_size, 140)):
                        for px in range(x, min(x + checker_size, 140)):
                            bg.putpixel((px, py), color)
            bg.paste(img_thumb, (0, 0), img_thumb)
        else:
            if img_thumb.mode != 'RGB':
                img_thumb = img_thumb.convert('RGB')
            bg.paste(img_thumb, (0, 0))

        # 使用CTkImage
        self.preview_ctk_image = ctk.CTkImage(
            light_image=bg,
            dark_image=bg,
            size=(140, 140)
        )

        self.preview_label.configure(image=self.preview_ctk_image, text="")

    def clear_texture(self):
        """清除纹理"""
        self.texture_path = None
        self.image_array = None
        self.image_channels = []
        self.preview_ctk_image = None

        # 重置预览
        self.preview_label.configure(
            image="",
            text="点击选择图片文件"
        )

        # 清除文件名
        self.filename_label.configure(text="")

        # 隐藏清除按钮
        self.clear_btn.pack_forget()

        # 清除通道按钮
        for btn in self.channel_buttons.values():
            btn.destroy()
        self.channel_buttons.clear()


class TextureChannelMixer(ctk.CTk):
    """纹理通道混合器主窗口"""

    def __init__(self):
        super().__init__()

        self.title("纹理通道混合器")
        self.geometry("1200x750")
        self.minsize(1100, 700)

        # 设置主题
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.selected_source = None
        self.output_slots = {}
        self.current_hover_slot = None
        self.drag_preview_canvas = None

        self.create_ui()

    def create_ui(self):
        """创建用户界面"""
        # 主容器
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 左侧：纹理输入区域（固定2x2网格，添加背景）
        left_frame = ctk.CTkFrame(
            main_frame,
            fg_color=("gray75", "gray30"),
            corner_radius=10
        )
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 1))

        # 左侧内容容器
        left_content = ctk.CTkFrame(left_frame, fg_color="transparent")
        left_content.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            left_content,
            text="输入纹理",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(0, 10))

        # 纹理面板容器（固定2x2网格布局）
        textures_container = ctk.CTkFrame(left_content, fg_color="transparent")
        textures_container.pack(fill="both", expand=True)

        # 配置网格权重
        textures_container.grid_rowconfigure(0, weight=1, minsize=280)
        textures_container.grid_rowconfigure(1, weight=1, minsize=280)
        textures_container.grid_columnconfigure(0, weight=1, minsize=260)
        textures_container.grid_columnconfigure(1, weight=1, minsize=260)

        self.texture_panels = []
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]

        for i, (row, col) in enumerate(positions):
            panel = TexturePanel(
                textures_container,
                index=i,
                get_channel_preview=self.get_channel_preview,
                on_drag_start=self.on_drag_start,
                on_drag_move=self.on_drag_move,
                on_drag_end=self.on_drag_end
            )
            panel.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            self.texture_panels.append(panel)

        # 右侧：输出通道区域（固定宽度，添加背景色）
        right_frame = ctk.CTkFrame(
            main_frame,
            fg_color=("gray75", "gray30"),
            corner_radius=10,
            width=350
        )
        right_frame.pack(side="right", fill="y", padx=(1, 0))
        right_frame.pack_propagate(False)

        # 右侧内容容器
        right_content = ctk.CTkFrame(right_frame, fg_color="transparent")
        right_content.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            right_content,
            text="输出通道映射",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(0, 10))

        # 输出槽位容器
        slots_container = ctk.CTkFrame(right_content, fg_color="transparent")
        slots_container.pack(fill="both", expand=True, pady=(0, 5))

        channels = ["R", "G", "B", "A"]
        for i, ch in enumerate(channels):
            slot = ChannelSlot(slots_container, ch)
            slot.pack(fill="both", expand=True, pady=3)
            self.output_slots[ch] = slot

        # 说明文本
        info_frame = ctk.CTkFrame(right_content, fg_color=("gray85", "gray25"), corner_radius=8)
        info_frame.pack(pady=5, padx=0, fill="x")

        info_text = "操作说明：\n1. 点击左侧预览区域选择图片\n2. 按住通道按钮拖拽到右侧槽位\n3. 松开鼠标完成通道映射\n4. 点击下方按钮导出合成纹理"
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=10),
            justify="left"
        ).pack(pady=8, padx=10)

        # 输出按钮
        self.output_btn = ctk.CTkButton(
            right_content,
            text="生成输出",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.generate_output
        )
        self.output_btn.pack(pady=5, padx=0, fill="x")

        # 创建拖拽预览画布（隐藏状态）
        self.drag_preview_canvas = DragPreviewCanvas(self)

    def get_channel_preview(self, texture_index: int, channel: str) -> Optional[Image.Image]:
        """获取通道预览图"""
        panel = self.texture_panels[texture_index]
        if panel.image_array is None:
            return None

        channel_data = self.extract_channel(texture_index, channel)
        if channel_data is None:
            return None

        return Image.fromarray(channel_data, mode='L')

    def on_drag_start(self, texture_index: int, channel: str, preview_img: Optional[Image.Image]):
        """开始拖拽通道"""
        self.selected_source = (texture_index, channel)

        # 显示拖拽预览
        if preview_img:
            self.drag_preview_canvas.set_preview(preview_img, f"纹理{texture_index + 1}-{channel}")
            self.drag_preview_canvas.place(x=-100, y=-100)

    def on_drag_move(self, x: int, y: int):
        """拖拽移动中"""
        # 更新预览画布位置
        if self.drag_preview_canvas:
            window_x = x - self.winfo_rootx() + 15
            window_y = y - self.winfo_rooty() + 15
            self.drag_preview_canvas.place(x=window_x, y=window_y)

        # 检查鼠标位置
        target_slot = None
        for ch, slot in self.output_slots.items():
            slot_x = slot.winfo_rootx()
            slot_y = slot.winfo_rooty()
            slot_width = slot.winfo_width()
            slot_height = slot.winfo_height()

            if (slot_x <= x <= slot_x + slot_width and
                    slot_y <= y <= slot_y + slot_height):
                target_slot = slot
                break

        # 更新悬停高亮
        if target_slot != self.current_hover_slot:
            if self.current_hover_slot:
                self.current_hover_slot.highlight(False)
            if target_slot:
                target_slot.highlight(True)
            self.current_hover_slot = target_slot

    def on_drag_end(self, texture_index: int, channel: str, x: int, y: int):
        """拖拽结束"""
        # 隐藏预览画布
        if self.drag_preview_canvas:
            self.drag_preview_canvas.place_forget()

        # 取消高亮
        if self.current_hover_slot:
            self.current_hover_slot.highlight(False)

        # 检查释放位置
        target_slot = None
        for ch, slot in self.output_slots.items():
            slot_x = slot.winfo_rootx()
            slot_y = slot.winfo_rooty()
            slot_width = slot.winfo_width()
            slot_height = slot.winfo_height()

            if (slot_x <= x <= slot_x + slot_width and
                    slot_y <= y <= slot_y + slot_height):
                target_slot = slot
                break

        # 完成映射
        if target_slot and self.selected_source:
            texture_idx, ch = self.selected_source
            target_slot.set_channel(texture_idx, ch, f"纹理{texture_idx + 1}")

        self.selected_source = None
        self.current_hover_slot = None

    def extract_channel(self, texture_index: int, channel: str) -> Optional[np.ndarray]:
        """从纹理中提取指定通道"""
        panel = self.texture_panels[texture_index]
        if panel.image_array is None:
            return None

        img_array = panel.image_array

        if channel == "灰度":
            if len(img_array.shape) == 2:
                return img_array
            elif len(img_array.shape) == 3 and img_array.shape[2] >= 3:
                return np.dot(img_array[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)
        elif channel == "Gray":
            if len(img_array.shape) == 2:
                return img_array
            elif len(img_array.shape) == 3:
                return img_array[..., 0]
        else:
            channel_map = {"R": 0, "G": 1, "B": 2, "A": 3}
            if channel in channel_map:
                channel_idx = channel_map[channel]
                if len(img_array.shape) == 3 and channel_idx < img_array.shape[2]:
                    return img_array[..., channel_idx]

        return None

    def generate_output(self):
        """生成输出纹理"""
        assigned_slots = [ch for ch, slot in self.output_slots.items() if slot.source_info is not None]

        if not assigned_slots:
            messagebox.showwarning("警告", "请至少分配一个输出通道")
            return

        # 获取输出尺寸
        output_shape = None
        for panel in self.texture_panels:
            if panel.image_array is not None:
                if len(panel.image_array.shape) == 2:
                    output_shape = panel.image_array.shape
                else:
                    output_shape = panel.image_array.shape[:2]
                break

        if output_shape is None:
            messagebox.showerror("错误", "没有加载任何纹理")
            return

        # 创建输出数组
        output_array = np.zeros((*output_shape, 4), dtype=np.uint8)

        # 填充每个通道
        for i, ch in enumerate(["R", "G", "B", "A"]):
            slot = self.output_slots[ch]
            if slot.source_info is not None:
                texture_idx, source_channel = slot.source_info
                channel_data = self.extract_channel(texture_idx, source_channel)

                if channel_data is not None:
                    if channel_data.shape != output_shape:
                        channel_img = Image.fromarray(channel_data)
                        channel_img = channel_img.resize((output_shape[1], output_shape[0]), Image.Resampling.LANCZOS)
                        channel_data = np.array(channel_img)

                    output_array[..., i] = channel_data
                else:
                    output_array[..., i] = 255
            else:
                output_array[..., i] = 255 if ch == "A" else 0

        # 保存文件
        file_path = filedialog.asksaveasfilename(
            title="保存输出纹理",
            defaultextension=".png",
            filetypes=[
                ("PNG文件", "*.png"),
                ("TGA文件", "*.tga"),
                ("TIFF文件", "*.tiff"),
                ("所有文件", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            output_img = Image.fromarray(output_array, mode='RGBA')
            output_img.save(file_path)
            messagebox.showinfo("成功", f"纹理已保存至：\n{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存纹理失败：{str(e)}")


def main():
    app = TextureChannelMixer()
    app.mainloop()


if __name__ == "__main__":
    main()
