"""
Launcher untuk mode .exe (Windows).
Double-click InventarisSMPM22.exe → server jalan + browser terbuka.
"""

import os
import socket
import sys
import threading
import time
import webbrowser

os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

if getattr(sys, "frozen", False):
    sys.path.insert(0, getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))


def get_lan_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except OSError:
        return "127.0.0.1"


def open_browser(url):
    time.sleep(1.2)
    webbrowser.open(url)


def main():
    try:
        from app import create_app
        app = create_app()
    except Exception as exc:
        print("\n[ERROR] Gagal koneksi / inisialisasi MySQL.")
        print(f"Detail : {exc}")
        print("\nPastikan MySQL/XAMPP berjalan dan file .env benar.")
        print("Tekan Enter untuk keluar...")
        input()
        sys.exit(1)

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    lan_ip = get_lan_ip()
    local_url = f"http://127.0.0.1:{port}"
    lan_url = f"http://{lan_ip}:{port}"

    print("=" * 60)
    print("  Inventaris SMP Muhammadiyah 22 Setiabudi Pamulang")
    print("  Database: MySQL")
    print("=" * 60)
    print(f"  PC / laptop ini : {local_url}")
    print(f"  HP / laptop lain: {lan_url}")
    print("  (satu WiFi dengan komputer yang menjalankan .exe)")
    print()
    print("  Jangan tutup jendela ini selama aplikasi dipakai.")
    print("  Tekan CTRL+C untuk menghentikan.")
    print("=" * 60)

    threading.Thread(target=open_browser, args=(local_url,), daemon=True).start()
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
