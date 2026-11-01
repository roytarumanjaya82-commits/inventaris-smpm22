"""Blanko Excel & impor massal data barang."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from app import models

HEADERS = [
    "Kode",
    "Nama",
    "Kategori",
    "Lokasi",
    "Jumlah",
    "Satuan",
    "Kondisi",
    "Sumber",
    "Tahun",
    "Harga",
    "Keterangan",
]

HEADER_ALIASES = {
    "kode": "Kode",
    "kode barang": "Kode",
    "nama": "Nama",
    "nama barang": "Nama",
    "kategori": "Kategori",
    "lokasi": "Lokasi",
    "jumlah": "Jumlah",
    "qty": "Jumlah",
    "satuan": "Satuan",
    "kondisi": "Kondisi",
    "sumber": "Sumber",
    "tahun": "Tahun",
    "tahun perolehan": "Tahun",
    "harga": "Harga",
    "harga perolehan": "Harga",
    "keterangan": "Keterangan",
    "ket": "Keterangan",
}

KONDISI_VALID = {"Baik", "Rusak Ringan", "Rusak", "Hilang"}


def _style_header(ws, count: int):
    fill = PatternFill("solid", fgColor="1B5E4A")
    font = Font(color="FFFFFF", bold=True)
    thin = Border(
        left=Side(style="thin", color="D5E2DC"),
        right=Side(style="thin", color="D5E2DC"),
        top=Side(style="thin", color="D5E2DC"),
        bottom=Side(style="thin", color="D5E2DC"),
    )
    for col in range(1, count + 1):
        cell = ws.cell(1, col)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin
    ws.row_dimensions[1].height = 22


def _autosize(ws, max_width=36):
    for column in ws.columns:
        length = 0
        letter = get_column_letter(column[0].column)
        for cell in column:
            length = max(length, len(str(cell.value or "")))
        ws.column_dimensions[letter].width = min(max(length + 2, 12), max_width)


def build_blank_template() -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Barang"
    ws.append(HEADERS)
    _style_header(ws, len(HEADERS))

    # Contoh 1 baris
    ws.append([
        "INV-0001",
        "Laptop Acer Aspire 5",
        "Elektronik",
        "Lab Komputer",
        5,
        "unit",
        "Baik",
        "BOS",
        2024,
        7500000,
        "Contoh baris — hapus lalu isi data asli",
    ])

    # Validasi kondisi
    dv = DataValidation(
        type="list",
        formula1='"Baik,Rusak Ringan,Rusak,Hilang"',
        allow_blank=True,
    )
    dv.error = "Pilih kondisi yang tersedia"
    dv.errorTitle = "Kondisi tidak valid"
    ws.add_data_validation(dv)
    dv.add("G2:G1000")

    _autosize(ws)

    # Sheet petunjuk
    petunjuk = wb.create_sheet("Petunjuk")
    petunjuk["A1"] = "Cara isi blanko inventaris SMPM 22 Setiabudi"
    petunjuk["A1"].font = Font(bold=True, size=13, color="1B5E4A")
    lines = [
        "1. Isi data pada sheet 'Barang'. Jangan ubah nama kolom baris 1.",
        "2. Kolom wajib: Kode dan Nama.",
        "3. Jika Kode sudah ada di sistem, data akan diperbarui (update).",
        "4. Jika Kode kosong, sistem membuat kode otomatis (INV-xxxx).",
        "5. Kategori/Lokasi diisi dengan NAMA (bukan ID). Jika belum ada, akan dibuat otomatis.",
        "6. Kondisi harus: Baik / Rusak Ringan / Rusak / Hilang.",
        "7. Hapus baris contoh sebelum mengunggah, atau biarkan — baris tanpa Nama akan dilewati.",
        "8. Simpan file sebagai .xlsx lalu unggah lewat tombol Import Excel.",
    ]
    for i, text in enumerate(lines, start=3):
        petunjuk[f"A{i}"] = text
    petunjuk.column_dimensions["A"].width = 100

    # Referensi master
    ref = wb.create_sheet("Referensi")
    ref.append(["Kategori yang tersedia", "Lokasi yang tersedia"])
    _style_header(ref, 2)
    kategori = [k["nama"] for k in models.list_kategori()]
    lokasi = [l["nama"] for l in models.list_lokasi()]
    for i in range(max(len(kategori), len(lokasi))):
        ref.append([
            kategori[i] if i < len(kategori) else "",
            lokasi[i] if i < len(lokasi) else "",
        ])
    _autosize(ref)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def _cell_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_header(value: Any) -> str | None:
    key = _cell_str(value).lower()
    return HEADER_ALIASES.get(key)


def _resolve_kategori_id(nama: str) -> int | None:
    nama = _cell_str(nama)
    if not nama:
        return None
    for k in models.list_kategori():
        if k["nama"].lower() == nama.lower():
            return k["id"]
    models.add_kategori(nama, "Ditambahkan dari impor Excel")
    for k in models.list_kategori():
        if k["nama"].lower() == nama.lower():
            return k["id"]
    return None


def _resolve_lokasi_id(nama: str) -> int | None:
    nama = _cell_str(nama)
    if not nama:
        return None
    for l in models.list_lokasi():
        if l["nama"].lower() == nama.lower():
            return l["id"]
    models.add_lokasi(nama, "", "Ditambahkan dari impor Excel")
    for l in models.list_lokasi():
        if l["nama"].lower() == nama.lower():
            return l["id"]
    return None


def _to_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_barang_by_kode(kode: str):
    from app.db import get_connection

    conn = get_connection()
    row = conn.execute("SELECT * FROM barang WHERE kode = %s", (kode,)).fetchone()
    conn.close()
    return dict(row) if row else None


def import_barang_from_excel(file_storage) -> dict:
    wb = load_workbook(file_storage, data_only=True)
    if "Barang" in wb.sheetnames:
        ws = wb["Barang"]
    else:
        ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("File Excel kosong.")

    header_row = rows[0]
    col_map: dict[str, int] = {}
    for idx, cell in enumerate(header_row):
        normalized = _normalize_header(cell)
        if normalized:
            col_map[normalized] = idx

    if "Nama" not in col_map:
        raise ValueError(
            "Kolom 'Nama' tidak ditemukan. Unduh blanko Excel lalu isi sesuai format."
        )

    created = 0
    updated = 0
    skipped = 0
    errors: list[str] = []

    for row_num, row in enumerate(rows[1:], start=2):
        if row is None or all(v is None or str(v).strip() == "" for v in row):
            continue

        def get(col_name: str, default=""):
            idx = col_map.get(col_name)
            if idx is None or idx >= len(row):
                return default
            return row[idx]

        nama = _cell_str(get("Nama"))
        if not nama:
            skipped += 1
            continue

        kode = _cell_str(get("Kode"))
        if not kode:
            kode = models.next_kode_barang()

        kondisi = _cell_str(get("Kondisi")) or "Baik"
        if kondisi not in KONDISI_VALID:
            # toleransi kapitalisasi
            matched = next((k for k in KONDISI_VALID if k.lower() == kondisi.lower()), None)
            kondisi = matched or "Baik"

        data = {
            "kode": kode,
            "nama": nama,
            "kategori_id": _resolve_kategori_id(get("Kategori")),
            "lokasi_id": _resolve_lokasi_id(get("Lokasi")),
            "jumlah": max(0, _to_int(get("Jumlah"), 1)),
            "satuan": _cell_str(get("Satuan")) or "unit",
            "kondisi": kondisi,
            "sumber": _cell_str(get("Sumber")),
            "tahun_perolehan": _to_int(get("Tahun"), 0) or None,
            "harga_perolehan": _to_float(get("Harga"), 0),
            "keterangan": _cell_str(get("Keterangan")),
        }

        try:
            existing = get_barang_by_kode(kode)
            if existing:
                models.update_barang(existing["id"], data)
                updated += 1
            else:
                models.create_barang(data)
                created += 1
        except Exception as exc:
            errors.append(f"Baris {row_num} ({kode or nama}): {exc}")
            skipped += 1

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors[:20],
    }
