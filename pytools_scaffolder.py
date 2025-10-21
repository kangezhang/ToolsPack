#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目脚手架生成器 - 赛博朋克终端风格
v2.2 - 支持代码模板智能填充
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import json
from pathlib import Path
from datetime import datetime


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


# ==================== 代码模板管理器 ====================
class CodeTemplateManager:
    @staticmethod
    def parse_template_file(content):
        templates = {}
        current_file = None
        current_code = []

        for line in content.split('\n'):
            file_match = re.match(r'^#\s+([a-zA-Z0-9_/\\\.]+\.py)\s*[-\s]*(.*?)(?:={10,})?$', line)
            if file_match:
                if current_file and current_code:
                    code = '\n'.join(current_code).strip()
                    if code:
                        templates[current_file] = code
                current_file = file_match.group(1).strip()
                current_code = []
                continue
            if re.match(r'^#\s*={10,}\s*$', line):
                continue
            if current_file:
                current_code.append(line)

        if current_file and current_code:
            code = '\n'.join(current_code).strip()
            if code:
                templates[current_file] = code

        return templates

    @staticmethod
    def match_files(template_paths, project_files):
        matches = []
        for template_path in template_paths:
            template_norm = template_path.replace('\\', '/')
            for project_file in project_files:
                project_norm = project_file.replace('\\', '/')
                if template_norm == project_norm:
                    matches.append((template_path, project_file))
                    break
                elif template_norm.split('/')[-1] == project_norm.split('/')[-1]:
                    matches.append((template_path, project_file))
                    break
        return matches

    @staticmethod
    def backup_file(file_path):
        try:
            if Path(file_path).exists():
                return Path(file_path).read_text(encoding='utf-8')
        except:
            pass
        return None

    @staticmethod
    def write_file(file_path, content):
        try:
            Path(file_path).write_text(content, encoding='utf-8')
            return True
        except:
            return False


# ==================== 元数据管理器 ====================
class MetadataManager:
    META_FILE = '.scaffold_meta.json'

    @staticmethod
    def load_metadata(project_root):
        meta_path = Path(project_root) / MetadataManager.META_FILE
        if meta_path.exists():
            try:
                return json.loads(meta_path.read_text(encoding='utf-8'))
            except:
                return {}
        return {}

    @staticmethod
    def save_metadata(project_root, metadata):
        meta_path = Path(project_root) / MetadataManager.META_FILE
        try:
            meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
            return True
        except:
            return False

    @staticmethod
    def merge_metadata(existing, new_data):
        result = existing.copy()
        for path, comment in new_data.items():
            if comment:
                result[path] = comment
        return result


# ==================== ASCII LOGO ====================
ASCII_LOGO = """
╔═══════════════════════════════════════════════════╗
║   PROJECT SCAFFOLDER v2.2                        ║
║   [ SYSTEM READY ]                               ║
╚═══════════════════════════════════════════════════╝
"""


# ==================== 主应用 ====================
class ScaffolderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("[ PROJECT SCAFFOLDER ]")
        self.root.configure(bg=CyberTheme.BG)
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)

        # ==================== 动画配置参数 ====================
        self.arrow_animation_speed = 300  # 动画速度（毫秒），数值越大越慢，建议：100-500

        self.base_path = tk.StringVar(value=str(Path.home() / "Desktop"))
        self.mode = tk.StringVar(value="generate")
        self.operation_history = []
        self.template_history = []
        self.arrow_phase = 0

        self.default_structure = """my_project/
├── main.py
├── config.py
└── README.md"""

        self.structure_text = None
        self.template_text = None
        self.notebook = None
        self.arrow_labels = []

        self.setup_theme()
        self.create_widgets()
        self.on_mode_change()

    def setup_theme(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Cyber.TFrame', background=CyberTheme.BG)
        style.configure('Cyber.TLabelframe', background=CyberTheme.BG_LIGHT, foreground=CyberTheme.FG,
                        bordercolor=CyberTheme.BORDER)
        style.configure('Cyber.TLabelframe.Label', background=CyberTheme.BG_LIGHT, foreground=CyberTheme.FG,
                        font=('Courier New', 10, 'bold'))
        style.configure('Cyber.TButton', background=CyberTheme.BUTTON_BG, foreground=CyberTheme.FG,
                        font=('Courier New', 9, 'bold'))
        style.configure('Accent.TButton', background=CyberTheme.ACCENT, foreground=CyberTheme.BG,
                        font=('Courier New', 9, 'bold'))
        style.configure('Warning.TButton', background=CyberTheme.WARNING, foreground=CyberTheme.BG,
                        font=('Courier New', 9, 'bold'))
        style.configure('Cyber.TNotebook', background=CyberTheme.BG, borderwidth=0)
        style.configure('Cyber.TNotebook.Tab', background=CyberTheme.BG_LIGHT, foreground=CyberTheme.FG,
                        padding=[15, 8], font=('Courier New', 9, 'bold'))
        style.map('Cyber.TNotebook.Tab', background=[('selected', CyberTheme.BG_DARK)],
                  foreground=[('selected', CyberTheme.ACCENT)])

    def create_widgets(self):
        main = ttk.Frame(self.root, style='Cyber.TFrame')
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Logo 区域
        logo_frame = tk.Frame(main, bg=CyberTheme.BG_DARK)
        logo_frame.pack(fill=tk.X, padx=5, pady=(5, 2))

        content_frame = tk.Frame(logo_frame, bg=CyberTheme.BG_DARK)
        content_frame.pack(anchor='w', pady=3)

        # 箭头动画
        arrow_frame = tk.Frame(content_frame, bg=CyberTheme.BG_DARK)
        arrow_frame.pack(side=tk.LEFT, padx=(5, 10))

        for i in range(5):
            label = tk.Label(arrow_frame, text='>', bg=CyberTheme.BG_DARK, fg=CyberTheme.FG,
                             font=('Courier New', 12, 'bold'))
            label.pack(side=tk.LEFT)
            self.arrow_labels.append(label)

        # Logo 文字
        tk.Label(content_frame, text=ASCII_LOGO, bg=CyberTheme.BG_DARK, fg=CyberTheme.FG,
                 font=('Courier New', 7, 'bold'), justify=tk.LEFT, anchor='w').pack(side=tk.LEFT)

        # 配置区
        cfg = ttk.LabelFrame(main, text="[ CONFIGURATION ]", style='Cyber.TLabelframe', padding=8)
        cfg.pack(fill=tk.X, padx=5, pady=3)

        mode_frame = tk.Frame(cfg, bg=CyberTheme.BG_LIGHT)
        mode_frame.grid(row=0, column=0, columnspan=4, sticky='w', pady=(0, 10))
        tk.Label(mode_frame, text=">> MODE:", bg=CyberTheme.BG_LIGHT, fg=CyberTheme.FG, font=('Courier New', 9)).pack(
            side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(mode_frame, text="[ GENERATE ]", variable=self.mode, value="generate", bg=CyberTheme.BG_LIGHT,
                       fg=CyberTheme.FG, selectcolor=CyberTheme.BG_DARK, font=('Courier New', 9),
                       command=self.on_mode_change).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mode_frame, text="[ SCAN ]", variable=self.mode, value="scan", bg=CyberTheme.BG_LIGHT,
                       fg=CyberTheme.FG, selectcolor=CyberTheme.BG_DARK, font=('Courier New', 9),
                       command=self.on_mode_change).pack(side=tk.LEFT, padx=5)

        tk.Label(cfg, text=">> PROJECT ROOT:", bg=CyberTheme.BG_LIGHT, fg=CyberTheme.FG, font=('Courier New', 9)).grid(
            row=1, column=0, sticky='w', pady=5)
        tk.Entry(cfg, textvariable=self.base_path, bg=CyberTheme.BG_DARK, fg=CyberTheme.FG,
                 insertbackground=CyberTheme.FG, font=('Courier New', 10), relief='flat').grid(row=1, column=1,
                                                                                               sticky='ew', padx=10,
                                                                                               pady=5)
        ttk.Button(cfg, text="[ BROWSE ]", style='Cyber.TButton', command=self.browse_path).grid(row=1, column=2,
                                                                                                 padx=5)
        self.action_btn = ttk.Button(cfg, text="[ SCAN ]", style='Accent.TButton', command=self.scan_directory)
        self.action_btn.grid(row=1, column=3, padx=5)
        cfg.columnconfigure(1, weight=1)

        # Tab 控件
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=3)

        # Tab 1
        tab1 = ttk.Frame(self.notebook, style='Cyber.TFrame')
        self.notebook.add(tab1, text='[ PROJECT STRUCTURE ]')
        self.tip_label = tk.Label(tab1, text=">>> Supports tree, emoji, plain text formats", bg=CyberTheme.BG_LIGHT,
                                  fg=CyberTheme.FG_DIM, font=('Courier New', 8), anchor='w')
        self.tip_label.pack(fill=tk.X, pady=(8, 5), padx=8)
        frame1 = tk.Frame(tab1, bg=CyberTheme.BG_LIGHT)
        frame1.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        scroll1 = tk.Scrollbar(frame1)
        scroll1.pack(side=tk.RIGHT, fill=tk.Y)
        self.structure_text = tk.Text(frame1, bg=CyberTheme.BG_DARK, fg=CyberTheme.FG, insertbackground=CyberTheme.FG,
                                      font=('Courier New', 9), yscrollcommand=scroll1.set, relief='flat')
        self.structure_text.pack(fill=tk.BOTH, expand=True)
        scroll1.config(command=self.structure_text.yview)
        self.structure_text.insert('1.0', self.default_structure)

        # Tab 2
        tab2 = ttk.Frame(self.notebook, style='Cyber.TFrame')
        self.notebook.add(tab2, text='[ CODE TEMPLATES ]')
        tk.Label(tab2, text=">>> Paste code templates (format: # filename.py ...)", bg=CyberTheme.BG_LIGHT,
                 fg=CyberTheme.FG_DIM, font=('Courier New', 8), anchor='w').pack(fill=tk.X, pady=(8, 5), padx=8)
        frame2 = tk.Frame(tab2, bg=CyberTheme.BG_LIGHT)
        frame2.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        scroll2 = tk.Scrollbar(frame2)
        scroll2.pack(side=tk.RIGHT, fill=tk.Y)
        self.template_text = tk.Text(frame2, bg=CyberTheme.BG_DARK, fg=CyberTheme.FG, insertbackground=CyberTheme.FG,
                                     font=('Courier New', 9), yscrollcommand=scroll2.set, relief='flat')
        self.template_text.pack(fill=tk.BOTH, expand=True)
        scroll2.config(command=self.template_text.yview)

        # 按钮区
        btn_frame = tk.Frame(main, bg=CyberTheme.BG)
        btn_frame.pack(fill=tk.X, padx=5, pady=3)
        left = tk.Frame(btn_frame, bg=CyberTheme.BG)
        left.pack(side=tk.LEFT)
        self.undo_btn = ttk.Button(left, text="[ UNDO LAST ]", style='Warning.TButton',
                                   command=self.undo_last_operation, state='disabled')
        self.undo_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(left, text="[ FILL CODE ]", style='Accent.TButton', command=self.fill_code_templates).pack(
            side=tk.LEFT, padx=5)
        right = tk.Frame(btn_frame, bg=CyberTheme.BG)
        right.pack(side=tk.RIGHT)
        ttk.Button(right, text="[ PREVIEW ]", style='Cyber.TButton', command=self.preview_structure).pack(side=tk.LEFT,
                                                                                                          padx=5)
        ttk.Button(right, text="[ CLEAR ]", style='Cyber.TButton', command=self.clear_structure).pack(side=tk.LEFT,
                                                                                                      padx=5)

        # 底部
        footer = tk.Frame(self.root, bg=CyberTheme.BG_DARK, height=20)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(footer, text="© 2025 Kang Zhang | v2.2.0", bg=CyberTheme.BG_DARK, fg=CyberTheme.FG_DIM,
                 font=('Courier New', 7)).pack(fill=tk.BOTH, expand=True)

        # 启动动画
        self.animate_arrows()

    def animate_arrows(self):
        """箭头移动动画"""
        phase = self.arrow_phase % 5
        brightness_pattern = [
            [0.3, 0.5, 0.8, 1.0, 0.8],
            [0.5, 0.8, 1.0, 0.8, 0.5],
            [0.8, 1.0, 0.8, 0.5, 0.3],
            [1.0, 0.8, 0.5, 0.3, 0.5],
            [0.8, 0.5, 0.3, 0.5, 0.8],
        ]
        pattern = brightness_pattern[phase]

        for i, label in enumerate(self.arrow_labels):
            brightness = pattern[i]
            green = int(255 * brightness)
            color = f'#00{green:02x}{int(green * 0.25):02x}'
            label.config(fg=color)

        self.arrow_phase += 1
        # 使用实例属性配置动画速度
        self.root.after(self.arrow_animation_speed, self.animate_arrows)

    def browse_path(self):
        path = filedialog.askdirectory(initialdir=self.base_path.get())
        if path:
            self.base_path.set(path)

    def on_mode_change(self):
        if self.mode.get() == "generate":
            self.action_btn.config(text="[ QUICK CREATE ]", command=self.create_project)
            self.tip_label.config(text=">>> Paste structure to create files")
        else:
            self.action_btn.config(text="[ SCAN DIRECTORY ]", command=self.scan_directory)
            self.tip_label.config(text=">>> Click SCAN to generate structure")

    def scan_directory(self):
        target = Path(self.base_path.get())
        if not target.exists() or not target.is_dir():
            messagebox.showerror("[ ERROR ]", f"Invalid directory:\n{target}")
            return

        if self.structure_text.get('1.0', tk.END).strip():
            if not messagebox.askyesno("[ CONFIRM ]", "Replace current structure?"):
                return

        try:
            tree = self._generate_tree(target)
            self.structure_text.delete('1.0', tk.END)
            self.structure_text.insert('1.0', tree)
            messagebox.showinfo("[ SUCCESS ]", f"Scanned:\n{target}")
        except Exception as e:
            messagebox.showerror("[ ERROR ]", f"Scan failed:\n{e}")

    def _generate_tree(self, root_path, prefix="", is_last=True, max_depth=10, current_depth=0, parent_rel=""):
        if current_depth > max_depth:
            return ""

        ignore = {'.git', '__pycache__', 'node_modules', '.venv', MetadataManager.META_FILE}
        result = ""

        if current_depth == 0:
            result = f"{root_path.name}/\n"
            self.metadata = MetadataManager.load_metadata(root_path)

        try:
            items = sorted(root_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            filtered = [i for i in items if
                        i.name not in ignore and not (i.name.startswith('.') and i.name not in {'.gitignore', '.env'})]

            for i, item in enumerate(filtered):
                is_last_item = (i == len(filtered) - 1)
                rel_path = f"{parent_rel}/{item.name}" if parent_rel else item.name
                comment = f"  # {self.metadata[rel_path]}" if hasattr(self,
                                                                      'metadata') and rel_path in self.metadata else ""

                connector = ("└── " if is_last_item else "├── ") if current_depth == 0 else prefix + (
                    "└── " if is_last_item else "├── ")
                new_prefix = ("    " if is_last_item else "│   ") if current_depth == 0 else prefix + (
                    "    " if is_last_item else "│   ")

                if item.is_dir():
                    result += f"{connector}{item.name}/{comment}\n"
                    result += self._generate_tree(item, new_prefix, is_last_item, max_depth, current_depth + 1,
                                                  rel_path)
                else:
                    result += f"{connector}{item.name}{comment}\n"
        except PermissionError:
            result += f"{prefix}[Permission Denied]\n"

        return result

    def clear_structure(self):
        self.structure_text.delete('1.0', tk.END)

    def preview_structure(self):
        structure = self.structure_text.get('1.0', tk.END)
        files, dirs, comments = self.parse_structure(structure)

        win = tk.Toplevel(self.root)
        win.title("[ PREVIEW ]")
        win.configure(bg=CyberTheme.BG)
        win.geometry("800x600")

        frame = tk.Frame(win, bg=CyberTheme.BG)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(frame, text=">>> PARSED STRUCTURE", bg=CyberTheme.BG, fg=CyberTheme.FG,
                 font=('Courier New', 10, 'bold'), anchor='w').pack(fill=tk.X, pady=(0, 10))
        tk.Label(frame, text=f"Dirs: {len(dirs)} | Files: {len(files)} | Comments: {len(comments)}", bg=CyberTheme.BG,
                 fg=CyberTheme.FG_DIM, font=('Courier New', 9), anchor='w').pack(fill=tk.X, pady=(0, 5))

        text_frame = tk.Frame(frame, bg=CyberTheme.BG)
        text_frame.pack(fill=tk.BOTH, expand=True)
        scroll = tk.Scrollbar(text_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text = tk.Text(text_frame, bg=CyberTheme.BG_DARK, fg=CyberTheme.FG, font=('Courier New', 9),
                       yscrollcommand=scroll.set, state='normal', wrap='none')
        text.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=text.yview)

        text.insert('1.0', f">>> ROOT: {self.base_path.get()}\n\n")
        if dirs:
            text.insert(tk.END, "[>] DIRECTORIES:\n")
            for d in dirs:
                text.insert(tk.END, f"    📂 {d}/\n")
            text.insert(tk.END, "\n")
        if files:
            text.insert(tk.END, "[>] FILES:\n")
            for f in files:
                text.insert(tk.END, f"    📄 {f}\n")

        text.config(state='disabled')
        ttk.Button(frame, text="[ CLOSE ]", style='Cyber.TButton', command=win.destroy).pack(pady=(10, 0))

    def parse_structure(self, text):
        lines = text.split('\n')
        files = []
        dirs = set()
        comments = {}

        root_dir = None
        first_cleaned = self._clean_line(lines[0])
        if first_cleaned.endswith('/'):
            root_dir = first_cleaned[:-1]

        level_to_path = {}

        for line in lines:
            if not line.strip():
                continue

            comment = ""
            if '#' in line:
                parts = line.split('#', 1)
                line = parts[0]
                comment = parts[1].strip()

            cleaned = self._clean_line(line)
            if not cleaned or (root_dir and cleaned == root_dir + '/'):
                level_to_path = {}
                continue

            level = self._calculate_level_fixed(line)
            is_dir = cleaned.endswith('/')
            item_name = cleaned[:-1] if is_dir else cleaned

            parent_path = ""
            if level > 0:
                for check_level in range(level - 1, -1, -1):
                    if check_level in level_to_path:
                        parent_path = level_to_path[check_level]
                        break

            full_path = f"{parent_path}/{item_name}" if parent_path else item_name

            if root_dir and full_path.startswith(root_dir + '/'):
                full_path = full_path[len(root_dir) + 1:]
            elif root_dir and full_path == root_dir:
                continue

            if comment and full_path:
                comments[full_path] = comment

            if is_dir:
                if full_path:
                    dirs.add(full_path)
                    level_to_path[level] = full_path
                    for k in list(level_to_path.keys()):
                        if k > level:
                            del level_to_path[k]
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
                        level_to_path[level] = full_path

        return sorted(set(files)), sorted(dirs), comments

    def _calculate_level_fixed(self, line):
        clean = re.sub(r'[📄📂📁📋🔧🎨⚙️]', '', line)
        leading_spaces = sum(4 if c == '\t' else 1 for c in clean if
                             c in ' \t' and clean.index(c) < len(clean) and not clean[:clean.index(c) + 1].strip())
        pipe_count = clean.count('│')
        has_branch = '├' in clean or '└' in clean

        if pipe_count > 0:
            return pipe_count + 1 if has_branch else pipe_count
        elif has_branch:
            if leading_spaces == 0:
                return 1
            for unit in [4, 2, 8, 3]:
                if leading_spaces % unit == 0:
                    return (leading_spaces // unit) + 1
            return 1
        else:
            if leading_spaces == 0:
                return 0
            for unit in [4, 2, 8]:
                if leading_spaces % unit == 0:
                    return leading_spaces // unit
            return leading_spaces // 4

    def _clean_line(self, line):
        line = re.sub(r'[│├└─┌┐┘└┤├┴┬┼╭╮╰╯📄📂📁📋🔧🎨⚙️]', '', line)
        return line.strip()

    def _is_file(self, name):
        if '.' in name and not name.startswith('.'):
            return True
        if name in {'Makefile', 'Dockerfile', 'README', 'LICENSE'}:
            return True
        return name.startswith('.')

    def create_project(self):
        structure = self.structure_text.get('1.0', tk.END)
        files, dirs, comments = self.parse_structure(structure)
        project_root = Path(self.base_path.get())

        if not project_root.exists():
            if not messagebox.askyesno("[ CONFIRM ]", f"Create directory?\n{project_root}"):
                return

        try:
            project_root.mkdir(parents=True, exist_ok=True)

            created_items = {'root': str(project_root), 'dirs': [], 'files': [],
                             'timestamp': datetime.now().isoformat()}
            created_dirs = skipped_dirs = created_files = skipped_files = 0

            for d in dirs:
                dp = project_root / d
                if dp.exists():
                    skipped_dirs += 1
                else:
                    dp.mkdir(parents=True, exist_ok=True)
                    created_dirs += 1
                    created_items['dirs'].append(str(dp))

            for f in files:
                fp = project_root / f
                if fp.exists():
                    skipped_files += 1
                else:
                    fp.touch()
                    created_files += 1
                    created_items['files'].append(str(fp))

            if comments:
                old_meta = MetadataManager.load_metadata(project_root)
                merged = MetadataManager.merge_metadata(old_meta, comments)
                MetadataManager.save_metadata(project_root, merged)
                created_items['old_metadata'] = old_meta

            if created_items['dirs'] or created_items['files']:
                self.operation_history.append(created_items)
                self.undo_btn.config(state='normal')

            msg = f"[+] Project created!\n\n[*] Location: {project_root}\n\n>>> CREATED:\n  📂 Dirs: {created_dirs}\n  📄 Files: {created_files}\n"
            if skipped_dirs or skipped_files:
                msg += f"\n>>> SKIPPED:\n  📂 Dirs: {skipped_dirs}\n  📄 Files: {skipped_files}\n"
            if comments:
                msg += f"\n>>> METADATA:\n  💾 Comments: {len(comments)}\n"
            messagebox.showinfo("[ SUCCESS ]", msg)
        except Exception as e:
            messagebox.showerror("[ ERROR ]", f"Failed:\n{e}")

    def fill_code_templates(self):
        template_content = self.template_text.get('1.0', tk.END).strip()
        if not template_content:
            messagebox.showwarning("[ WARNING ]", "No template content")
            return

        try:
            templates = CodeTemplateManager.parse_template_file(template_content)
            if not templates:
                messagebox.showerror("[ ERROR ]", "Failed to parse templates\n\nFormat: # filename.py\ncode...")
                return
        except Exception as e:
            messagebox.showerror("[ ERROR ]", f"Parse error:\n{e}")
            return

        structure = self.structure_text.get('1.0', tk.END)
        files, dirs, comments = self.parse_structure(structure)

        if not files:
            messagebox.showwarning("[ WARNING ]", "No files in project structure")
            return

        matches = CodeTemplateManager.match_files(templates.keys(), files)

        if not matches:
            messagebox.showinfo("[ INFO ]", f"No matching files\n\nTemplates: {len(templates)}\nProject: {len(files)}")
            return

        self.show_fill_dialog(matches, templates)

    def show_fill_dialog(self, matches, templates):
        dlg = tk.Toplevel(self.root)
        dlg.title("[ CODE FILL CONFIRMATION ]")
        dlg.configure(bg=CyberTheme.BG)
        dlg.geometry("900x600")
        dlg.transient(self.root)
        dlg.grab_set()

        main = tk.Frame(dlg, bg=CyberTheme.BG)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        tk.Label(main, text=">>> SELECT FILES TO FILL", bg=CyberTheme.BG, fg=CyberTheme.FG,
                 font=('Courier New', 11, 'bold'), anchor='w').pack(fill=tk.X, pady=(0, 10))
        tk.Label(main, text="⚠️  Existing content will be backed up (UNDO available)", bg=CyberTheme.BG,
                 fg=CyberTheme.WARNING, font=('Courier New', 9), anchor='w').pack(fill=tk.X, pady=(0, 15))

        list_frame = tk.Frame(main, bg=CyberTheme.BG_DARK, highlightthickness=1, highlightbackground=CyberTheme.BORDER)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        canvas = tk.Canvas(list_frame, bg=CyberTheme.BG_DARK, highlightthickness=0)
        scroll = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=CyberTheme.BG_DARK)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        project_root = Path(self.base_path.get())
        check_vars = {}

        for template_path, project_file in matches:
            full_path = project_root / project_file
            file_exists = full_path.exists()
            has_content = False
            content_differs = False

            if file_exists:
                try:
                    current = full_path.read_text(encoding='utf-8').strip()
                    has_content = len(current) > 0
                    content_differs = (current != templates[template_path].strip())
                except:
                    pass

            row = tk.Frame(scrollable, bg=CyberTheme.BG_LIGHT, highlightthickness=1,
                           highlightbackground=CyberTheme.BORDER)
            row.pack(fill=tk.X, padx=5, pady=3)

            var = tk.BooleanVar(value=True)
            check_vars[project_file] = var
            tk.Checkbutton(row, variable=var, bg=CyberTheme.BG_LIGHT, fg=CyberTheme.FG,
                           selectcolor=CyberTheme.BG_DARK).pack(side=tk.LEFT, padx=(10, 5), pady=8)

            info = tk.Frame(row, bg=CyberTheme.BG_LIGHT)
            info.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=5)
            tk.Label(info, text=f"📄 {project_file}", bg=CyberTheme.BG_LIGHT, fg=CyberTheme.FG,
                     font=('Courier New', 9, 'bold'), anchor='w').pack(fill=tk.X)

            if not file_exists:
                status_text = "🆕 New file"
                status_color = CyberTheme.SUCCESS
            elif not has_content:
                status_text = "📝 Empty file"
                status_color = CyberTheme.ACCENT
            elif content_differs:
                status_text = "⚠️  Different content - will overwrite"
                status_color = CyberTheme.WARNING
            else:
                status_text = "✓ Same content"
                status_color = CyberTheme.FG_DIM
                var.set(False)

            tk.Label(info, text=status_text, bg=CyberTheme.BG_LIGHT, fg=status_color, font=('Courier New', 8),
                     anchor='w').pack(fill=tk.X, padx=(20, 0))

        btn_frame = tk.Frame(main, bg=CyberTheme.BG)
        btn_frame.pack(fill=tk.X)

        left = tk.Frame(btn_frame, bg=CyberTheme.BG)
        left.pack(side=tk.LEFT)
        ttk.Button(left, text="[ SELECT ALL ]", style='Cyber.TButton',
                   command=lambda: [v.set(True) for v in check_vars.values()]).pack(side=tk.LEFT, padx=5)
        ttk.Button(left, text="[ DESELECT ALL ]", style='Cyber.TButton',
                   command=lambda: [v.set(False) for v in check_vars.values()]).pack(side=tk.LEFT, padx=5)

        right = tk.Frame(btn_frame, bg=CyberTheme.BG)
        right.pack(side=tk.RIGHT)
        ttk.Button(right, text="[ CANCEL ]", style='Cyber.TButton', command=dlg.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(right, text="[ APPLY ]", style='Accent.TButton',
                   command=lambda: self.apply_templates(dlg, check_vars, matches, templates)).pack(side=tk.LEFT, padx=5)

    def apply_templates(self, dialog, check_vars, matches, templates):
        selected = [f for f, v in check_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("[ WARNING ]", "No files selected")
            return

        dialog.destroy()

        project_root = Path(self.base_path.get())
        operation = {'timestamp': datetime.now().isoformat(), 'files': {}}
        success = error = 0
        errors = []

        for template_path, project_file in matches:
            if project_file not in selected:
                continue

            full_path = project_root / project_file
            backup = CodeTemplateManager.backup_file(full_path)

            if CodeTemplateManager.write_file(full_path, templates[template_path]):
                success += 1
                operation['files'][str(full_path)] = backup
            else:
                error += 1
                errors.append(project_file)

        if operation['files']:
            self.template_history.append(operation)
            self.undo_btn.config(state='normal')

        msg = f"[+] Templates applied!\n\n✓ Success: {success}\n"
        if error:
            msg += f"✗ Failed: {error}\n"
            for e in errors[:5]:
                msg += f"  • {e}\n"
        msg += f"\n[!] Use UNDO to restore"
        messagebox.showinfo("[ SUCCESS ]", msg)

    def undo_last_operation(self):
        if self.template_history:
            self.undo_template_fill()
        elif self.operation_history:
            self.undo_file_creation()
        else:
            messagebox.showwarning("[ WARNING ]", "Nothing to undo")

    def undo_template_fill(self):
        last = self.template_history[-1]
        if not messagebox.askyesno("[ CONFIRM UNDO ]",
                                   f"Restore {len(last['files'])} files?\n\n{last['timestamp']}\n\nContinue?"):
            return

        try:
            restored = deleted = 0
            errors = []

            for file_path, backup in last['files'].items():
                try:
                    p = Path(file_path)
                    if backup is None:
                        if p.exists():
                            p.unlink()
                            deleted += 1
                    else:
                        p.write_text(backup, encoding='utf-8')
                        restored += 1
                except Exception as e:
                    errors.append(f"{p.name}: {e}")

            self.template_history.pop()
            if not self.template_history and not self.operation_history:
                self.undo_btn.config(state='disabled')

            msg = f"[+] Undo completed!\n\n✓ Restored: {restored}\n✗ Deleted: {deleted}\n"
            if errors:
                msg += f"\n[!] Errors: {len(errors)}\n"
            messagebox.showinfo("[ SUCCESS ]", msg)
        except Exception as e:
            messagebox.showerror("[ ERROR ]", f"Undo failed:\n{e}")

    def undo_file_creation(self):
        last = self.operation_history[-1]
        if not messagebox.askyesno("[ CONFIRM UNDO ]",
                                   f"Delete {len(last['dirs'])} dirs & {len(last['files'])} files?\n\n{last['timestamp']}\n\nContinue?"):
            return

        try:
            deleted_files = deleted_dirs = 0

            for fp in last['files']:
                try:
                    p = Path(fp)
                    if p.exists() and p.stat().st_size == 0:
                        p.unlink()
                        deleted_files += 1
                except:
                    pass

            for dp in sorted(last['dirs'], key=lambda x: x.count('/'), reverse=True):
                try:
                    p = Path(dp)
                    if p.exists() and not any(p.iterdir()):
                        p.rmdir()
                        deleted_dirs += 1
                except:
                    pass

            if last.get('old_metadata'):
                MetadataManager.save_metadata(Path(last['root']), last['old_metadata'])

            self.operation_history.pop()
            if not self.operation_history and not self.template_history:
                self.undo_btn.config(state='disabled')

            messagebox.showinfo("[ SUCCESS ]",
                                f"[+] Undo completed!\n\n✓ Deleted: {deleted_dirs} dirs, {deleted_files} files")
        except Exception as e:
            messagebox.showerror("[ ERROR ]", f"Undo failed:\n{e}")


# ==================== 主程序入口 ====================
def main():
    root = tk.Tk()
    app = ScaffolderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()