from flask import Blueprint, render_template
from flask_login import login_required

from app.models import dashboard_stats
from app.services import google_drive as gdrive

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def dashboard():
    stats = dashboard_stats()
    drive = gdrive.drive_status()
    return render_template("dashboard.html", stats=stats, drive=drive)
