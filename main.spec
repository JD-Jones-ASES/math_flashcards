# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import platform
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

# Use platform-agnostic path handling
if getattr(sys, 'frozen', False):
    # Running as compiled
    project_root = os.path.dirname(sys._MEIPASS)
else:
    # Running from source
    project_root = os.path.dirname(os.path.abspath('__file__'))

# Collect all submodules
hiddenimports = collect_submodules('math_flashcards')

# Add pygame modules explicitly
hiddenimports.extend([
    'pygame',
    'pygame.base',
    'pygame.constants',
    'pygame.display',
    'pygame.draw',
    'pygame.event',
    'pygame.font',
    'pygame.image',
    'pygame.locals',
    'pygame.mixer',
    'pygame.mixer_music',
    'pygame.mouse',
    'pygame.sprite',
    'pygame.threads',
    'pygame.rect',
    'pygame.color',
    'pygame.surface',
    'pygame.time',
    'pygame.transform',
    'pkg_resources.py2_warn'
])

# Add standard library modules
hiddenimports.extend([
    'platform',
    'datetime',
    'enum',
    'dataclasses',
    'typing',
    'json',
    'random',
    'math',
    'time',
    'logging',
    'os',
    'sys',
    'shutil'
])

# Collect pygame data files and binaries
pygame_datas = collect_data_files('pygame')
pygame_bins = collect_dynamic_libs('pygame')

# Platform-specific settings
if platform.system() == 'Darwin':
    # Mac-specific
    icon_file = os.path.join(project_root, 'math_flashcards', 'data', 'icon.icns')
    # Add any Mac-specific imports here if needed
    bundle_identifier = 'org.mathflashcards.app'
else:
    # Windows-specific
    icon_file = os.path.join(project_root, 'math_flashcards', 'data', 'icon.ico')

a = Analysis(
    [os.path.join(project_root, 'math_flashcards', 'main.py')],
    pathex=[project_root],
    binaries=pygame_bins,
    datas=[
        (os.path.join(project_root, 'math_flashcards', 'data'), 'data'),
        (os.path.join(project_root, 'math_flashcards', 'utils'), 'math_flashcards/utils'),
        (os.path.join(project_root, 'math_flashcards', 'controllers'), 'math_flashcards/controllers'),
        (os.path.join(project_root, 'math_flashcards', 'models'), 'math_flashcards/models'),
        (os.path.join(project_root, 'math_flashcards', 'views'), 'math_flashcards/views'),
    ] + pygame_datas,
    hiddenimports=hiddenimports,
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

# Platform-specific executable settings
if platform.system() == 'Darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='MathFlashcards',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        codesign_identity=None,  # Set this if you have a Mac Developer certificate
        entitlements_file=None,
        icon=icon_file
    )

    # Create Mac app bundle
    app = BUNDLE(
        exe,
        a.binaries,
        a.datas,
        name='MathFlashcards.app',
        icon=icon_file,
        bundle_identifier=bundle_identifier,
        info_plist={
            'CFBundleName': 'MathFlashcards',
            'CFBundleDisplayName': 'Math Flashcards',
            'CFBundleGetInfoString': "Math practice application",
            'CFBundleIdentifier': bundle_identifier,
            'CFBundleVersion': '0.8.7',
            'CFBundleShortVersionString': '0.8.7',
            'NSHighResolutionCapable': 'True'
        }
    )
else:
    # Windows executable
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='MathFlashcards',
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
        icon=icon_file
    )

    # Windows distribution
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='MathFlashcards'
    )