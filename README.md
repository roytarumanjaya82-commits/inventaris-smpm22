# Sistem Inventaris SMP Muhammadiyah 22 Setiabudi Pamulang

Aplikasi inventaris sekolah berbasis **Python + Flask**, database **MySQL**, dan cadangan ke **Google Drive**.

## Fitur

- Login petugas/admin (default: `admin` / `admin123`)
- CRUD data barang inventaris (kode, kategori, lokasi, kondisi, stok)
- Master kategori & lokasi
- Peminjaman & pengembalian barang
- Dashboard ringkasan
- Export laporan Excel
- Backup/restore data MySQL ke Google Drive (file JSON)

## Database MySQL

| Item | Nilai default |
|------|----------------|
| Host | `127.0.0.1` |
| Port | `3306` |
| User | `root` |
| Password | *(kosong — cocok XAMPP)* |
| Database | `inventaris_smpm22` |

Aplikasi **otomatis membuat database & tabel** saat pertama dijalankan.

Ubah pengaturan di file `.env`:

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=inventaris_smpm22
```

## Instalasi

### 1. Pastikan MySQL berjalan

Aktifkan **MySQL** di XAMPP / MariaDB / MySQL Server.

### 2. Virtual environment

```powershell
cd D:\ROY\INVENTARIS
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Jalankan

```powershell
python run.py
```

- Komputer server: `http://127.0.0.1:5000`
- Laptop / HP lain (satu WiFi): `http://192.168.x.x:5000`

Login: **admin** / **admin123**

## Google Drive (cadangan)

1. Aktifkan Google Drive API di Google Cloud Console
2. Buat OAuth Client (Web) dengan redirect:
   `http://127.0.0.1:5000/sync/google/callback`
3. Simpan JSON sebagai `credentials/client_secret.json`
4. Menu **Google Drive** → login → **Upload** (export MySQL → JSON) / **Download** (restore ke MySQL)

## File .exe (Windows)

```powershell
.\build_exe.bat
```

Hasil: `dist\InventarisSMPM22\InventarisSMPM22.exe`

- Jalankan di PC/laptop Windows (MySQL harus aktif)
- HP buka browser ke alamat LAN yang tampil di jendela aplikasi
- Salin juga file `.env` ke folder `.exe` agar koneksi MySQL benar

## Struktur

```
INVENTARIS/
├── app/
│   ├── db.py                 # Koneksi MySQL
│   ├── models.py
│   ├── routes/
│   ├── services/             # Google Drive + backup JSON
│   ├── templates/
│   └── static/
├── credentials/
├── data/                     # file backup JSON lokal
├── config.py
├── launcher.py               # entry point .exe
├── run.py
├── inventaris.spec
└── requirements.txt
```
