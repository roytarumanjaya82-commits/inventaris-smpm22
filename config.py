import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def app_base_dir() -> Path:
    """Folder aplikasi: sebelah .exe (mode frozen) atau root project (mode dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_dir() -> Path:
    """Folder resource baca-saja (templates/static) saat di-bundle PyInstaller."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


BASE_DIR = app_base_dir()
RESOURCE_DIR = resource_dir()

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "smpm22-inventaris-dev-key")
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# --- MySQL ---
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "inventaris_smpm22")

BACKUP_PATH = DATA_DIR / "inventaris_backup.json"

CREDENTIALS_DIR = BASE_DIR / "credentials"
CREDENTIALS_DIR.mkdir(exist_ok=True)

GOOGLE_CLIENT_SECRETS = os.getenv(
    "GOOGLE_CLIENT_SECRETS",
    str(CREDENTIALS_DIR / "client_secret.json"),
)
TOKEN_PATH = CREDENTIALS_DIR / "token.json"
DRIVE_FOLDER_NAME = os.getenv("DRIVE_FOLDER_NAME", "Inventaris SMPM22 Setiabudi")
DRIVE_DB_FILENAME = "inventaris_smpm22_backup.json"
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "0") == "1"

SCHOOL_NAME = "SMP Muhammadiyah 22 Setiabudi Pamulang"
SCHOOL_SHORT = "SMPM 22 Setiabudi"
SCHOOL_NPSN = os.getenv("SCHOOL_NPSN", "20603577")
SCHOOL_ADDRESS = os.getenv(
    "SCHOOL_ADDRESS",
    "Jl. Surya Kencana No. 29, Pamulang Barat, Pamulang, Tangerang Selatan, Banten",
)
SCHOOL_WEBSITE = os.getenv("SCHOOL_WEBSITE", "smpm22pamulang.sch.id")
SCHOOL_KEPALA = os.getenv("SCHOOL_KEPALA", "Ikhsan Saepul Munir, M.Pd.")
SCHOOL_NBM_KEPALA = os.getenv("SCHOOL_NBM_KEPALA", "73281733")
SCHOOL_KOTA = os.getenv("SCHOOL_KOTA", "Tangerang Selatan")

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]
