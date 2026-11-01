from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from app.db import db_session, get_connection


class User(UserMixin):
    def __init__(self, row):
        self.id = row["id"]
        self.username = row["username"]
        self.password_hash = row["password_hash"]
        self.nama_lengkap = row["nama_lengkap"]
        self.role = row["role"]
        self.email = row["email"]

    @staticmethod
    def get_by_id(user_id):
        conn = get_connection()
        row = conn.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()
        conn.close()
        return User(row) if row else None

    @staticmethod
    def get_by_username(username):
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE username = %s", (username,)
        ).fetchone()
        conn.close()
        return User(row) if row else None

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"


def row_to_dict(row):
    return dict(row) if row else None


# --- Kategori ---
def list_kategori():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM kategori ORDER BY nama").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_kategori(nama, deskripsi=""):
    with db_session() as conn:
        conn.execute(
            "INSERT INTO kategori (nama, deskripsi) VALUES (%s, %s)",
            (nama, deskripsi),
        )


# --- Lokasi ---
def list_lokasi():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM lokasi ORDER BY nama").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_lokasi(nama, gedung="", keterangan=""):
    with db_session() as conn:
        conn.execute(
            "INSERT INTO lokasi (nama, gedung, keterangan) VALUES (%s, %s, %s)",
            (nama, gedung, keterangan),
        )


# --- Barang ---
def list_barang(q=None, kategori_id=None, kondisi=None):
    conn = get_connection()
    sql = """
        SELECT b.*, k.nama AS kategori_nama, l.nama AS lokasi_nama
        FROM barang b
        LEFT JOIN kategori k ON k.id = b.kategori_id
        LEFT JOIN lokasi l ON l.id = b.lokasi_id
        WHERE 1=1
    """
    params = []
    if q:
        sql += " AND (b.nama LIKE %s OR b.kode LIKE %s OR b.keterangan LIKE %s)"
        like = f"%{q}%"
        params.extend([like, like, like])
    if kategori_id:
        sql += " AND b.kategori_id = %s"
        params.append(kategori_id)
    if kondisi:
        sql += " AND b.kondisi = %s"
        params.append(kondisi)
    sql += " ORDER BY b.nama"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_barang(barang_id):
    conn = get_connection()
    row = conn.execute(
        """
        SELECT b.*, k.nama AS kategori_nama, l.nama AS lokasi_nama
        FROM barang b
        LEFT JOIN kategori k ON k.id = b.kategori_id
        LEFT JOIN lokasi l ON l.id = b.lokasi_id
        WHERE b.id = %s
        """,
        (barang_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def next_kode_barang():
    conn = get_connection()
    row = conn.execute(
        "SELECT kode FROM barang WHERE kode LIKE 'INV-%%' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return "INV-0001"
    try:
        num = int(row["kode"].split("-")[1]) + 1
    except (IndexError, ValueError):
        num = 1
    return f"INV-{num:04d}"


def create_barang(data):
    now = datetime.now().isoformat(timespec="seconds")
    jumlah = int(data.get("jumlah") or 1)
    with db_session() as conn:
        cur = conn.execute(
            """
            INSERT INTO barang (
                kode, nama, kategori_id, lokasi_id, jumlah, jumlah_tersedia,
                satuan, kondisi, sumber, tahun_perolehan, harga_perolehan,
                keterangan, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data["kode"],
                data["nama"],
                data.get("kategori_id") or None,
                data.get("lokasi_id") or None,
                jumlah,
                jumlah,
                data.get("satuan") or "unit",
                data.get("kondisi") or "Baik",
                data.get("sumber") or "",
                data.get("tahun_perolehan") or None,
                float(data.get("harga_perolehan") or 0),
                data.get("keterangan") or "",
                now,
                now,
            ),
        )
        return cur.lastrowid


def update_barang(barang_id, data):
    now = datetime.now().isoformat(timespec="seconds")
    current = get_barang(barang_id)
    if not current:
        return False
    jumlah = int(data.get("jumlah") or current["jumlah"])
    dipinjam = current["jumlah"] - current["jumlah_tersedia"]
    jumlah_tersedia = max(0, jumlah - dipinjam)
    with db_session() as conn:
        conn.execute(
            """
            UPDATE barang SET
                kode=%s, nama=%s, kategori_id=%s, lokasi_id=%s, jumlah=%s,
                jumlah_tersedia=%s, satuan=%s, kondisi=%s, sumber=%s,
                tahun_perolehan=%s, harga_perolehan=%s, keterangan=%s, updated_at=%s
            WHERE id=%s
            """,
            (
                data["kode"],
                data["nama"],
                data.get("kategori_id") or None,
                data.get("lokasi_id") or None,
                jumlah,
                jumlah_tersedia,
                data.get("satuan") or "unit",
                data.get("kondisi") or "Baik",
                data.get("sumber") or "",
                data.get("tahun_perolehan") or None,
                float(data.get("harga_perolehan") or 0),
                data.get("keterangan") or "",
                now,
                barang_id,
            ),
        )
    return True


def delete_barang(barang_id):
    with db_session() as conn:
        conn.execute("DELETE FROM barang WHERE id = %s", (barang_id,))


# --- Peminjaman ---
def list_peminjaman(status=None):
    conn = get_connection()
    sql = """
        SELECT p.*, b.nama AS barang_nama, b.kode AS barang_kode
        FROM peminjaman p
        JOIN barang b ON b.id = p.barang_id
        WHERE 1=1
    """
    params = []
    if status:
        sql += " AND p.status = %s"
        params.append(status)
    sql += " ORDER BY p.id DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_peminjaman(data, petugas=""):
    barang = get_barang(int(data["barang_id"]))
    if not barang:
        raise ValueError("Barang tidak ditemukan.")
    jumlah = int(data.get("jumlah") or 1)
    if jumlah > barang["jumlah_tersedia"]:
        raise ValueError("Stok tersedia tidak mencukupi.")
    now = datetime.now().strftime("%Y-%m-%d")
    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO peminjaman (
                barang_id, peminjam, kelas_unit, jumlah, tanggal_pinjam,
                tanggal_kembali_rencana, status, petugas, keterangan
            ) VALUES (%s, %s, %s, %s, %s, %s, 'Dipinjam', %s, %s)
            """,
            (
                data["barang_id"],
                data["peminjam"],
                data.get("kelas_unit") or "",
                jumlah,
                data.get("tanggal_pinjam") or now,
                data.get("tanggal_kembali_rencana") or None,
                petugas,
                data.get("keterangan") or "",
            ),
        )
        conn.execute(
            "UPDATE barang SET jumlah_tersedia = jumlah_tersedia - %s WHERE id = %s",
            (jumlah, data["barang_id"]),
        )


def kembalikan_peminjaman(peminjaman_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM peminjaman WHERE id = %s", (peminjaman_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise ValueError("Data peminjaman tidak ditemukan.")
    if row["status"] != "Dipinjam":
        raise ValueError("Barang sudah dikembalikan.")
    now = datetime.now().strftime("%Y-%m-%d")
    with db_session() as conn:
        conn.execute(
            """
            UPDATE peminjaman
            SET status = 'Dikembalikan', tanggal_kembali_aktual = %s
            WHERE id = %s
            """,
            (now, peminjaman_id),
        )
        conn.execute(
            "UPDATE barang SET jumlah_tersedia = jumlah_tersedia + %s WHERE id = %s",
            (row["jumlah"], row["barang_id"]),
        )


# --- Dashboard stats ---
def dashboard_stats():
    conn = get_connection()
    total_barang = conn.execute("SELECT COUNT(*) AS c FROM barang").fetchone()["c"]
    total_unit = conn.execute(
        "SELECT COALESCE(SUM(jumlah),0) AS c FROM barang"
    ).fetchone()["c"]
    tersedia = conn.execute(
        "SELECT COALESCE(SUM(jumlah_tersedia),0) AS c FROM barang"
    ).fetchone()["c"]
    dipinjam = conn.execute(
        "SELECT COUNT(*) AS c FROM peminjaman WHERE status = 'Dipinjam'"
    ).fetchone()["c"]
    rusak = conn.execute(
        "SELECT COUNT(*) AS c FROM barang WHERE kondisi IN ('Rusak','Hilang')"
    ).fetchone()["c"]
    by_kondisi = conn.execute(
        "SELECT kondisi, COUNT(*) AS c FROM barang GROUP BY kondisi"
    ).fetchall()
    by_kategori = conn.execute(
        """
        SELECT COALESCE(k.nama, 'Tanpa Kategori') AS nama, COUNT(b.id) AS c
        FROM barang b
        LEFT JOIN kategori k ON k.id = b.kategori_id
        GROUP BY k.nama
        ORDER BY c DESC
        """
    ).fetchall()
    recent = conn.execute(
        """
        SELECT b.*, k.nama AS kategori_nama
        FROM barang b
        LEFT JOIN kategori k ON k.id = b.kategori_id
        ORDER BY b.id DESC LIMIT 5
        """
    ).fetchall()
    conn.close()
    return {
        "total_barang": total_barang,
        "total_unit": total_unit,
        "tersedia": tersedia,
        "dipinjam": dipinjam,
        "rusak": rusak,
        "by_kondisi": [dict(r) for r in by_kondisi],
        "by_kategori": [dict(r) for r in by_kategori],
        "recent": [dict(r) for r in recent],
    }


def add_sync_log(aksi, status, pesan=""):
    with db_session() as conn:
        conn.execute(
            "INSERT INTO sync_log (aksi, status, pesan, created_at) VALUES (%s, %s, %s, %s)",
            (aksi, status, pesan, datetime.now().isoformat(timespec="seconds")),
        )


def list_sync_log(limit=20):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM sync_log ORDER BY id DESC LIMIT %s", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_user(username, password, nama_lengkap, role="petugas", email=""):
    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO users (username, password_hash, nama_lengkap, role, email, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                username,
                generate_password_hash(password),
                nama_lengkap,
                role,
                email,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def list_users():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, username, nama_lengkap, role, email, created_at FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
