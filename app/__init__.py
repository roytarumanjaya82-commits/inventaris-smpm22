from flask import Flask
from flask_login import LoginManager

from config import SECRET_KEY, SCHOOL_NAME, SCHOOL_SHORT, RESOURCE_DIR


login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Silakan masuk terlebih dahulu."
login_manager.login_message_category = "warning"


def create_app():
    template_folder = str(RESOURCE_DIR / "app" / "templates")
    static_folder = str(RESOURCE_DIR / "app" / "static")

    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder,
    )
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB upload Excel

    login_manager.init_app(app)

    from app.db import init_db
    from app.models import User
    from app.services import google_drive as gdrive

    init_db()

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))

    @app.context_processor
    def inject_globals():
        return {
            "school_name": SCHOOL_NAME,
            "school_short": SCHOOL_SHORT,
            "drive_connected": gdrive.is_connected(),
            "drive_offline": gdrive.is_offline(),
        }

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.barang import barang_bp
    from app.routes.peminjaman import peminjaman_bp
    from app.routes.sync import sync_bp
    from app.routes.laporan import laporan_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(barang_bp)
    app.register_blueprint(peminjaman_bp)
    app.register_blueprint(sync_bp)
    app.register_blueprint(laporan_bp)

    return app
