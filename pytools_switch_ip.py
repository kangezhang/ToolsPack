import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json
import os
import re
import sys


class DarkTheme:
    """暗黑主题配色方案"""
    BG_DARK = "#1e1e1e"
    BG_DARKER = "#252526"
    BG_LIGHT = "#2d2d30"
    BG_HOVER = "#3e3e42"

    FG_PRIMARY = "#ffffff"
    FG_SECONDARY = "#cccccc"
    FG_DISABLED = "#666666"

    ACCENT_BLUE = "#0e639c"
    ACCENT_BLUE_HOVER = "#1177bb"
    ACCENT_GREEN = "#0e8a16"
    ACCENT_BORDER = "#3e3e42"

    INPUT_BG = "#3c3c3c"
    INPUT_FG = "#ffffff"
    INPUT_BORDER = "#555555"


class IPSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("网络IP配置工具")
        self.root.geometry("560x520")
        self.root.resizable(False, False)
        self.root.configure(bg=DarkTheme.BG_DARK)

        # 设置窗口图标
        try:
            if getattr(sys, 'frozen', False):
                application_path = sys._MEIPASS
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))

            icon_path = os.path.join(application_path, 'switch_ip.ico')
            self.root.iconbitmap(icon_path)

            try:
                import ctypes
                myappid = 'mycompany.ipswitcher.app.1'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except:
                pass
        except Exception as e:
            print(f"加载图标失败: {e}")

        self.config_file = "ip_config.json"
        self.setup_dark_theme()
        self.load_config()
        self.create_widgets()
        self.refresh_adapters()

    def setup_dark_theme(self):
        """配置暗黑主题样式"""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.',
                        background=DarkTheme.BG_DARK,
                        foreground=DarkTheme.FG_PRIMARY,
                        fieldbackground=DarkTheme.INPUT_BG,
                        bordercolor=DarkTheme.ACCENT_BORDER,
                        darkcolor=DarkTheme.BG_DARKER,
                        lightcolor=DarkTheme.BG_LIGHT)

        style.configure('TLabel',
                        background=DarkTheme.BG_DARK,
                        foreground=DarkTheme.FG_PRIMARY,
                        font=('Microsoft YaHei UI', 9))

        style.configure('TFrame',
                        background=DarkTheme.BG_DARK,
                        bordercolor=DarkTheme.ACCENT_BORDER)

        style.configure('Card.TFrame',
                        background=DarkTheme.BG_DARKER,
                        relief='flat',
                        borderwidth=1)

        style.configure('TLabelframe',
                        background=DarkTheme.BG_DARK,
                        foreground=DarkTheme.FG_PRIMARY,
                        bordercolor=DarkTheme.ACCENT_BORDER,
                        relief='flat',
                        borderwidth=1)

        style.configure('TLabelframe.Label',
                        background=DarkTheme.BG_DARK,
                        foreground=DarkTheme.FG_PRIMARY,
                        font=('Microsoft YaHei UI', 9, 'bold'))

        style.configure('TEntry',
                        fieldbackground=DarkTheme.INPUT_BG,
                        foreground=DarkTheme.FG_PRIMARY,
                        bordercolor=DarkTheme.INPUT_BORDER,
                        lightcolor=DarkTheme.INPUT_BORDER,
                        darkcolor=DarkTheme.INPUT_BORDER,
                        insertcolor=DarkTheme.FG_PRIMARY)

        style.configure('TCombobox',
                        fieldbackground=DarkTheme.INPUT_BG,
                        background=DarkTheme.INPUT_BG,
                        foreground=DarkTheme.FG_PRIMARY,
                        arrowcolor=DarkTheme.FG_PRIMARY,
                        bordercolor=DarkTheme.INPUT_BORDER,
                        lightcolor=DarkTheme.INPUT_BORDER,
                        darkcolor=DarkTheme.INPUT_BORDER)

        style.map('TCombobox',
                  fieldbackground=[('readonly', DarkTheme.INPUT_BG)],
                  selectbackground=[('readonly', DarkTheme.INPUT_BG)],
                  selectforeground=[('readonly', DarkTheme.FG_PRIMARY)])

        style.configure('Primary.TButton',
                        background=DarkTheme.ACCENT_BLUE,
                        foreground=DarkTheme.FG_PRIMARY,
                        bordercolor=DarkTheme.ACCENT_BLUE,
                        lightcolor=DarkTheme.ACCENT_BLUE,
                        darkcolor=DarkTheme.ACCENT_BLUE,
                        relief='flat',
                        font=('Microsoft YaHei UI', 9),
                        padding=(10, 5))

        style.map('Primary.TButton',
                  background=[('active', DarkTheme.ACCENT_BLUE_HOVER),
                              ('pressed', DarkTheme.ACCENT_BLUE_HOVER)],
                  relief=[('pressed', 'flat')])

        style.configure('Secondary.TButton',
                        background=DarkTheme.BG_LIGHT,
                        foreground=DarkTheme.FG_PRIMARY,
                        bordercolor=DarkTheme.ACCENT_BORDER,
                        lightcolor=DarkTheme.BG_LIGHT,
                        darkcolor=DarkTheme.BG_LIGHT,
                        relief='flat',
                        font=('Microsoft YaHei UI', 9),
                        padding=(8, 4))

        style.map('Secondary.TButton',
                  background=[('active', DarkTheme.BG_HOVER),
                              ('pressed', DarkTheme.BG_HOVER)])

        style.configure('TRadiobutton',
                        background=DarkTheme.BG_DARK,
                        foreground=DarkTheme.FG_PRIMARY,
                        font=('Microsoft YaHei UI', 9))

        style.map('TRadiobutton',
                  background=[('active', DarkTheme.BG_DARK)])

        style.configure('TSeparator',
                        background=DarkTheme.ACCENT_BORDER)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="15", style='TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 标题区域 - 减少间距
        title_frame = ttk.Frame(main_frame, style='TFrame')
        title_frame.grid(row=0, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=(0, 10))

        title_label = ttk.Label(title_frame,
                                text="⚙ 网络配置管理",
                                font=('Microsoft YaHei UI', 13, 'bold'),
                                foreground=DarkTheme.FG_PRIMARY)
        title_label.pack(side=tk.LEFT)

        # 网络适配器选择区域 - 压缩padding
        adapter_frame = ttk.Frame(main_frame, style='Card.TFrame', padding="12")
        adapter_frame.grid(row=1, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(adapter_frame, text="网络适配器",
                  font=('Microsoft YaHei UI', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 6))

        adapter_control_frame = ttk.Frame(adapter_frame, style='Card.TFrame')
        adapter_control_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E))

        self.adapter_combo = ttk.Combobox(adapter_control_frame, width=35, font=('Consolas', 9))
        self.adapter_combo.pack(side=tk.LEFT, padx=(0, 6))
        self.adapter_combo.bind('<<ComboboxSelected>>', self.on_adapter_change)

        ttk.Button(adapter_control_frame, text="🔄 刷新",
                   command=self.refresh_adapters,
                   style='Secondary.TButton').pack(side=tk.LEFT, padx=2)

        ttk.Button(adapter_control_frame, text="🔍 调试",
                   command=self.show_debug_info,
                   style='Secondary.TButton').pack(side=tk.LEFT, padx=2)

        # 配置模式选择 - 压缩padding
        mode_frame = ttk.Frame(main_frame, style='Card.TFrame', padding="12")
        mode_frame.grid(row=2, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(mode_frame, text="配置模式",
                  font=('Microsoft YaHei UI', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 6))

        self.mode_var = tk.StringVar(value="auto")

        radio_frame = ttk.Frame(mode_frame, style='Card.TFrame')
        radio_frame.grid(row=1, column=0, sticky=tk.W)

        ttk.Radiobutton(radio_frame, text="🔄 自动获取 (DHCP)",
                        variable=self.mode_var,
                        value="auto",
                        command=self.toggle_mode).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Radiobutton(radio_frame, text="⚙ 手动配置",
                        variable=self.mode_var,
                        value="manual",
                        command=self.toggle_mode).pack(side=tk.LEFT)

        # 手动配置区域 - 压缩padding和行距
        config_frame = ttk.LabelFrame(main_frame, text="  IP 配置参数  ", padding="12")
        config_frame.grid(row=3, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=(0, 10))

        config_items = [
            ("IP 地址", 'ip', '192.168.1.100'),
            ("子网掩码", 'mask', '255.255.255.0'),
            ("默认网关", 'gateway', '192.168.1.1'),
            ("首选 DNS", 'dns1', '8.8.8.8'),
            ("备用 DNS", 'dns2', '8.8.4.4')
        ]

        self.entries = {}

        for i, (label_text, key, default_value) in enumerate(config_items):
            label = ttk.Label(config_frame, text=label_text, width=10)
            label.grid(row=i, column=0, sticky=tk.W, pady=4, padx=(0, 10))

            entry = ttk.Entry(config_frame, width=40, font=('Consolas', 9))
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=4)
            entry.insert(0, self.config.get(key, default_value))
            self.entries[key] = entry

        self.ip_entry = self.entries['ip']
        self.mask_entry = self.entries['mask']
        self.gateway_entry = self.entries['gateway']
        self.dns1_entry = self.entries['dns1']
        self.dns2_entry = self.entries['dns2']

        # 按钮区域 - 减少上边距
        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.grid(row=4, column=0, columnspan=5, pady=(8, 0))

        ttk.Button(button_frame, text="✓ 应用设置",
                   command=self.apply_settings,
                   style='Primary.TButton',
                   width=14).pack(side=tk.LEFT, padx=4)

        ttk.Button(button_frame, text="💾 保存配置",
                   command=self.save_config,
                   style='Secondary.TButton',
                   width=14).pack(side=tk.LEFT, padx=4)

        ttk.Button(button_frame, text="📥 获取当前",
                   command=self.get_current_ip,
                   style='Secondary.TButton',
                   width=14).pack(side=tk.LEFT, padx=4)

        self.toggle_mode()
        config_frame.columnconfigure(1, weight=1)

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except:
                self.config = {}
        else:
            self.config = {}

    def save_config(self):
        """保存配置到文件"""
        self.config = {
            'ip': self.ip_entry.get(),
            'mask': self.mask_entry.get(),
            'gateway': self.gateway_entry.get(),
            'dns1': self.dns1_entry.get(),
            'dns2': self.dns2_entry.get(),
            'mode': self.mode_var.get(),
            'adapter': self.adapter_combo.get()
        }

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.show_custom_message("✓ 成功", "配置已成功保存！", "info")
        except Exception as e:
            self.show_custom_message("✗ 错误", f"保存配置失败: {str(e)}", "error")

    def show_custom_message(self, title, message, msg_type="info"):
        """显示自定义样式的消息框"""
        msg_window = tk.Toplevel(self.root)
        msg_window.title(title)
        msg_window.geometry("350x150")
        msg_window.resizable(False, False)
        msg_window.configure(bg=DarkTheme.BG_DARKER)

        msg_window.transient(self.root)
        msg_window.grab_set()

        icon_map = {"info": "ℹ", "error": "✗", "warning": "⚠"}
        color_map = {"info": "#4CAF50", "error": "#f44336", "warning": "#ff9800"}

        icon_label = tk.Label(msg_window,
                              text=icon_map.get(msg_type, "ℹ"),
                              font=('Arial', 32),
                              fg=color_map.get(msg_type, "#4CAF50"),
                              bg=DarkTheme.BG_DARKER)
        icon_label.pack(pady=(20, 10))

        msg_label = tk.Label(msg_window,
                             text=message,
                             font=('Microsoft YaHei UI', 10),
                             fg=DarkTheme.FG_PRIMARY,
                             bg=DarkTheme.BG_DARKER,
                             wraplength=300)
        msg_label.pack(pady=10)

        btn_frame = tk.Frame(msg_window, bg=DarkTheme.BG_DARKER)
        btn_frame.pack(pady=(10, 20))

        ok_btn = tk.Button(btn_frame,
                           text="确定",
                           command=msg_window.destroy,
                           bg=DarkTheme.ACCENT_BLUE,
                           fg=DarkTheme.FG_PRIMARY,
                           font=('Microsoft YaHei UI', 9),
                           relief='flat',
                           padx=30,
                           pady=8,
                           cursor='hand2',
                           activebackground=DarkTheme.ACCENT_BLUE_HOVER,
                           activeforeground=DarkTheme.FG_PRIMARY,
                           bd=0)
        ok_btn.pack()

        msg_window.update_idletasks()
        x = (msg_window.winfo_screenwidth() // 2) - (msg_window.winfo_width() // 2)
        y = (msg_window.winfo_screenheight() // 2) - (msg_window.winfo_height() // 2)
        msg_window.geometry(f'+{x}+{y}')

    def get_adapters(self):
        """获取网络适配器列表"""
        adapters = []
        try:
            import platform

            if platform.system() != 'Windows':
                messagebox.showerror("错误", "此工具仅支持Windows系统")
                return []

            encodings = ['utf-8', 'gbk', 'gb2312', 'cp936']

            for encoding in encodings:
                try:
                    result = subprocess.run(
                        'chcp 65001 & netsh interface ip show config',
                        capture_output=True,
                        text=True,
                        shell=True,
                        encoding=encoding,
                        errors='ignore'
                    )

                    if result.returncode == 0 and result.stdout:
                        lines = result.stdout.split('\n')
                        for line in lines:
                            match = re.search(r'[""]([^""]+)[""]', line)
                            if match:
                                adapter_name = match.group(1).strip()
                                if adapter_name and adapter_name not in adapters:
                                    if 'Loopback' not in adapter_name and 'Pseudo' not in adapter_name:
                                        adapters.append(adapter_name)

                        if adapters:
                            break
                except:
                    continue

            if not adapters:
                for encoding in encodings:
                    try:
                        result = subprocess.run(
                            'chcp 65001 & netsh interface show interface',
                            capture_output=True,
                            text=True,
                            shell=True,
                            encoding=encoding,
                            errors='ignore'
                        )

                        if result.returncode == 0:
                            lines = result.stdout.split('\n')
                            for line in lines[3:]:
                                line = line.strip()
                                if line:
                                    parts = line.split()
                                    if len(parts) >= 4:
                                        if any(word in line for word in ['已连接', 'Connected', '连接']):
                                            adapter_name = ' '.join(parts[3:])
                                            if adapter_name and adapter_name not in adapters:
                                                adapters.append(adapter_name)

                            if adapters:
                                break
                    except:
                        continue

            if not adapters:
                adapters = ['以太网', '以太网 2', '本地连接', 'WLAN', 'WLAN 2', 'Wi-Fi', 'Ethernet']
                self.show_custom_message("⚠ 警告",
                                         "无法自动检测网络适配器。\n已加载常见适配器名称。\n请手动输入正确的适配器名称。",
                                         "warning")

            return adapters

        except Exception as e:
            adapters = ['以太网', '以太网 2', '本地连接', 'WLAN', 'WLAN 2', 'Wi-Fi', 'Ethernet', 'LetsTAP']
            self.show_custom_message("✗ 错误",
                                     f"获取网络适配器时出错: {str(e)}\n已加载常见适配器名称。",
                                     "error")
            return adapters

    def refresh_adapters(self):
        """刷新网络适配器列表"""
        adapters = self.get_adapters()
        common_adapters = ['以太网 2', 'LetsTAP', 'WLAN 2', 'vEthernet (Default Switch)',
                           '以太网', '本地连接', 'WLAN', 'Wi-Fi']
        all_adapters = list(dict.fromkeys(adapters + common_adapters))
        self.adapter_combo['values'] = all_adapters

        if all_adapters:
            saved_adapter = self.config.get('adapter', '')
            if saved_adapter in all_adapters:
                self.adapter_combo.set(saved_adapter)
            else:
                self.adapter_combo.current(0)

    def on_adapter_change(self, event):
        """适配器选择变化时的处理"""
        pass

    def toggle_mode(self):
        """切换配置模式时启用/禁用输入框"""
        state = 'disabled' if self.mode_var.get() == "auto" else 'normal'
        for entry in self.entries.values():
            entry.config(state=state)

    def validate_ip(self, ip):
        """验证IP地址格式"""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(pattern, ip):
            parts = ip.split('.')
            return all(0 <= int(part) <= 255 for part in parts)
        return False

    def show_debug_info(self):
        """显示调试信息窗口"""
        debug_window = tk.Toplevel(self.root)
        debug_window.title("调试信息")
        debug_window.geometry("750x550")
        debug_window.configure(bg=DarkTheme.BG_DARK)

        text_frame = ttk.Frame(debug_window, padding="15", style='TFrame')
        text_frame.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(text_frame,
                          text="🔍 网络适配器调试信息",
                          font=('Microsoft YaHei UI', 12, 'bold'))
        title.pack(pady=(0, 10))

        text_container = tk.Frame(text_frame, bg=DarkTheme.BG_DARKER, bd=1, relief='flat')
        text_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(text_container, bg=DarkTheme.BG_LIGHT)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(text_container,
                              wrap=tk.WORD,
                              yscrollcommand=scrollbar.set,
                              bg=DarkTheme.INPUT_BG,
                              fg=DarkTheme.FG_PRIMARY,
                              font=('Consolas', 9),
                              insertbackground=DarkTheme.FG_PRIMARY,
                              selectbackground=DarkTheme.ACCENT_BLUE,
                              selectforeground=DarkTheme.FG_PRIMARY,
                              padx=10,
                              pady=10,
                              bd=0)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        debug_info = "=== 网络适配器调试信息 ===\n\n"

        try:
            debug_info += "测试命令 1: netsh interface show interface\n"
            debug_info += "-" * 60 + "\n"
            result = subprocess.run(
                'chcp 65001 & netsh interface show interface',
                capture_output=True,
                text=True,
                shell=True,
                encoding='utf-8',
                errors='ignore'
            )
            debug_info += f"返回码: {result.returncode}\n"
            debug_info += f"输出:\n{result.stdout}\n"
            if result.stderr:
                debug_info += f"错误:\n{result.stderr}\n"
            debug_info += "\n\n"

            debug_info += "测试命令 2: netsh interface ip show config\n"
            debug_info += "-" * 60 + "\n"
            result = subprocess.run(
                'chcp 65001 & netsh interface ip show config',
                capture_output=True,
                text=True,
                shell=True,
                encoding='utf-8',
                errors='ignore'
            )
            debug_info += f"返回码: {result.returncode}\n"
            debug_info += f"输出:\n{result.stdout}\n"
            if result.stderr:
                debug_info += f"错误:\n{result.stderr}\n"
            debug_info += "\n\n"

            debug_info += "测试命令 3: 使用PowerShell获取网络适配器\n"
            debug_info += "-" * 60 + "\n"
            result = subprocess.run(
                'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Up\'} | Select-Object -ExpandProperty Name"',
                capture_output=True,
                text=True,
                shell=True,
                encoding='utf-8',
                errors='ignore'
            )
            debug_info += f"返回码: {result.returncode}\n"
            debug_info += f"输出:\n{result.stdout}\n"
            if result.stderr:
                debug_info += f"错误:\n{result.stderr}\n"
            debug_info += "\n\n"

            debug_info += "=== 解析到的适配器 ===\n"
            debug_info += "-" * 60 + "\n"
            adapters = self.get_adapters()
            if adapters:
                for i, adapter in enumerate(adapters, 1):
                    debug_info += f"{i}. {adapter}\n"
            else:
                debug_info += "未检测到任何适配器\n"

        except Exception as e:
            debug_info += f"\n发生错误: {str(e)}\n"

        text_widget.insert('1.0', debug_info)
        text_widget.config(state='disabled')

        def copy_to_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(debug_info)
            self.show_custom_message("✓ 成功", "调试信息已复制到剪贴板", "info")

        btn_frame = tk.Frame(text_frame, bg=DarkTheme.BG_DARK)
        btn_frame.pack(pady=(15, 0))

        copy_btn = tk.Button(btn_frame,
                             text="📋 复制到剪贴板",
                             command=copy_to_clipboard,
                             bg=DarkTheme.ACCENT_BLUE,
                             fg=DarkTheme.FG_PRIMARY,
                             font=('Microsoft YaHei UI', 9),
                             relief='flat',
                             padx=20,
                             pady=8,
                             cursor='hand2',
                             activebackground=DarkTheme.ACCENT_BLUE_HOVER,
                             activeforeground=DarkTheme.FG_PRIMARY,
                             bd=0)
        copy_btn.pack()

    def get_current_ip(self):
        """获取当前适配器的IP配置"""
        adapter = self.adapter_combo.get()
        if not adapter:
            self.show_custom_message("✗ 错误", "请先选择或输入网络适配器名称！", "error")
            return

        try:
            cmd = f'netsh interface ip show config "{adapter}"'
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=True,
                encoding='gbk',
                errors='ignore'
            )

            if result.returncode == 0 and result.stdout:
                output = result.stdout

                ip_match = re.search(r'IP [Aa]ddress.*?(\d+\.\d+\.\d+\.\d+)', output)
                if ip_match:
                    self.ip_entry.delete(0, tk.END)
                    self.ip_entry.insert(0, ip_match.group(1))

                mask_match = re.search(r'mask (\d+\.\d+\.\d+\.\d+)', output, re.IGNORECASE)
                if mask_match:
                    self.mask_entry.delete(0, tk.END)
                    self.mask_entry.insert(0, mask_match.group(1))

                gateway_match = re.search(r'[Dd]efault [Gg]ateway.*?(\d+\.\d+\.\d+\.\d+)', output)
                if gateway_match:
                    self.gateway_entry.delete(0, tk.END)
                    self.gateway_entry.insert(0, gateway_match.group(1))

                dns_matches = re.findall(r'(\d+\.\d+\.\d+\.\d+)', output)
                dns_list = []
                for match in dns_matches:
                    if match not in [ip_match.group(1) if ip_match else '',
                                     gateway_match.group(1) if gateway_match else '']:
                        dns_list.append(match)

                if len(dns_list) >= 1:
                    self.dns1_entry.delete(0, tk.END)
                    self.dns1_entry.insert(0, dns_list[0])

                if len(dns_list) >= 2:
                    self.dns2_entry.delete(0, tk.END)
                    self.dns2_entry.insert(0, dns_list[1])

                if 'DHCP' in output or 'dhcp' in output.lower():
                    self.mode_var.set("auto")
                else:
                    self.mode_var.set("manual")

                self.toggle_mode()
                self.show_custom_message("✓ 成功", f"已获取适配器 [{adapter}] 的当前配置！", "info")
            else:
                self.show_custom_message("✗ 错误", "无法获取适配器信息\n请检查适配器名称是否正确", "error")

        except Exception as e:
            self.show_custom_message("✗ 错误", f"获取当前IP配置失败:\n{str(e)}", "error")

    def apply_settings(self):
        """应用网络设置"""
        adapter = self.adapter_combo.get()
        if not adapter:
            self.show_custom_message("✗ 错误", "请选择或输入网络适配器名称！", "error")
            return

        try:
            if self.mode_var.get() == "auto":
                cmd1 = f'netsh interface ip set address "{adapter}" dhcp'
                result1 = subprocess.run(cmd1, shell=True, capture_output=True, text=True)

                cmd2 = f'netsh interface ip set dns "{adapter}" dhcp'
                result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)

                if result1.returncode != 0 or result2.returncode != 0:
                    error_msg = result1.stderr + result2.stderr
                    raise Exception(f"命令执行失败:\n{error_msg}")

                self.show_custom_message("✓ 成功", "已切换到自动获取IP模式！\n可能需要几秒钟生效。", "info")
            else:
                ip = self.ip_entry.get()
                mask = self.mask_entry.get()
                gateway = self.gateway_entry.get().strip()
                dns1 = self.dns1_entry.get()
                dns2 = self.dns2_entry.get()

                if not all([self.validate_ip(ip), self.validate_ip(mask)]):
                    self.show_custom_message("✗ 错误", "IP地址或子网掩码格式不正确！", "error")
                    return

                if gateway and not self.validate_ip(gateway):
                    self.show_custom_message("✗ 错误", "默认网关格式不正确！", "error")
                    return

                if not self.validate_ip(dns1):
                    self.show_custom_message("✗ 错误", "首选DNS格式不正确！", "error")
                    return

                # 根据是否有网关构建不同的命令
                if gateway:
                    cmd1 = f'netsh interface ip set address "{adapter}" static {ip} {mask} {gateway}'
                else:
                    cmd1 = f'netsh interface ip set address "{adapter}" static {ip} {mask}'

                result1 = subprocess.run(cmd1, shell=True, capture_output=True, text=True, encoding='gbk',
                                         errors='ignore')

                if result1.returncode != 0:
                    raise Exception(f"设置IP失败:\n{result1.stderr}")

                cmd2 = f'netsh interface ip set dns "{adapter}" static {dns1}'
                result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True, encoding='gbk',
                                         errors='ignore')

                if result2.returncode != 0:
                    raise Exception(f"设置DNS失败:\n{result2.stderr}")

                if dns2 and self.validate_ip(dns2):
                    cmd3 = f'netsh interface ip add dns "{adapter}" {dns2} index=2'
                    subprocess.run(cmd3, shell=True, capture_output=True, text=True, encoding='gbk', errors='ignore')

                self.show_custom_message("✓ 成功", "手动IP配置已应用！\n可能需要几秒钟生效。", "info")

        except Exception as e:
            self.show_custom_message("✗ 错误",
                                     f"应用设置失败！\n\n{str(e)}\n\n请确保：\n1. 以管理员身份运行此程序\n2. 适配器名称正确\n3. IP地址格式正确",
                                     "error")


if __name__ == "__main__":
    root = tk.Tk()
    app = IPSwitcher(root)
    root.mainloop()