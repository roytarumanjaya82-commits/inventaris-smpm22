from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required

from app import models
from app.services import excel_import

barang_bp = Blueprint("barang", __name__, url_prefix="/barang")


@barang_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    kategori_id = request.args.get("kategori_id") or None
    kondisi = request.args.get("kondisi") or None
    if kategori_id:
        kategori_id = int(kategori_id)
    items = models.list_barang(q=q or None, kategori_id=kategori_id, kondisi=kondisi)
    return render_template(
        "barang/index.html",
        items=items,
        kategori_list=models.list_kategori(),
        q=q,
        kategori_id=kategori_id,
        kondisi=kondisi,
    )


@barang_bp.route("/tambah", methods=["GET", "POST"])
@login_required
def tambah():
    if request.method == "POST":
        data = {
            "kode": request.form.get("kode", "").strip(),
            "nama": request.form.get("nama", "").strip(),
            "kategori_id": request.form.get("kategori_id") or None,
            "lokasi_id": request.form.get("lokasi_id") or None,
            "jumlah": request.form.get("jumlah") or 1,
            "satuan": request.form.get("satuan") or "unit",
            "kondisi": request.form.get("kondisi") or "Baik",
            "sumber": request.form.get("sumber") or "",
            "tahun_perolehan": request.form.get("tahun_perolehan") or None,
            "harga_perolehan": request.form.get("harga_perolehan") or 0,
            "keterangan": request.form.get("keterangan") or "",
        }
        if not data["kode"] or not data["nama"]:
            flash("Kode dan nama barang wajib diisi.", "danger")
        else:
            try:
                models.create_barang(data)
                flash("Barang berhasil ditambahkan.", "success")
                return redirect(url_for("barang.index"))
            except Exception as exc:
                flash(f"Gagal menyimpan: {exc}", "danger")

    return render_template(
        "barang/form.html",
        item=None,
        kode_default=models.next_kode_barang(),
        kategori_list=models.list_kategori(),
        lokasi_list=models.list_lokasi(),
        title="Tambah Barang",
    )


@barang_bp.route("/<int:barang_id>/edit", methods=["GET", "POST"])
@login_required
def edit(barang_id):
    item = models.get_barang(barang_id)
    if not item:
        flash("Barang tidak ditemukan.", "danger")
        return redirect(url_for("barang.index"))

    if request.method == "POST":
        data = {
            "kode": request.form.get("kode", "").strip(),
            "nama": request.form.get("nama", "").strip(),
            "kategori_id": request.form.get("kategori_id") or None,
            "lokasi_id": request.form.get("lokasi_id") or None,
            "jumlah": request.form.get("jumlah") or 1,
            "satuan": request.form.get("satuan") or "unit",
            "kondisi": request.form.get("kondisi") or "Baik",
            "sumber": request.form.get("sumber") or "",
            "tahun_perolehan": request.form.get("tahun_perolehan") or None,
            "harga_perolehan": request.form.get("harga_perolehan") or 0,
            "keterangan": request.form.get("keterangan") or "",
        }
        try:
            models.update_barang(barang_id, data)
            flash("Barang berhasil diperbarui.", "success")
            return redirect(url_for("barang.index"))
        except Exception as exc:
            flash(f"Gagal memperbarui: {exc}", "danger")

    return render_template(
        "barang/form.html",
        item=item,
        kode_default=item["kode"],
        kategori_list=models.list_kategori(),
        lokasi_list=models.list_lokasi(),
        title="Edit Barang",
    )


@barang_bp.route("/<int:barang_id>/hapus", methods=["POST"])
@login_required
def hapus(barang_id):
    models.delete_barang(barang_id)
    flash("Barang dihapus.", "info")
    return redirect(url_for("barang.index"))


@barang_bp.route("/blanko-excel")
@login_required
def blanko_excel():
    buffer = excel_import.build_blank_template()
    return send_file(
        buffer,
        as_attachment=True,
        download_name="blanko_inventaris_smpm22.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@barang_bp.route("/import-excel", methods=["POST"])
@login_required
def import_excel():
    file = request.files.get("file_excel")
    if not file or not file.filename:
        flash("Pilih file Excel (.xlsx) terlebih dahulu.", "warning")
        return redirect(url_for("barang.index"))

    filename = file.filename.lower()
    if not (filename.endswith(".xlsx") or filename.endswith(".xlsm")):
        flash("Format tidak didukung. Gunakan file .xlsx dari blanko Excel.", "danger")
        return redirect(url_for("barang.index"))

    try:
        result = excel_import.import_barang_from_excel(file)
        msg = (
            f"Impor selesai: {result['created']} ditambah, "
            f"{result['updated']} diperbarui, {result['skipped']} dilewati."
        )
        flash(msg, "success")
        for err in result.get("errors") or []:
            flash(err, "warning")
    except Exception as exc:
        flash(f"Gagal impor Excel: {exc}", "danger")

    return redirect(url_for("barang.index"))


@barang_bp.route("/kategori", methods=["GET", "POST"])
@login_required
def kategori():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        deskripsi = request.form.get("deskripsi", "").strip()
        edit_id = request.form.get("id") or None
        if nama:
            try:
                if edit_id:
                    models.update_kategori(int(edit_id), nama, deskripsi)
                    flash("Kategori berhasil diperbarui.", "success")
                else:
                    models.add_kategori(nama, deskripsi)
                    flash("Kategori ditambahkan.", "success")
            except Exception as exc:
                flash(f"Gagal: {exc}", "danger")
        return redirect(url_for("barang.kategori"))

    edit_item = None
    edit_id = request.args.get("edit")
    if edit_id:
        edit_item = models.get_kategori(int(edit_id))
        if not edit_item:
            flash("Kategori tidak ditemukan.", "warning")
            return redirect(url_for("barang.kategori"))

    return render_template(
        "barang/kategori.html",
        items=models.list_kategori(),
        edit_item=edit_item,
    )


@barang_bp.route("/kategori/<int:kategori_id>/hapus", methods=["POST"])
@login_required
def hapus_kategori(kategori_id):
    try:
        models.delete_kategori(kategori_id)
        flash("Kategori dihapus.", "info")
    except Exception as exc:
        flash(f"Gagal menghapus kategori: {exc}", "danger")
    return redirect(url_for("barang.kategori"))


@barang_bp.route("/lokasi", methods=["GET", "POST"])
@login_required
def lokasi():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        gedung = request.form.get("gedung", "").strip()
        keterangan = request.form.get("keterangan", "").strip()
        edit_id = request.form.get("id") or None
        if nama:
            try:
                if edit_id:
                    models.update_lokasi(int(edit_id), nama, gedung, keterangan)
                    flash("Lokasi berhasil diperbarui.", "success")
                else:
                    models.add_lokasi(nama, gedung, keterangan)
                    flash("Lokasi ditambahkan.", "success")
            except Exception as exc:
                flash(f"Gagal: {exc}", "danger")
        return redirect(url_for("barang.lokasi"))

    edit_item = None
    edit_id = request.args.get("edit")
    if edit_id:
        edit_item = models.get_lokasi(int(edit_id))
        if not edit_item:
            flash("Lokasi tidak ditemukan.", "warning")
            return redirect(url_for("barang.lokasi"))

    return render_template(
        "barang/lokasi.html",
        items=models.list_lokasi(),
        edit_item=edit_item,
    )


@barang_bp.route("/lokasi/<int:lokasi_id>/hapus", methods=["POST"])
@login_required
def hapus_lokasi(lokasi_id):
    try:
        models.delete_lokasi(lokasi_id)
        flash("Lokasi dihapus.", "info")
    except Exception as exc:
        flash(f"Gagal menghapus lokasi: {exc}", "danger")
    return redirect(url_for("barang.lokasi"))
