"""
Sinkronisasi cadangan MySQL (JSON) ke Google Drive.

- Runtime: MySQL lokal/server
- Backup: export JSON → upload ke Drive
- Restore: download JSON → import ke MySQL
"""

from __future__ import annotations

import io
import shutil
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from config import (
    BACKUP_PATH,
    DRIVE_DB_FILENAME,
    DRIVE_FOLDER_NAME,
    GOOGLE_CLIENT_SECRETS,
    GOOGLE_SCOPES,
    MYSQL_DATABASE,
    MYSQL_HOST,
    OFFLINE_MODE,
    TOKEN_PATH,
)
from app.models import add_sync_log
from app.services import backup as mysql_backup
from app.db import mysql_status


class GoogleDriveError(Exception):
    pass


def secrets_available() -> bool:
    return Path(GOOGLE_CLIENT_SECRETS).exists()


def is_offline() -> bool:
    return OFFLINE_MODE or not secrets_available()


def get_credentials() -> Optional[Credentials]:
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), GOOGLE_SCOPES)
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_credentials(creds)
        except Exception:
            return None
    if creds and creds.valid:
        return creds
    return None


def save_credentials(creds: Credentials) -> None:
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")


def clear_credentials() -> None:
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()


def is_connected() -> bool:
    if is_offline():
        return False
    return get_credentials() is not None


def get_auth_flow(redirect_uri: str) -> Flow:
    if not secrets_available():
        raise GoogleDriveError(
            "File credentials/client_secret.json belum ada. "
            "Unduh dari Google Cloud Console."
        )
    return Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS,
        scopes=GOOGLE_SCOPES,
        redirect_uri=redirect_uri,
    )


def get_user_info(creds: Optional[Credentials] = None) -> Optional[dict]:
    creds = creds or get_credentials()
    if not creds:
        return None
    try:
        service = build("oauth2", "v2", credentials=creds)
        return service.userinfo().get().execute()
    except Exception:
        return None


def _drive_service(creds: Optional[Credentials] = None):
    creds = creds or get_credentials()
    if not creds:
        raise GoogleDriveError("Belum terhubung ke Google Drive. Silakan login Google.")
    return build("drive", "v3", credentials=creds)


def _find_folder(service, name: str) -> Optional[str]:
    query = (
        f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    result = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id, name)", pageSize=1)
        .execute()
    )
    files = result.get("files", [])
    return files[0]["id"] if files else None


def _ensure_folder(service) -> str:
    folder_id = _find_folder(service, DRIVE_FOLDER_NAME)
    if folder_id:
        return folder_id
    meta = {
        "name": DRIVE_FOLDER_NAME,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def _find_db_file(service, folder_id: str) -> Optional[dict]:
    query = (
        f"name = '{DRIVE_DB_FILENAME}' and '{folder_id}' in parents and trashed = false"
    )
    result = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id, name, modifiedTime)", pageSize=1)
        .execute()
    )
    files = result.get("files", [])
    return files[0] if files else None


def upload_database() -> dict:
    """Export MySQL → JSON lalu upload ke Google Drive."""
    if is_offline():
        raise GoogleDriveError("Mode offline aktif atau credentials belum dikonfigurasi.")

    try:
        export_path = mysql_backup.export_to_json(BACKUP_PATH)
    except Exception as exc:
        add_sync_log("upload", "gagal", str(exc))
        raise GoogleDriveError(f"Gagal export MySQL: {exc}") from exc

    service = _drive_service()
    folder_id = _ensure_folder(service)
    existing = _find_db_file(service, folder_id)

    media = MediaFileUpload(
        str(export_path),
        mimetype="application/json",
        resumable=True,
    )

    try:
        if existing:
            updated = (
                service.files()
                .update(fileId=existing["id"], media_body=media, fields="id, modifiedTime")
                .execute()
            )
            msg = f"Backup MySQL diperbarui di Drive (ID: {updated['id']})"
            add_sync_log("upload", "sukses", msg)
            return {"action": "update", "file_id": updated["id"], "message": msg}

        meta = {"name": DRIVE_DB_FILENAME, "parents": [folder_id]}
        created = (
            service.files()
            .create(body=meta, media_body=media, fields="id, modifiedTime")
            .execute()
        )
        msg = f"Backup MySQL diunggah ke Drive (ID: {created['id']})"
        add_sync_log("upload", "sukses", msg)
        return {"action": "create", "file_id": created["id"], "message": msg}
    except Exception as exc:
        add_sync_log("upload", "gagal", str(exc))
        raise GoogleDriveError(f"Gagal upload: {exc}") from exc


def download_database(backup_local: bool = True) -> dict:
    """Download JSON dari Drive lalu restore ke MySQL."""
    if is_offline():
        raise GoogleDriveError("Mode offline aktif atau credentials belum dikonfigurasi.")

    service = _drive_service()
    folder_id = _ensure_folder(service)
    existing = _find_db_file(service, folder_id)
    if not existing:
        raise GoogleDriveError(
            f"File '{DRIVE_DB_FILENAME}' belum ada di folder '{DRIVE_FOLDER_NAME}'."
        )

    try:
        if backup_local and BACKUP_PATH.exists():
            shutil.copy2(BACKUP_PATH, BACKUP_PATH.with_suffix(".json.bak"))

        request = service.files().get_media(fileId=existing["id"])
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
        BACKUP_PATH.write_bytes(buffer.getvalue())

        result = mysql_backup.import_from_json(BACKUP_PATH, make_local_bak=False)
        msg = (
            f"{result['message']} "
            f"(remote dimodifikasi: {existing.get('modifiedTime')})"
        )
        add_sync_log("download", "sukses", msg)
        return {
            "action": "download",
            "file_id": existing["id"],
            "modified": existing.get("modifiedTime"),
            "message": msg,
        }
    except GoogleDriveError:
        raise
    except Exception as exc:
        add_sync_log("download", "gagal", str(exc))
        raise GoogleDriveError(f"Gagal download/restore: {exc}") from exc


def drive_status() -> dict:
    db = mysql_status()
    status = {
        "offline_mode": is_offline(),
        "secrets_ok": secrets_available(),
        "connected": False,
        "email": None,
        "folder": DRIVE_FOLDER_NAME,
        "db_filename": DRIVE_DB_FILENAME,
        "remote_file": None,
        "mysql_ok": db["ok"],
        "mysql_host": db["host"],
        "mysql_database": db["database"],
        "mysql_error": db["error"],
        "barang_count": db["barang_count"],
        "local_backup_exists": BACKUP_PATH.exists(),
        "local_backup_size": BACKUP_PATH.stat().st_size if BACKUP_PATH.exists() else 0,
    }
    if status["offline_mode"]:
        return status

    creds = get_credentials()
    if not creds:
        return status

    status["connected"] = True
    info = get_user_info(creds)
    if info:
        status["email"] = info.get("email")

    try:
        service = _drive_service(creds)
        folder_id = _find_folder(service, DRIVE_FOLDER_NAME)
        if folder_id:
            remote = _find_db_file(service, folder_id)
            if remote:
                status["remote_file"] = {
                    "id": remote["id"],
                    "modified": remote.get("modifiedTime"),
                }
    except Exception:
        pass

    return status
