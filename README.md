# 💰 Cash Flow Pribadi

Aplikasi pencatatan cash flow pribadi berbasis Streamlit untuk dipakai bersama 3–5 orang. Semua data disimpan di **Google Sheets** sebagai backend — mudah diakses, real-time sync, dan gratis!

---

## 🚀 Cara Install & Jalankan

### Prasyarat

- Python 3.8+
- Google Cloud Project dengan Google Sheets API enabled
- Service Account credentials (lihat [SETUP_GOOGLE_SHEETS.md](SETUP_GOOGLE_SHEETS.md))

### 1. Clone repository

```bash
git clone <repository-url>
cd my-finance
```

### 2. Install dependensi

```bash
pip install -r requirements.txt
```

### 3. Setup Google Sheets credentials

**Untuk development lokal:**

1. Download service account JSON dari Google Cloud Console
2. Rename menjadi `service_account.json`
3. Taruh di root folder project

**Untuk Streamlit Cloud:**

- Lihat panduan lengkap di [QUICK_FIX.md](QUICK_FIX.md) atau [STREAMLIT_CLOUD_FIX.md](STREAMLIT_CLOUD_FIX.md)

### 4. Test koneksi (opsional)

```bash
python test_sheets_connection.py
```

### 5. Jalankan aplikasi

```bash
streamlit run app.py
```

Buka browser di `http://localhost:8501`

---

## 👤 User Default

Saat pertama kali dijalankan, aplikasi otomatis membuat struktur Google Sheets yang dibutuhkan.

**Tidak ada user default** — Anda perlu mendaftar akun baru melalui halaman registrasi.

### Cara Daftar User Pertama

1. Buka halaman aplikasi
2. Klik tombol **"Daftar Akun Baru"** di halaman login
3. Isi form: Nama Lengkap, Username, Password, Konfirmasi Password
4. Klik **Daftar**

Maksimum 10 akun dapat didaftarkan (dapat diubah di konstanta `MAX_USERS` di `app.py`).

---

## 📁 Struktur File

```
my-finance/
├── app.py                      ← Entry point & router halaman
├── auth.py                     ← Login, register, ganti password, session management
├── data.py                     ← Baca/tulis Google Sheets & data operations
├── dashboard.py                ← Metric cards & chart Plotly
├── sheets_config.py            ← Google Sheets API configuration & retry logic
├── service_account.json        ← Google service account credentials (local only, gitignored)
├── sessions.json               ← Session tokens (gitignored)
├── test_sheets_connection.py  ← Diagnostic tool untuk test koneksi
├── requirements.txt
├── README.md
├── SETUP_GOOGLE_SHEETS.md      ← Panduan setup Google Sheets API
├── QUICK_FIX.md                ← Quick fix untuk Streamlit Cloud error
├── STREAMLIT_CLOUD_FIX.md      ← Panduan lengkap deploy ke Streamlit Cloud
├── FIXES_SUMMARY.md            ← Ringkasan semua perbaikan
└── .streamlit/
    ├── config.toml             ← Streamlit configuration
    └── secrets.toml.example    ← Template untuk secrets (local dev)
```

**Google Sheets Structure:**

- Spreadsheet: `cashflow_app_data`
  - Sheet: `users` (username, password_hash, display_name, created_at)
  - Sheet: `transactions` (id, username, date, type, category, amount, note, created_at)
  - Sheet: `sessions` (token, username, display_name, expires_at)

---

## ✨ Fitur

- **Login** — pilih username dari dropdown, verifikasi bcrypt
- **Register** — validasi username unik, password minimal 6 karakter
- **Dashboard** — 4 metric cards + 3 chart interaktif (Plotly)
- **Tambah Transaksi** — form dengan kategori dinamis per tipe
- **Riwayat** — filter tipe/kategori/tanggal, hapus dengan konfirmasi
- **Export CSV** — download data per bulan atau semua data
- **Ganti Password** — proteksi brute force (max 3 percobaan per sesi)
- **Session Persistence** — login tetap aktif setelah refresh (via URL token)
- **Google Sheets Backend** — data tersimpan real-time, bisa diakses dari mana saja
- **Auto Retry** — otomatis retry jika ada transient API errors
- **Cache Management** — data selalu fresh setelah operasi write

---

## 🔒 Keamanan

- Password di-hash dengan **bcrypt** (tidak disimpan plain text)
- Session tokens dengan expiry time (24 jam)
- Google Sheets API dengan service account authentication
- Credentials tidak pernah di-commit ke Git (`.gitignore`)
- Brute force protection pada form ganti password
- Retry mechanism hanya untuk transient errors (429, 500, 502, 503, 504)

---

## 🚀 Deploy ke Streamlit Cloud

### Quick Steps:

1. **Push ke GitHub**

   ```bash
   git add .
   git commit -m "Deploy to Streamlit Cloud"
   git push origin main
   ```

2. **Deploy di Streamlit Cloud**
   - Buka https://share.streamlit.io/
   - Connect repository
   - Deploy app

3. **Konfigurasi Secrets**
   - Buka app Settings → Secrets
   - Copy-paste dari [QUICK_FIX.md](QUICK_FIX.md)
   - Save & Reboot

**Panduan lengkap:** [STREAMLIT_CLOUD_FIX.md](STREAMLIT_CLOUD_FIX.md)

---

## 🔧 Troubleshooting

### Error: "gspread.exceptions.APIError"

**Solusi cepat:** Lihat [QUICK_FIX.md](QUICK_FIX.md)

**Penyebab umum:**

1. Secrets belum dikonfigurasi di Streamlit Cloud
2. Google Sheets API belum diaktifkan
3. Service account tidak punya akses ke spreadsheet

**Test koneksi lokal:**

```bash
python test_sheets_connection.py
```

### Error saat hapus transaksi

**Fixed!** Cache sekarang otomatis di-clear setelah operasi write.

### Spreadsheet tidak ditemukan

App akan otomatis membuat spreadsheet baru bernama `cashflow_app_data` jika belum ada.

**Spreadsheet URL:** https://docs.google.com/spreadsheets/d/14Qhbqb42t8gp_tl7z_HisM2C3fFPrX03rDSKXGuhKx4

---

## 📚 Dokumentasi

- **[SETUP_GOOGLE_SHEETS.md](SETUP_GOOGLE_SHEETS.md)** - Setup Google Sheets API dari awal
- **[QUICK_FIX.md](QUICK_FIX.md)** - Quick fix untuk Streamlit Cloud error (5 menit)
- **[STREAMLIT_CLOUD_FIX.md](STREAMLIT_CLOUD_FIX.md)** - Panduan lengkap deploy ke Streamlit Cloud
- **[FIXES_SUMMARY.md](FIXES_SUMMARY.md)** - Ringkasan semua perbaikan yang sudah dilakukan

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **Backend:** Google Sheets API (via gspread)
- **Authentication:** bcrypt
- **Charts:** Plotly
- **Session Management:** JSON file + URL tokens
- **Deployment:** Streamlit Cloud

---

## 📝 Changelog

### v2.0 (2026-05-13)

- ✅ Migrated from CSV to Google Sheets backend
- ✅ Added retry mechanism for transient API errors
- ✅ Improved error handling with specific error messages
- ✅ Fixed cache management (clear after write operations)
- ✅ Added diagnostic tool (`test_sheets_connection.py`)
- ✅ Added comprehensive deployment documentation
- ✅ Session persistence via URL tokens

### v1.0 (Initial)

- ✅ Basic cash flow tracking
- ✅ Multi-user support (CSV backend)
- ✅ Dashboard with charts
- ✅ Export to CSV

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

MIT License - feel free to use this project for personal or commercial purposes.

---

## 💡 Tips

1. **Backup data:** Google Sheets otomatis menyimpan version history
2. **Monitor usage:** Check Google Cloud Console untuk API quota
3. **Security:** Jangan share `service_account.json` atau commit ke Git
4. **Performance:** Cache di-clear otomatis, tapi bisa manual clear via `st.cache_resource.clear()`

---

**Need help?** Check the documentation files or open an issue on GitHub.
