# 🔧 Setup Google Sheets sebagai Database

Aplikasi ini menggunakan Google Sheets sebagai storage backend agar data persisten saat deploy ke Streamlit Cloud.

---

## 📋 Langkah Setup (5 menit)

### 1. Buat Google Cloud Project & Enable API

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Klik **"Create Project"** → beri nama `cashflow-app` → **Create**
3. Pilih project yang baru dibuat
4. Buka **"APIs & Services"** → **"Library"**
5. Cari dan enable 2 API ini:
   - **Google Sheets API** → klik **Enable**
   - **Google Drive API** → klik **Enable**

### 2. Buat Service Account

1. Di Google Cloud Console, buka **"APIs & Services"** → **"Credentials"**
2. Klik **"Create Credentials"** → pilih **"Service Account"**
3. Isi:
   - **Service account name:** `cashflow-service`
   - **Service account ID:** (auto-generated)
   - Klik **Create and Continue**
4. **Grant this service account access to project:**
   - Role: **Editor** (atau bisa skip, tidak wajib)
   - Klik **Continue** → **Done**

### 3. Download Service Account Key (JSON)

1. Klik service account yang baru dibuat (`cashflow-service@...`)
2. Tab **"Keys"** → **"Add Key"** → **"Create new key"**
3. Pilih **JSON** → **Create**
4. File JSON akan terdownload otomatis
5. **Rename file** menjadi `service_account.json`
6. **Pindahkan** ke folder project ini (sejajar dengan `app.py`)

⚠️ **PENTING:** Jangan commit file ini ke Git! Sudah ada di `.gitignore`.

### 4. Buat Google Spreadsheet

1. Buka [Google Sheets](https://sheets.google.com)
2. Buat spreadsheet baru
3. **Rename** menjadi: `cashflow_app_data` (harus sama persis!)
4. Buka file `service_account.json`, copy value dari key `"client_email"` (format: `...@....iam.gserviceaccount.com`)
5. Di Google Sheets, klik **Share** → paste email service account → pilih **Editor** → **Send**

✅ Sekarang service account punya akses ke spreadsheet!

---

## 🚀 Testing Lokal

```bash
# Install dependencies
pip install -r requirements.txt

# Jalankan app
streamlit run app.py
```

Saat pertama jalan, app akan otomatis membuat 3 worksheets (tabs) di spreadsheet:

- `users` — data akun
- `transactions` — data transaksi
- `sessions` — session tokens

---

## ☁️ Deploy ke Streamlit Cloud

### 1. Push ke GitHub

```bash
git add .
git commit -m "Add Google Sheets backend"
git push
```

⚠️ Pastikan `service_account.json` **TIDAK** ikut ter-push (cek `.gitignore`).

### 2. Setup Streamlit Secrets

1. Buka [Streamlit Cloud](https://share.streamlit.io/)
2. Deploy app dari GitHub repo
3. Setelah deploy, buka **Settings** → **Secrets**
4. Copy **seluruh isi** file `service_account.json` lokal
5. Paste ke Streamlit Secrets dengan format:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "abc123..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "cashflow-service@....iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

6. **Save** → app akan restart otomatis

✅ Sekarang app di cloud bisa akses Google Sheets!

---

## 🔍 Troubleshooting

### Error: "Spreadsheet not found"

- Pastikan nama spreadsheet **persis** `cashflow_app_data`
- Pastikan service account email sudah di-share ke spreadsheet dengan role **Editor**

### Error: "Credentials not found"

- **Lokal:** Pastikan file `service_account.json` ada di folder project
- **Cloud:** Pastikan Streamlit Secrets sudah diisi dengan benar

### Error: "API has not been used in project"

- Pastikan Google Sheets API dan Google Drive API sudah di-enable di Google Cloud Console

### Data tidak muncul setelah deploy

- Buka Google Sheets di browser, cek apakah data ada di sana
- Jika ada, berarti app berhasil — mungkin perlu refresh browser

---

## 📊 Monitoring Data

Buka spreadsheet `cashflow_app_data` di Google Sheets untuk:

- Lihat semua data real-time
- Edit manual jika perlu
- Export ke Excel/CSV
- Buat backup

---

## 🔐 Keamanan

- Service account key adalah **kredensial sensitif** — jangan share atau commit ke Git
- Hanya share spreadsheet ke service account email, jangan ke publik
- Rotate service account key secara berkala (setiap 90 hari)
