# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

datas = [
    ("app/templates", "app/templates"),
    ("app/static", "app/static"),
    ("app/static/img/logo-smpm22.png", "app/static/img"),
]

hiddenimports = [
    "flask",
    "flask_login",
    "werkzeug",
    "werkzeug.security",
    "dotenv",
    "openpyxl",
    "pymysql",
    "pymysql.cursors",
    "cryptography",
    "google.auth",
    "google.auth.transport.requests",
    "google.oauth2.credentials",
    "google_auth_oauthlib",
    "google_auth_oauthlib.flow",
    "googleapiclient",
    "googleapiclient.discovery",
    "googleapiclient.http",
    "app",
    "app.db",
    "app.models",
    "app.routes",
    "app.routes.auth",
    "app.routes.main",
    "app.routes.barang",
    "app.routes.peminjaman",
    "app.routes.sync",
    "app.routes.laporan",
    "app.services",
    "app.services.google_drive",
    "app.services.backup",
    "app.services.excel_import",
    "config",
]

# googleapiclient discovery docs
tmp_ret = collect_all("googleapiclient")
datas += tmp_ret[0]
hiddenimports += tmp_ret[1]
hiddenimports += collect_submodules("googleapiclient")

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=[],
    datas=datas,
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

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="InventarisSMPM22",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # jendela hitam menampilkan alamat untuk HP
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="InventarisSMPM22",
)
