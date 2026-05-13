# 🔧 Streamlit Cloud Deployment - Google Sheets API Error Fix

## Problem

Your app is showing this error on Streamlit Cloud:

```
gspread.exceptions.APIError: This app has encountered an error.
```

The error occurs at `worksheet.row_values(1)` when trying to read from Google Sheets.

## Root Cause

The Google Sheets API credentials are not properly configured in Streamlit Cloud secrets.

## ✅ Solution: Configure Secrets on Streamlit Cloud

### Step 1: Access Your App Settings

1. Go to your Streamlit Cloud dashboard: https://share.streamlit.io/
2. Find your app (borota-finance)
3. Click the **⋮** (three dots) menu
4. Select **"Settings"**

### Step 2: Add Secrets

1. In the Settings page, click on the **"Secrets"** tab
2. Copy and paste the following into the secrets editor:

```toml
[gcp_service_account]
type = "service_account"
project_id = "cashflow-app-496214"
private_key_id = "b0d60cf3e2c6bf2588c787822da35249836a199c"
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCldryEWa1yZrlj\nS0eAXXCiqOvP2m1JX2btgjMtA2KjlILK9tGkJ1biLmnMh0x5+WdUc0QSbdoduvdB\n0cktWyWOGbxcZqjF0BkY6E+WlyjNtFCu6C0oGLp95TCLKNzakWSu0EKTn9e5zx0+\nJIRoXyuEBGnyCJiP26CbCbtwvr84VyhpcibRIEKPt6N+Gjx7EfoPaxkRZERhyq7h\nNj0iVsiBbWUkMLEA++O8kyfq4K29GDz6NILKQEWwuXXIgFtf6WjyVW/oCIUp+NMp\nwLi9bjAkLIDd92B7uw5laWTgZLu9hqiXwf1/qzbxjLanmRQN1A85uz3AihyuXY8K\nXY8XbK2BAgMBAAECggEAAPzmo4aCr5iZswsRTcp34rC7yNagBLNqHgyehwePJRBP\nNwfdXWuuIvmSiZDKYD5XrJfVTO0nQ4ObQXV9VUmQK2jh7SmXLTqZ1zAWLP1IDTpb\n8q0axHypTz2wEPAP8qWNlMPmaLeDvTaw7G8PGHa3211/YZQg/Q5SNQPnt5cJrGCS\n9C5B1b2svv6dAOIWVCYujHGuJJXa8euUOAZ0zZ/YGuAwizu5GZ/2MQtP3qIVsyu5\nYP7bRKWtDsnXwRV9mRZ6VYGZlMMKUy4GqZ9O9qHjFzAULtcesQL7qBwTKwjJCvRt\nFRA3LwMGycCqLn07KlXpUHntst+yKLmimVem0W4G8QKBgQDOkFFrNYdxzz5vRZBu\nYOl3oCG2ycp935JUxYzYrLE+m8caM3Yo5Xokzr7xFA/IWAlbaPE5mzeDlhmuP+4+\n58fQe7Zl0E8RkuOfI12Ig7E9k9HZOQbOBplqKuUfWw3qhKV/NJaQCzSJb1nYMQQ8\n+nyeatB5TpVq6k3lVLncrNw9zQKBgQDNEFIqXWPIXpFRthh7C1ZRbG0rtZwjjz4m\nNrLZ5FpKJoIgsq4pwsSxd1wrGTSvfD2Ixbq/je//BQFgHax9S0/dc2SpBsZK+dUY\nlucmuxkBMFkyfgwToh0vbjD/6WB8tpAyaeQjp+ssHGZRUvtRDNefeVTULt7NV8bU\nKEANTeDahQKBgBjJSHvM2IvXim5fso0MI/eux1zfqeSgxzZU3inBzyLsHmAOfMc7\nggSYqmDTP3GS3syRMyDudyLbCAnYsgXqWheyQJjG/jXlolqeK8MNyl7RNgUSyrY+\nJHqQ2x2AF5Nkh1dUQBzYu10id21xtEh85ic8OffUbil+JAq4t/S66VKhAoGAd/Y7\nSwNVM0t3UcjoK1snhPycJPzaOcc7gVlwaZ134HcEmyJMVqvVK0h7R884DgztZozd\nwd/D7Xk9I8BYPvgG4bL2yRboe8YJjpgA45yCdTqWg75PTFEDJ9MboSoiwvJ+Cq/9\nwYojPqvig2K7GOAdZ/Kv2G0O9CuMamKdjeroRo0CgYEAzTQFPzSYoUpp8fjxef4U\nvJVtthHbxlSZKL9oUPMV1W5f/vDdcg4hq0gjGFz86s5aA5+zOoVCDK+tmwKGi9GN\nSUUjAyBDGw5BVrfZaKQKTd/mshROOWaRZuUZSygDK4K6KGhAPCwqPpqQ19I4XuiZ\nNTggBCX1ONWeVUeDN+38QeU=\n-----END PRIVATE KEY-----\n"
client_email = "cashflow-service@cashflow-app-496214.iam.gserviceaccount.com"
client_id = "101054089335297559745"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/cashflow-service%40cashflow-app-496214.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

3. Click **"Save"**

### Step 3: Reboot Your App

1. After saving secrets, click **"Reboot app"** button
2. Wait for the app to restart (usually takes 30-60 seconds)
3. Your app should now work correctly!

## 🔍 Verification

After rebooting, your app should:

- ✅ Connect to Google Sheets successfully
- ✅ Load the login page without errors
- ✅ Allow users to register and login
- ✅ Save and retrieve transactions

## 📝 Important Notes

### Security

- **NEVER** commit `service_account.json` to Git (it's already in `.gitignore`)
- The secrets in Streamlit Cloud are encrypted and secure
- Only you (the app owner) can see and edit the secrets

### Local Development

- For local development, use `service_account.json` file (already configured)
- For Streamlit Cloud, use the secrets configuration (as shown above)
- The app automatically detects which environment it's running in

### Troubleshooting

If the error persists after adding secrets:

1. **Check API Status**
   - Verify Google Sheets API is enabled: https://console.cloud.google.com/apis/library/sheets.googleapis.com
   - Verify Google Drive API is enabled: https://console.cloud.google.com/apis/library/drive.googleapis.com

2. **Check Spreadsheet Permissions**
   - Open your spreadsheet: https://docs.google.com/spreadsheets/d/14Qhbqb42t8gp_tl7z_HisM2C3fFPrX03rDSKXGuhKx4
   - Click "Share" button
   - Make sure `cashflow-service@cashflow-app-496214.iam.gserviceaccount.com` has "Editor" access

3. **Check Logs**
   - In Streamlit Cloud, click "Manage app" → "Logs"
   - Look for more detailed error messages

4. **Verify Secrets Format**
   - Make sure there are no extra spaces or line breaks
   - The `private_key` must include `\n` characters (not actual line breaks in TOML)
   - All fields must be in quotes

## 📚 Additional Resources

- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Google Sheets API Setup Guide](./SETUP_GOOGLE_SHEETS.md)
- [Test Connection Script](./test_sheets_connection.py)

## ✅ Success Checklist

- [ ] Secrets added to Streamlit Cloud
- [ ] App rebooted
- [ ] Login page loads without errors
- [ ] Can register new users
- [ ] Can add transactions
- [ ] Data persists in Google Sheets

---

**Need Help?** Check the Streamlit Cloud logs for detailed error messages.
