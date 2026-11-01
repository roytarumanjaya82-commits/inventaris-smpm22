from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from app import models

peminjaman_bp = Blueprint("peminjaman", __name__, url_prefix="/peminjaman")


@peminjaman_bp.route("/")
@login_required
def index():
    status = request.args.get("status") or None
    items = models.list_peminjaman(status=status)
    return render_template("peminjaman/index.html", items=items, status=status)


@peminjaman_bp.route("/tambah", methods=["GET", "POST"])
@login_required
def tambah():
    if request.method == "POST":
        data = {
            "barang_id": request.form.get("barang_id"),
            "peminjam": request.form.get("peminjam", "").strip(),
            "kelas_unit": request.form.get("kelas_unit", "").strip(),
            "jumlah": request.form.get("jumlah") or 1,
            "tanggal_pinjam": request.form.get("tanggal_pinjam"),
            "tanggal_kembali_rencana": request.form.get("tanggal_kembali_rencana"),
            "keterangan": request.form.get("keterangan", "").strip(),
        }
        try:
            if not data["barang_id"] or not data["peminjam"]:
                raise ValueError("Barang dan nama peminjam wajib diisi.")
            models.create_peminjaman(data, petugas=current_user.nama_lengkap)
            flash("Peminjaman berhasil dicatat.", "success")
            return redirect(url_for("peminjaman.index"))
        except Exception as exc:
            flash(str(exc), "danger")

    barang_tersedia = [
        b for b in models.list_barang() if b["jumlah_tersedia"] > 0
    ]
    return render_template("peminjaman/form.html", barang_list=barang_tersedia)


@peminjaman_bp.route("/<int:peminjaman_id>/kembalikan", methods=["POST"])
@login_required
def kembalikan(peminjaman_id):
    try:
        models.kembalikan_peminjaman(peminjaman_id)
        flash("Barang berhasil dikembalikan.", "success")
    except Exception as exc:
        flash(str(exc), "danger")
    return redirect(url_for("peminjaman.index"))
