#!/bin/bash
# PyInstaller Build Script
# Generated: 2025-10-21 14:49:54

echo "[PYINSTALLER BUILD]"
echo ""

echo "[*] Cleaning build directories..."
rm -rf "./build"
rm -rf "./dist"
echo "[+] Clean complete"
echo ""

echo "[*] Starting build process..."
pyinstaller --distpath "./dist" --workpath "./build" "dependency_analyzer.spec"

if [ $? -eq 0 ]; then
    echo ""
    echo "[+] Build successful!"
    echo "[*] Output directory: ./dist"
else
    echo ""
    echo "[!] Build failed!"
    exit 1
fi
