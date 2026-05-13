"""
sheets_config.py — Konfigurasi Google Sheets sebagai storage backend
"""

import os
import json
import time
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Nama spreadsheet di Google Sheets
SPREADSHEET_NAME = "cashflow_app_data"

# Nama worksheet (tab) di spreadsheet
USERS_SHEET = "users"
TRANSACTIONS_SHEET = "transactions"
SESSIONS_SHEET = "sessions"

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


def retry_on_api_error(func):
    """Decorator untuk retry API calls yang gagal karena transient errors."""

    def wrapper(*args, **kwargs):
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except gspread.exceptions.APIError as e:
                last_error = e
                error_msg = str(e)

                # Untuk quota exceeded (429), JANGAN retry - langsung raise
                if "429" in error_msg or "Quota exceeded" in error_msg:
                    raise

                # Retry hanya untuk transient errors lainnya (500, 502, 503, 504)
                if any(code in error_msg for code in ["500", "502", "503", "504"]):
                    if attempt < MAX_RETRIES - 1:
                        # Exponential backoff: 2s, 4s, 8s
                        wait_time = RETRY_DELAY * (2**attempt)
                        time.sleep(wait_time)
                        continue
                # Untuk error lain, langsung raise
                raise
            except Exception as e:
                # Untuk non-API errors, langsung raise
                raise
        # Jika semua retry gagal
        raise last_error

    return wrapper


@retry_on_api_error
def get_gspread_client():
    """
    Buat dan return gspread client.
    Credentials diambil dari st.secrets atau file lokal untuk development.
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    # Coba file lokal dulu (development)
    if os.path.exists("service_account.json"):
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            "service_account.json", scope
        )
    else:
        # Coba ambil dari Streamlit secrets (production)
        try:
            if "gcp_service_account" in st.secrets:
                creds_dict = dict(st.secrets["gcp_service_account"])
                credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                    creds_dict, scope
                )
            else:
                raise Exception("gcp_service_account not found in secrets")
        except Exception:
            raise Exception(
                "Google Sheets credentials tidak ditemukan.\n\n"
                "Untuk development lokal:\n"
                "1. Download service account JSON dari Google Cloud Console\n"
                "2. Rename menjadi 'service_account.json'\n"
                "3. Taruh di folder project (sejajar dengan app.py)\n\n"
                "Untuk production (Streamlit Cloud):\n"
                "1. Buka app settings di Streamlit Cloud\n"
                "2. Tambahkan 'gcp_service_account' di Secrets\n\n"
                "Lihat SETUP_GOOGLE_SHEETS.md untuk panduan lengkap."
            )

    return gspread.authorize(credentials)


@retry_on_api_error
def get_or_create_spreadsheet():
    """
    Buka spreadsheet, atau buat baru jika belum ada.
    Return spreadsheet object.
    """
    client = get_gspread_client()

    try:
        # Coba buka spreadsheet yang sudah ada
        spreadsheet = client.open(SPREADSHEET_NAME)
        return spreadsheet
    except gspread.SpreadsheetNotFound:
        # Buat spreadsheet baru
        try:
            spreadsheet = client.create(SPREADSHEET_NAME)
            return spreadsheet
        except gspread.exceptions.APIError as e:
            raise Exception(
                f"Gagal membuat spreadsheet '{SPREADSHEET_NAME}'.\n\n"
                f"Kemungkinan penyebab:\n"
                f"1. Google Sheets API belum diaktifkan di Google Cloud Console\n"
                f"   → Kunjungi: https://console.cloud.google.com/apis/library/sheets.googleapis.com\n"
                f"2. Google Drive API belum diaktifkan\n"
                f"   → Kunjungi: https://console.cloud.google.com/apis/library/drive.googleapis.com\n"
                f"3. Service account tidak memiliki permission yang cukup\n"
                f"4. Quota API sudah terlampaui\n\n"
                f"Error detail: {str(e)}"
            )
    except gspread.exceptions.APIError as e:
        # Jika error bukan karena not found, coba diagnosa
        error_msg = str(e)
        if "PERMISSION_DENIED" in error_msg or "403" in error_msg:
            raise Exception(
                f"Permission denied saat mengakses Google Sheets.\n\n"
                f"Solusi:\n"
                f"1. Pastikan Google Sheets API sudah diaktifkan\n"
                f"2. Pastikan service account memiliki akses ke spreadsheet\n"
                f"3. Share spreadsheet dengan: cashflow-service@cashflow-app-496214.iam.gserviceaccount.com\n\n"
                f"Error detail: {error_msg}"
            )
        elif "UNAUTHENTICATED" in error_msg or "401" in error_msg:
            raise Exception(
                f"Authentication failed.\n\n"
                f"Solusi:\n"
                f"1. Periksa credentials di Streamlit Cloud secrets\n"
                f"2. Pastikan service_account.json valid (untuk local)\n"
                f"3. Pastikan private_key tidak corrupt\n\n"
                f"Error detail: {error_msg}"
            )
        else:
            raise Exception(
                f"Error saat mengakses Google Sheets API.\n\n"
                f"Kemungkinan penyebab:\n"
                f"1. Google Sheets API belum diaktifkan\n"
                f"2. Credentials tidak valid atau sudah expired\n"
                f"3. Quota API sudah terlampaui\n"
                f"4. Network/connectivity issues\n\n"
                f"Error detail: {error_msg}"
            )


@retry_on_api_error
def get_or_create_worksheet(spreadsheet, sheet_name: str, headers: list):
    """
    Buka worksheet, atau buat baru dengan headers jika belum ada.
    Return worksheet object.
    """
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        # Cek apakah header sudah ada dengan error handling
        try:
            existing_headers = worksheet.row_values(1)
            if not existing_headers:
                worksheet.append_row(headers)
        except gspread.exceptions.APIError as e:
            # Jika error saat membaca, coba tulis header langsung
            print(
                f"Warning: Could not read headers from {sheet_name}, attempting to write: {e}"
            )
            try:
                worksheet.append_row(headers)
            except Exception as write_error:
                print(f"Error writing headers to {sheet_name}: {write_error}")
                raise
    except gspread.WorksheetNotFound:
        # Buat worksheet baru dengan headers
        try:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            worksheet.append_row(headers)
        except gspread.exceptions.APIError as e:
            raise Exception(
                f"Gagal membuat worksheet '{sheet_name}'. "
                f"Pastikan:\n"
                f"1. Google Sheets API sudah diaktifkan di Google Cloud Console\n"
                f"2. Service account memiliki akses ke spreadsheet\n"
                f"3. Quota API belum terlampaui\n"
                f"Error detail: {str(e)}"
            )

    return worksheet


def init_sheets():
    """
    Inisialisasi semua worksheets yang dibutuhkan.
    Dipanggil sekali di awal app.py.
    Optimized untuk menghindari quota exceeded.
    """
    try:
        spreadsheet = get_or_create_spreadsheet()

        # Dapatkan semua worksheet yang ada sekaligus untuk mengurangi API calls
        try:
            existing_worksheets = {ws.title: ws for ws in spreadsheet.worksheets()}
        except Exception:
            existing_worksheets = {}

        # Users sheet
        if USERS_SHEET not in existing_worksheets:
            get_or_create_worksheet(
                spreadsheet,
                USERS_SHEET,
                ["username", "password_hash", "display_name", "created_at"],
            )

        # Transactions sheet
        if TRANSACTIONS_SHEET not in existing_worksheets:
            get_or_create_worksheet(
                spreadsheet,
                TRANSACTIONS_SHEET,
                [
                    "id",
                    "username",
                    "date",
                    "type",
                    "category",
                    "amount",
                    "note",
                    "created_at",
                ],
            )

        # Sessions sheet
        if SESSIONS_SHEET not in existing_worksheets:
            get_or_create_worksheet(
                spreadsheet,
                SESSIONS_SHEET,
                ["token", "username", "display_name", "expires_at"],
            )
    except gspread.exceptions.APIError as e:
        error_msg = str(e)
        if "429" in error_msg or "Quota exceeded" in error_msg:
            # Jangan raise exception, biarkan app tetap jalan dengan cache
            print(
                f"Warning: Quota exceeded during init_sheets, will retry later: {error_msg}"
            )
            return
        raise
