#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目脚手架生成器 - 赛博朋克终端风格
支持 Windows / macOS 跨平台
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import platform
import re
import json
from pathlib import Path


# ==================== 配色主题 ====================
class CyberTheme:
    BG = '#1e1e1e'
    BG_LIGHT = '#2d2d2d'
    BG_DARK = '#151515'
    BUTTON_BG = '#252525'

    FG = '#00ff41'
    FG_DIM = '#00aa2e'

    ACCENT = '#00d4aa'
    SUCCESS = '#00ff41'
    ERROR = '#ff0055'
    WARNING = '#ffaa00'
    BORDER = '#333333'


# ==================== 元数据管理器 ====================
class MetadataManager:
    """管理项目结构注释的元数据"""
    META_FILE = '.scaffold_meta.json'

    @staticmethod
    def load_metadata(project_root):
        """加载元数据文件"""
        meta_path = Path(project_root) / MetadataManager.META_FILE
        if meta_path.exists():
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    @staticmethod
    def save_metadata(project_root, metadata):
        """保存元数据文件"""
        meta_path = Path(project_root) / MetadataManager.META_FILE
        try:
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save metadata: {e}")
            return False

    @staticmethod
    def merge_metadata(existing, new_data):
        """增量合并元数据"""
        result = existing.copy()
        for path, comment in new_data.items():
            if comment:  # 只更新有注释的项
                result[path] = comment
        return result


# ==================== ASCII LOGO ====================
ASCII_LOGO = """
╔═══════════════════════════════════════════════════╗
║                                                   ║
║   ██████╗ ██████╗  ██████╗      ██╗███████╗ ██████╗████████╗
║   ██╔══██╗██╔══██╗██╔═══██╗     ██║██╔════╝██╔════╝╚══██╔══╝
║   ██████╔╝██████╔╝██║   ██║     ██║█████╗  ██║        ██║   
║   ██╔═══╝ ██╔══██╗██║   ██║██   ██║██╔══╝  ██║        ██║   
║   ██║     ██║  ██║╚██████╔╝╚█████╔╝███████╗╚██████╗   ██║   
║   ╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚════╝ ╚══════╝ ╚═════╝   ╚═╝   
║                                                   ║
║   SCAFFOLDER v2.0                                ║
║   [ SYSTEM READY ]                               ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
"""


# ==================== 主应用 ====================
class ScaffolderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("[ PROJECT SCAFFOLDER ]")
        self.root.configure(bg=CyberTheme.BG)
        self.root.geometry("1000x800")  # 加宽加高，确保所有内容可见

        # 设置最小窗口大小
        self.root.minsize(900, 700)

        # 默认值
        self.base_path = tk.StringVar(value=str(Path.home() / "Desktop"))
        self.mode = tk.StringVar(value="generate")  # "generate" 或 "scan"

        # 操作历史记录
        self.operation_history = []  # 存储操作记录

        # 默认项目结构 - 带注释示例
        self.default_structure = """my_project/
├── main.py                  # 程序入口
├── config.py                # 配置管理
├── README.md                # 项目说明
├── core/                    # 核心框架
│   ├── __init__.py          # 包初始化
│   ├── app.py               # 应用主类
│   └── registry.py          # 注册表操作封装
├── ui/                      # UI 框架
│   ├── __init__.py
│   ├── cyber_theme.py       # 主题配色常量
│   └── windows/             # 功能窗口
│       ├── __init__.py
│       └── main_window.py   # 主窗口
├── features/                # 功能插件
│   ├── __init__.py
│   ├── base.py              # 插件基类
│   └── plugin_example/      # 示例插件
│       ├── __init__.py
│       └── feature.py       # 功能实现
└── utils/                   # 工具函数
    ├── __init__.py
    └── helpers.py           # 辅助函数"""

        self.structure_text = None

        self.setup_theme()
        self.create_widgets()

        # 初始化模式显示
        self.on_mode_change()

    def setup_theme(self):
        """配置 ttk 主题样式"""
        style = ttk.Style()
        style.theme_use('clam')

        # Frame
        style.configure('Cyber.TFrame', background=CyberTheme.BG)

        # LabelFrame
        style.configure('Cyber.TLabelframe',
                        background=CyberTheme.BG_LIGHT,
                        foreground=CyberTheme.FG,
                        bordercolor=CyberTheme.BORDER,
                        relief='flat',
                        borderwidth=1)
        style.configure('Cyber.TLabelframe.Label',
                        background=CyberTheme.BG_LIGHT,
                        foreground=CyberTheme.FG,
                        font=('Courier New', 10, 'bold'))

        # Button - 普通按钮
        style.configure('Cyber.TButton',
                        background=CyberTheme.BUTTON_BG,
                        foreground=CyberTheme.FG,
                        borderwidth=0,
                        relief='flat',
                        font=('Courier New', 9, 'bold'))
        style.map('Cyber.TButton',
                  background=[('active', CyberTheme.BG_LIGHT)])

        # Button - 主按钮
        style.configure('Accent.TButton',
                        background=CyberTheme.ACCENT,
                        foreground=CyberTheme.BG,
                        borderwidth=0,
                        relief='flat',
                        font=('Courier New', 9, 'bold'))
        style.map('Accent.TButton',
                  background=[('active', '#00ffcc')])

        # Label
        style.configure('Cyber.TLabel',
                        background=CyberTheme.BG_LIGHT,
                        foreground=CyberTheme.FG,
                        font=('Courier New', 9))

    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_container = ttk.Frame(self.root, style='Cyber.TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ========== ASCII LOGO ==========
        logo_frame = tk.Frame(main_container, bg=CyberTheme.BG_DARK)
        logo_frame.pack(fill=tk.X, padx=5, pady=(5, 2))  # 减少底部 padding

        logo_label = tk.Label(logo_frame,
                              text=ASCII_LOGO,
                              bg=CyberTheme.BG_DARK,
                              fg=CyberTheme.FG,
                              font=('Courier New', 7, 'bold'),  # 字体缩小
                              justify=tk.LEFT,
                              anchor='w')
        logo_label.pack(anchor='w', pady=3)  # 减少 padding

        # ========== 配置区 ==========
        config_frame = ttk.LabelFrame(main_container,
                                      text="[ CONFIGURATION ]",
                                      style='Cyber.TLabelframe',
                                      padding=8)  # 减小 padding
        config_frame.pack(fill=tk.X, padx=5, pady=3)  # 减小间距

        # 模式选择
        mode_frame = tk.Frame(config_frame, bg=CyberTheme.BG_LIGHT)
        mode_frame.grid(row=0, column=0, columnspan=4, sticky='w', pady=(0, 10))

        mode_label = tk.Label(mode_frame,
                              text=">> MODE:",
                              bg=CyberTheme.BG_LIGHT,
                              fg=CyberTheme.FG,
                              font=('Courier New', 9))
        mode_label.pack(side=tk.LEFT, padx=(0, 10))

        # 自定义单选按钮样式
        generate_radio = tk.Radiobutton(mode_frame,
                                        text="[ GENERATE ] Create files from structure",
                                        variable=self.mode,
                                        value="generate",
                                        bg=CyberTheme.BG_LIGHT,
                                        fg=CyberTheme.FG,
                                        selectcolor=CyberTheme.BG_DARK,
                                        activebackground=CyberTheme.BG_LIGHT,
                                        activeforeground=CyberTheme.ACCENT,
                                        font=('Courier New', 9),
                                        command=self.on_mode_change)
        generate_radio.pack(side=tk.LEFT, padx=5)

        scan_radio = tk.Radiobutton(mode_frame,
                                    text="[ SCAN ] Generate structure from directory",
                                    variable=self.mode,
                                    value="scan",
                                    bg=CyberTheme.BG_LIGHT,
                                    fg=CyberTheme.FG,
                                    selectcolor=CyberTheme.BG_DARK,
                                    activebackground=CyberTheme.BG_LIGHT,
                                    activeforeground=CyberTheme.ACCENT,
                                    font=('Courier New', 9),
                                    command=self.on_mode_change)
        scan_radio.pack(side=tk.LEFT, padx=5)

        # 项目根路径
        path_label = tk.Label(config_frame,
                              text=">> PROJECT ROOT:",
                              bg=CyberTheme.BG_LIGHT,
                              fg=CyberTheme.FG,
                              font=('Courier New', 9))
        path_label.grid(row=1, column=0, sticky='w', pady=5)

        path_entry = tk.Entry(config_frame,
                              textvariable=self.base_path,
                              bg=CyberTheme.BG_DARK,
                              fg=CyberTheme.FG,
                              insertbackground=CyberTheme.FG,
                              font=('Courier New', 10),
                              relief='flat',
                              borderwidth=0,
                              highlightthickness=0)
        path_entry.grid(row=1, column=1, sticky='ew', padx=10, pady=5)

        browse_btn = ttk.Button(config_frame,
                                text="[ BROWSE ]",
                                style='Cyber.TButton',
                                command=self.browse_path)
        browse_btn.grid(row=1, column=2, padx=5)

        self.action_btn = ttk.Button(config_frame,
                                     text="[ SCAN DIRECTORY ]",
                                     style='Accent.TButton',
                                     command=self.scan_directory)
        self.action_btn.grid(row=1, column=3, padx=5)

        config_frame.columnconfigure(1, weight=1)

        # ========== 目录结构区 ==========
        structure_frame = ttk.LabelFrame(main_container,
                                         text="[ PROJECT STRUCTURE ]",
                                         style='Cyber.TLabelframe',
                                         padding=8)  # 减小 padding
        structure_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=3)  # 减小间距

        # 提示信息
        self.tip_label = tk.Label(structure_frame,
                                  text=">>> Supports multiple formats: tree, emoji, plain text, etc.",
                                  bg=CyberTheme.BG_LIGHT,
                                  fg=CyberTheme.FG_DIM,
                                  font=('Courier New', 8),
                                  anchor='w')
        self.tip_label.pack(fill=tk.X, pady=(0, 5))

        # 文本框
        text_frame = tk.Frame(structure_frame, bg=CyberTheme.BG_LIGHT)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(text_frame, bg=CyberTheme.BG_DARK)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.structure_text = tk.Text(text_frame,
                                      bg=CyberTheme.BG_DARK,
                                      fg=CyberTheme.FG,
                                      insertbackground=CyberTheme.FG,
                                      font=('Courier New', 9),
                                      relief='flat',
                                      borderwidth=0,
                                      highlightthickness=0,
                                      yscrollcommand=scrollbar.set)
        self.structure_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.structure_text.yview)

        # 插入默认结构
        self.structure_text.insert('1.0', self.default_structure)

        # ========== 操作按钮区 ==========
        button_frame = tk.Frame(main_container, bg=CyberTheme.BG)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        # 检测系统类型
        system = platform.system()

        # 左侧：生成脚本按钮
        left_buttons = tk.Frame(button_frame, bg=CyberTheme.BG)
        left_buttons.pack(side=tk.LEFT)

        if system == 'Windows':
            ttk.Button(left_buttons,
                       text="[ GENERATE .BAT ]",
                       style='Accent.TButton',
                       command=self.generate_bat).pack(side=tk.LEFT, padx=5)

        ttk.Button(left_buttons,
                   text="[ GENERATE .PY ]",
                   style='Accent.TButton',
                   command=self.generate_py).pack(side=tk.LEFT, padx=5)

        if system in ['Darwin', 'Linux']:
            ttk.Button(left_buttons,
                       text="[ GENERATE .SH ]",
                       style='Accent.TButton',
                       command=self.generate_sh).pack(side=tk.LEFT, padx=5)

        # Undo 按钮（特殊样式）
        style = ttk.Style()
        style.configure('Warning.TButton',
                        background=CyberTheme.WARNING,
                        foreground=CyberTheme.BG,
                        borderwidth=0,
                        relief='flat',
                        font=('Courier New', 9, 'bold'))
        style.map('Warning.TButton',
                  background=[('active', '#ffcc00')])

        self.undo_btn = ttk.Button(left_buttons,
                                   text="[ UNDO LAST ]",
                                   style='Warning.TButton',
                                   command=self.undo_last_operation,
                                   state='disabled')
        self.undo_btn.pack(side=tk.LEFT, padx=5)

        # 右侧：功能按钮
        right_buttons = tk.Frame(button_frame, bg=CyberTheme.BG)
        right_buttons.pack(side=tk.RIGHT)

        ttk.Button(right_buttons,
                   text="[ PREVIEW ]",
                   style='Cyber.TButton',
                   command=self.preview_structure).pack(side=tk.LEFT, padx=5)

        ttk.Button(right_buttons,
                   text="[ CLEAR ]",
                   style='Cyber.TButton',
                   command=self.clear_structure).pack(side=tk.LEFT, padx=5)

        # ========== 底部版权信息 ==========
        footer = tk.Frame(self.root, bg=CyberTheme.BG_DARK, height=25)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        copyright_label = tk.Label(footer,
                                   text="© 2025 Cyber Tools | Version 2.0.0 | Made with ❤ in Python",
                                   bg=CyberTheme.BG_DARK,
                                   fg=CyberTheme.FG_DIM,
                                   font=('Courier New', 8),
                                   anchor=tk.CENTER)
        copyright_label.pack(fill=tk.X, padx=10, pady=3)

    # ==================== 功能方法 ====================

    def browse_path(self):
        """浏览文件夹"""
        path = filedialog.askdirectory(initialdir=self.base_path.get())
        if path:
            self.base_path.set(path)

    def on_mode_change(self):
        """模式切换时更新界面"""
        mode = self.mode.get()

        if mode == "generate":
            # 生成模式
            self.action_btn.config(text="[ QUICK CREATE ]", command=self.create_project)
            self.tip_label.config(text=">>> Paste structure to create files (existing files will be skipped)")
        else:
            # 扫描模式
            self.action_btn.config(text="[ SCAN DIRECTORY ]", command=self.scan_directory)
            self.tip_label.config(text=">>> Click SCAN to generate structure from existing directory")

    def scan_directory(self):
        """扫描现有目录，生成结构文本"""
        target_path = Path(self.base_path.get())

        if not target_path.exists():
            messagebox.showerror(
                "[ ERROR ]",
                f"[!] Directory does not exist:\n{target_path}"
            )
            return

        if not target_path.is_dir():
            messagebox.showerror(
                "[ ERROR ]",
                f"[!] Not a directory:\n{target_path}"
            )
            return

        # 确认是否覆盖当前内容
        current_text = self.structure_text.get('1.0', tk.END).strip()
        if current_text:
            result = messagebox.askyesno(
                "[ CONFIRM ]",
                "Current structure will be replaced.\n\nContinue?"
            )
            if not result:
                return

        try:
            # 生成目录树
            tree_text = self._generate_tree(target_path)

            # 清空并插入新内容
            self.structure_text.delete('1.0', tk.END)
            self.structure_text.insert('1.0', tree_text)

            messagebox.showinfo(
                "[ SUCCESS ]",
                f"[+] Directory scanned successfully!\n\n[*] Path: {target_path}"
            )
        except Exception as e:
            messagebox.showerror(
                "[ ERROR ]",
                f"[!] Failed to scan directory:\n{str(e)}"
            )

    def _generate_tree(self, root_path, prefix="", is_last=True, max_depth=10, current_depth=0, parent_rel_path=""):
        """递归生成目录树文本，包含元数据注释"""
        if current_depth > max_depth:
            return ""

        # 只忽略版本控制和系统文件
        ignore_names = {
            '.git', '.svn', '.hg', '.DS_Store',
            '__pycache__', 'node_modules',
            '.venv', 'venv',
            MetadataManager.META_FILE
        }

        # 忽略的文件扩展名
        ignore_extensions = {'.pyc', '.pyo', '.pyd'}

        result = ""

        # 根目录
        if current_depth == 0:
            result = f"{root_path.name}/\n"
            # 加载元数据
            self.metadata = MetadataManager.load_metadata(root_path)

        try:
            # 获取所有子项并排序
            items = sorted(root_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

            # 过滤忽略项
            filtered_items = []
            for item in items:
                # 跳过以点开头的隐藏文件（除了常见配置文件）
                if item.name.startswith('.') and item.name not in {'.gitignore', '.env', '.dockerignore'}:
                    continue
                # 跳过忽略名单中的项
                if item.name in ignore_names:
                    continue
                # 跳过特定扩展名
                if item.is_file() and item.suffix in ignore_extensions:
                    continue

                filtered_items.append(item)

            for i, item in enumerate(filtered_items):
                is_last_item = (i == len(filtered_items) - 1)

                # 构建相对路径用于查找注释
                if current_depth == 0:
                    relative_path = item.name
                else:
                    relative_path = f"{parent_rel_path}/{item.name}" if parent_rel_path else item.name

                # 获取注释
                comment = ""
                if hasattr(self, 'metadata') and relative_path in self.metadata:
                    comment = f"  # {self.metadata[relative_path]}"

                # 绘制树形结构
                if current_depth == 0:
                    connector = "└── " if is_last_item else "├── "
                    new_prefix = "    " if is_last_item else "│   "
                else:
                    connector = prefix + ("└── " if is_last_item else "├── ")
                    new_prefix = prefix + ("    " if is_last_item else "│   ")

                if item.is_dir():
                    result += f"{connector}{item.name}/{comment}\n"
                    # 递归处理子目录，传递相对路径
                    result += self._generate_tree(
                        item,
                        new_prefix,
                        is_last_item,
                        max_depth,
                        current_depth + 1,
                        relative_path  # 传递当前相对路径
                    )
                else:
                    result += f"{connector}{item.name}{comment}\n"

        except PermissionError:
            result += f"{prefix}[Permission Denied]\n"

        return result

    def clear_structure(self):
        """清空结构"""
        self.structure_text.delete('1.0', tk.END)

    def preview_structure(self):
        """预览解析结果"""
        structure = self.structure_text.get('1.0', tk.END)
        files, dirs, comments = self.parse_structure(structure)

        # 创建预览窗口
        preview_win = tk.Toplevel(self.root)
        preview_win.title("[ STRUCTURE PREVIEW ]")
        preview_win.configure(bg=CyberTheme.BG)
        preview_win.geometry("700x600")

        # 主容器
        main_frame = tk.Frame(preview_win, bg=CyberTheme.BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        title_label = tk.Label(main_frame,
                               text=">>> PARSED STRUCTURE",
                               bg=CyberTheme.BG,
                               fg=CyberTheme.FG,
                               font=('Courier New', 10, 'bold'),
                               anchor='w')
        title_label.pack(fill=tk.X, pady=(0, 10))

        # 统计信息
        stats_text = f"[*] Directories: {len(dirs)}  |  Files: {len(files)}  |  Comments: {len(comments)}"
        stats_label = tk.Label(main_frame,
                               text=stats_text,
                               bg=CyberTheme.BG,
                               fg=CyberTheme.FG_DIM,
                               font=('Courier New', 9),
                               anchor='w')
        stats_label.pack(fill=tk.X, pady=(0, 5))

        # 文本框
        text_frame = tk.Frame(main_frame, bg=CyberTheme.BG)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        preview_text = tk.Text(text_frame,
                               bg=CyberTheme.BG_DARK,
                               fg=CyberTheme.FG,
                               font=('Courier New', 9),
                               relief='flat',
                               borderwidth=0,
                               highlightthickness=0,
                               yscrollcommand=scrollbar.set)
        preview_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=preview_text.yview)

        # 显示解析结果
        preview_text.insert('1.0', f">>> ROOT: {self.base_path.get()}\n\n")

        if dirs:
            preview_text.insert(tk.END, "[>] DIRECTORIES:\n")
            for d in dirs:
                comment = f"  # {comments[d]}" if d in comments else ""
                preview_text.insert(tk.END, f"    📂 {d}/{comment}\n")
            preview_text.insert(tk.END, "\n")

        if files:
            preview_text.insert(tk.END, "[>] FILES:\n")
            for f in files:
                comment = f"  # {comments[f]}" if f in comments else ""
                preview_text.insert(tk.END, f"    📄 {f}{comment}\n")

        if comments:
            preview_text.insert(tk.END, f"\n[*] Metadata will be saved to: {MetadataManager.META_FILE}\n")

        preview_text.config(state='disabled')

        # 关闭按钮
        close_btn = ttk.Button(main_frame,
                               text="[ CLOSE ]",
                               style='Cyber.TButton',
                               command=preview_win.destroy)
        close_btn.pack(pady=(10, 0))

    def parse_structure(self, text):
        """智能解析目录结构 - 支持注释"""
        lines = text.split('\n')
        files = []
        dirs = set()
        comments = {}  # 存储路径和注释的映射

        # 找出根目录
        root_dir = None
        first_line_cleaned = self._clean_line(lines[0])
        if first_line_cleaned.endswith('/'):
            root_dir = first_line_cleaned[:-1]

        # 使用字典记录每个缩进级别对应的完整路径
        indent_to_path = {}

        for line in lines:
            original_line = line
            if not line.strip():
                continue

            # 提取注释（在 # 之后的内容）
            comment = ""
            if '#' in line:
                parts = line.split('#', 1)
                line = parts[0]
                comment = parts[1].strip()

            # 先移除树形字符，但保留空格缩进
            line_without_tree = line
            for char in ['│', '├', '└', '─', '┌', '┐', '┘', '┤', '┴', '┬', '┼', '╭', '╮', '╰', '╯']:
                line_without_tree = line_without_tree.replace(char, '')

            # 计算缩进
            stripped = line_without_tree.lstrip()
            indent = len(line_without_tree) - len(stripped)

            # 完全清理
            cleaned = self._clean_line(line)

            if not cleaned:
                continue

            # 跳过根目录行
            if root_dir and cleaned == root_dir + '/':
                indent_to_path = {}
                continue

            # 判断是文件还是目录
            is_directory = cleaned.endswith('/')
            item_name = cleaned[:-1] if is_directory else cleaned

            # 查找父级路径
            parent_path = ""
            if indent > 0:
                parent_indents = [i for i in indent_to_path.keys() if i < indent]
                if parent_indents:
                    parent_indent = max(parent_indents)
                    parent_path = indent_to_path[parent_indent]

            # 构建完整路径
            if parent_path:
                full_path = parent_path + '/' + item_name
            else:
                full_path = item_name

            # 移除根目录前缀
            if root_dir and full_path.startswith(root_dir + '/'):
                full_path = full_path[len(root_dir) + 1:]
            elif root_dir and full_path == root_dir:
                continue

            # 存储注释
            if comment and full_path:
                comments[full_path] = comment

            # 处理结果
            if is_directory:
                if full_path:
                    dirs.add(full_path)
                    indent_to_path[indent] = full_path
            else:
                if self._is_file(item_name):
                    if full_path:
                        files.append(full_path)
                        parent = os.path.dirname(full_path)
                        if parent:
                            parts = parent.split('/')
                            for i in range(1, len(parts) + 1):
                                dirs.add('/'.join(parts[:i]))
                else:
                    if full_path:
                        dirs.add(full_path)
                        indent_to_path[indent] = full_path

        return sorted(set(files)), sorted(dirs), comments

    def _clean_line(self, line):
        """清理一行文本中的装饰符号"""
        line = re.sub(r'[│├└─┌┐┘└┤├┴┬┼╭╮╰╯]', '', line)
        line = re.sub(r'[📄📂📁📋🔧🎨⚙️]', '', line)
        line = line.strip()
        return line

    def _is_file(self, name):
        """判断是否是文件"""
        if '.' in name and not name.startswith('.'):
            return True

        common_files = {
            'Makefile', 'Dockerfile', 'Jenkinsfile', 'Vagrantfile',
            'README', 'LICENSE', 'CHANGELOG', 'AUTHORS'
        }
        if name in common_files:
            return True

        if name.startswith('.'):
            return True

        return False

    def generate_bat(self):
        """生成 Windows 批处理脚本"""
        structure = self.structure_text.get('1.0', tk.END)
        files, dirs, comments = self.parse_structure(structure)

        script = f"""@echo off
chcp 65001 >nul
echo ╔═══════════════════════════════════════╗
echo ║   PROJECT SCAFFOLDER v2.0            ║
echo ╚═══════════════════════════════════════╝
echo.
echo [>] Creating project structure...
echo [*] Target: {self.base_path.get()}
echo.

cd /d "{self.base_path.get()}"

echo [>] Creating directories...
"""

        for d in dirs:
            script += f'mkdir "{d}" 2>nul\n'

        script += '\necho [>] Creating files...\n'
        for f in files:
            script += f'type nul > "{f}"\n'

        script += f"""
echo.
echo [+] Project structure created successfully!
echo [*] Location: {self.base_path.get()}
pause
"""

        self._save_script('create_project.bat', script)

    def generate_py(self):
        """生成 Python 脚本"""
        structure = self.structure_text.get('1.0', tk.END)
        files, dirs, comments = self.parse_structure(structure)

        script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Project Scaffolder - Auto Generated"""

from pathlib import Path

def create_project():
    print("╔═══════════════════════════════════════╗")
    print("║   PROJECT SCAFFOLDER v2.0            ║")
    print("╚═══════════════════════════════════════╝")
    print()

    project_root = Path(r"{self.base_path.get()}")

    print(f"[>] Creating project structure...")
    print(f"[*] Target: {{project_root}}")
    print()

    # Create directories
    print("[>] Creating directories...")
    dirs = {dirs}
    for d in dirs:
        (project_root / d).mkdir(parents=True, exist_ok=True)

    # Create files
    print("[>] Creating files...")
    files = {files}
    for f in files:
        (project_root / f).touch()

    print()
    print("[+] Project structure created successfully!")
    print(f"[*] Location: {{project_root}}")

if __name__ == "__main__":
    create_project()
'''

        self._save_script('create_project.py', script)

    def generate_sh(self):
        """生成 Shell 脚本"""
        structure = self.structure_text.get('1.0', tk.END)
        files, dirs, comments = self.parse_structure(structure)

        script = f"""#!/bin/bash

echo "╔═══════════════════════════════════════╗"
echo "║   PROJECT SCAFFOLDER v2.0            ║"
echo "╚═══════════════════════════════════════╝"
echo ""
echo "[>] Creating project structure..."
echo "[*] Target: {self.base_path.get()}"
echo ""

PROJECT_ROOT="{self.base_path.get()}"

cd "$PROJECT_ROOT"

echo "[>] Creating directories..."
"""

        for d in dirs:
            script += f'mkdir -p "{d}"\n'

        script += '\necho "[>] Creating files..."\n'
        for f in files:
            script += f'touch "{f}"\n'

        script += f"""
echo ""
echo "[+] Project structure created successfully!"
echo "[*] Location: $PROJECT_ROOT"
"""

        self._save_script('create_project.sh', script)

    def create_project(self):
        """直接创建项目 - 智能跳过已存在的文件，保存元数据，记录操作历史"""
        structure = self.structure_text.get('1.0', tk.END)
        files, dirs, comments = self.parse_structure(structure)

        project_root = Path(self.base_path.get())

        if not project_root.exists():
            result = messagebox.askyesno(
                "[ CONFIRM ]",
                f"Directory does not exist:\n{project_root}\n\nCreate it?"
            )
            if not result:
                return

        try:
            project_root.mkdir(parents=True, exist_ok=True)

            # 记录本次操作 - 只记录真正新创建的
            created_items = {
                'root': str(project_root),
                'dirs': [],  # 只记录新创建的目录
                'files': [],  # 只记录新创建的文件
                'metadata_updated': bool(comments),
                'timestamp': __import__('datetime').datetime.now().isoformat()
            }

            # 统计信息
            created_dirs = 0
            skipped_dirs = 0
            created_files = 0
            skipped_files = 0

            # 创建目录 - 区分新建和已存在
            for d in dirs:
                dir_path = project_root / d
                if dir_path.exists():
                    skipped_dirs += 1
                    # 不记录到创建列表
                else:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created_dirs += 1
                    created_items['dirs'].append(str(dir_path))  # 只记录新建的

            # 创建文件 - 区分新建和已存在
            for f in files:
                file_path = project_root / f
                if file_path.exists():
                    skipped_files += 1
                    # 不记录到创建列表
                else:
                    file_path.touch()
                    created_files += 1
                    created_items['files'].append(str(file_path))  # 只记录新建的

            # 处理元数据（增量合并）
            old_metadata = {}
            if comments:
                old_metadata = MetadataManager.load_metadata(project_root)
                merged_meta = MetadataManager.merge_metadata(old_metadata, comments)
                MetadataManager.save_metadata(project_root, merged_meta)
                # 记录旧的元数据用于 undo
                created_items['old_metadata'] = old_metadata

            # 只有真正创建了东西才添加到历史记录
            if created_items['dirs'] or created_items['files']:
                self.operation_history.append(created_items)
                self.undo_btn.config(state='normal')

            # 显示详细结果
            result_msg = f"[+] Project structure created!\n\n"
            result_msg += f"[*] Location: {project_root}\n\n"
            result_msg += f">>> CREATED:\n"
            result_msg += f"    📂 Directories: {created_dirs}\n"
            result_msg += f"    📄 Files: {created_files}\n"

            if skipped_dirs > 0 or skipped_files > 0:
                result_msg += f"\n>>> SKIPPED (already exists):\n"
                result_msg += f"    📂 Directories: {skipped_dirs}\n"
                result_msg += f"    📄 Files: {skipped_files}\n"

            if comments:
                result_msg += f"\n>>> METADATA:\n"
                result_msg += f"    💾 Comments saved: {len(comments)}\n"
                result_msg += f"    📋 File: {MetadataManager.META_FILE}\n"

            if created_items['dirs'] or created_items['files']:
                result_msg += f"\n[!] Undo available - only newly created items will be deleted"

            messagebox.showinfo("[ SUCCESS ]", result_msg)

        except Exception as e:
            messagebox.showerror(
                "[ ERROR ]",
                f"[!] Failed to create project:\n{str(e)}"
            )

    def undo_last_operation(self):
        """撤销最后一次创建操作 - 只删除新创建的项"""
        if not self.operation_history:
            messagebox.showwarning(
                "[ WARNING ]",
                "[!] No operations to undo"
            )
            return

        last_op = self.operation_history[-1]

        # 构建详细的撤销信息
        info_lines = [
            "This will DELETE ONLY newly created items:\n",
            f"📂 New Directories: {len(last_op['dirs'])}",
            f"📄 New Files: {len(last_op['files'])}\n",
            f"Location: {last_op['root']}\n"
        ]

        if last_op.get('timestamp'):
            info_lines.append(f"Created at: {last_op['timestamp']}\n")

        info_lines.append("⚠️ Pre-existing files/folders will NOT be deleted\n")
        info_lines.append("Continue?")

        result = messagebox.askyesno(
            "[ CONFIRM UNDO ]",
            "\n".join(info_lines)
        )

        if not result:
            return

        try:
            deleted_files = 0
            deleted_dirs = 0
            skipped_items = []
            errors = []

            # 删除文件 - 只删除列表中的（都是新创建的）
            for file_path in last_op['files']:
                try:
                    path = Path(file_path)
                    if path.exists():
                        # 额外安全检查：确认文件大小为 0（刚 touch 创建的）
                        if path.stat().st_size == 0:
                            path.unlink()
                            deleted_files += 1
                        else:
                            skipped_items.append(f"File modified: {path.name}")
                    else:
                        skipped_items.append(f"Already deleted: {path.name}")
                except Exception as e:
                    errors.append(f"File: {path.name} - {str(e)}")

            # 删除目录 - 从深到浅，只删除空目录
            sorted_dirs = sorted(last_op['dirs'], key=lambda x: x.count('/'), reverse=True)
            for dir_path in sorted_dirs:
                try:
                    path = Path(dir_path)
                    if path.exists():
                        # 检查目录是否为空
                        if not any(path.iterdir()):
                            path.rmdir()
                            deleted_dirs += 1
                        else:
                            skipped_items.append(f"Dir not empty: {path.name}")
                    else:
                        skipped_items.append(f"Already deleted: {path.name}")
                except Exception as e:
                    errors.append(f"Dir: {Path(dir_path).name} - {str(e)}")

            # 恢复旧的元数据（如果有）
            if last_op.get('old_metadata') is not None:
                project_root = Path(last_op['root'])
                MetadataManager.save_metadata(project_root, last_op['old_metadata'])

            # 移除历史记录
            self.operation_history.pop()

            # 更新按钮状态
            if not self.operation_history:
                self.undo_btn.config(state='disabled')

            # 显示结果
            result_msg = f"[+] Undo completed!\n\n"
            result_msg += f">>> DELETED (newly created items only):\n"
            result_msg += f"    📂 Directories: {deleted_dirs}\n"
            result_msg += f"    📄 Files: {deleted_files}\n"

            if skipped_items:
                result_msg += f"\n>>> PROTECTED (not deleted):\n"
                for item in skipped_items[:5]:
                    result_msg += f"    ✓ {item}\n"
                if len(skipped_items) > 5:
                    result_msg += f"    ... and {len(skipped_items) - 5} more\n"

            if errors:
                result_msg += f"\n[!] ERRORS ({len(errors)}):\n"
                for err in errors[:3]:
                    result_msg += f"    {err}\n"
                if len(errors) > 3:
                    result_msg += f"    ... and {len(errors) - 3} more\n"

            if self.operation_history:
                result_msg += f"\n[*] {len(self.operation_history)} operation(s) remaining in history"

            messagebox.showinfo("[ UNDO SUCCESS ]", result_msg)

        except Exception as e:
            messagebox.showerror(
                "[ ERROR ]",
                f"[!] Failed to undo:\n{str(e)}"
            )

    def _save_script(self, filename, content):
        """保存脚本到文件"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=os.path.splitext(filename)[1],
            initialfile=filename,
            filetypes=[
                ("All Files", "*.*"),
                ("Batch Files", "*.bat"),
                ("Python Files", "*.py"),
                ("Shell Scripts", "*.sh")
            ]
        )

        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo(
                "[ SUCCESS ]",
                f"[+] Script saved:\n{filepath}"
            )


# ==================== 主程序入口 ====================
def main():
    root = tk.Tk()
    app = ScaffolderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()