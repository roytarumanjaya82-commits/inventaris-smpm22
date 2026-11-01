from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import login_required, current_user

from app.models import list_sync_log
from app.services import google_drive as gdrive

sync_bp = Blueprint("sync", __name__, url_prefix="/sync")


@sync_bp.route("/")
@login_required
def index():
    status = gdrive.drive_status()
    logs = list_sync_log()
    return render_template("sync.html", status=status, logs=logs)


@sync_bp.route("/google/login")
@login_required
def google_login():
    if gdrive.is_offline() and not gdrive.secrets_available():
        flash(
            "File credentials/client_secret.json belum tersedia. "
            "Ikuti petunjuk di README untuk setup Google Cloud.",
            "warning",
        )
        return redirect(url_for("sync.index"))

    redirect_uri = url_for("sync.google_callback", _external=True)
    try:
        flow = gdrive.get_auth_flow(redirect_uri)
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        session["oauth_state"] = state
        return redirect(auth_url)
    except Exception as exc:
        flash(f"Gagal memulai login Google: {exc}", "danger")
        return redirect(url_for("sync.index"))


@sync_bp.route("/google/callback")
@login_required
def google_callback():
    state = session.get("oauth_state")
    redirect_uri = url_for("sync.google_callback", _external=True)
    try:
        flow = gdrive.get_auth_flow(redirect_uri)
        flow.fetch_token(authorization_response=request.url)
        creds = flow.credentials
        gdrive.save_credentials(creds)
        info = gdrive.get_user_info(creds) or {}
        email = info.get("email", "akun Google")
        flash(f"Terhubung ke Google Drive sebagai {email}.", "success")
    except Exception as exc:
        flash(f"Login Google gagal: {exc}", "danger")
    return redirect(url_for("sync.index"))


@sync_bp.route("/google/logout", methods=["POST"])
@login_required
def google_logout():
    gdrive.clear_credentials()
    flash("Koneksi Google Drive diputus.", "info")
    return redirect(url_for("sync.index"))


@sync_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    if not current_user.is_admin:
        flash("Hanya admin yang dapat mengunggah ke Drive.", "warning")
        return redirect(url_for("sync.index"))
    try:
        result = gdrive.upload_database()
        flash(result["message"], "success")
    except Exception as exc:
        flash(str(exc), "danger")
    return redirect(url_for("sync.index"))


@sync_bp.route("/download", methods=["POST"])
@login_required
def download():
    if not current_user.is_admin:
        flash("Hanya admin yang dapat mengunduh dari Drive.", "warning")
        return redirect(url_for("sync.index"))
    try:
        result = gdrive.download_database(backup_local=True)
        flash(result["message"], "success")
    except Exception as exc:
        flash(str(exc), "danger")
    return redirect(url_for("sync.index"))
