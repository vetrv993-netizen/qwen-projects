# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for Accounting System.
Build with: pyinstaller --clean --noconfirm app.spec
"""

import os
import sys
from pathlib import Path

block_cipher = None

# Project paths
PROJECT_ROOT = os.path.abspath(os.path.dirname(SPEC))

# Build datas list dynamically
_datas = [
    (os.path.join('database', 'migrations', '*.sql'), 'database/migrations'),
]
_icon_path = os.path.join('assets', 'icon.ico')
if os.path.exists(_icon_path):
    _datas.append((_icon_path, 'assets'))

a = Analysis(
    ['main.py'],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=_datas,
    hiddenimports=[
        'bcrypt',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtSql',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'PIL',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AccountingSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icon_path if os.path.exists(_icon_path) else None,
    version='version_info.txt',
)
