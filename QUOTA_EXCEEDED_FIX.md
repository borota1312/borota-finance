# 🚨 Google Sheets API Quota Exceeded - Solusi

## ❌ Error yang Terjadi

```
APIError: [429]: Quota exceeded for quota metric 'Read requests'
and limit 'Read requests per minute per user' of service
'sheets.googleapis.com' for consumer 'project_number:925658252968'.
```

## 📊 Penjelasan Masalah

### Penyebab

1. **Google Sheets API Limits:**
   - **60 read requests per minute per user**
   - **60 write requests per minute per user**

2. **Streamlit Behavior:**
   - Setiap kali user berinteraksi, Streamlit melakukan rerun
   - Setiap rerun memanggil `initialize_data()` yang membaca spreadsheet
   - Jika banyak user atau banyak interaksi → quota cepat habis

3. **Root Cause:**
   - App tidak menggunakan cache dengan efektif
   - Terlalu banyak API calls yang tidak perlu
   - Setiap page load membaca spreadsheet berkali-kali

## ✅ Solusi yang Sudah Diterapkan

### 1. **Session-Based Initialization**

```python
# app.py - Initialize hanya sekali per session
if "data_initialized" not in st.session_state:
    try:
        initialize_data()
        st.session_state["data_initialized"] = True
    except Exception as e:
        if "429" in str(e) or "Quota exceeded" in str(e):
            st.error("⚠️ Quota exceeded, tunggu 1-2 menit")
            st.stop()
```

**Benefit:** Mengurangi API calls dari setiap rerun menjadi hanya 1x per session.

### 2. **Optimized init_sheets()**

```python
# sheets_config.py - Batch check worksheets
existing_worksheets = {ws.title: ws for ws in spreadsheet.worksheets()}

# Hanya create jika belum ada
if USERS_SHEET not in existing_worksheets:
    get_or_create_worksheet(...)
```

**Benefit:** 1 API call untuk check semua worksheets, bukan 3 API calls terpisah.

### 3. **No Retry on 429**

```python
# Jangan retry quota exceeded - langsung raise
if "429" in error_msg or "Quota exceeded" in error_msg:
    raise
```

**Benefit:** Tidak memperburuk quota dengan retry yang sia-sia.

### 4. **Graceful Degradation**

```python
# Jika quota exceeded saat init, jangan crash
except gspread.exceptions.APIError as e:
    if "429" in str(e):
        print("Warning: Quota exceeded, will retry later")
        return  # Continue dengan cache
```

**Benefit:** App tetap bisa jalan dengan data yang sudah di-cache.

## 🔧 Solusi Tambahan (Jika Masih Terjadi)

### Opsi 1: Increase Quota (Recommended)

1. **Buka Google Cloud Console:**
   https://console.cloud.google.com/apis/api/sheets.googleapis.com/quotas?project=cashflow-app-496214

2. **Request Quota Increase:**
   - Pilih "Read requests per minute per user"
   - Klik "Edit Quotas"
   - Request increase ke 300 atau 600 requests/minute
   - Isi justification: "Multi-user cash flow app with real-time data sync"

3. **Approval Time:** Biasanya 1-2 hari kerja

### Opsi 2: Implement Rate Limiting

Tambahkan rate limiter di app:

```python
import time
from functools import wraps

# Global rate limiter
_last_api_call = {}
_min_interval = 1.0  # 1 second between calls

def rate_limit(key):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            last_call = _last_api_call.get(key, 0)
            elapsed = now - last_call

            if elapsed < _min_interval:
                time.sleep(_min_interval - elapsed)

            result = func(*args, **kwargs)
            _last_api_call[key] = time.time()
            return result
        return wrapper
    return decorator

@rate_limit('spreadsheet')
def _get_spreadsheet():
    return get_or_create_spreadsheet()
```

### Opsi 3: Batch Operations

Gunakan batch update untuk mengurangi API calls:

```python
# Instead of multiple append_row calls
worksheet.append_rows(all_rows)  # 1 API call

# Instead of multiple update calls
worksheet.batch_update([
    {'range': 'A1', 'values': [[value1]]},
    {'range': 'A2', 'values': [[value2]]},
])  # 1 API call
```

### Opsi 4: Caching Strategy

Tambahkan TTL (Time To Live) pada cache:

```python
@st.cache_data(ttl=300)  # Cache 5 menit
def load_transactions():
    # ... existing code
```

### Opsi 5: Migrate to Database

Untuk production dengan banyak user, pertimbangkan:

- **PostgreSQL** (Supabase, Neon, Railway)
- **MongoDB** (MongoDB Atlas)
- **Firebase Firestore**

## 📈 Monitoring Quota Usage

### Check Current Usage:

1. Buka: https://console.cloud.google.com/apis/api/sheets.googleapis.com/metrics?project=cashflow-app-496214
2. Lihat grafik "Read requests" dan "Write requests"
3. Monitor apakah mendekati limit

### Set Up Alerts:

1. Google Cloud Console → Monitoring → Alerting
2. Create alert untuk "sheets.googleapis.com quota usage"
3. Set threshold: 80% of quota
4. Email notification

## 🎯 Best Practices

### DO ✅

- Cache data dengan `@st.cache_resource` atau `@st.cache_data`
- Batch operations when possible
- Initialize once per session
- Use TTL on cache untuk data yang jarang berubah
- Monitor quota usage regularly

### DON'T ❌

- Jangan read/write di setiap rerun
- Jangan retry pada 429 errors
- Jangan clear cache terlalu sering
- Jangan fetch data yang tidak dibutuhkan
- Jangan loop API calls tanpa delay

## 🚀 Immediate Actions

### Untuk User:

1. **Tunggu 1-2 menit** sebelum refresh
2. **Hindari rapid clicking** pada tombol
3. **Logout dan login kembali** untuk reset session

### Untuk Admin:

1. ✅ **Code fixes sudah diterapkan** (session-based init, optimized init_sheets)
2. ⏳ **Deploy update** ke Streamlit Cloud
3. ⏳ **Request quota increase** di Google Cloud Console
4. ⏳ **Monitor usage** setelah deploy

## 📊 Expected Improvement

### Before Fix:

- ~10-15 API calls per page load
- Quota habis dalam ~4-6 page loads per minute
- Frequent 429 errors

### After Fix:

- ~2-3 API calls per session
- Quota cukup untuk ~20-30 sessions per minute
- Rare 429 errors (hanya jika traffic sangat tinggi)

## 🔍 Troubleshooting

### Jika masih error setelah fix:

1. **Check logs:**

   ```
   Streamlit Cloud → Manage app → Logs
   ```

2. **Verify cache working:**
   - Lihat apakah `data_initialized` di session state
   - Check apakah `_get_spreadsheet` cache hit

3. **Check concurrent users:**
   - Jika >10 concurrent users, quota increase diperlukan

4. **Temporary workaround:**
   - Restart app di Streamlit Cloud
   - Clear cache: `st.cache_resource.clear()`

## 📞 Support

Jika masalah berlanjut:

1. Check dokumentasi: `FIXES_SUMMARY.md`
2. Review logs untuk error patterns
3. Consider database migration untuk scale

---

**Status:** ✅ Fixes applied, ready to deploy

**Next Steps:**

1. Deploy ke Streamlit Cloud
2. Monitor quota usage
3. Request quota increase jika diperlukan

**Updated:** 2026-05-13
