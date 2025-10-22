#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目脚手架生成器 - 赛博朋克终端风格
v3.1 - 独立Scan结果显示
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional


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


# ==================== 智能模板解析器 ====================
class IntelligentTemplateParser:
    """智能模板解析器 - 高容错率"""

    # 文件扩展名白名单
    KNOWN_EXTENSIONS = {
        '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c', '.h', '.hpp',
        '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.sh', '.bash',
        '.html', '.css', '.scss', '.sass', '.less', '.xml', '.json', '.yaml', '.yml',
        '.md', '.txt', '.sql', '.env', '.toml', '.ini', '.cfg', '.conf',
        '.vue', '.svelte', '.dart', '.r', '.lua', '.perl', '.pl'
    }

    # 无扩展名的特殊文件
    SPECIAL_FILES = {
        'Makefile', 'Dockerfile', 'Jenkinsfile', 'Vagrantfile',
        'README', 'LICENSE', 'CHANGELOG', 'AUTHORS', 'CONTRIBUTING',
        '.gitignore', '.dockerignore', '.eslintrc', '.prettierrc',
        '.babelrc', '.editorconfig', '.env', '.env.example'
    }

    @classmethod
    def parse(cls, content: str) -> Dict[str, str]:
        """
        智能解析模板内容
        策略：
        1. 识别所有可能的文件头（多种格式）
        2. 使用文件扩展名验证
        3. 分析代码块边界
        4. 智能处理注释和文档字符串
        """
        templates = {}
        lines = content.split('\n')

        # 第一步：扫描并标记所有可能的文件头
        file_headers = cls._scan_file_headers(lines)

        # 第二步：提取每个文件的代码块
        for i, (line_num, filepath, confidence) in enumerate(file_headers):
            # 确定代码块的结束位置
            next_line = file_headers[i + 1][0] if i + 1 < len(file_headers) else len(lines)

            # 提取代码内容
            code_lines = lines[line_num + 1:next_line]
            code = cls._extract_code(code_lines, filepath)

            if code.strip():
                templates[filepath] = code

        return templates

    @classmethod
    def _scan_file_headers(cls, lines: List[str]) -> List[Tuple[int, str, float]]:
        """
        扫描所有可能的文件头
        返回: [(行号, 文件路径, 置信度)]
        """
        headers = []

        for i, line in enumerate(lines):
            result = cls._analyze_line_as_header(line, i, lines)
            if result:
                filepath, confidence = result
                headers.append((i, filepath, confidence))

        # 按行号排序
        headers.sort(key=lambda x: x[0])

        # 过滤低置信度的重复项
        return cls._filter_headers(headers)

    @classmethod
    def _analyze_line_as_header(cls, line: str, line_num: int, all_lines: List[str]) -> Optional[Tuple[str, float]]:
        """
        分析一行是否为文件头，返回 (文件路径, 置信度)
        置信度 0-1，1为最确定
        """
        stripped = line.strip()

        # 空行或纯代码行
        if not stripped or not stripped.startswith('#'):
            return None

        # 移除开头的 # 和空格
        content = re.sub(r'^#+\s*', '', stripped)

        # 情况1：标准分隔符格式 # ==== filename ====
        match = re.match(r'^=+\s*(.+?)\s*=+$', content)
        if match:
            filepath = match.group(1).strip()
            if cls._is_valid_filepath(filepath):
                return (filepath, 0.95)

        # 情况2：带横线分隔 # filename ----
        match = re.match(r'^(.+?)\s+[-=]{3,}$', content)
        if match:
            filepath = match.group(1).strip()
            if cls._is_valid_filepath(filepath):
                return (filepath, 0.90)

        # 情况3：纯文件路径 # path/to/file.ext
        if cls._is_valid_filepath(content):
            # 检查上下文提高置信度
            confidence = 0.80

            # 如果下一行是空行或注释，提高置信度
            if line_num + 1 < len(all_lines):
                next_line = all_lines[line_num + 1].strip()
                if not next_line or next_line.startswith('"""') or next_line.startswith("'''"):
                    confidence = 0.85

            # 如果上一行是分隔符，提高置信度
            if line_num > 0:
                prev_line = all_lines[line_num - 1].strip()
                if re.match(r'^#+\s*[-=]{10,}\s*$', prev_line):
                    confidence = 0.90

            return (content, confidence)

        # 情况4：可能是文件路径但格式不规范
        # 尝试提取路径模式
        path_pattern = r'([a-zA-Z0-9_\-./\\]+(?:\.[a-zA-Z0-9]+)?)'
        matches = re.findall(path_pattern, content)

        for match in matches:
            if cls._is_valid_filepath(match):
                # 如果找到的路径占据了大部分内容，可能是文件头
                if len(match) / max(len(content), 1) > 0.5:
                    return (match, 0.60)

        return None

    @classmethod
    def _is_valid_filepath(cls, path: str) -> bool:
        """判断是否为有效的文件路径"""
        if not path or len(path) > 200:
            return False

        # 检查是否包含无效字符
        invalid_chars = set('<>"|?*')
        if any(c in path for c in invalid_chars):
            return False

        # 特殊文件名（无扩展名）
        filename = path.split('/')[-1].split('\\')[-1]
        if filename in cls.SPECIAL_FILES:
            return True

        # 检查文件扩展名
        if '.' in filename:
            ext = '.' + filename.split('.')[-1].lower()
            if ext in cls.KNOWN_EXTENSIONS:
                return True

        # 如果包含路径分隔符，可能是目录+文件
        if '/' in path or '\\' in path:
            # 检查是否像一个合理的路径
            parts = re.split(r'[/\\]', path)
            if len(parts) >= 2 and all(p.strip() for p in parts):
                return True

        return False

    @classmethod
    def _filter_headers(cls, headers: List[Tuple[int, str, float]]) -> List[Tuple[int, str, float]]:
        """过滤掉低置信度或重复的文件头"""
        if not headers:
            return []

        filtered = []
        seen_paths = set()

        for line_num, filepath, confidence in headers:
            # 跳过置信度过低的
            if confidence < 0.55:
                continue

            # 标准化路径
            normalized = filepath.replace('\\', '/')

            # 如果已经见过这个路径，保留置信度更高的
            if normalized in seen_paths:
                # 检查是否需要替换
                for i, (_, existing_path, existing_conf) in enumerate(filtered):
                    if existing_path.replace('\\', '/') == normalized:
                        if confidence > existing_conf:
                            filtered[i] = (line_num, filepath, confidence)
                        break
            else:
                filtered.append((line_num, filepath, confidence))
                seen_paths.add(normalized)

        return sorted(filtered, key=lambda x: x[0])

    @classmethod
    def _extract_code(cls, lines: List[str], filepath: str) -> str:
        """
        从行列表中提取代码内容
        智能处理：
        - 移除文件头分隔符
        - 保留文档字符串
        - 移除尾部的分隔符
        """
        if not lines:
            return ""

        code_lines = []
        in_docstring = False
        docstring_char = None
        skip_next_empty = False

        for line in lines:
            stripped = line.strip()

            # 跳过明显的分隔符行
            if re.match(r'^#+\s*[-=]{10,}\s*$', stripped):
                skip_next_empty = True
                continue

            # 跳过 YAML 文档分隔符
            if stripped == '---':
                skip_next_empty = True
                continue

            # 跳过分隔符后的第一个空行
            if skip_next_empty and not stripped:
                skip_next_empty = False
                continue

            skip_next_empty = False

            # 检测文档字符串
            if '"""' in line or "'''" in line:
                if not in_docstring:
                    in_docstring = True
                    docstring_char = '"""' if '"""' in line else "'''"
                elif docstring_char in line:
                    in_docstring = False

            code_lines.append(line)

        # 移除开头和结尾的空行
        while code_lines and not code_lines[0].strip():
            code_lines.pop(0)
        while code_lines and not code_lines[-1].strip():
            code_lines.pop()

        return '\n'.join(code_lines)

    @classmethod
    def validate_and_report(cls, content: str) -> Dict:
        """验证并生成详细报告"""
        lines = content.split('\n')
        headers = cls._scan_file_headers(lines)
        templates = cls.parse(content)

        report = {
            'success': True,
            'file_count': len(templates),
            'files': [],
            'warnings': [],
            'low_confidence': []
        }

        for line_num, filepath, confidence in headers:
            file_info = {
                'path': filepath,
                'line': line_num + 1,
                'confidence': f"{confidence * 100:.0f}%",
                'parsed': filepath in templates
            }

            if filepath in templates:
                code = templates[filepath]
                file_info['lines'] = len(code.split('\n'))
                file_info['size'] = len(code)
                file_info['preview'] = code[:80].replace('\n', ' ')

            report['files'].append(file_info)

            # 低置信度警告
            if confidence < 0.75:
                report['low_confidence'].append({
                    'path': filepath,
                    'confidence': confidence,
                    'line': line_num + 1
                })

        # 检查未解析的可疑行
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#') and '/' in stripped:
                # 可能是文件路径但未被识别
                found = any(h[0] == i for h in headers)
                if not found:
                    # 尝试提取可能的路径
                    potential = re.findall(r'[a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+', stripped)
                    if potential:
                        report['warnings'].append({
                            'line': i + 1,
                            'content': line[:80],
                            'suggestion': f"Possible file path not detected: {potential[0]}"
                        })

        return report


# ==================== 代码模板管理器 ====================
class CodeTemplateManager:
    @staticmethod
    def parse_template_file(content):
        """使用智能解析器"""
        return IntelligentTemplateParser.parse(content)

    @staticmethod
    def validate_and_preview(content):
        """验证并预览模板"""
        return IntelligentTemplateParser.validate_and_report(content)

    @staticmethod
    def match_files(template_paths, project_files):
        """
        智能匹配模板文件和项目文件
        策略：
        1. 完整路径匹配（忽略大小写和路径分隔符）
        2. 文件名精确匹配
        3. 部分路径匹配（最后N层目录）
        4. 相对路径匹配
        """
        matches = []
        used_templates = set()  # 防止一个模板匹配多个文件
        used_projects = set()  # 防止一个项目文件被多个模板匹配

        # 标准化路径的辅助函数
        def normalize_path(path):
            return path.replace('\\', '/').lower().strip('/')

        # 构建标准化映射
        template_map = {normalize_path(tp): tp for tp in template_paths}
        project_map = {normalize_path(pf): pf for pf in project_files}

        # 策略1: 完整路径精确匹配
        for template_norm, template_orig in template_map.items():
            for project_norm, project_orig in project_map.items():
                if template_norm == project_norm:
                    if template_orig not in used_templates and project_orig not in used_projects:
                        matches.append((template_orig, project_orig))
                        used_templates.add(template_orig)
                        used_projects.add(project_orig)
                        break

        # 策略1.5: 智能根目录匹配（去掉第一层目录后精确匹配）⭐ 新增
        # 解决模板路径带根目录前缀（如 pytools_scaffolder/main.py）而结构文件不带的问题
        for template_orig in template_paths:
            if template_orig in used_templates:
                continue

            template_norm = normalize_path(template_orig)
            template_parts = template_norm.split('/')

            # 如果模板路径有多层，尝试去掉第一层（根目录）后匹配
            if len(template_parts) > 1:
                template_without_root = '/'.join(template_parts[1:])

                for project_orig in project_files:
                    if project_orig in used_projects:
                        continue

                    project_norm = normalize_path(project_orig)

                    # 精确匹配去掉根目录后的路径
                    if template_without_root == project_norm:
                        matches.append((template_orig, project_orig))
                        used_templates.add(template_orig)
                        used_projects.add(project_orig)
                        break

        # 策略2: 文件名完全匹配（处理路径深度不同的情况）
        for template_orig in template_paths:
            if template_orig in used_templates:
                continue

            template_norm = normalize_path(template_orig)
            template_filename = template_norm.split('/')[-1]

            for project_orig in project_files:
                if project_orig in used_projects:
                    continue

                project_norm = normalize_path(project_orig)
                project_filename = project_norm.split('/')[-1]

                # 文件名完全相同
                if template_filename == project_filename:
                    matches.append((template_orig, project_orig))
                    used_templates.add(template_orig)
                    used_projects.add(project_orig)
                    break

        # 策略3: 部分路径匹配（最后2-3层目录相同）
        for template_orig in template_paths:
            if template_orig in used_templates:
                continue

            template_norm = normalize_path(template_orig)
            template_parts = template_norm.split('/')

            for project_orig in project_files:
                if project_orig in used_projects:
                    continue

                project_norm = normalize_path(project_orig)
                project_parts = project_norm.split('/')

                # 尝试匹配最后2层
                if len(template_parts) >= 2 and len(project_parts) >= 2:
                    if template_parts[-2:] == project_parts[-2:]:
                        matches.append((template_orig, project_orig))
                        used_templates.add(template_orig)
                        used_projects.add(project_orig)
                        break

        # 策略4: 模糊匹配（模板路径是项目路径的子串）
        for template_orig in template_paths:
            if template_orig in used_templates:
                continue

            template_norm = normalize_path(template_orig)

            for project_orig in project_files:
                if project_orig in used_projects:
                    continue

                project_norm = normalize_path(project_orig)

                # 检查模板路径是否在项目路径中
                if template_norm in project_norm or project_norm.endswith(template_norm):
                    matches.append((template_orig, project_orig))
                    used_templates.add(template_orig)
                    used_projects.add(project_orig)
                    break

        return matches

    @staticmethod
    def backup_file(file_path):
        """备份文件内容"""
        try:
            if Path(file_path).exists():
                return Path(file_path).read_text(encoding='utf-8')
        except:
            pass
        return None

    @staticmethod
    def write_file(file_path, content):
        """写入文件"""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(file_path).write_text(content, encoding='utf-8')
            return True
        except Exception as e:
            print(f"写入失败 {file_path}: {e}")
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
║   PROJECT SCAFFOLDER v3.1                        ║
║   [ INTELLIGENT PARSING SYSTEM ]                 ║
╚═══════════════════════════════════════════════════╝
"""


# ==================== 主应用 ====================
class ScaffolderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("[ PROJECT SCAFFOLDER v3.1 ]")
        self.root.configure(bg=CyberTheme.BG)
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)

        self.arrow_animation_speed = 300
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
        self.scan_result_text = None  # 新增：scan结果文本框
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

        arrow_frame = tk.Frame(content_frame, bg=CyberTheme.BG_DARK)
        arrow_frame.pack(side=tk.LEFT, padx=(5, 10))

        for i in range(5):
            label = tk.Label(arrow_frame, text='>', bg=CyberTheme.BG_DARK, fg=CyberTheme.FG,
                             font=('Courier New', 12, 'bold'))
            label.pack(side=tk.LEFT)
            self.arrow_labels.append(label)

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

        # Tab 1: PROJECT STRUCTURE (用户手动输入)
        tab1 = ttk.Frame(self.notebook, style='Cyber.TFrame')
        self.notebook.add(tab1, text='[ PROJECT STRUCTURE ]')
        self.tip_label = tk.Label(tab1,
                                  text=">>> Supports tree, emoji, plain text formats | Manual input for generation",
                                  bg=CyberTheme.BG_LIGHT, fg=CyberTheme.FG_DIM, font=('Courier New', 8), anchor='w')
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

        # Tab 2: SCAN RESULT (扫描结果显示，只读)
        tab_scan = ttk.Frame(self.notebook, style='Cyber.TFrame')
        self.notebook.add(tab_scan, text='[ SCAN RESULT ]')
        scan_tip = tk.Label(tab_scan,
                            text=">>> Scanned directory structure | Read-only | Use 'Copy to Structure' to edit",
                            bg=CyberTheme.BG_LIGHT, fg=CyberTheme.ACCENT, font=('Courier New', 8), anchor='w')
        scan_tip.pack(fill=tk.X, pady=(8, 5), padx=8)

        frame_scan = tk.Frame(tab_scan, bg=CyberTheme.BG_LIGHT)
        frame_scan.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        scroll_scan = tk.Scrollbar(frame_scan)
        scroll_scan.pack(side=tk.RIGHT, fill=tk.Y)
        self.scan_result_text = tk.Text(frame_scan, bg=CyberTheme.BG_DARK, fg=CyberTheme.ACCENT,
                                        insertbackground=CyberTheme.FG, font=('Courier New', 9),
                                        yscrollcommand=scroll_scan.set, relief='flat', state='disabled')
        self.scan_result_text.pack(fill=tk.BOTH, expand=True)
        scroll_scan.config(command=self.scan_result_text.yview)

        # Scan结果tab的按钮区
        scan_btn_frame = tk.Frame(tab_scan, bg=CyberTheme.BG_LIGHT)
        scan_btn_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Button(scan_btn_frame, text="[ COPY TO STRUCTURE ]", style='Accent.TButton',
                   command=self.copy_scan_to_structure).pack(side=tk.LEFT, padx=5)
        ttk.Button(scan_btn_frame, text="[ CLEAR SCAN ]", style='Cyber.TButton',
                   command=self.clear_scan_result).pack(side=tk.LEFT, padx=5)

        # Tab 3: CODE TEMPLATES
        tab2 = ttk.Frame(self.notebook, style='Cyber.TFrame')
        self.notebook.add(tab2, text='[ CODE TEMPLATES ]')

        tip_frame = tk.Frame(tab2, bg=CyberTheme.BG_LIGHT)
        tip_frame.pack(fill=tk.X, pady=(8, 5), padx=8)

        tk.Label(tip_frame, text=">>> Intelligent Parser - Paste any format!", bg=CyberTheme.BG_LIGHT,
                 fg=CyberTheme.ACCENT, font=('Courier New', 9, 'bold'), anchor='w').pack(fill=tk.X)
        tk.Label(tip_frame, text="    ✓ Auto-detects file paths  ✓ Multiple formats  ✓ High fault tolerance",
                 bg=CyberTheme.BG_LIGHT, fg=CyberTheme.FG_DIM, font=('Courier New', 8), anchor='w').pack(fill=tk.X)

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
        ttk.Button(left, text="[ VALIDATE TEMPLATE ]", style='Cyber.TButton', command=self.validate_template).pack(
            side=tk.LEFT, padx=5)
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
        tk.Label(footer, text="© 2025 Kang Zhang | v3.1.0 | Separate Scan Display", bg=CyberTheme.BG_DARK,
                 fg=CyberTheme.FG_DIM, font=('Courier New', 7)).pack(fill=tk.BOTH, expand=True)

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
        self.root.after(self.arrow_animation_speed, self.animate_arrows)

    def browse_path(self):
        path = filedialog.askdirectory(initialdir=self.base_path.get())
        if path:
            self.base_path.set(path)

    def on_mode_change(self):
        if self.mode.get() == "generate":
            self.action_btn.config(text="[ QUICK CREATE ]", command=self.create_project)
            self.tip_label.config(text=">>> Paste structure to create files | Manual input mode")
        else:
            self.action_btn.config(text="[ SCAN DIRECTORY ]", command=self.scan_directory)
            self.tip_label.config(text=">>> Click SCAN to generate structure | Results in SCAN RESULT tab")

    def copy_scan_to_structure(self):
        """将扫描结果复制到结构编辑区"""
        scan_content = self.scan_result_text.get('1.0', tk.END).strip()
        if not scan_content:
            messagebox.showwarning("[ WARNING ]", "No scan result to copy")
            return

        if self.structure_text.get('1.0', tk.END).strip():
            if not messagebox.askyesno("[ CONFIRM ]", "Replace current structure with scan result?"):
                return

        self.structure_text.delete('1.0', tk.END)
        self.structure_text.insert('1.0', scan_content)
        self.notebook.select(0)  # 切换到 PROJECT STRUCTURE tab
        messagebox.showinfo("[ SUCCESS ]", "Scan result copied to PROJECT STRUCTURE tab")

    def clear_scan_result(self):
        """清空扫描结果"""
        self.scan_result_text.config(state='normal')
        self.scan_result_text.delete('1.0', tk.END)
        self.scan_result_text.config(state='disabled')

    def validate_template(self):
        """验证模板格式 - 使用智能解析器"""
        template_content = self.template_text.get('1.0', tk.END).strip()
        if not template_content:
            messagebox.showwarning("[ WARNING ]", "No template content to validate")
            return

        try:
            report = CodeTemplateManager.validate_and_preview(template_content)

            # 创建验证报告窗口
            win = tk.Toplevel(self.root)
            win.title("[ INTELLIGENT PARSING REPORT ]")
            win.configure(bg=CyberTheme.BG)
            win.geometry("900x700")

            frame = tk.Frame(win, bg=CyberTheme.BG)
            frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

            # 标题
            title_frame = tk.Frame(frame, bg=CyberTheme.BG)
            title_frame.pack(fill=tk.X, pady=(0, 15))

            tk.Label(title_frame, text=">>> INTELLIGENT PARSING REPORT", bg=CyberTheme.BG, fg=CyberTheme.FG,
                     font=('Courier New', 12, 'bold'), anchor='w').pack(side=tk.LEFT)

            # 统计信息
            stats_frame = tk.Frame(frame, bg=CyberTheme.BG_DARK, highlightthickness=1,
                                   highlightbackground=CyberTheme.BORDER)
            stats_frame.pack(fill=tk.X, pady=(0, 15))

            status_color = CyberTheme.SUCCESS if report['file_count'] > 0 else CyberTheme.ERROR

            stats_text = f"""
  ✓ Detected Files: {report['file_count']}
  ⚠ Low Confidence: {len(report['low_confidence'])}
  ⚡ Warnings: {len(report['warnings'])}
            """

            tk.Label(stats_frame, text=stats_text, bg=CyberTheme.BG_DARK, fg=status_color,
                     font=('Courier New', 10, 'bold'), justify=tk.LEFT, anchor='w').pack(
                fill=tk.X, padx=15, pady=10)

            # 创建Notebook显示详细信息
            nb = ttk.Notebook(frame, style='Cyber.TNotebook')
            nb.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

            # Tab 1: 文件列表
            files_tab = ttk.Frame(nb, style='Cyber.TFrame')
            nb.add(files_tab, text='[ FILES ]')

            files_frame = tk.Frame(files_tab, bg=CyberTheme.BG_DARK, highlightthickness=1,
                                   highlightbackground=CyberTheme.BORDER)
            files_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            scroll1 = tk.Scrollbar(files_frame)
            scroll1.pack(side=tk.RIGHT, fill=tk.Y)

            files_text = tk.Text(files_frame, bg=CyberTheme.BG_DARK, fg=CyberTheme.FG,
                                 font=('Courier New', 9), yscrollcommand=scroll1.set, wrap='none')
            files_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            scroll1.config(command=files_text.yview)

            if report['file_count'] > 0:
                for file_info in report['files']:
                    conf_color = CyberTheme.SUCCESS if float(
                        file_info['confidence'].strip('%')) >= 75 else CyberTheme.WARNING

                    files_text.insert(tk.END, f"📄 {file_info['path']}\n", 'filename')
                    files_text.insert(tk.END, f"   Line: {file_info['line']} | ", 'info')
                    files_text.insert(tk.END, f"Confidence: {file_info['confidence']}", 'confidence')

                    if file_info['parsed']:
                        files_text.insert(tk.END, f" | Lines: {file_info['lines']} | Size: {file_info['size']}B\n",
                                          'info')
                        if 'preview' in file_info:
                            files_text.insert(tk.END, f"   Preview: {file_info['preview']}\n\n", 'preview')
                    else:
                        files_text.insert(tk.END, " | NOT PARSED\n\n", 'error')

                files_text.tag_config('filename', foreground=CyberTheme.ACCENT, font=('Courier New', 9, 'bold'))
                files_text.tag_config('info', foreground=CyberTheme.FG_DIM)
                files_text.tag_config('confidence', foreground=conf_color)
                files_text.tag_config('preview', foreground=CyberTheme.FG)
                files_text.tag_config('error', foreground=CyberTheme.ERROR)
            else:
                files_text.insert(tk.END, "❌ No files detected!\n\n")
                files_text.insert(tk.END, "The intelligent parser supports:\n")
                files_text.insert(tk.END, "  • Any format with # + filepath\n")
                files_text.insert(tk.END, "  • Separators like ==== or ----\n")
                files_text.insert(tk.END, "  • Automatic path detection\n")

            files_text.config(state='disabled')

            # Tab 2: 警告
            if report['warnings'] or report['low_confidence']:
                warnings_tab = ttk.Frame(nb, style='Cyber.TFrame')
                nb.add(warnings_tab, text='[ WARNINGS ]')

                warn_frame = tk.Frame(warnings_tab, bg=CyberTheme.BG_DARK, highlightthickness=1,
                                      highlightbackground=CyberTheme.BORDER)
                warn_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

                scroll2 = tk.Scrollbar(warn_frame)
                scroll2.pack(side=tk.RIGHT, fill=tk.Y)

                warn_text = tk.Text(warn_frame, bg=CyberTheme.BG_DARK, fg=CyberTheme.WARNING,
                                    font=('Courier New', 9), yscrollcommand=scroll2.set, wrap='word')
                warn_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                scroll2.config(command=warn_text.yview)

                if report['low_confidence']:
                    warn_text.insert(tk.END, "⚠️  LOW CONFIDENCE FILES:\n\n", 'header')
                    for item in report['low_confidence']:
                        warn_text.insert(tk.END, f"  • {item['path']}\n")
                        warn_text.insert(tk.END,
                                         f"    Line {item['line']} | Confidence: {item['confidence'] * 100:.0f}%\n")
                        warn_text.insert(tk.END, f"    Suggestion: Check if this is the correct file path\n\n")

                if report['warnings']:
                    warn_text.insert(tk.END, "\n⚡ POTENTIAL ISSUES:\n\n", 'header')
                    for item in report['warnings']:
                        warn_text.insert(tk.END, f"  • Line {item['line']}: {item['suggestion']}\n")
                        warn_text.insert(tk.END, f"    Content: {item['content']}\n\n")

                warn_text.tag_config('header', foreground=CyberTheme.ACCENT, font=('Courier New', 10, 'bold'))
                warn_text.config(state='disabled')

            # 关闭按钮
            btn_container = tk.Frame(frame, bg=CyberTheme.BG)
            btn_container.pack(fill=tk.X)

            ttk.Button(btn_container, text="[ CLOSE ]", style='Cyber.TButton',
                       command=win.destroy).pack(side=tk.RIGHT)

            if report['file_count'] > 0:
                ttk.Button(btn_container, text="[ PROCEED TO FILL ]", style='Accent.TButton',
                           command=lambda: [win.destroy(), self.fill_code_templates()]).pack(side=tk.RIGHT, padx=5)

        except Exception as e:
            messagebox.showerror("[ ERROR ]", f"Validation failed:\n{e}")

    def scan_directory(self):
        """扫描目录并将结果显示在SCAN RESULT tab中"""
        target = Path(self.base_path.get())
        if not target.exists() or not target.is_dir():
            messagebox.showerror("[ ERROR ]", f"Invalid directory:\n{target}")
            return

        try:
            tree = self._generate_tree(target)

            # 将结果写入scan_result_text（而非structure_text）
            self.scan_result_text.config(state='normal')
            self.scan_result_text.delete('1.0', tk.END)
            self.scan_result_text.insert('1.0', tree)
            self.scan_result_text.config(state='disabled')

            # 自动切换到SCAN RESULT tab
            self.notebook.select(1)  # 索引1是SCAN RESULT tab

            messagebox.showinfo("[ SUCCESS ]",
                                f"Scan completed!\n\nTarget: {target}\n\nResults displayed in SCAN RESULT tab")
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
                messagebox.showerror("[ ERROR ]",
                                     "Failed to parse templates\n\nTip: Use VALIDATE TEMPLATE button first")
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
            messagebox.showinfo("[ INFO ]",
                                f"No matching files found\n\nTemplates: {len(templates)}\nProject files: {len(files)}\n\nTip: Check file names and paths")
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