#!/usr/bin/env python3
"""
PyInstaller 交互式部署工具
自动生成 .spec 配置文件和打包脚本
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_logo():
    """打印 ASCII LOGO"""
    logo = f"""{Colors.GREEN}
╔═══════════════════════════════════════════╗
║                                           ║
║   ██████╗ ███████╗██████╗ ██╗      ██████╗║
║   ██╔══██╗██╔════╝██╔══██╗██║     ██╔═══██╗
║   ██║  ██║█████╗  ██████╔╝██║     ██║   ██║
║   ██║  ██║██╔══╝  ██╔═══╝ ██║     ██║   ██║
║   ██████╔╝███████╗██║     ███████╗╚██████╔╝
║   ╚═════╝ ╚══════╝╚═╝     ╚══════╝ ╚═════╝ ║
║                                           ║
║   PyInstaller Deployment Tool v1.0       ║
║   [ SYSTEM READY ]                       ║
║                                           ║
╚═══════════════════════════════════════════╝
{Colors.END}"""
    print(logo)


def log(message, level="info"):
    """日志输出"""
    timestamp = datetime.now().strftime('%H:%M:%S')

    if level == "success":
        prefix = f"{Colors.GREEN}[+]{Colors.END}"
    elif level == "error":
        prefix = f"{Colors.RED}[!]{Colors.END}"
    elif level == "warning":
        prefix = f"{Colors.YELLOW}[!]{Colors.END}"
    elif level == "process":
        prefix = f"{Colors.CYAN}[>]{Colors.END}"
    else:
        prefix = f"{Colors.GRAY}[*]{Colors.END}"

    print(f"[{timestamp}] {prefix} {message}")


def prompt(question, default=None, required=False):
    """交互式提示输入"""
    if default:
        question_text = f"{Colors.CYAN}>> {question}{Colors.END} {Colors.GRAY}[{default}]{Colors.END}: "
    else:
        question_text = f"{Colors.CYAN}>> {question}{Colors.END}: "

    while True:
        answer = input(question_text).strip()

        if not answer and default:
            return default
        elif not answer and required:
            log("This field is required!", "error")
            continue
        elif not answer:
            return None
        else:
            return answer


def prompt_yes_no(question, default=True):
    """是/否提示"""
    default_text = "Y/n" if default else "y/N"
    answer = input(
        f"{Colors.CYAN}>> {question}{Colors.END} {Colors.GRAY}[{default_text}]{Colors.END}: ").strip().lower()

    if not answer:
        return default
    return answer in ['y', 'yes', '是']


def prompt_choice(question, choices, default=0):
    """选择提示"""
    print(f"\n{Colors.CYAN}>> {question}{Colors.END}")
    for i, choice in enumerate(choices):
        prefix = f"{Colors.GREEN}●{Colors.END}" if i == default else f"{Colors.GRAY}○{Colors.END}"
        print(f"   {prefix} [{i + 1}] {choice}")

    while True:
        answer = input(
            f"{Colors.CYAN}   Select (1-{len(choices)}){Colors.END} {Colors.GRAY}[{default + 1}]{Colors.END}: ").strip()

        if not answer:
            return default

        try:
            index = int(answer) - 1
            if 0 <= index < len(choices):
                return index
            else:
                log(f"Please enter a number between 1 and {len(choices)}", "error")
        except ValueError:
            log("Please enter a valid number", "error")


def prompt_file(question, file_type="file", required=False):
    """文件/目录选择提示"""
    while True:
        path = prompt(question, required=required)

        if not path:
            return None

        if file_type == "file" and not os.path.isfile(path):
            log(f"File not found: {path}", "error")
            if not prompt_yes_no("Try again?", True):
                return None
            continue
        elif file_type == "dir" and not os.path.isdir(path):
            log(f"Directory not found: {path}", "error")
            if not prompt_yes_no("Try again?", True):
                return None
            continue

        return os.path.abspath(path)


def find_icon(icon_name, search_dir='.'):
    """在项目目录中查找图标文件，优先选择平台适配格式"""
    # 根据平台确定支持的图标格式（按优先级排序）
    if sys.platform == 'darwin':  # macOS
        extensions = ['.icns', '.png', '.ico']  # .icns 优先
    elif sys.platform == 'win32':  # Windows
        extensions = ['.ico', '.png', '.icns']  # .ico 优先
    else:  # Linux
        extensions = ['.png', '.ico', '.icns']  # .png 优先

    # 移除用户输入的扩展名（如果有）
    icon_base = os.path.splitext(icon_name)[0]

    # 定义搜索目录（包括当前目录和常见资源目录）
    search_dirs = [search_dir]
    common_dirs = ['assets', 'resources', 'icons', 'res', 'img', 'images']
    for dir_name in common_dirs:
        dir_path = os.path.join(search_dir, dir_name)
        if os.path.isdir(dir_path):
            search_dirs.append(dir_path)

    # 按照扩展名优先级顺序搜索
    for ext in extensions:
        for search_path in search_dirs:
            icon_path = os.path.join(search_path, f"{icon_base}{ext}")
            if os.path.isfile(icon_path):
                return os.path.abspath(icon_path)

    return None


def collect_config():
    """收集配置信息"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}[ CONFIGURATION WIZARD ]{Colors.END}\n")

    config = {}

    # 1. 主入口文件
    log("Step 1: Main Python Script", "process")
    config['main_script'] = prompt_file("Main Python file (e.g., main.py)", "file", required=True)

    # 2. 应用名称
    log("\nStep 2: Application Name", "process")
    default_name = Path(config['main_script']).stem
    config['app_name'] = prompt("Application name", default_name, required=True)

    # 3. 打包模式
    log("\nStep 3: Build Mode", "process")
    mode_choice = prompt_choice(
        "Select build mode",
        ["One File (single executable)", "One Folder (with dependencies)"],
        default=1  # 默认选择 One Folder
    )
    config['one_file'] = (mode_choice == 0)

    # 4. 窗口模式
    log("\nStep 4: Window Mode", "process")
    window_choice = prompt_choice(
        "Select window mode",
        ["Console (with terminal window)", "Windowed (GUI only, no console)"],
        default=1  # 默认选择 Windowed
    )
    config['windowed'] = (window_choice == 1)

    # macOS App Bundle
    if sys.platform == 'darwin' and config['windowed']:
        config['macos_bundle'] = prompt_yes_no("Create macOS .app bundle?", True)
    else:
        config['macos_bundle'] = False

    # 5. 图标
    log("\nStep 5: Application Icon (Optional)", "process")
    if sys.platform == 'darwin':
        print(f"{Colors.GRAY}   (macOS: .icns or .png format recommended){Colors.END}")
    elif sys.platform == 'win32':
        print(f"{Colors.GRAY}   (Windows: .ico or .png format recommended){Colors.END}")
    print(f"{Colors.GRAY}   (Enter icon name without extension, e.g., 'icon' or 'app_icon'){Colors.END}")

    icon_name = prompt("Icon name (or press Enter to skip)")

    if icon_name:
        project_dir = os.path.dirname(os.path.abspath(config['main_script']))
        icon_path = find_icon(icon_name, project_dir)

        if icon_path:
            config['icon'] = icon_path
            log(f"Found icon: {icon_path}", "success")

            # 检查格式是否正确
            icon_ext = os.path.splitext(icon_path)[1].lower()
            if sys.platform == 'darwin' and icon_ext not in ['.icns', '.png']:
                log(f"Warning: {icon_ext} format may not work on macOS, .icns or .png recommended", "warning")
                log("Tip: Install Pillow for automatic conversion: pip install Pillow", "info")
            elif sys.platform == 'win32' and icon_ext not in ['.ico', '.png']:
                log(f"Warning: {icon_ext} format may not work on Windows, .ico or .png recommended", "warning")
        else:
            log(f"Icon '{icon_name}' not found, skipping", "warning")
            config['icon'] = None
    else:
        config['icon'] = None

    # 6. 版本信息
    log("\nStep 6: Version Information (Optional)", "process")
    if prompt_yes_no("Add version information?", True):
        config['version'] = prompt("Version", "1.0.0")
        config['company'] = prompt("Company name", "")
        config['copyright'] = prompt("Copyright", f"© {datetime.now().year}")
        config['description'] = prompt("Description", "")
    else:
        config['version'] = None

    # 7. 额外文件/目录
    log("\nStep 7: Additional Files (Optional)", "process")
    config['datas'] = []
    if prompt_yes_no("Include additional files or folders?", False):
        while True:
            src = prompt("Source file/folder path (or press Enter to finish)")
            if not src:
                break
            dst = prompt("Destination in app (. for root)", ".")
            config['datas'].append((src, dst))
            log(f"Added: {src} -> {dst}", "success")

    # 8. 隐藏导入
    log("\nStep 8: Hidden Imports (Optional)", "process")
    config['hidden_imports'] = []
    if prompt_yes_no("Add hidden imports?", False):
        print(f"{Colors.GRAY}   (Comma-separated, e.g., PIL,requests,numpy){Colors.END}")
        imports = prompt("Hidden imports")
        if imports:
            config['hidden_imports'] = [i.strip() for i in imports.split(',')]

    # 9. 输出目录
    log("\nStep 9: Output Directory", "process")
    config['dist_dir'] = prompt("Output directory", "./dist")
    config['build_dir'] = prompt("Build directory", "./build")

    # 10. 清理旧文件和调试选项
    log("\nStep 10: Build Options", "process")
    config['clean'] = prompt_yes_no("Clean build directories before building?", True)
    config['upx'] = prompt_yes_no("Use UPX compression (smaller size)?", False)
    config['debug'] = prompt_yes_no("Enable debug mode (for troubleshooting)?", False)

    return config


def generate_spec_file(config):
    """生成 .spec 配置文件"""
    spec_filename = f"{config['app_name']}.spec"

    # 构建 datas 列表
    datas_str = "[]"
    if config['datas']:
        datas_list = [f"('{src}', '{dst}')" for src, dst in config['datas']]
        datas_str = "[\n        " + ",\n        ".join(datas_list) + "\n    ]"

    # 构建 hidden_imports 列表
    hidden_imports_str = str(config['hidden_imports']) if config['hidden_imports'] else "[]"

    # 基本 spec 内容
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
# Generated by PyInstaller Deployment Tool
# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

block_cipher = None

a = Analysis(
    ['{config['main_script']}'],
    pathex=[],
    binaries=[],
    datas={datas_str},
    hiddenimports={hidden_imports_str},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
"""

    # 根据打包模式添加不同内容
    if config['one_file']:
        spec_content += f"""
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{config['app_name']}',
    debug={config.get('debug', False)},
    bootloader_ignore_signals=False,
    strip=False,
    upx={config['upx']},
    upx_exclude=[],
    runtime_tmpdir=None,
    console={not config['windowed']},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
"""
        if config['icon']:
            spec_content += f"    icon='{config['icon']}',\n"
        spec_content += ")\n"
    else:
        spec_content += f"""
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{config['app_name']}',
    debug={config.get('debug', False)},
    bootloader_ignore_signals=False,
    strip=False,
    upx={config['upx']},
    console={not config['windowed']},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
"""
        if config['icon']:
            spec_content += f"    icon='{config['icon']}',\n"
        spec_content += ")\n"

        spec_content += f"""
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx={config['upx']},
    upx_exclude=[],
    name='{config['app_name']}',
)
"""

    # macOS App Bundle（只在 One Folder 模式下）
    if config.get('macos_bundle', False) and not config['one_file']:
        spec_content += f"""
app = BUNDLE(
    coll,
    name='{config['app_name']}.app',
    icon='{config['icon']}' if '{config.get('icon', '')}' else None,
    bundle_identifier='com.{config['app_name'].lower()}.app',
    info_plist={{
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '{config.get('version', '1.0.0')}',
    }},
)
"""
    elif config.get('macos_bundle', False) and config['one_file']:
        # One File 模式不适合 macOS Bundle
        log("Warning: One File mode is not compatible with macOS .app bundle", "warning")
        log("The executable will be created without .app bundle", "warning")

    # 写入文件
    with open(spec_filename, 'w', encoding='utf-8') as f:
        f.write(spec_content)

    return spec_filename


def generate_build_script(config, spec_filename):
    """生成打包脚本"""
    is_windows = sys.platform == 'win32'
    script_ext = '.bat' if is_windows else '.sh'
    script_filename = f"build{script_ext}"

    print(f"{Colors.GRAY}   Detected platform: {sys.platform}{Colors.END}")
    print(f"{Colors.GRAY}   Generating: {script_filename}{Colors.END}")

    if is_windows:
        script_content = f"""@echo off
REM PyInstaller Build Script
REM Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo [PYINSTALLER BUILD]
echo.

"""
        if config['clean']:
            script_content += f"""echo [*] Cleaning build directories...
if exist "{config['build_dir']}" rmdir /s /q "{config['build_dir']}"
if exist "{config['dist_dir']}" rmdir /s /q "{config['dist_dir']}"
echo [+] Clean complete
echo.

"""
        script_content += f"""echo [*] Starting build process...
pyinstaller --distpath "{config['dist_dir']}" --workpath "{config['build_dir']}" "{spec_filename}"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [+] Build successful!
    echo [*] Output directory: {config['dist_dir']}
    pause
) else (
    echo.
    echo [!] Build failed!
    pause
    exit /b 1
)
"""
    else:
        script_content = f"""#!/bin/bash
# PyInstaller Build Script
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "[PYINSTALLER BUILD]"
echo ""

"""
        if config['clean']:
            script_content += f"""echo "[*] Cleaning build directories..."
rm -rf "{config['build_dir']}"
rm -rf "{config['dist_dir']}"
echo "[+] Clean complete"
echo ""

"""
        script_content += f"""echo "[*] Starting build process..."
pyinstaller --distpath "{config['dist_dir']}" --workpath "{config['build_dir']}" "{spec_filename}"

if [ $? -eq 0 ]; then
    echo ""
    echo "[+] Build successful!"
    echo "[*] Output directory: {config['dist_dir']}"
else
    echo ""
    echo "[!] Build failed!"
    exit 1
fi
"""

    # 写入文件
    with open(script_filename, 'w', encoding='utf-8') as f:
        f.write(script_content)

    # 添加执行权限 (Unix/Linux/macOS)
    if not is_windows:
        os.chmod(script_filename, 0o755)

    return script_filename


def save_config(config):
    """保存配置到 JSON"""
    config_filename = 'deploy_config.json'

    # 转换为可序列化的格式
    save_config = config.copy()

    with open(config_filename, 'w', encoding='utf-8') as f:
        json.dump(save_config, f, indent=2, ensure_ascii=False)

    return config_filename


def load_previous_config():
    """加载之前的配置"""
    if os.path.exists('deploy_config.json'):
        try:
            with open('deploy_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None


def display_summary(config, spec_file, build_script, config_file):
    """显示配置摘要"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}[ CONFIGURATION SUMMARY ]{Colors.END}\n")

    print(f"{Colors.CYAN}Application:{Colors.END}")
    print(f"  Name: {config['app_name']}")
    print(f"  Main Script: {config['main_script']}")
    print(f"  Mode: {'One File' if config['one_file'] else 'One Folder'}")
    print(f"  Window: {'Console' if not config['windowed'] else 'Windowed'}")

    if config['icon']:
        print(f"  Icon: {config['icon']}")

    if config['version']:
        print(f"\n{Colors.CYAN}Version:{Colors.END}")
        print(f"  Version: {config['version']}")
        if config['company']:
            print(f"  Company: {config['company']}")
        if config['copyright']:
            print(f"  Copyright: {config['copyright']}")

    if config['datas']:
        print(f"\n{Colors.CYAN}Additional Files:{Colors.END}")
        for src, dst in config['datas']:
            print(f"  {src} -> {dst}")

    if config['hidden_imports']:
        print(f"\n{Colors.CYAN}Hidden Imports:{Colors.END}")
        print(f"  {', '.join(config['hidden_imports'])}")

    print(f"\n{Colors.CYAN}Output:{Colors.END}")
    print(f"  Distribution: {config['dist_dir']}")
    print(f"  Build: {config['build_dir']}")

    print(f"\n{Colors.CYAN}Generated Files:{Colors.END}")
    print(f"  {Colors.GREEN}✓{Colors.END} {spec_file}")
    print(f"  {Colors.GREEN}✓{Colors.END} {build_script}")
    print(f"  {Colors.GREEN}✓{Colors.END} {config_file}")


def main():
    """主函数"""
    print_logo()

    log("PyInstaller Deployment Tool initialized", "success")
    log("This tool will generate configuration files for PyInstaller", "info")

    # 检查是否有之前的配置
    previous_config = load_previous_config()
    if previous_config:
        print(f"\n{Colors.YELLOW}[!] Found previous configuration{Colors.END}")
        if prompt_yes_no("Load previous configuration?", False):
            log("Loading previous configuration...", "process")
            config = previous_config
        else:
            config = collect_config()
    else:
        config = collect_config()

    # 生成文件
    print(f"\n{Colors.BOLD}{Colors.GREEN}[ GENERATING FILES ]{Colors.END}\n")

    log("Generating .spec file...", "process")
    spec_file = generate_spec_file(config)
    log(f"Created: {spec_file}", "success")

    log("Generating build script...", "process")
    build_script = generate_build_script(config, spec_file)
    log(f"Created: {build_script}", "success")

    log("Saving configuration...", "process")
    config_file = save_config(config)
    log(f"Created: {config_file}", "success")

    # 显示摘要
    display_summary(config, spec_file, build_script, config_file)

    # 完成
    print(f"\n{Colors.BOLD}{Colors.GREEN}[ SETUP COMPLETE ]{Colors.END}\n")

    print(f"{Colors.CYAN}Next Steps:{Colors.END}")
    print(f"  1. Review the generated {spec_file}")
    print(f"  2. Run the build script:")
    if sys.platform == 'win32':
        print(f"     {Colors.GREEN}> {build_script}{Colors.END}")
    else:
        print(f"     {Colors.GREEN}$ ./{build_script}{Colors.END}")
    print(f"  3. Find your executable in: {config['dist_dir']}")

    print(f"\n{Colors.GRAY}Tip: You can re-run this tool to update configuration{Colors.END}\n")

    # 询问是否立即构建
    if prompt_yes_no("Build application now?", False):
        print(f"\n{Colors.BOLD}{Colors.GREEN}[ BUILDING APPLICATION ]{Colors.END}\n")
        log("Starting PyInstaller build...", "process")

        try:
            if sys.platform == 'win32':
                result = subprocess.run([build_script], shell=True)
            else:
                result = subprocess.run([f'./{build_script}'], shell=True)

            if result.returncode == 0:
                log("Build completed successfully!", "success")
            else:
                log("Build failed. Please check the output above.", "error")
        except Exception as e:
            log(f"Error running build script: {e}", "error")
    else:
        log("Configuration saved. Run the build script when ready.", "info")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}[!] Operation cancelled by user{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}[!] Error: {e}{Colors.END}")
        sys.exit(1)