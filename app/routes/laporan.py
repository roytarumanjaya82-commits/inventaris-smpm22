from datetime import datetime
from io import BytesIO

from flask import Blueprint, render_template, request, send_file
from flask_login import login_required, current_user
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from app import models
from config import (
    SCHOOL_ADDRESS,
    SCHOOL_KEPALA,
    SCHOOL_KOTA,
    SCHOOL_NAME,
    SCHOOL_NBM_KEPALA,
    SCHOOL_NPSN,
    SCHOOL_WEBSITE,
)

laporan_bp = Blueprint("laporan", __name__, url_prefix="/laporan")


def _school_meta():
    return {
        "nama": SCHOOL_NAME,
        "npsn": SCHOOL_NPSN,
        "alamat": SCHOOL_ADDRESS,
        "website": SCHOOL_WEBSITE,
        "kepala": SCHOOL_KEPALA,
        "nbm_kepala": SCHOOL_NBM_KEPALA,
        "kota": SCHOOL_KOTA,
    }


def _report_stats(items):
    total_jenis = len(items)
    total_unit = sum(int(b.get("jumlah") or 0) for b in items)
    tersedia = sum(int(b.get("jumlah_tersedia") or 0) for b in items)
    by_kondisi = {}
    by_kategori = {}
    for b in items:
        kondisi = b.get("kondisi") or "Lainnya"
        by_kondisi[kondisi] = by_kondisi.get(kondisi, 0) + 1
        kat = b.get("kategori_nama") or "Tanpa Kategori"
        by_kategori[kat] = by_kategori.get(kat, 0) + 1
    return {
        "total_jenis": total_jenis,
        "total_unit": total_unit,
        "tersedia": tersedia,
        "dipinjam_unit": max(0, total_unit - tersedia),
        "by_kondisi": sorted(by_kondisi.items(), key=lambda x: (-x[1], x[0])),
        "by_kategori": sorted(by_kategori.items(), key=lambda x: (-x[1], x[0])),
    }


@laporan_bp.route("/")
@login_required
def index():
    return render_template("laporan/index.html")


@laporan_bp.route("/barang")
@login_required
def barang():
    q = request.args.get("q", "").strip()
    kategori_id = request.args.get("kategori_id") or None
    kondisi = request.args.get("kondisi") or None
    if kategori_id:
        kategori_id = int(kategori_id)

    items = models.list_barang(
        q=q or None,
        kategori_id=kategori_id,
        kondisi=kondisi,
    )
    stats = _report_stats(items)
    now = datetime.now()
    bulan = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    ]
    tanggal_cetak = f"{now.day} {bulan[now.month]} {now.year}"

    return render_template(
        "laporan/barang.html",
        items=items,
        stats=stats,
        school=_school_meta(),
        petugas=current_user.nama_lengkap,
        tanggal_cetak=tanggal_cetak,
        waktu_cetak=now.strftime("%d/%m/%Y %H:%M"),
        q=q,
        kategori_id=kategori_id,
        kondisi=kondisi,
        kategori_list=models.list_kategori(),
        print_mode=request.args.get("print") == "1",
    )


@laporan_bp.route("/export-excel")
@login_required
def export_excel():
    wb = Workbook()

    ws = wb.active
    ws.title = "Barang"
    headers = [
        "Kode", "Nama", "Kategori", "Lokasi", "Jumlah", "Tersedia",
        "Satuan", "Kondisi", "Sumber", "Tahun", "Harga", "Keterangan",
    ]
    ws.append(headers)
    header_fill = PatternFill("solid", fgColor="1B5E4A")
    header_font = Font(color="FFFFFF", bold=True)
    for col, _ in enumerate(headers, 1):
        cell = ws.cell(1, col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for b in models.list_barang():
        ws.append([
            b["kode"],
            b["nama"],
            b.get("kategori_nama") or "",
            b.get("lokasi_nama") or "",
            b["jumlah"],
            b["jumlah_tersedia"],
            b["satuan"],
            b["kondisi"],
            b.get("sumber") or "",
            b.get("tahun_perolehan") or "",
            b.get("harga_perolehan") or 0,
            b.get("keterangan") or "",
        ])

    ws2 = wb.create_sheet("Peminjaman")
    headers2 = [
        "Kode Barang", "Nama Barang", "Peminjam", "Kelas/Unit", "Jumlah",
        "Tgl Pinjam", "Rencana Kembali", "Tgl Kembali", "Status", "Petugas",
    ]
    ws2.append(headers2)
    for col, _ in enumerate(headers2, 1):
        cell = ws2.cell(1, col)
        cell.fill = header_fill
        cell.font = header_font

    for p in models.list_peminjaman():
        ws2.append([
            p.get("barang_kode"),
            p.get("barang_nama"),
            p["peminjam"],
            p.get("kelas_unit") or "",
            p["jumlah"],
            p["tanggal_pinjam"],
            p.get("tanggal_kembali_rencana") or "",
            p.get("tanggal_kembali_aktual") or "",
            p["status"],
            p.get("petugas") or "",
        ])

    for sheet in (ws, ws2):
        for column in sheet.columns:
            max_len = 0
            col_letter = column[0].column_letter
            for cell in column:
                max_len = max(max_len, len(str(cell.value or "")))
            sheet.column_dimensions[col_letter].width = min(max_len + 2, 40)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="laporan_inventaris_smpm22.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
