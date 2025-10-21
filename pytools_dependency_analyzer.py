import ast
import os
import sys
import json
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import subprocess

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError


class CyberTheme:
    """赛博朋克主题配置"""
    BG = '#1e1e1e'  # 主背景 - 黑灰色
    BG_LIGHT = '#2d2d2d'  # 面板背景 - 浅灰
    BG_DARK = '#151515'  # 深背景/输入框
    FG = '#00ff41'  # 矩阵绿
    FG_DIM = '#00aa2e'  # 暗绿
    FG_BRIGHT = '#00ffff'  # 青色
    ACCENT = '#00d4aa'  # 青绿强调
    ACCENT_DARK = '#00a885'  # 深强调色
    SUCCESS = '#00ff41'  # 成功绿
    ERROR = '#ff0055'  # 错误红
    WARNING = '#ffaa00'  # 警告橙
    BORDER = '#3a3a3a'  # 低调暗灰边框
    BUTTON_BG = '#252525'  # 按钮背景


ASCII_LOGO = """
╔═══════════════════════════════════════════╗
║                                           ║
║   ██████╗ ███████╗██████╗                ║
║   ██╔══██╗██╔════╝██╔══██╗               ║
║   ██║  ██║█████╗  ██████╔╝               ║
║   ██║  ██║██╔══╝  ██╔═══╝                ║
║   ██████╔╝███████╗██║                    ║
║   ╚═════╝ ╚══════╝╚═╝                    ║
║                                           ║
║   Python Dependency Analyzer v2.0        ║
║   [ SYSTEM READY ]                       ║
║                                           ║
╚═══════════════════════════════════════════╝
"""


class DependencyAnalyzer:
    """依赖分析器"""

    STDLIB_MODULES = {
        'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
        'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins',
        'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs',
        'codeop', 'collections', 'colorsys', 'compileall', 'concurrent', 'configparser',
        'contextlib', 'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
        'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib',
        'dis', 'distutils', 'doctest', 'email', 'encodings', 'enum', 'errno', 'faulthandler',
        'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'formatter', 'fractions', 'ftplib',
        'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob', 'grp', 'gzip',
        'hashlib', 'heapq', 'hmac', 'html', 'http', 'imaplib', 'imghdr', 'imp',
        'importlib', 'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword',
        'lib2to3', 'linecache', 'locale', 'logging', 'lzma', 'mailbox', 'mailcap',
        'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder', 'multiprocessing',
        'netrc', 'nis', 'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev',
        'parser', 'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil',
        'platform', 'plistlib', 'poplib', 'posix', 'posixpath', 'pprint', 'profile',
        'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri',
        'random', 're', 'readline', 'reprlib', 'resource', 'rlcompleter', 'runpy',
        'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil', 'signal',
        'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd', 'sqlite3',
        'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct', 'subprocess',
        'sunau', 'symbol', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny',
        'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap', 'threading',
        'time', 'timeit', 'tkinter', 'token', 'tokenize', 'trace', 'traceback',
        'tracemalloc', 'tty', 'turtle', 'types', 'typing', 'unicodedata', 'unittest',
        'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser',
        'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile',
        'zipimport', 'zlib', '_thread'
    }

    def __init__(self):
        self.dependencies = set()
        self.py_files = []
        self.errors = []

    def analyze_project(self, project_path):
        """分析项目依赖"""
        self.dependencies.clear()
        self.py_files.clear()
        self.errors.clear()

        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in {'venv', 'env', '.venv', '__pycache__', '.git', 'node_modules'}]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.py_files.append(file_path)
                    self._analyze_file(file_path)

        return self.dependencies, self.py_files, self.errors

    def _analyze_file(self, file_path):
        """分析单个Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._add_dependency(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._add_dependency(node.module)

        except SyntaxError as e:
            self.errors.append(f"Syntax error in {file_path}: {str(e)}")
        except Exception as e:
            self.errors.append(f"Failed to analyze {file_path}: {str(e)}")

    def _add_dependency(self, module_name):
        """添加依赖（排除标准库）"""
        top_module = module_name.split('.')[0]

        if top_module not in self.STDLIB_MODULES:
            self.dependencies.add(top_module)

    def get_installed_version(self, package_name):
        """获取已安装包的版本"""
        try:
            return version(package_name)
        except PackageNotFoundError:
            try:
                package_mapping = {
                    'PIL': 'Pillow',
                    'cv2': 'opencv-python',
                    'sklearn': 'scikit-learn',
                    'yaml': 'PyYAML',
                }
                if package_name in package_mapping:
                    return version(package_mapping[package_name])
            except:
                pass
            return None
        except Exception:
            return None


class CyberPunkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("[ DEPENDENCY ANALYZER v2.0 ]")
        self.root.geometry("1100x850")

        self.project_path = ""
        self.analyzer = DependencyAnalyzer()
        self.dependencies = {}
        self.config_file = 'analyzer_config.json'
        self.log_counter = 0

        # 设置赛博朋克主题
        self.setup_cyber_theme()
        self.create_widgets()
        self.load_config()
        self.show_startup_animation()

    def setup_cyber_theme(self):
        """设置赛博朋克主题"""
        self.root.configure(bg=CyberTheme.BG)

        style = ttk.Style()
        style.theme_use('clam')

        # Frame 样式
        style.configure('Cyber.TFrame', background=CyberTheme.BG)
        style.configure('Card.TFrame', background=CyberTheme.BG_LIGHT,
                        relief='flat', borderwidth=0)

        # LabelFrame 样式
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

        # Label 样式
        style.configure('Cyber.TLabel',
                        background=CyberTheme.BG_LIGHT,
                        foreground=CyberTheme.FG)

        # Entry 样式 - 完全无边框
        style.configure('Cyber.TEntry',
                        fieldbackground=CyberTheme.BG_DARK,
                        foreground=CyberTheme.FG,
                        borderwidth=0,
                        relief='flat',
                        insertcolor=CyberTheme.FG,
                        highlightthickness=0)

        # Button 样式
        style.configure('Cyber.TButton',
                        background=CyberTheme.BUTTON_BG,
                        foreground=CyberTheme.FG,
                        borderwidth=0,
                        relief='flat',
                        font=('Courier New', 9, 'bold'))
        style.map('Cyber.TButton',
                  background=[('active', CyberTheme.BG_DARK)],
                  foreground=[('active', CyberTheme.FG_BRIGHT)])

        # Accent Button
        style.configure('Accent.TButton',
                        background=CyberTheme.ACCENT,
                        foreground=CyberTheme.BG,
                        borderwidth=0,
                        relief='flat',
                        font=('Courier New', 9, 'bold'))
        style.map('Accent.TButton',
                  background=[('active', CyberTheme.ACCENT_DARK)])

        # Checkbutton 样式
        style.configure('Cyber.TCheckbutton',
                        background=CyberTheme.BG_LIGHT,
                        foreground=CyberTheme.FG,
                        font=('Courier New', 9))

        # Treeview 样式 - 完全无边框
        style.configure('Cyber.Treeview',
                        background=CyberTheme.BG_DARK,
                        foreground=CyberTheme.FG,
                        fieldbackground=CyberTheme.BG_DARK,
                        borderwidth=0,
                        relief='flat',
                        highlightthickness=0,
                        font=('Courier New', 9))
        style.configure('Cyber.Treeview.Heading',
                        background=CyberTheme.BG_LIGHT,
                        foreground=CyberTheme.FG,
                        borderwidth=0,
                        relief='flat',
                        font=('Courier New', 9, 'bold'))
        style.map('Cyber.Treeview',
                  background=[('selected', CyberTheme.ACCENT)],
                  foreground=[('selected', CyberTheme.BG)])
        style.layout('Cyber.Treeview', [('Cyber.Treeview.treearea', {'sticky': 'nswe'})])

    def create_widgets(self):
        # 主容器
        main_container = ttk.Frame(self.root, style='Cyber.TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ASCII Logo 区域
        logo_frame = tk.Frame(main_container, bg=CyberTheme.BG_DARK,
                              relief='flat', borderwidth=0)
        logo_frame.pack(fill=tk.X, padx=5, pady=5)

        self.logo_label = tk.Label(logo_frame, text=ASCII_LOGO,
                                   bg=CyberTheme.BG_DARK,
                                   fg=CyberTheme.FG,
                                   font=('Courier New', 8, 'bold'),
                                   justify=tk.LEFT,
                                   anchor='w')
        self.logo_label.pack(anchor='w', pady=5)

        # 状态栏
        status_frame = tk.Frame(main_container, bg=CyberTheme.BG_LIGHT,
                                relief='flat', borderwidth=0)
        status_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(status_frame, text="[ STATUS ]",
                 bg=CyberTheme.BG_LIGHT, fg=CyberTheme.FG_BRIGHT,
                 font=('Courier New', 9, 'bold')).pack(side=tk.LEFT, padx=10)

        self.status_label = tk.Label(status_frame, text="● READY",
                                     bg=CyberTheme.BG_LIGHT,
                                     fg=CyberTheme.SUCCESS,
                                     font=('Courier New', 9, 'bold'))
        self.status_label.pack(side=tk.LEFT, padx=10)

        # 项目路径选择
        path_frame = ttk.LabelFrame(main_container, text="[ PROJECT PATH ]",
                                    style='Cyber.TLabelframe', padding="10")
        path_frame.pack(fill=tk.X, padx=5, pady=5)

        path_input = ttk.Frame(path_frame, style='Cyber.TFrame')
        path_input.pack(fill=tk.X, pady=5)

        # 用 tk.Entry 替代 ttk.Entry 以更好地控制边框
        self.path_entry = tk.Entry(path_input, width=70,
                                   bg=CyberTheme.BG_DARK,
                                   fg=CyberTheme.FG,
                                   insertbackground=CyberTheme.FG,
                                   font=('Courier New', 10),
                                   relief='flat',
                                   borderwidth=0,
                                   highlightthickness=0)
        self.path_entry.pack(side=tk.LEFT, padx=(5, 5), pady=5, fill=tk.X, expand=True)

        ttk.Button(path_input, text="[ BROWSE ]",
                   command=self.browse_directory,
                   style='Cyber.TButton').pack(side=tk.LEFT, padx=2)

        ttk.Button(path_input, text="[ ANALYZE ]",
                   command=self.analyze_project,
                   style='Accent.TButton').pack(side=tk.LEFT, padx=2)

        # 统计信息
        self.stats_label = tk.Label(path_frame, text=">>> Waiting for project selection...",
                                    bg=CyberTheme.BG_LIGHT,
                                    fg=CyberTheme.FG_DIM,
                                    font=('Courier New', 9),
                                    anchor='w')
        self.stats_label.pack(fill=tk.X, pady=2)

        # 选项区域
        options_frame = ttk.LabelFrame(main_container, text="[ OPTIONS ]",
                                       style='Cyber.TLabelframe', padding="10")
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        opts_container = ttk.Frame(options_frame, style='Cyber.TFrame')
        opts_container.pack(fill=tk.X)

        self.include_version_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_container, text="Include Version",
                        variable=self.include_version_var,
                        style='Cyber.TCheckbutton').pack(side=tk.LEFT, padx=10)

        self.merge_existing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_container, text="Merge Existing",
                        variable=self.merge_existing_var,
                        style='Cyber.TCheckbutton').pack(side=tk.LEFT, padx=10)

        self.backup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_container, text="Backup Old File",
                        variable=self.backup_var,
                        style='Cyber.TCheckbutton').pack(side=tk.LEFT, padx=10)

        self.include_pyinstaller_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_container, text="Include PyInstaller",
                        variable=self.include_pyinstaller_var,
                        style='Cyber.TCheckbutton').pack(side=tk.LEFT, padx=10)

        # 依赖列表
        deps_frame = ttk.LabelFrame(main_container, text="[ DEPENDENCIES DETECTED ]",
                                    style='Cyber.TLabelframe', padding="10")
        deps_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 搜索和统计
        search_frame = ttk.Frame(deps_frame, style='Cyber.TFrame')
        search_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Label(search_frame, text=">> SEARCH:",
                 bg=CyberTheme.BG_LIGHT, fg=CyberTheme.FG,
                 font=('Courier New', 9)).pack(side=tk.LEFT, padx=5)

        # 用 tk.Entry 替代 ttk.Entry
        self.search_entry = tk.Entry(search_frame, width=40,
                                     bg=CyberTheme.BG_DARK,
                                     fg=CyberTheme.FG,
                                     insertbackground=CyberTheme.FG,
                                     font=('Courier New', 9),
                                     relief='flat',
                                     borderwidth=0,
                                     highlightthickness=0)
        self.search_entry.pack(side=tk.LEFT, padx=(5, 5), pady=5)
        self.search_entry.bind('<KeyRelease>', self.filter_dependencies)

        ttk.Button(search_frame, text="[ CLEAR ]",
                   command=lambda: self.search_entry.delete(0, tk.END),
                   style='Cyber.TButton').pack(side=tk.LEFT, padx=2)

        self.dep_count_label = tk.Label(search_frame, text="TOTAL: 0",
                                        bg=CyberTheme.BG_LIGHT,
                                        fg=CyberTheme.FG_BRIGHT,
                                        font=('Courier New', 9, 'bold'))
        self.dep_count_label.pack(side=tk.RIGHT, padx=10)

        # Treeview
        tree_container = tk.Frame(deps_frame, bg=CyberTheme.BG_DARK)
        tree_container.pack(fill=tk.BOTH, expand=True)

        columns = ('Version', 'Status')
        self.tree = ttk.Treeview(tree_container, columns=columns,
                                 show='tree headings', height=12,
                                 style='Cyber.Treeview')
        self.tree.heading('#0', text='PACKAGE')
        self.tree.heading('Version', text='VERSION')
        self.tree.heading('Status', text='STATUS')

        self.tree.column('#0', width=300)
        self.tree.column('Version', width=150)
        self.tree.column('Status', width=250)

        vsb = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew', padx=0, pady=0)
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # 操作按钮
        action_frame = ttk.Frame(main_container, style='Cyber.TFrame', padding="5")
        action_frame.pack(fill=tk.X, padx=5)

        ttk.Button(action_frame, text="[ GENERATE REQUIREMENTS.TXT ]",
                   command=self.generate_requirements,
                   style='Accent.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(action_frame, text="[ COPY TO CLIPBOARD ]",
                   command=self.copy_to_clipboard,
                   style='Cyber.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(action_frame, text="[ OPEN PROJECT DIR ]",
                   command=self.open_project_dir,
                   style='Cyber.TButton').pack(side=tk.LEFT, padx=5)

        # 系统日志
        log_frame = ttk.LabelFrame(main_container, text="[ SYSTEM LOG ]",
                                   style='Cyber.TLabelframe', padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        log_container = tk.Frame(log_frame, bg=CyberTheme.BG_DARK,
                                 relief='flat', borderwidth=0)
        log_container.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_container, height=8,
                                                  bg=CyberTheme.BG_DARK,
                                                  fg=CyberTheme.FG,
                                                  insertbackground=CyberTheme.FG,
                                                  state=tk.DISABLED,
                                                  font=('Courier New', 9),
                                                  relief='flat',
                                                  borderwidth=0)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    def show_startup_animation(self):
        """显示启动动画"""
        self.log("[>] System initialized", CyberTheme.SUCCESS)
        self.log("[>] Loading modules...", CyberTheme.FG)
        self.log("[>] Dependency Analyzer ready", CyberTheme.SUCCESS)
        self.log("[>] Awaiting user input...", CyberTheme.FG_DIM)

    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    last_path = config.get('last_project_path', '')
                    if last_path and os.path.exists(last_path):
                        self.path_entry.insert(0, last_path)
                        self.log("[+] Configuration loaded", CyberTheme.SUCCESS)
        except Exception as e:
            self.log(f"[!] Config load failed: {e}", CyberTheme.WARNING)

    def save_config(self):
        """保存配置"""
        try:
            config = {'last_project_path': self.project_path}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log(f"[!] Config save failed: {e}", CyberTheme.WARNING)

    def browse_directory(self):
        """浏览选择项目目录"""
        directory = filedialog.askdirectory(title="Select Python Project")
        if directory:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, directory)
            self.project_path = directory
            self.log(f"[+] Project selected: {directory}", CyberTheme.FG_BRIGHT)

    def analyze_project(self):
        """分析项目"""
        self.project_path = self.path_entry.get().strip()

        if not self.project_path:
            messagebox.showerror("ERROR", "Please select a project directory")
            return

        if not os.path.exists(self.project_path):
            messagebox.showerror("ERROR", "Project directory does not exist")
            return

        self.log(f"[>] Starting analysis: {self.project_path}", CyberTheme.FG_BRIGHT)
        self.status_label.config(text="● ANALYZING...", fg=CyberTheme.WARNING)
        self.save_config()

        threading.Thread(target=self._analyze_thread, daemon=True).start()

    def _analyze_thread(self):
        """分析线程"""
        try:
            self.root.after(0, self.log, "[>] Scanning Python files...", CyberTheme.FG)
            dependencies, py_files, errors = self.analyzer.analyze_project(self.project_path)

            self.root.after(0, self.log, f"[+] Found {len(py_files)} Python files", CyberTheme.SUCCESS)

            # 获取版本信息
            self.dependencies = {}
            for dep in dependencies:
                version = self.analyzer.get_installed_version(dep)
                self.dependencies[dep] = version

            self.root.after(0, self._update_analysis_results, py_files, errors)
        except Exception as e:
            self.root.after(0, self.log, f"[!] Analysis failed: {str(e)}", CyberTheme.ERROR)
            self.root.after(0, self.status_label.config, {'text': "● ERROR", 'fg': CyberTheme.ERROR})

    def _update_analysis_results(self, py_files, errors):
        """更新分析结果"""
        self.tree.delete(*self.tree.get_children())

        self.log(f"[+] Analysis complete!", CyberTheme.SUCCESS)
        self.log(f"    Files scanned: {len(py_files)}", CyberTheme.FG)
        self.log(f"    Dependencies found: {len(self.dependencies)}", CyberTheme.FG)

        if errors:
            self.log(f"[!] Errors encountered: {len(errors)}", CyberTheme.WARNING)
            for error in errors[:3]:
                self.log(f"    {error}", CyberTheme.FG_DIM)

        self.stats_label.config(
            text=f">>> FILES: {len(py_files)} | DEPENDENCIES: {len(self.dependencies)} | ERRORS: {len(errors)}")
        self.dep_count_label.config(text=f"TOTAL: {len(self.dependencies)}")
        self.status_label.config(text="● COMPLETE", fg=CyberTheme.SUCCESS)

        # 更新树视图
        for package, version in sorted(self.dependencies.items()):
            if version:
                status = f"[✓] INSTALLED ({version})"
                version_text = version
            else:
                status = "[!] NOT INSTALLED"
                version_text = "N/A"

            self.tree.insert('', tk.END, text=package,
                             values=(version_text, status))

    def filter_dependencies(self, event=None):
        """搜索过滤依赖"""
        search_text = self.search_entry.get().lower()

        for item in self.tree.get_children():
            text = self.tree.item(item)['text'].lower()
            if search_text in text:
                self.tree.reattach(item, '', 'end')
            else:
                self.tree.detach(item)

    def generate_requirements(self):
        """生成 requirements.txt"""
        if not self.dependencies:
            messagebox.showwarning("WARNING", "Please analyze project first")
            return

        self.log("[>] Generating requirements.txt...", CyberTheme.FG_BRIGHT)

        requirements_path = os.path.join(self.project_path, 'requirements.txt')
        existing_requirements = {}

        # 读取现有文件
        if os.path.exists(requirements_path) and self.merge_existing_var.get():
            try:
                with open(requirements_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '==' in line:
                                pkg, ver = line.split('==', 1)
                                existing_requirements[pkg.strip()] = ver.strip()
                            else:
                                existing_requirements[line] = None
                self.log(f"[+] Loaded existing requirements: {len(existing_requirements)} packages", CyberTheme.SUCCESS)
            except Exception as e:
                self.log(f"[!] Failed to load existing file: {e}", CyberTheme.WARNING)

        # 备份
        if os.path.exists(requirements_path) and self.backup_var.get():
            backup_path = requirements_path + f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            try:
                import shutil
                shutil.copy2(requirements_path, backup_path)
                self.log(f"[+] Backup created: {os.path.basename(backup_path)}", CyberTheme.SUCCESS)
            except Exception as e:
                self.log(f"[!] Backup failed: {e}", CyberTheme.WARNING)

        # 合并依赖
        all_requirements = existing_requirements.copy()
        new_count = 0
        for package, version in self.dependencies.items():
            if package not in all_requirements:
                all_requirements[package] = version
                new_count += 1

        # 添加 PyInstaller
        if self.include_pyinstaller_var.get():
            if 'pyinstaller' not in all_requirements:
                pyinstaller_version = self.analyzer.get_installed_version('pyinstaller')
                all_requirements['pyinstaller'] = pyinstaller_version
                self.log(f"[+] Added PyInstaller", CyberTheme.SUCCESS)
                new_count += 1

        # 生成文件
        try:
            with open(requirements_path, 'w', encoding='utf-8') as f:
                f.write(f"# Generated by Dependency Analyzer v2.0\n")
                f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Project: {self.project_path}\n\n")

                for package in sorted(all_requirements.keys()):
                    version = all_requirements[package]
                    if self.include_version_var.get() and version:
                        f.write(f"{package}=={version}\n")
                    else:
                        f.write(f"{package}\n")

            self.log(f"[+] SUCCESS! Generated requirements.txt", CyberTheme.SUCCESS)
            self.log(f"    Location: {requirements_path}", CyberTheme.FG)
            self.log(f"    Total packages: {len(all_requirements)}", CyberTheme.FG)
            self.log(f"    New packages: {new_count}", CyberTheme.FG)

            messagebox.showinfo("SUCCESS",
                                f"requirements.txt generated!\n\n"
                                f"Total: {len(all_requirements)} packages\n"
                                f"New: {new_count} packages")

        except Exception as e:
            self.log(f"[!] FAILED: {str(e)}", CyberTheme.ERROR)
            messagebox.showerror("ERROR", f"Generation failed:\n{str(e)}")

    def copy_to_clipboard(self):
        """复制到剪贴板"""
        if not self.dependencies:
            messagebox.showwarning("WARNING", "No dependencies to copy")
            return

        content = ""
        for package in sorted(self.dependencies.keys()):
            version = self.dependencies[package]
            if self.include_version_var.get() and version:
                content += f"{package}=={version}\n"
            else:
                content += f"{package}\n"

        if self.include_pyinstaller_var.get():
            pyinstaller_version = self.analyzer.get_installed_version('pyinstaller')
            if self.include_version_var.get() and pyinstaller_version:
                content += f"pyinstaller=={pyinstaller_version}\n"
            else:
                content += "pyinstaller\n"

        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.log("[+] Copied to clipboard", CyberTheme.SUCCESS)
        messagebox.showinfo("SUCCESS", "Copied to clipboard!")

    def open_project_dir(self):
        """打开项目目录"""
        if not self.project_path or not os.path.exists(self.project_path):
            messagebox.showwarning("WARNING", "Project directory does not exist")
            return

        try:
            if sys.platform == 'win32':
                os.startfile(self.project_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', self.project_path])
            else:
                subprocess.run(['xdg-open', self.project_path])
            self.log("[+] Opened project directory", CyberTheme.SUCCESS)
        except Exception as e:
            self.log(f"[!] Failed to open directory: {e}", CyberTheme.ERROR)

    def log(self, message, color=None):
        """添加日志"""
        if color is None:
            color = CyberTheme.FG

        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime('%H:%M:%S')

        # 添加带颜色的日志
        tag_name = f"color_{self.log_counter}"
        self.log_counter += 1

        self.log_text.tag_config(tag_name, foreground=color)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag_name)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)


def main():
    root = tk.Tk()

    # 设置窗口图标
    try:
        root.iconbitmap('icon.ico')
    except:
        pass

    app = CyberPunkGUI(root)

    # 窗口居中
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.mainloop()


if __name__ == '__main__':
    main()