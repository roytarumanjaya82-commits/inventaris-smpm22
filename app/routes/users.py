from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import models

users_bp = Blueprint("users", __name__, url_prefix="/administrator")


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Hanya administrator yang dapat mengelola akun.", "warning")
            return redirect(url_for("main.dashboard"))
        return view(*args, **kwargs)

    return wrapped


@users_bp.route("/", methods=["GET", "POST"])
@login_required
@admin_required
def index():
    if request.method == "POST":
        edit_id = request.form.get("id") or None
        username = (request.form.get("username") or "").strip()
        nama_lengkap = (request.form.get("nama_lengkap") or "").strip()
        email = (request.form.get("email") or "").strip()
        role = (request.form.get("role") or "petugas").strip()
        password = request.form.get("password") or ""
        password2 = request.form.get("password2") or ""

        if role not in ("admin", "petugas"):
            role = "petugas"

        if not nama_lengkap:
            flash("Nama lengkap wajib diisi.", "danger")
            return redirect(url_for("users.index", edit=edit_id) if edit_id else url_for("users.index"))

        try:
            if edit_id:
                user = models.get_user(int(edit_id))
                if not user:
                    flash("Akun tidak ditemukan.", "danger")
                    return redirect(url_for("users.index"))

                # Jangan turunkan admin terakhir
                if user["role"] == "admin" and role != "admin" and models.count_admins() <= 1:
                    flash("Tidak dapat mengubah role admin terakhir.", "warning")
                    return redirect(url_for("users.index", edit=edit_id))

                if password or password2:
                    if len(password) < 6:
                        flash("Password minimal 6 karakter.", "danger")
                        return redirect(url_for("users.index", edit=edit_id))
                    if password != password2:
                        flash("Konfirmasi password tidak sama.", "danger")
                        return redirect(url_for("users.index", edit=edit_id))
                    models.update_user(
                        int(edit_id),
                        nama_lengkap=nama_lengkap,
                        role=role,
                        email=email,
                        password=password,
                    )
                else:
                    models.update_user(
                        int(edit_id),
                        nama_lengkap=nama_lengkap,
                        role=role,
                        email=email,
                    )
                flash("Data administrator diperbarui.", "success")
            else:
                if not username:
                    flash("Username wajib diisi.", "danger")
                    return redirect(url_for("users.index"))
                if len(password) < 6:
                    flash("Password minimal 6 karakter.", "danger")
                    return redirect(url_for("users.index"))
                if password != password2:
                    flash("Konfirmasi password tidak sama.", "danger")
                    return redirect(url_for("users.index"))
                if models.User.get_by_username(username):
                    flash("Username sudah digunakan.", "danger")
                    return redirect(url_for("users.index"))

                models.create_user(
                    username=username,
                    password=password,
                    nama_lengkap=nama_lengkap,
                    role=role,
                    email=email,
                )
                flash("Administrator inventaris berhasil ditambahkan.", "success")
        except Exception as exc:
            flash(f"Gagal menyimpan: {exc}", "danger")

        return redirect(url_for("users.index"))

    edit_item = None
    edit_id = request.args.get("edit")
    if edit_id:
        edit_item = models.get_user(int(edit_id))
        if not edit_item:
            flash("Akun tidak ditemukan.", "warning")
            return redirect(url_for("users.index"))

    return render_template(
        "users/index.html",
        items=models.list_users(),
        edit_item=edit_item,
    )


@users_bp.route("/<int:user_id>/hapus", methods=["POST"])
@login_required
@admin_required
def hapus(user_id):
    user = models.get_user(user_id)
    if not user:
        flash("Akun tidak ditemukan.", "danger")
        return redirect(url_for("users.index"))

    if user_id == current_user.id:
        flash("Tidak dapat menghapus akun yang sedang digunakan.", "warning")
        return redirect(url_for("users.index"))

    if user["role"] == "admin" and models.count_admins() <= 1:
        flash("Tidak dapat menghapus admin terakhir.", "warning")
        return redirect(url_for("users.index"))

    try:
        models.delete_user(user_id)
        flash("Akun administrator dihapus.", "info")
    except Exception as exc:
        flash(f"Gagal menghapus: {exc}", "danger")
    return redirect(url_for("users.index"))
