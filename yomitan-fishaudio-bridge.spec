# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — cross-platform onefile build."""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).resolve()
ASSETS = ROOT / "assets"

is_win = sys.platform == "win32"
is_mac = sys.platform == "darwin"

datas = [(str(ASSETS), "assets")]
datas += collect_data_files("customtkinter")

hiddenimports = []
hiddenimports += collect_submodules("customtkinter")
hiddenimports += ["PIL._tkinter_finder"]

if is_win:
    hiddenimports += ["pystray._win32"]
elif is_mac:
    hiddenimports += ["pystray._darwin"]
else:
    hiddenimports += [
        "pystray._xorg",
        "pystray._gtk",
        "pystray._appindicator",
    ]

excludes = [
    "pytest", "unittest", "numpy", "matplotlib",
    "scipy", "pandas", "PyQt5", "PyQt6", "PySide2", "PySide6",
]

icon_file = None
if is_win and (ASSETS / "icon.ico").exists():
    icon_file = str(ASSETS / "icon.ico")
elif is_mac and (ASSETS / "icon.icns").exists():
    icon_file = str(ASSETS / "icon.icns")

a = Analysis(
    [str(ROOT / "launcher.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="yomitan-fishaudio-bridge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)
