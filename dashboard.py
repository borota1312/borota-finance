"""
dashboard.py — Komponen dashboard: metric cards, chart Plotly
"""

from datetime import date, timedelta
import calendar

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data import get_user_transactions, INCOME_CATEGORIES, EXPENSE_CATEGORIES


# ══════════════════════════════════════════════════════════════════════════
# FORMAT RUPIAH
# ══════════════════════════════════════════════════════════════════════════


def fmt_rupiah(amount: float) -> str:
    """Format angka ke string Rupiah: Rp 1.500.000"""
    return f"Rp {amount:,.0f}".replace(",", ".")


# ══════════════════════════════════════════════════════════════════════════
# CUSTOM CSS
# ══════════════════════════════════════════════════════════════════════════


def inject_css() -> None:
    st.markdown(
        """
        <style>
        /* Metric card */
        .metric-card {
            background: #ffffff;
            border-radius: 10px;
            padding: 1.2rem 1.4rem;
            box-shadow: 0 1px 6px rgba(0,0,0,0.08);
            margin-bottom: 0.5rem;
        }
        .metric-card .label {
            font-size: 0.82rem;
            color: #6b7280;
            font-weight: 500;
            margin-bottom: 0.3rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .metric-card .value {
            font-size: 1.8rem;
            font-weight: 700;
            line-height: 1.2;
        }
        .metric-card .sub {
            font-size: 0.78rem;
            color: #9ca3af;
            margin-top: 0.2rem;
        }
        /* Sidebar avatar */
        .avatar-circle {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3b82f6, #6366f1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            font-weight: 700;
            color: white;
            margin: 0 auto 0.5rem auto;
        }
        /* Tabel riwayat */
        .income-row  { background-color: #f0fdf4 !important; }
        .expense-row { background-color: #fef2f2 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════
# METRIC CARDS
# ══════════════════════════════════════════════════════════════════════════


def _card_html(label: str, value: str, sub: str, border_color: str) -> str:
    return f"""
    <div class="metric-card" style="border-left: 4px solid {border_color};">
        <div class="label">{label}</div>
        <div class="value" style="color:{border_color};">{value}</div>
        <div class="sub">{sub}</div>
    </div>
    """


def render_metric_cards(df_month: pd.DataFrame, month_label: str) -> None:
    """Render 4 metric cards dalam satu baris."""
    income = df_month[df_month["type"] == "Pemasukan"]["amount"].sum()
    expense = df_month[df_month["type"] == "Pengeluaran"]["amount"].sum()
    balance = income - expense
    count = len(df_month)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            _card_html("Total Pemasukan", fmt_rupiah(income), month_label, "#22c55e"),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            _card_html(
                "Total Pengeluaran", fmt_rupiah(expense), month_label, "#ef4444"
            ),
            unsafe_allow_html=True,
        )
    with c3:
        color = "#22c55e" if balance >= 0 else "#ef4444"
        st.markdown(
            _card_html("Saldo Bersih", fmt_rupiah(balance), month_label, color),
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            _card_html(
                "Jumlah Transaksi", str(count), f"transaksi {month_label}", "#6b7280"
            ),
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════
# CHARTS
# ══════════════════════════════════════════════════════════════════════════


def render_donut_chart(df_month: pd.DataFrame) -> None:
    """Donut chart: breakdown pengeluaran per kategori bulan ini."""
    st.subheader("🍩 Pengeluaran per Kategori")
    expense_df = df_month[df_month["type"] == "Pengeluaran"]

    if expense_df.empty:
        st.info("Belum ada data pengeluaran bulan ini.")
        return

    grouped = expense_df.groupby("category")["amount"].sum().reset_index()
    grouped.columns = ["Kategori", "Jumlah"]

    fig = px.pie(
        grouped,
        names="Kategori",
        values="Jumlah",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Rp %{value:,.0f}<extra></extra>",
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5),
        margin=dict(t=20, b=20, l=20, r=20),
        height=320,
    )
    st.plotly_chart(fig, width="stretch")


def render_weekly_bar_chart(df_month: pd.DataFrame) -> None:
    """Bar chart: pemasukan vs pengeluaran per minggu bulan ini."""
    st.subheader("📊 Pemasukan vs Pengeluaran per Minggu")

    if df_month.empty:
        st.info("Belum ada data transaksi bulan ini.")
        return

    df = df_month.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.isocalendar().week.astype(str)
    df["week_label"] = "Minggu ke-" + (((df["date"].dt.day - 1) // 7 + 1).astype(str))

    grouped = df.groupby(["week_label", "type"])["amount"].sum().reset_index()
    grouped.columns = ["Minggu", "Tipe", "Jumlah"]

    # Pastikan urutan minggu benar
    week_order = [f"Minggu ke-{i}" for i in range(1, 6)]
    grouped["Minggu"] = pd.Categorical(
        grouped["Minggu"], categories=week_order, ordered=True
    )
    grouped = grouped.sort_values("Minggu")

    fig = px.bar(
        grouped,
        x="Minggu",
        y="Jumlah",
        color="Tipe",
        barmode="group",
        color_discrete_map={"Pemasukan": "#22c55e", "Pengeluaran": "#ef4444"},
        text_auto=False,
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>%{fullData.name}: Rp %{y:,.0f}<extra></extra>"
    )
    fig.update_layout(
        yaxis_title="Jumlah (Rp)",
        xaxis_title="",
        legend_title="",
        margin=dict(t=20, b=20, l=20, r=20),
        height=320,
    )
    st.plotly_chart(fig, width="stretch")


def render_daily_balance_chart(df_all: pd.DataFrame) -> None:
    """Line chart: tren saldo harian 30 hari terakhir."""
    st.subheader("📈 Tren Saldo Harian (30 Hari Terakhir)")

    if df_all.empty:
        st.info("Belum ada data transaksi.")
        return

    today = date.today()
    start = today - timedelta(days=29)

    df = df_all.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df[df["date"] >= start]

    if df.empty:
        st.info("Belum ada transaksi dalam 30 hari terakhir.")
        return

    # Hitung net per hari
    df["signed"] = df.apply(
        lambda r: r["amount"] if r["type"] == "Pemasukan" else -r["amount"], axis=1
    )
    daily = df.groupby("date")["signed"].sum().reset_index()
    daily.columns = ["Tanggal", "Net"]

    # Isi hari yang tidak ada transaksi dengan 0
    all_dates = pd.date_range(start=start, end=today, freq="D").date
    date_df = pd.DataFrame({"Tanggal": all_dates})
    daily = date_df.merge(daily, on="Tanggal", how="left").fillna(0)
    daily["Saldo Kumulatif"] = daily["Net"].cumsum()
    daily["Tanggal"] = pd.to_datetime(daily["Tanggal"])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily["Tanggal"],
            y=daily["Saldo Kumulatif"],
            mode="lines+markers",
            line=dict(color="#3b82f6", width=2.5),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.08)",
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Saldo: Rp %{y:,.0f}<extra></extra>",
            name="Saldo",
        )
    )
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Saldo (Rp)",
        margin=dict(t=20, b=20, l=20, r=20),
        height=300,
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")


# ══════════════════════════════════════════════════════════════════════════
# FILTER PERIODE
# ══════════════════════════════════════════════════════════════════════════


def render_period_filter() -> tuple[int, int]:
    """
    Render filter bulan & tahun.
    Return (month, year) yang dipilih.
    """
    today = date.today()
    months = {
        1: "Januari",
        2: "Februari",
        3: "Maret",
        4: "April",
        5: "Mei",
        6: "Juni",
        7: "Juli",
        8: "Agustus",
        9: "September",
        10: "Oktober",
        11: "November",
        12: "Desember",
    }
    col1, col2, _ = st.columns([1, 1, 3])
    with col1:
        month = st.selectbox(
            "Bulan",
            options=list(months.keys()),
            format_func=lambda m: months[m],
            index=today.month - 1,
        )
    with col2:
        year = st.selectbox(
            "Tahun",
            options=list(range(today.year - 3, today.year + 1)),
            index=3,
        )
    return month, year


def filter_by_month(df: pd.DataFrame, month: int, year: int) -> pd.DataFrame:
    """Filter DataFrame transaksi berdasarkan bulan dan tahun."""
    if df.empty:
        return df
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    return df[(df["date"].dt.month == month) & (df["date"].dt.year == year)]


# ══════════════════════════════════════════════════════════════════════════
# HALAMAN DASHBOARD UTAMA
# ══════════════════════════════════════════════════════════════════════════


def render_dashboard_page() -> None:
    """Render halaman dashboard lengkap."""
    from auth import require_login

    require_login()

    inject_css()

    username = st.session_state["username"]
    display_name = st.session_state["display_name"]

    st.markdown(f"## 👋 Selamat datang, **{display_name}**!")
    st.markdown("---")

    # Filter periode
    month, year = render_period_filter()
    months_id = {
        1: "Januari",
        2: "Februari",
        3: "Maret",
        4: "April",
        5: "Mei",
        6: "Juni",
        7: "Juli",
        8: "Agustus",
        9: "September",
        10: "Oktober",
        11: "November",
        12: "Desember",
    }
    month_label = f"{months_id[month]} {year}"

    # Ambil data
    df_all = get_user_transactions(username)
    df_month = filter_by_month(df_all, month, year)

    # Metric cards
    render_metric_cards(df_month, month_label)
    st.markdown("<br>", unsafe_allow_html=True)

    # Charts — baris 1
    col_left, col_right = st.columns([1, 1])
    with col_left:
        render_donut_chart(df_month)
    with col_right:
        render_weekly_bar_chart(df_month)

    # Charts — baris 2
    render_daily_balance_chart(df_all)
