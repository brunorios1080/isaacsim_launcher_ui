# isaac_launcher.spec
# PyInstaller spec file for your Isaac Sim Launcher

# --- Imports ---
from PyInstaller.utils.hooks import collect_submodules
import PyInstaller.config

# --- Main Analysis ---
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('ui/*.ui', 'ui'),
        ('core/*.py', 'core'),
        ('settings.json', '.'),
    ],
    hiddenimports=collect_submodules('PySide6'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# --- Python bytecode package ---
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# --- EXE build settings ---
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='IsaacSimLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,     # Hide console window
    icon='ui/icon.ico' # Optional: add an icon file here if you have one
)

# --- Bundle everything together ---
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='IsaacSimLauncher'
)
