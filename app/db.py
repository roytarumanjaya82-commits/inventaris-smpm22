"""Koneksi & inisialisasi database MySQL."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime

import pymysql
from pymysql.cursors import DictCursor
from werkzeug.security import generate_password_hash

from config import (
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)


class DB:
    """Wrapper agar API mirip sqlite (execute → fetchone/fetchall/lastrowid)."""

    def __init__(self, conn):
        self._conn = conn
        self._cursor = conn.cursor()

    def execute(self, sql, params=None):
        self._cursor.execute(sql, params or ())
        return self

    def executemany(self, sql, seq_of_params):
        self._cursor.executemany(sql, seq_of_params)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        try:
            self._cursor.close()
        finally:
            self._conn.close()


def _connect(database=None):
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=database,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )


def ensure_database():
    """Buat database jika belum ada."""
    conn = _connect(database=None)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()


def get_connection() -> DB:
    return DB(_connect(database=MYSQL_DATABASE))


@contextmanager
def db_session():
    db = get_connection()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(80) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        nama_lengkap VARCHAR(150) NOT NULL,
        role VARCHAR(30) NOT NULL DEFAULT 'petugas',
        email VARCHAR(150) NULL,
        created_at VARCHAR(32) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS kategori (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nama VARCHAR(100) NOT NULL UNIQUE,
        deskripsi TEXT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS lokasi (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nama VARCHAR(100) NOT NULL UNIQUE,
        gedung VARCHAR(100) NULL,
        keterangan TEXT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS barang (
        id INT AUTO_INCREMENT PRIMARY KEY,
        kode VARCHAR(50) NOT NULL UNIQUE,
        nama VARCHAR(200) NOT NULL,
        kategori_id INT NULL,
        lokasi_id INT NULL,
        jumlah INT NOT NULL DEFAULT 1,
        jumlah_tersedia INT NOT NULL DEFAULT 1,
        satuan VARCHAR(30) DEFAULT 'unit',
        kondisi VARCHAR(40) DEFAULT 'Baik',
        sumber VARCHAR(100) NULL,
        tahun_perolehan INT NULL,
        harga_perolehan DOUBLE DEFAULT 0,
        keterangan TEXT NULL,
        created_at VARCHAR(32) NOT NULL,
        updated_at VARCHAR(32) NOT NULL,
        CONSTRAINT fk_barang_kategori
            FOREIGN KEY (kategori_id) REFERENCES kategori(id) ON DELETE SET NULL,
        CONSTRAINT fk_barang_lokasi
            FOREIGN KEY (lokasi_id) REFERENCES lokasi(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS peminjaman (
        id INT AUTO_INCREMENT PRIMARY KEY,
        barang_id INT NOT NULL,
        peminjam VARCHAR(150) NOT NULL,
        kelas_unit VARCHAR(80) NULL,
        jumlah INT NOT NULL DEFAULT 1,
        tanggal_pinjam VARCHAR(20) NOT NULL,
        tanggal_kembali_rencana VARCHAR(20) NULL,
        tanggal_kembali_aktual VARCHAR(20) NULL,
        status VARCHAR(30) NOT NULL DEFAULT 'Dipinjam',
        petugas VARCHAR(150) NULL,
        keterangan TEXT NULL,
        CONSTRAINT fk_peminjaman_barang
            FOREIGN KEY (barang_id) REFERENCES barang(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS sync_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        aksi VARCHAR(40) NOT NULL,
        status VARCHAR(40) NOT NULL,
        pesan TEXT NULL,
        created_at VARCHAR(32) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS app_meta (
        meta_key VARCHAR(80) PRIMARY KEY,
        meta_value TEXT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]


def init_db():
    ensure_database()
    with db_session() as conn:
        for stmt in SCHEMA_STATEMENTS:
            conn.execute(stmt)

        admin = conn.execute(
            "SELECT id FROM users WHERE username = %s", ("admin",)
        ).fetchone()
        if not admin:
            now = datetime.now().isoformat(timespec="seconds")
            conn.execute(
                """
                INSERT INTO users (username, password_hash, nama_lengkap, role, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    "admin",
                    generate_password_hash("admin123"),
                    "Administrator",
                    "admin",
                    now,
                ),
            )

        default_kategori = [
            ("Elektronik", "Perangkat elektronik & IT"),
            ("Furniture", "Meja, kursi, lemari, dll"),
            ("Alat Olahraga", "Peralatan olahraga"),
            ("Alat Laboratorium", "Peralatan lab IPA/komputer"),
            ("ATK", "Alat tulis kantor"),
            ("Lainnya", "Inventaris lainnya"),
        ]
        for nama, deskripsi in default_kategori:
            exists = conn.execute(
                "SELECT id FROM kategori WHERE nama = %s", (nama,)
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO kategori (nama, deskripsi) VALUES (%s, %s)",
                    (nama, deskripsi),
                )

        default_lokasi = [
            ("Ruang Guru", "Gedung Utama", None),
            ("Ruang Kepala Sekolah", "Gedung Utama", None),
            ("Ruang Tata Usaha", "Gedung Utama", None),
            ("Lab Komputer", "Gedung Lab", None),
            ("Lab IPA", "Gedung Lab", None),
            ("Perpustakaan", "Gedung Utama", None),
            ("Aula", "Gedung Utama", None),
            ("Lapangan", "Outdoor", None),
            ("Gudang", "Gedung Belakang", None),
        ]
        for nama, gedung, ket in default_lokasi:
            exists = conn.execute(
                "SELECT id FROM lokasi WHERE nama = %s", (nama,)
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO lokasi (nama, gedung, keterangan) VALUES (%s, %s, %s)",
                    (nama, gedung, ket),
                )

        meta = conn.execute(
            "SELECT meta_value FROM app_meta WHERE meta_key = %s", ("initialized",)
        ).fetchone()
        if not meta:
            conn.execute(
                "INSERT INTO app_meta (meta_key, meta_value) VALUES (%s, %s)",
                ("initialized", datetime.now().isoformat(timespec="seconds")),
            )


def mysql_status() -> dict:
    try:
        db = get_connection()
        row = db.execute("SELECT DATABASE() AS db_name").fetchone()
        count = db.execute("SELECT COUNT(*) AS c FROM barang").fetchone()["c"]
        db.close()
        return {
            "ok": True,
            "host": MYSQL_HOST,
            "port": MYSQL_PORT,
            "database": row["db_name"] if row else MYSQL_DATABASE,
            "barang_count": count,
            "error": None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "host": MYSQL_HOST,
            "port": MYSQL_PORT,
            "database": MYSQL_DATABASE,
            "barang_count": 0,
            "error": str(exc),
        }
