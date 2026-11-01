import os
import socket
import sys

os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")


def get_lan_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except OSError:
        return "IP-KOMPUTER-INI"


if __name__ == "__main__":
    try:
        from app import create_app
        app = create_app()
    except Exception as exc:
        print("\n[ERROR] Gagal koneksi / inisialisasi MySQL.")
        print(f"Detail : {exc}")
        print("\nPastikan:")
        print("  1. MySQL / MariaDB / XAMPP sudah berjalan")
        print("  2. Pengaturan di file .env sudah benar")
        print("     MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE")
        print("  3. User MySQL boleh membuat database\n")
        sys.exit(1)

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    lan_ip = get_lan_ip()

    print("\n" + "=" * 56)
    print("  Inventaris SMP Muhammadiyah 22 Setiabudi Pamulang")
    print("  Database: MySQL")
    print("=" * 56)
    print(f"  Komputer ini : http://127.0.0.1:{port}")
    print(f"  Laptop / HP  : http://{lan_ip}:{port}")
    print("  (HP/laptop harus satu WiFi dengan komputer server)")
    print("=" * 56 + "\n")

    app.run(host=host, port=port, debug=False)
