# -*- mode: python ; coding: utf-8 -*-
# https://pyinstaller.readthedocs.io/en/stable/spec-files.html
PROJECT_NAME = "rogelikedev-2024"

a = Analysis(  # type: ignore[name-defined]
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[("assets", "assets")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)  # type: ignore[name-defined]

exe = EXE(  # type: ignore[name-defined]
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=PROJECT_NAME,  # Name of the executable
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["icon.ico"],  # Windows icon file
)
coll = COLLECT(  # type: ignore[name-defined]
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=PROJECT_NAME,  # Name of the distribution directory
)
