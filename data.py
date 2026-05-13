"""
data.py — Semua fungsi baca/tulis data (Google Sheets backend)
Menangani: users, transactions
"""

import uuid
from datetime import datetime, date

import pandas as pd
import streamlit as st

from sheets_config import (
    get_or_create_spreadsheet,
    get_or_create_worksheet,
    USERS_SHEET,
    TRANSACTIONS_SHEET,
)

# ── Kategori ───────────────────────────────────────────────────────────────
INCOME_CATEGORIES = ["Gaji", "Freelance", "Bisnis", "Investasi", "Lainnya"]
EXPENSE_CATEGORIES = [
    "Makan",
    "Transport",
    "Belanja",
    "Hiburan",
    "Kesehatan",
    "Tagihan",
    "Tabungan",
    "Lainnya",
]


# ══════════════════════════════════════════════════════════════════════════
# CACHE SPREADSHEET CONNECTION
# ══════════════════════════════════════════════════════════════════════════


@st.cache_resource
def _get_spreadsheet():
    """Cache spreadsheet connection untuk performa."""
    return get_or_create_spreadsheet()


# ══════════════════════════════════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════════════════════════════════


def load_users() -> pd.DataFrame:
    """Baca users dari Google Sheets. Return DataFrame."""
    spreadsheet = _get_spreadsheet()
    worksheet = get_or_create_worksheet(
        spreadsheet,
        USERS_SHEET,
        ["username", "password_hash", "display_name", "created_at"],
    )

    data = worksheet.get_all_records()
    if not data:
        return pd.DataFrame(
            columns=["username", "password_hash", "display_name", "created_at"]
        )

    return pd.DataFrame(data)


def save_users(df: pd.DataFrame) -> None:
    """Tulis DataFrame users ke Google Sheets."""
    spreadsheet = _get_spreadsheet()
    worksheet = spreadsheet.worksheet(USERS_SHEET)

    # Clear semua data kecuali header
    worksheet.clear()

    # Tulis header
    headers = ["username", "password_hash", "display_name", "created_at"]
    worksheet.append_row(headers)

    # Tulis data
    if not df.empty:
        values = df[headers].fillna("").values.tolist()
        worksheet.append_rows(values)


def get_user(username: str) -> dict | None:
    """Return dict user atau None jika tidak ditemukan."""
    df = load_users()
    row = df[df["username"] == username]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def add_user(username: str, password_hash: str, display_name: str) -> None:
    """Tambah user baru ke Google Sheets."""
    df = load_users()
    new_row = pd.DataFrame(
        [
            {
                "username": username,
                "password_hash": password_hash,
                "display_name": display_name,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
        ]
    )
    df = pd.concat([df, new_row], ignore_index=True)
    save_users(df)


def update_user_password(username: str, new_hash: str) -> None:
    """Update password_hash user di Google Sheets."""
    df = load_users()
    df.loc[df["username"] == username, "password_hash"] = new_hash
    save_users(df)


def get_all_usernames() -> list[str]:
    """Return list semua username yang terdaftar."""
    return load_users()["username"].tolist()


def count_users() -> int:
    """Return jumlah user terdaftar."""
    return len(load_users())


# ══════════════════════════════════════════════════════════════════════════
# TRANSACTIONS
# ══════════════════════════════════════════════════════════════════════════


def load_transactions() -> pd.DataFrame:
    """Baca transactions dari Google Sheets. Return DataFrame."""
    spreadsheet = _get_spreadsheet()
    worksheet = get_or_create_worksheet(
        spreadsheet,
        TRANSACTIONS_SHEET,
        ["id", "username", "date", "type", "category", "amount", "note", "created_at"],
    )

    data = worksheet.get_all_records()
    if not data:
        return pd.DataFrame(
            columns=[
                "id",
                "username",
                "date",
                "type",
                "category",
                "amount",
                "note",
                "created_at",
            ]
        )

    df = pd.DataFrame(data)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def save_transactions(df: pd.DataFrame) -> None:
    """Tulis DataFrame transaksi ke Google Sheets."""
    spreadsheet = _get_spreadsheet()
    worksheet = spreadsheet.worksheet(TRANSACTIONS_SHEET)

    # Clear semua data kecuali header
    worksheet.clear()

    # Tulis header
    headers = [
        "id",
        "username",
        "date",
        "type",
        "category",
        "amount",
        "note",
        "created_at",
    ]
    worksheet.append_row(headers)

    # Tulis data
    if not df.empty:
        # Normalkan kolom date ke format YYYY-MM-DD
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        values = df[headers].fillna("").values.tolist()
        worksheet.append_rows(values)


def get_user_transactions(username: str) -> pd.DataFrame:
    """Return semua transaksi milik username tertentu."""
    df = load_transactions()
    return df[df["username"] == username].copy()


def add_transaction(
    username: str,
    txn_date: date,
    txn_type: str,
    category: str,
    amount: float,
    note: str,
) -> str:
    """Tambah transaksi baru. Return id transaksi."""
    df = load_transactions()
    txn_id = str(uuid.uuid4())
    new_row = pd.DataFrame(
        [
            {
                "id": txn_id,
                "username": username,
                "date": txn_date.isoformat(),
                "type": txn_type,
                "category": category,
                "amount": amount,
                "note": note,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
        ]
    )
    df = pd.concat([df, new_row], ignore_index=True)
    save_transactions(df)
    return txn_id


def delete_transaction(txn_id: str) -> bool:
    """Hapus transaksi berdasarkan id. Return True jika berhasil."""
    df = load_transactions()
    before = len(df)
    df = df[df["id"] != txn_id]
    if len(df) == before:
        return False
    save_transactions(df)
    return True


# ══════════════════════════════════════════════════════════════════════════
# INITIALIZE
# ══════════════════════════════════════════════════════════════════════════


def initialize_data() -> None:
    """Inisialisasi Google Sheets worksheets."""
    from sheets_config import init_sheets

    init_sheets()
