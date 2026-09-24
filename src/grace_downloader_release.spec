# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — GRACE Downloader v1.0.1 (release build)
========================================================
Builds the frozen v1.0.1 release from ``grace_downloader_gui_release.py``.

Usage (from this folder):
    pyinstaller --clean --noconfirm grace_downloader_release.spec

Output:
    dist/GRACE_Downloader_v1.0.1/GRACE_Downloader.exe
    dist/GRACE_Downloader_v1.0.1/_internal/...   (runtime, PyInstaller 6 layout)

Bundled next to the executable by the build script:
    grace_icon.ico, grace_icon_preview.png, 使用说明.md, 方法说明.md, 发行说明.md
and inside the bundle (read at run time):
    grace_icon.ico, 地球重力与人类生活TVGG.jpg, help_docs/ 使用说明.html + 截图

NOTE — OpenSSL DLLs
-------------------
``_ssl.pyd`` (the stdlib SSL extension) links against libssl/libcrypto, which
live in the *environment* DLL folder.  Meson/conda-built CPython does not put
them next to ``_ssl.pyd``, so PyInstaller alone produces an .exe where
``import ssl`` fails with "DLL load failed while importing _ssl" — and with it
earthaccess, requests and every HTTPS call.  The DLLs are therefore collected
explicitly below.
"""

from pathlib import Path
import sys
import sysconfig

from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

PROJECT_DIR = Path(SPECPATH)                 # folder that holds this .spec
APP_NAME = "GRACE_Downloader"
RELEASE_DIR = "GRACE_Downloader_v1.0.1"

# ── Data files read at run time ───────────────────────────────────────────────
datas = [
    # App icon — referenced via Path(__file__).parent
    ("grace_icon.ico", "."),
    # WeChat official-account QR image (non-ASCII name is fine: bundled)
    ("地球重力与人类生活TVGG.jpg", "."),
    # Pre-generated screenshot guide (the release ships it; the program also
    # regenerates any missing screenshot from its own interface)
    ("help_docs", "help_docs"),
]

# ── Packages with data files / lazy submodules PyInstaller misses ─────────────
# Only earthaccess itself needs explicit collection (its API is assembled from
# lazy submodules).  Do NOT collect_all() the cloud stack (s3fs / botocore /
# aiobotocore / requests): that stages their dependency tree as loose data
# files, and the staged copy of urllib3 then shadows the correctly frozen one,
# which makes `from urllib3.util.ssl_ import ssl` fail inside the packaged app.
# PyInstaller's own analysis handles those packages correctly.
hiddenimports = ["PyQt5.sip"]
binaries = []

# ── OpenSSL: required by the stdlib _ssl extension ────────────────────────────
# Without these, the packaged app cannot even `import ssl`.
for pkg in ("_ssl", "ssl", "libcrypto", "libssl", "openssl"):
    try:
        found = collect_dynamic_libs(pkg)
    except Exception as exc:                 # pragma: no cover - build-time only
        print(f"[spec] collect_dynamic_libs({pkg!r}) skipped: {exc}")
        continue
    if found:
        print(f"[spec] OpenSSL libs from {pkg!r}: {[Path(f[0]).name for f in found]}")
    binaries += found

# Conda keeps them in <env>\Library\bin (outside every package folder), where no
# hook looks, so glob the Python prefix explicitly.
import sysconfig
_roots = [
    Path(sysconfig.get_paths()["data"]) / "Library" / "bin",   # conda / venv
    Path(sys.prefix) / "Library" / "bin",
    Path(sys.prefix) / "DLLs",
    Path(sys.prefix) / "Scripts",
]
_seen = set()
for _root in _roots:
    if not _root.is_dir():
        continue
    for _pattern in ("libssl*.dll", "libcrypto*.dll"):
        for _dll in sorted(_root.glob(_pattern)):
            if _dll.name in _seen:
                continue
            _seen.add(_dll.name)
            binaries.append((str(_dll), "."))
            print(f"[spec] OpenSSL DLL: {_dll}")

for pkg in ("earthaccess",):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    except Exception as exc:                 # pragma: no cover - build-time only
        print(f"[spec] collect_all({pkg!r}) skipped: {exc}")
        continue
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    ["grace_downloader_gui_release.py"],
    pathex=[str(PROJECT_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Qt modules this program never touches — keeps the bundle smaller
        "PyQt5.QtBluetooth",
        "PyQt5.QtDesigner",
        "PyQt5.QtHelp",
        "PyQt5.QtLocation",
        "PyQt5.QtMultimedia",
        "PyQt5.QtMultimediaWidgets",
        "PyQt5.QtNfc",
        "PyQt5.QtOpenGL",
        "PyQt5.QtPositioning",
        "PyQt5.QtPrintSupport",
        "PyQt5.QtQml",
        "PyQt5.QtQuick",
        "PyQt5.QtQuickWidgets",
        "PyQt5.QtSensors",
        "PyQt5.QtSerialPort",
        "PyQt5.QtSql",
        "PyQt5.QtSvg",
        "PyQt5.QtTest",
        "PyQt5.QtWebChannel",
        "PyQt5.QtWebEngine",
        "PyQt5.QtWebEngineCore",
        "PyQt5.QtWebEngineWidgets",
        "PyQt5.QtWebSockets",
        "PyQt5.QtXml",
        "PyQt5.QtXmlPatterns",
        # Heavy / unused scientific stack (never imported by this program).
        # These arrive only as transitive imports of xarray/earthaccess and
        # would add ~300 MB to the bundle for no functionality.
        "numba",
        "llvmlite",
        "rasterio",
        "fiona",
        "geopandas",
        "osgeo",
        "gdal",
        "shapely",
        "pyproj",
        "h5py",
        "netCDF4",
        "xarray",
        "pandas",
        "scipy",
        "sklearn",
        "skimage",
        "matplotlib",
        "seaborn",
        "dask",
        "distributed",
        "zarr",
        "highspy",
        "cvxpy",
        "IPython",
        "jupyter",
        "notebook",
        "pytest",
        "tkinter",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                     # windowed: users use the Log view
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="grace_icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=RELEASE_DIR,
)

