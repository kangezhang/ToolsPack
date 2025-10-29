# ==== hcross_splitter/main.py ====
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
from typing import Optional, Tuple
import os


class FacePreview(ctk.CTkFrame):
    """单个面的预览组件"""

    def __init__(self, master, face_name: str, **kwargs):
        super().__init__(master, **kwargs)
        self.face_name = face_name
        self.image_array = None
        self.preview_ctk_image = None

        self.configure(fg_color=("gray90", "gray20"), corner_radius=10)

        # 标签
        self.label = ctk.CTkLabel(
            self,
            text=face_name,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.label.pack(pady=(10, 5))

        # 预览区域
        self.preview_label = ctk.CTkLabel(
            self,
            text="未加载",
            width=180,
            height=180,
            fg_color=("gray80", "gray30"),
            corner_radius=8
        )
        self.preview_label.pack(padx=10, pady=(5, 10))

        # 尺寸信息
        self.info_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.info_label.pack(pady=(0, 10))

    def set_image(self, image_array: np.ndarray):
        """设置预览图像"""
        self.image_array = image_array

        # 生成预览
        img = Image.fromarray(image_array)
        img_preview = img.copy()
        img_preview.thumbnail((180, 180), Image.Resampling.LANCZOS)

        self.preview_ctk_image = ctk.CTkImage(
            light_image=img_preview,
            dark_image=img_preview,
            size=(img_preview.width, img_preview.height)
        )

        self.preview_label.configure(
            image=self.preview_ctk_image,
            text=""
        )

        # 更新尺寸信息
        h, w = image_array.shape[:2]
        channels = image_array.shape[2] if len(image_array.shape) == 3 else 1
        self.info_label.configure(
            text=f"{w}x{h} | {channels}通道"
        )

    def clear(self):
        """清除预览"""
        self.image_array = None
        self.preview_ctk_image = None
        self.preview_label.configure(image="", text="未加载")
        self.info_label.configure(text="")


class HCrossSplitter(ctk.CTk):
    """HCross贴图分割工具主窗口"""

    def __init__(self):
        super().__init__()

        # 窗口设置
        self.title("HCross 贴图分割工具")
        self.geometry("1400x900")

        # 设置外观
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 数据存储
        self.source_image = None
        self.face_images = {}  # {face_name: numpy_array}
        self.face_previews = {}  # {face_name: FacePreview}

        self._setup_ui()

    def _setup_ui(self):
        """构建用户界面"""
        # 主容器
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # 顶部控制区域
        top_frame = ctk.CTkFrame(main_frame, fg_color=("gray85", "gray25"), corner_radius=10)
        top_frame.pack(fill="x", pady=(0, 10))

        # 标题和按钮容器
        top_content = ctk.CTkFrame(top_frame, fg_color="transparent")
        top_content.pack(fill="x", padx=15, pady=15)

        # 左侧标题
        title_frame = ctk.CTkFrame(top_content, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_frame,
            text="HCross 环境贴图分割工具",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="支持将十字展开格式的环境贴图分割为六个独立的立方体面贴图",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor="w", pady=(5, 0))

        # 右侧按钮组
        button_frame = ctk.CTkFrame(top_content, fg_color="transparent")
        button_frame.pack(side="right")

        self.load_btn = ctk.CTkButton(
            button_frame,
            text="加载 HCross 贴图",
            width=160,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.load_hcross_image
        )
        self.load_btn.pack(side="left", padx=5)

        self.export_btn = ctk.CTkButton(
            button_frame,
            text="导出所有面",
            width=140,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.export_all_faces,
            state="disabled"
        )
        self.export_btn.pack(side="left", padx=5)

        self.clear_btn = ctk.CTkButton(
            button_frame,
            text="清除",
            width=100,
            height=40,
            font=ctk.CTkFont(size=14),
            command=self.clear_all,
            fg_color="transparent",
            border_width=2,
            state="disabled"
        )
        self.clear_btn.pack(side="left", padx=5)

        # 源图预览区域
        source_frame = ctk.CTkFrame(main_frame, fg_color=("gray90", "gray20"), corner_radius=10)
        source_frame.pack(fill="x", pady=(0, 10))

        source_content = ctk.CTkFrame(source_frame, fg_color="transparent")
        source_content.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            source_content,
            text="源 HCross 贴图",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=(0, 15))

        self.source_preview = ctk.CTkLabel(
            source_content,
            text="点击上方按钮加载 HCross 格式贴图",
            width=250,
            height=150,
            fg_color=("gray80", "gray30"),
            corner_radius=8
        )
        self.source_preview.pack(side="left", padx=(0, 15))

        self.source_info_label = ctk.CTkLabel(
            source_content,
            text="",
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        self.source_info_label.pack(side="left", anchor="w")

        # 分割结果区域
        result_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        result_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            result_frame,
            text="分割结果",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(0, 10))

        # 面预览网格容器
        grid_container = ctk.CTkFrame(result_frame, fg_color="transparent")
        grid_container.pack(fill="both", expand=True)

        # 配置网格权重
        for i in range(3):
            grid_container.grid_columnconfigure(i, weight=1, uniform="col")
        for i in range(2):
            grid_container.grid_rowconfigure(i, weight=1, uniform="row")

        # 创建六个面的预览（按照标准立方体贴图顺序）
        face_names = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]
        positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]

        for name, (row, col) in zip(face_names, positions):
            preview = FacePreview(grid_container, name)
            preview.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            self.face_previews[name] = preview

    def load_hcross_image(self):
        """加载HCross格式贴图"""
        file_path = filedialog.askopenfilename(
            title="选择 HCross 格式贴图",
            filetypes=[
                ("图像文件", "*.png *.jpg *.jpeg *.tga *.bmp *.tiff *.exr *.hdr"),
                ("所有文件", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            # 加载图像
            img = Image.open(file_path)
            img_array = np.array(img)

            # 验证HCross格式
            h, w = img_array.shape[:2]

            # HCross格式应该是3:4或4:3的比例
            # 水平十字: 宽度=face_size*4, 高度=face_size*3
            # 垂直十字: 宽度=face_size*3, 高度=face_size*4

            if w == h * 4 // 3:  # 水平十字
                face_size = w // 4
                if h != face_size * 3:
                    messagebox.showerror("格式错误", "图像比例不符合 HCross 格式 (4:3)")
                    return
                layout_type = "horizontal"
            elif h == w * 4 // 3:  # 垂直十字
                face_size = h // 4
                if w != face_size * 3:
                    messagebox.showerror("格式错误", "图像比例不符合 HCross 格式 (3:4)")
                    return
                layout_type = "vertical"
            else:
                messagebox.showerror("格式错误", "图像比例不符合 HCross 格式 (需要 4:3 或 3:4)")
                return

            self.source_image = img_array

            # 更新源图预览
            self._update_source_preview(img, file_path)

            # 分割图像
            self._split_hcross(layout_type, face_size)

            # 启用按钮
            self.export_btn.configure(state="normal")
            self.clear_btn.configure(state="normal")

            messagebox.showinfo("成功", f"HCross 贴图加载成功\n已分割为 6 个独立面")

        except Exception as e:
            messagebox.showerror("错误", f"加载图像失败: {str(e)}")

    def _update_source_preview(self, img: Image.Image, file_path: str):
        """更新源图预览"""
        # 生成预览
        img_preview = img.copy()
        img_preview.thumbnail((250, 150), Image.Resampling.LANCZOS)

        preview_ctk_image = ctk.CTkImage(
            light_image=img_preview,
            dark_image=img_preview,
            size=(img_preview.width, img_preview.height)
        )

        self.source_preview.configure(image=preview_ctk_image, text="")

        # 更新信息
        w, h = img.size
        channels = len(img.getbands())
        mode = img.mode
        file_name = os.path.basename(file_path)

        info_text = f"文件名: {file_name}\n"
        info_text += f"尺寸: {w} x {h}\n"
        info_text += f"模式: {mode} ({channels} 通道)\n"
        info_text += f"格式: {'水平' if w > h else '垂直'} HCross"

        self.source_info_label.configure(text=info_text)

    def _split_hcross(self, layout_type: str, face_size: int):
        """分割HCross格式贴图"""
        img_array = self.source_image

        if layout_type == "horizontal":
            # 水平十字布局:
            #     [+Y]
            # [-X][+Z][+X][-Z]
            #     [-Y]

            faces = {
                "+Y": img_array[0:face_size, face_size:face_size * 2],
                "-X": img_array[face_size:face_size * 2, 0:face_size],
                "+Z": img_array[face_size:face_size * 2, face_size:face_size * 2],
                "+X": img_array[face_size:face_size * 2, face_size * 2:face_size * 3],
                "-Z": img_array[face_size:face_size * 2, face_size * 3:face_size * 4],
                "-Y": img_array[face_size * 2:face_size * 3, face_size:face_size * 2]
            }
        else:  # vertical
            # 垂直十字布局:
            #     [+Y]
            #     [+Z]
            # [-X][+X]
            #     [-Z]
            #     [-Y]

            faces = {
                "+Y": img_array[0:face_size, face_size:face_size * 2],
                "+Z": img_array[face_size:face_size * 2, face_size:face_size * 2],
                "-X": img_array[face_size * 2:face_size * 3, 0:face_size],
                "+X": img_array[face_size * 2:face_size * 3, face_size:face_size * 2],
                "-Z": img_array[face_size * 2:face_size * 3, face_size * 2:face_size * 3],
                "-Y": img_array[face_size * 3:face_size * 4, face_size:face_size * 2]
            }

        self.face_images = faces

        # 更新预览
        for name, face_array in faces.items():
            self.face_previews[name].set_image(face_array)

    def export_all_faces(self):
        """导出所有面"""
        if not self.face_images:
            messagebox.showwarning("警告", "没有可导出的面")
            return

        # 选择输出目录
        output_dir = filedialog.askdirectory(title="选择输出目录")
        if not output_dir:
            return

        # 询问文件格式
        format_window = ctk.CTkToplevel(self)
        format_window.title("选择输出格式")
        format_window.geometry("300x200")
        format_window.transient(self)
        format_window.grab_set()

        ctk.CTkLabel(
            format_window,
            text="选择输出格式",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=20)

        format_var = ctk.StringVar(value="png")

        formats = [
            ("PNG (无损)", "png"),
            ("TGA (无损)", "tga"),
            ("TIFF (无损)", "tiff"),
            ("JPEG (有损)", "jpg")
        ]

        for text, value in formats:
            ctk.CTkRadioButton(
                format_window,
                text=text,
                variable=format_var,
                value=value
            ).pack(pady=5)

        def confirm_export():
            format_window.destroy()
            self._export_faces(output_dir, format_var.get())

        ctk.CTkButton(
            format_window,
            text="确认导出",
            command=confirm_export
        ).pack(pady=20)

    def _export_faces(self, output_dir: str, file_format: str):
        """执行导出操作"""
        try:
            exported_files = []

            for face_name, face_array in self.face_images.items():
                # 文件名格式: face_name.format
                file_name = f"{face_name}.{file_format}"
                file_path = os.path.join(output_dir, file_name)

                # 保存图像
                img = Image.fromarray(face_array)
                img.save(file_path)
                exported_files.append(file_name)

            # 显示成功信息
            file_list = "\n".join(exported_files)
            messagebox.showinfo(
                "导出成功",
                f"已导出 {len(exported_files)} 个文件到:\n{output_dir}\n\n文件列表:\n{file_list}"
            )

        except Exception as e:
            messagebox.showerror("导出错误", f"导出失败: {str(e)}")

    def clear_all(self):
        """清除所有数据"""
        self.source_image = None
        self.face_images = {}

        # 清除源图预览
        self.source_preview.configure(
            image="",
            text="点击上方按钮加载 HCross 格式贴图"
        )
        self.source_info_label.configure(text="")

        # 清除所有面预览
        for preview in self.face_previews.values():
            preview.clear()

        # 禁用按钮
        self.export_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")


def main():
    app = HCrossSplitter()
    app.mainloop()


if __name__ == "__main__":
    main()