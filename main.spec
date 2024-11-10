# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import platform

# Add project root to path to import version
project_root = os.path.dirname(os.path.abspath('__file__'))
sys.path.insert(0, os.path.join(project_root, 'math_flashcards'))

# Import version information
from utils.version import (
    VERSION, APP_NAME, APP_AUTHOR, APP_COPYRIGHT,
    APP_LICENSE, APP_REPOSITORY, APP_ID, WINDOWS_METADATA
)
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
    bundle_identifier = APP_ID

    # Mac signing settings - updated for universal binary support
    codesign_identity = None  # Will be set by build script
    entitlements_file = os.path.join(project_root, 'entitlements.plist')

    # Architecture settings for universal binary
    target_arch = None  # This allows PyInstaller to build for the current architecture

    # When building universal binary, we'll run this twice:
    # Once with target_arch = 'x86_64' (Intel)
    # Once with target_arch = 'arm64' (Apple Silicon)
    if os.environ.get('ARCH_TARGET'):
        target_arch = os.environ['ARCH_TARGET']

    # Additional Mac-specific options
    INFO_PLIST = {
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleGetInfoString': WINDOWS_METADATA['FileDescription'],
        'CFBundleIdentifier': bundle_identifier,
        'CFBundleVersion': VERSION,
        'CFBundleShortVersionString': VERSION,
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.12',
        'NSAppleArchitecturePriority': ['arm64', 'x86_64'],  # Prioritize Apple Silicon
        'LSArchitecturePriority': ['arm64', 'x86_64'],
    }
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
        codesign_identity=codesign_identity,
        entitlements_file=entitlements_file,
        icon=icon_file,
        target_arch=target_arch  # Add explicit architecture target
    )

    app = BUNDLE(
        exe,
        a.binaries,
        a.datas,
        name='MathFlashcards.app',
        icon=icon_file,
        bundle_identifier=bundle_identifier,
        info_plist=INFO_PLIST,
        sign_with_entitlements=True
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
            'CFBundleName': APP_NAME,
            'CFBundleDisplayName': APP_NAME,
            'CFBundleGetInfoString': WINDOWS_METADATA['FileDescription'],
            'CFBundleIdentifier': bundle_identifier,
            'CFBundleVersion': VERSION,
            'CFBundleShortVersionString': VERSION,
            'NSHighResolutionCapable': 'True',
            **MAC_METADATA  # Unpack all Mac-specific metadata from version.py
        },
        sign_with_entitlements=True
    )
else:
    # Windows executable settings remain unchanged
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