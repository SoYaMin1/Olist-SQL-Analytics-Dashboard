"""Аналитический дашборд Olist: KPI, RFM, Cohort, Retention."""
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine, text

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "olist.db"
SQL_DIR = Path(__file__).resolve().parent.parent / "sql"

st.set_page_config(page_title="Olist Analytics", page_icon="📊", layout="wide")


@st.cache_resource
def get_engine():
    return create_engine(f"sqlite:///{DB_PATH}")


@st.cache_data
def run_sql(filename: str, params: dict | None = None) -> pd.DataFrame:
    sql = (SQL_DIR / filename).read_text(encoding="utf-8")
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


@st.cache_data
def load_orders_filtered(
    date_from: str, date_to: str, states: tuple, statuses: tuple
) -> pd.DataFrame:
    state_filter = ",".join(f"'{s}'" for s in states) if states else "''"
    status_filter = ",".join(f"'{s}'" for s in statuses) if statuses else "''"
    sql = f"""
        SELECT * FROM orders
        WHERE order_month BETWEEN :d1 AND :d2
          AND customer_state IN ({state_filter})
          AND order_status IN ({status_filter})
    """
    with get_engine().connect() as conn:
        return pd.read_sql(
            text(sql), conn, params={"d1": date_from, "d2": date_to}
        )


# ─────────────────────── БОКОВАЯ ПАНЕЛЬ ───────────────────────
st.sidebar.title("🎛️ Фильтры")

meta = pd.read_sql(
    "SELECT MIN(order_month) AS mn, MAX(order_month) AS mx FROM orders",
    get_engine(),
)
min_month, max_month = meta.iloc[0]["mn"], meta.iloc[0]["mx"]

date_range = st.sidebar.date_input(
    "Период",
    value=(pd.to_datetime(min_month), pd.to_datetime(max_month)),
    min_value=pd.to_datetime(min_month),
    max_value=pd.to_datetime(max_month),
)

all_states = pd.read_sql(
    "SELECT DISTINCT customer_state FROM orders ORDER BY 1", get_engine()
)["customer_state"].tolist()
states = st.sidebar.multiselect("Штаты", all_states, default=all_states[:5])

all_statuses = pd.read_sql(
    "SELECT DISTINCT order_status FROM orders ORDER BY 1", get_engine()
)["order_status"].tolist()
statuses = st.sidebar.multiselect(
    "Статусы заказа", all_statuses, default=["delivered"]
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    d1 = date_range[0].strftime("%Y-%m")
    d2 = date_range[1].strftime("%Y-%m")
else:
    d1, d2 = min_month, max_month

orders = load_orders_filtered(d1, d2, tuple(states), tuple(statuses))

# ─────────────────────── KPI ───────────────────────
st.title("📊 Olist Analytics Dashboard")
st.caption(f"Период: **{d1}** — **{d2}** | Штатов: {len(states)} | Заказов: {len(orders):,}")

if orders.empty:
    st.warning("Нет данных по заданным фильтрам.")
    st.stop()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Заказов", f"{len(orders):,}")
c2.metric("Уник. клиентов", f"{orders['customer_unique_id'].nunique():,}")
c3.metric("Выручка", f"R$ {orders['order_total'].sum():,.0f}")
c4.metric("Средний чек", f"R$ {orders['order_total'].mean():.2f}")
c5.metric("Средний отзыв", f"{orders['review_score'].mean():.2f} ⭐")

st.divider()

# ─────────────────────── KPI ПО МЕСЯЦАМ ───────────────────────
st.subheader("📈 Динамика по месяцам")
monthly = (
    orders.groupby("order_month", as_index=False)
    .agg(
        orders_cnt=("order_id", "count"),
        revenue=("order_total", "sum"),
        avg_check=("order_total", "mean"),
        avg_review=("review_score", "mean"),
    )
    .sort_values("order_month")
)

fig = px.line(
    monthly, x="order_month", y="revenue", markers=True,
    title="Выручка по месяцам", labels={"revenue": "R$", "order_month": ""},
)
st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    fig2 = px.bar(
        monthly, x="order_month", y="orders_cnt",
        title="Количество заказов", labels={"orders_cnt": "шт", "order_month": ""},
    )
    st.plotly_chart(fig2, use_container_width=True)
with col2:
    fig3 = px.line(
        monthly, x="order_month", y="avg_review",
        title="Средний рейтинг", markers=True,
        labels={"avg_review": "⭐", "order_month": ""},
    )
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ─────────────────────── RFM ───────────────────────
st.subheader("🎯 RFM-сегментация клиентов")
rfm = run_sql("rfm.sql")

col1, col2 = st.columns([2, 3])
with col1:
    st.dataframe(rfm, use_container_width=True, hide_index=True)
with col2:
    fig = px.bar(
        rfm, x="segment", y="total_revenue",
        color="segment", title="Выручка по сегментам",
        labels={"total_revenue": "R$", "segment": ""},
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ─────────────────────── COHORT ───────────────────────
st.subheader("👥 Cohort Analysis (retention по месяцам)")
cohort = run_sql("cohort.sql")
pivot = cohort.pivot_table(
    index="cohort_month", columns="month_offset",
    values="retention_pct", aggfunc="mean",
)

fig = px.imshow(
    pivot,
    aspect="auto",
    color_continuous_scale="Blues",
    labels=dict(x="Месяцев с первой покупки", y="Когорта", color="Retention %"),
    title="Retention % по когортам",
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ─────────────────────── RETENTION ───────────────────────
st.subheader("🔁 Retention по штатам")
ret = run_sql("retention.sql").head(15)
fig = px.bar(
    ret, x="customer_state", y="retention_pct",
    color="retention_pct", color_continuous_scale="Teal",
    title="Доля вернувшихся клиентов (%)",
    labels={"retention_pct": "%", "customer_state": ""},
)
st.plotly_chart(fig, use_container_width=True)

st.caption("Данные: Olist Brazilian E-Commerce | Стек: Python + SQLite + Streamlit")