"""
auth.py — Autentikasi: login, register, ganti password, require_login
         Session persistence via st.query_params + server-side token file
"""

import re
import json
import uuid
import os
from datetime import datetime, timedelta

import streamlit as st
import bcrypt

from data import (
    get_user,
    add_user,
    update_user_password,
    get_all_usernames,
    count_users,
)

# ── Konstanta ──────────────────────────────────────────────────────────────
MAX_USERS = 10
SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions.json")
SESSION_EXPIRY_DAYS = 7
PARAM_KEY = "sid"  # nama query param di URL


# ══════════════════════════════════════════════════════════════════════════
# SERVER-SIDE SESSION STORE  (sessions.json)
# ══════════════════════════════════════════════════════════════════════════


def _load_sessions() -> dict:
    if not os.path.exists(SESSION_FILE):
        return {}
    try:
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_sessions(sessions: dict) -> None:
    with open(SESSION_FILE, "w") as f:
        json.dump(sessions, f)


def _purge_expired(sessions: dict) -> dict:
    """Hapus token yang sudah expired."""
    now = datetime.now().isoformat()
    return {k: v for k, v in sessions.items() if v.get("expires_at", "") > now}


def create_session_token(username: str, display_name: str) -> str:
    """Buat token baru, simpan ke sessions.json, return token string."""
    sessions = _load_sessions()
    sessions = _purge_expired(sessions)

    token = str(uuid.uuid4())
    sessions[token] = {
        "username": username,
        "display_name": display_name,
        "expires_at": (
            datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)
        ).isoformat(),
    }
    _save_sessions(sessions)
    return token


def get_session_by_token(token: str) -> dict | None:
    """Return session dict jika token valid dan belum expired, else None."""
    if not token:
        return None
    sessions = _load_sessions()
    session = sessions.get(token)
    if not session:
        return None
    if session.get("expires_at", "") < datetime.now().isoformat():
        # Expired — hapus
        del sessions[token]
        _save_sessions(sessions)
        return None
    # Verifikasi user masih ada
    if get_user(session["username"]) is None:
        return None
    return session


def delete_session_token(token: str) -> None:
    """Hapus token dari sessions.json."""
    if not token:
        return
    sessions = _load_sessions()
    sessions.pop(token, None)
    _save_sessions(sessions)


# ══════════════════════════════════════════════════════════════════════════
# QUERY PARAM HELPERS
# ══════════════════════════════════════════════════════════════════════════


def get_token_from_url() -> str:
    """Baca token dari URL query param ?sid=..."""
    return st.query_params.get(PARAM_KEY, "")


def set_token_in_url(token: str) -> None:
    """Tulis token ke URL query param."""
    st.query_params[PARAM_KEY] = token


def clear_token_from_url() -> None:
    """Hapus token dari URL query param."""
    if PARAM_KEY in st.query_params:
        del st.query_params[PARAM_KEY]


# ══════════════════════════════════════════════════════════════════════════
# SESSION STATE HELPERS
# ══════════════════════════════════════════════════════════════════════════


def _init_session() -> None:
    defaults = {
        "logged_in": False,
        "username": "",
        "display_name": "",
        "page": "login",
        "fail_count": 0,
        "form_key": 0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def restore_session_from_token() -> bool:
    """
    Coba restore session dari URL token.
    Return True jika berhasil, False jika tidak.
    Dipanggil di awal app.py sebelum routing.
    """
    _init_session()
    if st.session_state["logged_in"]:
        return True

    token = get_token_from_url()
    session = get_session_by_token(token)
    if session:
        st.session_state["logged_in"] = True
        st.session_state["username"] = session["username"]
        st.session_state["display_name"] = session["display_name"]
        if st.session_state["page"] == "login":
            st.session_state["page"] = "dashboard"
        return True
    return False


def require_login() -> None:
    """
    Cek apakah user sudah login.
    Coba restore dari URL token dulu. Jika gagal → redirect login.
    """
    _init_session()
    if st.session_state["logged_in"]:
        return

    # Coba restore dari token di URL
    if restore_session_from_token():
        return

    # Tidak ada session valid → ke login
    st.session_state["page"] = "login"
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# VERIFY PASSWORD
# ══════════════════════════════════════════════════════════════════════════


def verify_password(username: str, password: str) -> bool:
    user = get_user(username)
    if user is None:
        return False
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), user["password_hash"].encode("utf-8")
        )
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════


def render_login_page() -> None:
    _init_session()

    st.markdown(
        """
        <div style="text-align:center; padding: 2rem 0 1rem 0;">
            <h1 style="font-size:2.2rem;">💰 Cash Flow Pribadi</h1>
            <p style="color:#6b7280;">Kelola keuangan bersama teman-teman</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 Masuk ke Akun")

        usernames = get_all_usernames()
        if not usernames:
            st.warning("Belum ada akun terdaftar. Silakan daftar terlebih dahulu.")
            if st.button("Daftar Sekarang", width="stretch"):
                st.session_state["page"] = "register"
                st.rerun()
            return

        with st.form("login_form"):
            selected_user = st.selectbox("Username", options=usernames)
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Masuk", width="stretch")

        if submitted:
            if not password:
                st.error("Password tidak boleh kosong.")
            elif verify_password(selected_user, password):
                user = get_user(selected_user)
                token = create_session_token(selected_user, user["display_name"])

                # Simpan ke session state
                st.session_state["logged_in"] = True
                st.session_state["username"] = selected_user
                st.session_state["display_name"] = user["display_name"]
                st.session_state["page"] = "dashboard"
                st.session_state["fail_count"] = 0

                # Simpan token ke URL — synchronous, langsung efektif
                set_token_in_url(token)
                st.rerun()
            else:
                st.error("❌ Password salah. Silakan coba lagi.")

        st.markdown("---")
        st.markdown(
            "<p style='text-align:center;'>Belum punya akun? "
            "<span style='color:#3b82f6;'>Daftar di sini</span></p>",
            unsafe_allow_html=True,
        )
        if st.button("➕ Daftar Akun Baru", width="stretch", type="secondary"):
            st.session_state["page"] = "register"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# REGISTER
# ══════════════════════════════════════════════════════════════════════════


def is_username_taken(username: str) -> bool:
    return username in get_all_usernames()


def register_user(username: str, password: str, display_name: str) -> tuple[bool, str]:
    display_name = display_name.strip()
    if len(display_name) < 2:
        return False, "Nama lengkap minimal 2 karakter."

    username = username.strip().lower()
    if not (3 <= len(username) <= 20):
        return False, "Username harus 3–20 karakter."
    if not re.match(r"^[a-z0-9_]+$", username):
        return False, "Username hanya boleh huruf kecil, angka, dan underscore (_)."
    if is_username_taken(username):
        return False, "Username sudah dipakai. Pilih username lain."
    if len(password) < 6:
        return False, "Password minimal 6 karakter."

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    add_user(username, hashed, display_name)
    return True, "Akun berhasil dibuat! Silakan login."


def render_register_page(max_users: int = MAX_USERS) -> None:
    _init_session()

    st.markdown(
        """
        <div style="text-align:center; padding: 2rem 0 1rem 0;">
            <h1 style="font-size:2.2rem;">💰 Cash Flow Pribadi</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("📝 Daftar Akun Baru")

        if count_users() >= max_users:
            st.error("🚫 Pendaftaran ditutup. Hubungi admin.")
            if st.button("← Kembali ke Login", width="stretch"):
                st.session_state["page"] = "login"
                st.rerun()
            return

        with st.form(f"register_form_{st.session_state['form_key']}"):
            display_name = st.text_input("Nama Lengkap")
            username = st.text_input(
                "Username", help="3–20 karakter, huruf kecil, angka, underscore"
            )
            password = st.text_input(
                "Password", type="password", help="Minimal 6 karakter"
            )
            confirm_password = st.text_input("Konfirmasi Password", type="password")
            submitted = st.form_submit_button("Daftar", width="stretch")

        if submitted:
            if password != confirm_password:
                st.error("❌ Password dan konfirmasi tidak cocok.")
            else:
                ok, msg = register_user(username, password, display_name)
                if ok:
                    st.success(f"✅ {msg}")
                    st.session_state["form_key"] += 1
                    st.session_state["page"] = "login"
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

        st.markdown("---")
        if st.button("← Sudah punya akun? Login", width="stretch", type="secondary"):
            st.session_state["page"] = "login"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# GANTI PASSWORD
# ══════════════════════════════════════════════════════════════════════════


def change_password(username: str, old_pass: str, new_pass: str) -> tuple[bool, str]:
    if not verify_password(username, old_pass):
        return False, "Password lama tidak cocok."
    if len(new_pass) < 6:
        return False, "Password baru minimal 6 karakter."
    if old_pass == new_pass:
        return False, "Password baru tidak boleh sama dengan password lama."

    new_hash = bcrypt.hashpw(new_pass.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    update_user_password(username, new_hash)
    return True, "Password berhasil diubah."


def render_change_password_page() -> None:
    require_login()

    st.title("🔑 Ganti Password")
    st.markdown("---")

    username = st.session_state["username"]
    fail_count = st.session_state.get("fail_count", 0)

    if fail_count >= 3:
        st.error("🚫 Terlalu banyak percobaan. Logout dan login kembali.")
        return

    with st.form(f"change_pass_form_{st.session_state['form_key']}"):
        old_pass = st.text_input("Password Lama", type="password")
        new_pass = st.text_input(
            "Password Baru", type="password", help="Minimal 6 karakter"
        )
        confirm_pass = st.text_input("Konfirmasi Password Baru", type="password")
        submitted = st.form_submit_button("Simpan Password Baru", width="stretch")

    if submitted:
        if not old_pass or not new_pass or not confirm_pass:
            st.error("❌ Semua field harus diisi.")
        elif new_pass != confirm_pass:
            st.error("❌ Password baru dan konfirmasi tidak cocok.")
        else:
            ok, msg = change_password(username, old_pass, new_pass)
            if ok:
                st.success(f"✅ {msg}")
                st.session_state["fail_count"] = 0
                st.session_state["form_key"] += 1
                st.rerun()
            else:
                st.session_state["fail_count"] += 1
                remaining = 3 - st.session_state["fail_count"]
                if remaining > 0:
                    st.error(f"❌ {msg} Sisa percobaan: {remaining}.")
                else:
                    st.error("🚫 Terlalu banyak percobaan. Logout dan login kembali.")
                    st.rerun()
