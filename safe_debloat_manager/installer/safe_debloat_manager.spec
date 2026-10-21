# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../../run_safe_debloat_manager.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'safe_debloat_manager.core.models',
        'safe_debloat_manager.core.exclusions',
        'safe_debloat_manager.core.scanner',
        'safe_debloat_manager.core.cleaner',
        'safe_debloat_manager.core.logger',
        'safe_debloat_manager.core.recovery',
        'safe_debloat_manager.gui.app',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='SafeDebloatManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
