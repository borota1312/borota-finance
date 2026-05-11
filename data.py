"""
data.py — Semua fungsi baca/tulis CSV (single responsibility)
Menangani: users.csv, transactions.csv, file lock.

File CSV dibuat otomatis saat pertama kali data disimpan —
tidak ada seed/dummy data. users.csv terbentuk saat register pertama,
transactions.csv terbentuk saat transaksi pertama disimpan.
"""

import os
import uuid
import fcntl
import tempfile
import shutil
from datetime import datetime, date

import pandas as pd

# ── Path file ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_CSV = os.path.join(BASE_DIR, "users.csv")
TRANSACTIONS_CSV = os.path.join(BASE_DIR, "transactions.csv")

# ── Kolom CSV ──────────────────────────────────────────────────────────────
USER_COLS = ["username", "password_hash", "display_name", "created_at"]
TXN_COLS = [
    "id",
    "username",
    "date",
    "type",
    "category",
    "amount",
    "note",
    "created_at",
]

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
# HELPER: File-safe write (tmp-rename trick + fcntl lock)
# ══════════════════════════════════════════════════════════════════════════


def _safe_write_csv(df: pd.DataFrame, filepath: str, columns: list) -> None:
    """Tulis DataFrame ke CSV secara aman menggunakan tmp-rename trick."""
    dir_name = os.path.dirname(filepath)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w") as tmp_file:
            fcntl.flock(tmp_file, fcntl.LOCK_EX)
            df[columns].to_csv(tmp_file, index=False)
            fcntl.flock(tmp_file, fcntl.LOCK_UN)
        shutil.move(tmp_path, filepath)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


# ══════════════════════════════════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════════════════════════════════


def load_users() -> pd.DataFrame:
    """Baca users.csv. Return DataFrame kosong jika file belum ada."""
    if not os.path.exists(USERS_CSV):
        return pd.DataFrame(columns=USER_COLS)
    df = pd.read_csv(USERS_CSV, dtype=str)
    for col in USER_COLS:
        if col not in df.columns:
            df[col] = ""
    return df[USER_COLS]


def save_users(df: pd.DataFrame) -> None:
    """Tulis DataFrame users ke CSV. File dibuat otomatis jika belum ada."""
    _safe_write_csv(df, USERS_CSV, USER_COLS)


def get_user(username: str) -> dict | None:
    """Return dict user atau None jika tidak ditemukan."""
    df = load_users()
    row = df[df["username"] == username]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def add_user(username: str, password_hash: str, display_name: str) -> None:
    """
    Tambah user baru ke users.csv.
    Jika users.csv belum ada, file dibuat otomatis saat save_users dipanggil.
    """
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
    """Update password_hash user di users.csv."""
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
    """Baca transactions.csv. Return DataFrame kosong jika file belum ada."""
    if not os.path.exists(TRANSACTIONS_CSV):
        return pd.DataFrame(columns=TXN_COLS)
    df = pd.read_csv(TRANSACTIONS_CSV, dtype=str)
    for col in TXN_COLS:
        if col not in df.columns:
            df[col] = ""
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df[TXN_COLS]


def save_transactions(df: pd.DataFrame) -> None:
    """Tulis DataFrame transaksi ke CSV. File dibuat otomatis jika belum ada."""
    # Normalkan kolom date ke format YYYY-MM-DD sebelum simpan
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    _safe_write_csv(df, TRANSACTIONS_CSV, TXN_COLS)


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
    """
    Tambah transaksi baru. Return id transaksi.
    Jika transactions.csv belum ada, file dibuat otomatis saat save_transactions dipanggil.
    """
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
# INITIALIZE — no-op, dipertahankan agar app.py tidak error
# ══════════════════════════════════════════════════════════════════════════


def initialize_data() -> None:
    """
    Tidak melakukan apa-apa.
    CSV dibuat otomatis oleh add_user() dan add_transaction()
    saat data pertama kali disimpan.
    """
    pass
