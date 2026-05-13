"""
app.py — Entry point Streamlit: router halaman, sidebar, navigasi
         Session persistence via URL query param ?sid=<token>
"""

import streamlit as st
from datetime import date
import pandas as pd

# ── Konstanta ──────────────────────────────────────────────────────────────
MAX_USERS = 10

# ── Konfigurasi halaman ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cash Flow Pribadi",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Import modul lokal ─────────────────────────────────────────────────────
from data import (
    initialize_data,
    get_user_transactions,
    add_transaction,
    delete_transaction,
    INCOME_CATEGORIES,
    EXPENSE_CATEGORIES,
)
from auth import (
    restore_session_from_token,
    delete_session_token,
    get_token_from_url,
    clear_token_from_url,
    require_login,
    render_login_page,
    render_register_page,
    render_change_password_page,
)
from dashboard import (
    render_dashboard_page,
    inject_css,
    fmt_rupiah,
    render_period_filter,
    filter_by_month,
)

# ══════════════════════════════════════════════════════════════════════════
# INISIALISASI
# ══════════════════════════════════════════════════════════════════════════

# Initialize data hanya sekali per session untuk menghindari quota exceeded
if "data_initialized" not in st.session_state:
    try:
        initialize_data()
        st.session_state["data_initialized"] = True
    except Exception as e:
        # Jika quota exceeded, tampilkan pesan yang lebih user-friendly
        if "429" in str(e) or "Quota exceeded" in str(e):
            st.error(
                "⚠️ **Google Sheets API Quota Exceeded**\n\n"
                "Aplikasi sedang mengalami traffic tinggi. "
                "Silakan tunggu 1-2 menit dan refresh halaman.\n\n"
                "Jika masalah berlanjut, hubungi administrator."
            )
            st.stop()
        else:
            raise

# Inisialisasi session state defaults
_defaults = {
    "logged_in": False,
    "username": "",
    "display_name": "",
    "page": "login",
    "fail_count": 0,
    "form_key": 0,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Restore session dari URL token ─────────────────────────────────────────
# st.query_params tersedia synchronous sejak run pertama — tidak ada delay.
# Saat refresh, token masih ada di URL → session ter-restore otomatis.
restore_session_from_token()


# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════


def render_sidebar() -> None:
    if not st.session_state.get("logged_in"):
        return

    display_name = st.session_state["display_name"]
    username = st.session_state["username"]
    initials = "".join(w[0].upper() for w in display_name.split()[:2])

    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align:center; padding: 1rem 0 0.5rem 0;">
                <div style="
                    width:60px; height:60px; border-radius:50%;
                    background: linear-gradient(135deg, #3b82f6, #6366f1);
                    display:flex; align-items:center; justify-content:center;
                    font-size:1.5rem; font-weight:700; color:white;
                    margin: 0 auto 0.6rem auto;
                ">{initials}</div>
                <div style="font-weight:600; font-size:1rem;">{display_name}</div>
                <div style="color:#6b7280; font-size:0.82rem;">@{username}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")

        menu_items = [
            ("🏠", "Dashboard", "dashboard"),
            ("➕", "Tambah Transaksi", "add_transaction"),
            ("📋", "Riwayat Transaksi", "history"),
            ("📥", "Export Data", "export"),
            ("🔑", "Ganti Password", "change_password"),
        ]

        for icon, label, page_key in menu_items:
            is_active = st.session_state["page"] == page_key
            if st.button(
                f"{icon} {label}",
                key=f"nav_{page_key}",
                width="stretch",
                type="primary" if is_active else "secondary",
            ):
                st.session_state["page"] = page_key
                st.rerun()

        st.markdown("---")

        if st.button("🚪 Logout", width="stretch", type="secondary"):
            # Hapus token dari server dan URL
            token = get_token_from_url()
            delete_session_token(token)
            clear_token_from_url()
            # Reset session state
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.session_state["display_name"] = ""
            st.session_state["fail_count"] = 0
            st.session_state["page"] = "login"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# HALAMAN: TAMBAH TRANSAKSI
# ══════════════════════════════════════════════════════════════════════════


def render_add_transaction_page() -> None:
    require_login()
    inject_css()

    st.title("➕ Tambah Transaksi")
    st.markdown("---")

    username = st.session_state["username"]

    col_type, _ = st.columns([1, 3])
    with col_type:
        txn_type = st.selectbox(
            "Tipe Transaksi",
            options=["Pemasukan", "Pengeluaran"],
            key="txn_type_select",
        )
    # Simpan ke session state agar nilai konsisten saat form submit
    st.session_state["_txn_type_confirmed"] = txn_type

    categories = INCOME_CATEGORIES if txn_type == "Pemasukan" else EXPENSE_CATEGORIES

    with st.form(f"add_txn_form_{st.session_state['form_key']}"):
        col1, col2 = st.columns(2)
        with col1:
            txn_date = st.date_input("Tanggal", value=date.today())
            st.text_input("Tipe", value=txn_type, disabled=True)
        with col2:
            category = st.selectbox("Kategori", options=categories)
            amount = st.number_input(
                "Jumlah (Rp)",
                min_value=0,
                step=10_000,
                format="%d",
                help="Masukkan jumlah dalam Rupiah",
            )

        note = st.text_area("Catatan (opsional)", height=80)
        submitted = st.form_submit_button("💾 Simpan Transaksi", width="stretch")

    if submitted:
        # Gunakan nilai yang dikonfirmasi sebelum form di-render
        final_type = st.session_state.get("_txn_type_confirmed", txn_type)
        if amount <= 0:
            st.error("❌ Jumlah harus lebih dari 0.")
        elif txn_date is None:
            st.error("❌ Tanggal tidak boleh kosong.")
        else:
            add_transaction(
                username, txn_date, final_type, category, float(amount), note
            )
            st.success(
                f"✅ Transaksi berhasil disimpan! ({final_type} — {fmt_rupiah(amount)})"
            )
            st.balloons()
            st.session_state["form_key"] += 1
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# HALAMAN: RIWAYAT TRANSAKSI
# ══════════════════════════════════════════════════════════════════════════


def render_history_page() -> None:
    require_login()
    inject_css()

    st.title("📋 Riwayat Transaksi")
    st.markdown("---")

    username = st.session_state["username"]
    df = get_user_transactions(username)

    if df.empty:
        st.info("Belum ada transaksi. Mulai tambahkan transaksi pertamamu!")
        return

    df["date"] = pd.to_datetime(df["date"])

    st.subheader("🔍 Filter")
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        type_filter = st.selectbox(
            "Tipe", options=["Semua", "Pemasukan", "Pengeluaran"]
        )
    with fc2:
        all_cats = ["Semua"] + INCOME_CATEGORIES + EXPENSE_CATEGORIES
        cat_filter = st.selectbox("Kategori", options=all_cats)
    with fc3:
        date_from = st.date_input("Dari Tanggal", value=df["date"].min().date())
    with fc4:
        date_to = st.date_input("Sampai Tanggal", value=date.today())

    filtered = df.copy()
    if type_filter != "Semua":
        filtered = filtered[filtered["type"] == type_filter]
    if cat_filter != "Semua":
        filtered = filtered[filtered["category"] == cat_filter]

    date_from_dt = pd.to_datetime(date_from)
    date_to_dt = pd.to_datetime(date_to)
    filtered = filtered[
        (filtered["date"] >= date_from_dt) & (filtered["date"] <= date_to_dt)
    ]
    filtered = filtered.sort_values("date", ascending=False)

    st.markdown(f"**{len(filtered)} transaksi ditemukan**")
    st.markdown("---")

    if filtered.empty:
        st.info("Tidak ada transaksi yang sesuai filter.")
        return

    if "confirm_delete_id" not in st.session_state:
        st.session_state["confirm_delete_id"] = None

    for _, row in filtered.iterrows():
        txn_id = row["id"]
        is_income = row["type"] == "Pemasukan"
        bg_color = "#f0fdf4" if is_income else "#fef2f2"
        amt_color = "#16a34a" if is_income else "#dc2626"
        icon = "📈" if is_income else "📉"
        note_html = (
            f'&nbsp;·&nbsp;<span style="color:#9ca3af; font-size:0.85rem;">{row["note"]}</span>'
            if row["note"] and str(row["note"]) not in ("", "nan")
            else ""
        )

        with st.container():
            st.markdown(
                f"""
                <div style="
                    background:{bg_color}; border-radius:8px;
                    padding:0.7rem 1rem; margin-bottom:0.4rem;
                    border-left: 3px solid {'#22c55e' if is_income else '#ef4444'};
                ">
                    <span style="font-weight:600;">{icon} {row['date'].strftime('%d %b %Y')}</span>
                    &nbsp;·&nbsp;
                    <span style="color:#6b7280;">{row['category']}</span>
                    &nbsp;·&nbsp;
                    <span style="font-weight:700; color:{amt_color};">{fmt_rupiah(row['amount'])}</span>
                    {note_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_spacer, col_del = st.columns([6, 1])
            with col_del:
                if st.session_state["confirm_delete_id"] == txn_id:
                    c_yes, c_no = st.columns(2)
                    with c_yes:
                        if st.button("✅ Ya", key=f"yes_{txn_id}", width="stretch"):
                            delete_transaction(txn_id)
                            st.session_state["confirm_delete_id"] = None
                            st.success("Transaksi dihapus.")
                            st.rerun()
                    with c_no:
                        if st.button("❌ Batal", key=f"no_{txn_id}", width="stretch"):
                            st.session_state["confirm_delete_id"] = None
                            st.rerun()
                else:
                    if st.button("🗑️", key=f"del_{txn_id}", help="Hapus transaksi ini"):
                        st.session_state["confirm_delete_id"] = txn_id
                        st.rerun()

    st.markdown("---")
    total_in = filtered[filtered["type"] == "Pemasukan"]["amount"].sum()
    total_out = filtered[filtered["type"] == "Pengeluaran"]["amount"].sum()
    s1, s2, s3 = st.columns(3)
    s1.metric("Total Pemasukan", fmt_rupiah(total_in))
    s2.metric("Total Pengeluaran", fmt_rupiah(total_out))
    s3.metric("Saldo Bersih", fmt_rupiah(total_in - total_out))


# ══════════════════════════════════════════════════════════════════════════
# HALAMAN: EXPORT DATA
# ══════════════════════════════════════════════════════════════════════════


def render_export_page() -> None:
    require_login()
    inject_css()

    st.title("📥 Export Data")
    st.markdown("---")

    username = st.session_state["username"]
    df = get_user_transactions(username)

    if df.empty:
        st.info("Belum ada transaksi untuk di-export.")
        return

    df["date"] = pd.to_datetime(df["date"])

    st.subheader("Filter Sebelum Download")
    month, year = render_period_filter()

    export_all = st.checkbox("Export semua data (abaikan filter bulan)", value=False)

    if export_all:
        export_df = df.copy()
        filename = f"cashflow_{username}_semua.csv"
    else:
        export_df = filter_by_month(df, month, year)
        months_id = {
            1: "Jan",
            2: "Feb",
            3: "Mar",
            4: "Apr",
            5: "Mei",
            6: "Jun",
            7: "Jul",
            8: "Agu",
            9: "Sep",
            10: "Okt",
            11: "Nov",
            12: "Des",
        }
        filename = f"cashflow_{username}_{months_id[month]}{year}.csv"

    st.markdown(f"**{len(export_df)} transaksi akan di-export**")

    if export_df.empty:
        st.warning("Tidak ada data untuk periode yang dipilih.")
        return

    preview = export_df.copy()
    preview["date"] = preview["date"].dt.strftime("%Y-%m-%d")
    preview["amount"] = preview["amount"].apply(fmt_rupiah)
    st.dataframe(
        preview[["date", "type", "category", "amount", "note"]].rename(
            columns={
                "date": "Tanggal",
                "type": "Tipe",
                "category": "Kategori",
                "amount": "Jumlah",
                "note": "Catatan",
            }
        ),
        width="stretch",
        hide_index=True,
    )

    csv_data = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download CSV",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        width="stretch",
    )


# ══════════════════════════════════════════════════════════════════════════
# ROUTER UTAMA
# ══════════════════════════════════════════════════════════════════════════


def main() -> None:
    render_sidebar()

    page = st.session_state.get("page", "login")

    if page == "login":
        render_login_page()
    elif page == "register":
        render_register_page(max_users=MAX_USERS)
    elif page == "dashboard":
        render_dashboard_page()
    elif page == "add_transaction":
        render_add_transaction_page()
    elif page == "history":
        render_history_page()
    elif page == "export":
        render_export_page()
    elif page == "change_password":
        render_change_password_page()
    else:
        st.session_state["page"] = "login"
        st.rerun()


main()
