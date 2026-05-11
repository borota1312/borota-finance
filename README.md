# 💰 Cash Flow Pribadi

Aplikasi pencatatan cash flow pribadi berbasis Streamlit untuk dipakai bersama 3–5 orang. Semua data disimpan di file CSV lokal — tidak perlu database atau cloud.

---

## 🚀 Cara Install & Jalankan

### 1. Install dependensi

```bash
pip install -r requirements.txt
```

### 2. Jalankan aplikasi

```bash
streamlit run app.py
```

Buka browser di `http://localhost:8501`

---

## 👤 User Default

Saat pertama kali dijalankan, aplikasi otomatis membuat 5 akun dan 30 transaksi sample.

| Username | Password | Nama Lengkap    |
| -------- | -------- | --------------- |
| budi     | pass123  | Budi Santoso    |
| sari     | pass123  | Sari Dewi       |
| andi     | pass123  | Andi Pratama    |
| dewi     | pass123  | Dewi Rahayu     |
| riko     | pass123  | Riko Firmansyah |

> ⚠️ Segera ganti password default setelah login pertama via menu **Ganti Password**.

---

## ➕ Menambah User Baru

1. Buka halaman aplikasi
2. Klik tombol **"Daftar Akun Baru"** di halaman login
3. Isi form: Nama Lengkap, Username, Password, Konfirmasi Password
4. Klik **Daftar**

Maksimum 10 akun dapat didaftarkan (dapat diubah di konstanta `MAX_USERS` di `app.py`).

---

## 📁 Struktur File

```
cashflow_app/
├── app.py               ← Entry point & router halaman
├── auth.py              ← Login, register, ganti password
├── data.py              ← Baca/tulis CSV & seed data
├── dashboard.py         ← Metric cards & chart Plotly
├── users.csv            ← Data user (dibuat otomatis)
├── transactions.csv     ← Data transaksi (dibuat otomatis)
├── requirements.txt
└── README.md
```

---

## ✨ Fitur

- **Login** — pilih username dari dropdown, verifikasi bcrypt
- **Register** — validasi username unik, password minimal 6 karakter
- **Dashboard** — 4 metric cards + 3 chart interaktif (Plotly)
- **Tambah Transaksi** — form dengan kategori dinamis per tipe
- **Riwayat** — filter tipe/kategori/tanggal, hapus dengan konfirmasi
- **Export CSV** — download data per bulan atau semua data
- **Ganti Password** — proteksi brute force (max 3 percobaan per sesi)

---

## 🔒 Keamanan

- Password di-hash dengan **bcrypt** (tidak disimpan plain text)
- File CSV ditulis dengan **file lock** (tmp-rename trick) agar aman saat multi-user akses bersamaan
- Brute force protection pada form ganti password
