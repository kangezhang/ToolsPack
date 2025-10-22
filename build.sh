#!/bin/bash
# PyInstaller Build Script
# Generated: 2025-10-21 16:28:13

echo "[PYINSTALLER BUILD]"
echo ""

echo "[*] Cleaning build directories..."
rm -rf "./build"
rm -rf "./dist"
echo "[+] Clean complete"
echo ""

echo "[*] Starting build process..."
pyinstaller --distpath "./dist" --workpath "./build" "pytools_scaffolder.spec"

if [ $? -eq 0 ]; then
    echo ""
    echo "[+] Build successful!"
    echo "[*] Output directory: ./dist"
else
    echo ""
    echo "[!] Build failed!"
    exit 1
fi
