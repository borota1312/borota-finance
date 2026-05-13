"""
test_sheets_connection.py — Script untuk test koneksi Google Sheets API
Jalankan: python test_sheets_connection.py
"""

import os
import sys
from oauth2client.service_account import ServiceAccountCredentials
import gspread


def test_connection():
    """Test koneksi ke Google Sheets API"""

    print("=" * 60)
    print("GOOGLE SHEETS API CONNECTION TEST")
    print("=" * 60)
    print()

    # 1. Check service account file
    print("1. Checking service account file...")
    if not os.path.exists("service_account.json"):
        print("   ❌ ERROR: service_account.json tidak ditemukan!")
        print("   → Download dari Google Cloud Console")
        return False
    print("   ✅ service_account.json ditemukan")
    print()

    # 2. Load credentials
    print("2. Loading credentials...")
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            "service_account.json", scope
        )
        print("   ✅ Credentials loaded successfully")
        print(f"   Service account email: {credentials.service_account_email}")
    except Exception as e:
        print(f"   ❌ ERROR loading credentials: {e}")
        return False
    print()

    # 3. Authorize gspread client
    print("3. Authorizing gspread client...")
    try:
        client = gspread.authorize(credentials)
        print("   ✅ Client authorized successfully")
    except Exception as e:
        print(f"   ❌ ERROR authorizing client: {e}")
        return False
    print()

    # 4. Try to open or create spreadsheet
    print("4. Testing spreadsheet access...")
    spreadsheet_name = "cashflow_app_data"
    try:
        spreadsheet = client.open(spreadsheet_name)
        print(f"   ✅ Spreadsheet '{spreadsheet_name}' opened successfully")
        print(f"   Spreadsheet ID: {spreadsheet.id}")
        print(f"   Spreadsheet URL: {spreadsheet.url}")
    except gspread.SpreadsheetNotFound:
        print(f"   ⚠️  Spreadsheet '{spreadsheet_name}' tidak ditemukan")
        print("   Mencoba membuat spreadsheet baru...")
        try:
            spreadsheet = client.create(spreadsheet_name)
            print(f"   ✅ Spreadsheet baru berhasil dibuat!")
            print(f"   Spreadsheet ID: {spreadsheet.id}")
            print(f"   Spreadsheet URL: {spreadsheet.url}")
        except gspread.exceptions.APIError as e:
            print(f"   ❌ ERROR membuat spreadsheet: {e}")
            print()
            print("   Kemungkinan penyebab:")
            print("   - Google Sheets API belum diaktifkan")
            print("   - Google Drive API belum diaktifkan")
            print("   - Service account tidak memiliki permission")
            print()
            print("   Solusi:")
            print("   1. Buka Google Cloud Console: https://console.cloud.google.com")
            print("   2. Pilih project: cashflow-app-496214")
            print("   3. Aktifkan Google Sheets API:")
            print(
                "      https://console.cloud.google.com/apis/library/sheets.googleapis.com"
            )
            print("   4. Aktifkan Google Drive API:")
            print(
                "      https://console.cloud.google.com/apis/library/drive.googleapis.com"
            )
            return False
    except gspread.exceptions.APIError as e:
        print(f"   ❌ API ERROR: {e}")
        print()
        print("   Kemungkinan penyebab:")
        print("   - API belum diaktifkan")
        print("   - Credentials tidak valid")
        print("   - Quota terlampaui")
        print("   - Network issues")
        return False
    print()

    # 5. Try to access/create worksheet
    print("5. Testing worksheet access...")
    try:
        # Try to get or create a test worksheet
        try:
            worksheet = spreadsheet.worksheet("users")
            print("   ✅ Worksheet 'users' ditemukan")
        except gspread.WorksheetNotFound:
            print("   ⚠️  Worksheet 'users' tidak ditemukan, membuat baru...")
            worksheet = spreadsheet.add_worksheet(title="users", rows=100, cols=10)
            print("   ✅ Worksheet 'users' berhasil dibuat")

        # Try to read from worksheet
        print("   Testing read operation...")
        try:
            values = worksheet.row_values(1)
            print(f"   ✅ Read successful. Row 1 values: {values}")
        except gspread.exceptions.APIError as e:
            print(f"   ❌ ERROR reading from worksheet: {e}")
            return False

        # Try to write to worksheet
        print("   Testing write operation...")
        try:
            if not values:
                worksheet.append_row(
                    ["username", "password_hash", "display_name", "created_at"]
                )
                print("   ✅ Write successful. Headers added.")
            else:
                print("   ✅ Headers already exist, skipping write.")
        except gspread.exceptions.APIError as e:
            print(f"   ❌ ERROR writing to worksheet: {e}")
            return False

    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    print()

    # Success!
    print("=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("Google Sheets API connection is working correctly.")
    print(f"Spreadsheet URL: {spreadsheet.url}")
    print()
    print("You can now run your Streamlit app:")
    print("  streamlit run app.py")
    print()

    return True


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
