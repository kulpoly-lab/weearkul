"""
Portfolio Dashboard – Investment Trend Analysis
Deployed on Railway · Data: Yahoo Finance (real-time)
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Portfolio Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #F0F4F8; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1rem; }
.kpi-card {
    background: #0D2137;
    border-radius: 12px;
    padding: 18px 20px;
    text-align: center;
    border-top: 3px solid #C9A84C;
}
.kpi-val { font-size: 1.7rem; font-weight: 700; }
.kpi-lbl { font-size: 0.78rem; color: #8A9BB0; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Config ────────────────────────────────────────────────────────────────────
TICKERS = {
    "SITHAI": "SITHAI.BK",
    "LH":     "LH.BK",
    "LHK":    "LHK.BK",
    "PT":     "PT.BK",
    "QH":     "QH.BK",
    "TISCO":  "TISCO.BK",
}
NAMES = {
    "SITHAI": "Srithai Superware",
    "LH":     "Land & Houses",
    "LHK":    "Lohakit Metal",
    "PT":     "Premier Technology",
    "QH":     "Quality Houses",
    "TISCO":  "TISCO Financial",
}
COLORS = ["#3498DB","#E74C3C","#2ECC71","#9B59B6","#F39C12","#1ABC9C","#C9A84C"]
STOCKS = list(TICKERS.keys())

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")
    period = st.selectbox("Period", ["1y","6mo","3mo","ytd"], index=0,
                          format_func=lambda x: {"1y":"1 Year","6mo":"6 Months","3mo":"3 Months","ytd":"Year-to-Date"}[x])
    selected = st.multiselect("Stocks", STOCKS, default=STOCKS)
    st.caption("Data refreshes every hour")

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_data(period: str):
    tickers_list = list(TICKERS.values()) + ["^SET.BK"]
    raw = yf.download(tickers_list, period=period, auto_adjust=True, progress=False)["Close"]
    raw = raw.ffill().dropna(how="all")
    col_map = {v: k for k, v in TICKERS.items()}
    col_map["^SET.BK"] = "SET"
    raw.columns = [col_map.get(c, c) for c in raw.columns]
    return raw

with st.spinner("กำลังดึงข้อมูลตลาด…"):
    data = load_data(period)

active = [s for s in selected if s in data.columns]

# ── Calculations ──────────────────────────────────────────────────────────────
def one_y(s): return (s.iloc[-1] / s.iloc[0] - 1) * 100
def ytd(s):
    d = s[s.index.year >= datetime.today().year]
    return (d.iloc[-1] / d.iloc[0] - 1) * 100 if len(d) >= 2 else 0.0
def cum(s): return (s / s.iloc[0] - 1) * 100

set_1y  = one_y(data["SET"]) if "SET" in data.columns else 0
set_ytd = ytd(data["SET"])   if "SET" in data.columns else 0

metrics = {k: {"last": data[k].iloc[-1], "one_y": one_y(data[k]), "ytd": ytd(data[k])}
           for k in active}
ranked  = sorted(metrics.items(), key=lambda x: x[1]["one_y"], reverse=True)
avg     = sum(m["one_y"] for _, m in metrics.items()) / len(metrics) if metrics else 0

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 📊 Portfolio Dashboard · Investment Trend Analysis")
st.caption(f"Last updated: {datetime.now().strftime('%d %B %Y %H:%M')} · Source: Yahoo Finance")
st.divider()

# ── KPIs ──────────────────────────────────────────────────────────────────────
cols = st.columns(5)
def kpi(col, label, val, color):
    col.markdown(f"""<div class="kpi-card">
        <div class="kpi-val" style="color:{color}">{val}</div>
        <div class="kpi-lbl">{label}</div></div>""", unsafe_allow_html=True)

kpi(cols[0], "Holdings",        str(len(active)),                                "#C9A84C")
kpi(cols[1], "SET Index",       f"{set_1y:+.2f}%",  "#2ECC71" if set_1y>=0 else "#E74C3C")
kpi(cols[2], f"Best · {ranked[0][0]}",   f"{ranked[0][1]['one_y']:+.2f}%",       "#2ECC71")
kpi(cols[3], f"Worst · {ranked[-1][0]}", f"{ranked[-1][1]['one_y']:+.2f}%",      "#E74C3C")
kpi(cols[4], "Portfolio vs SET",f"{avg-set_1y:+.2f}%","#2ECC71" if avg>=set_1y else "#E74C3C")

st.markdown("<br>", unsafe_allow_html=True)

# ── Cumulative Return Line Chart ──────────────────────────────────────────────
st.subheader("📈 Cumulative Return vs SET Index")
fig = go.Figure()
for i, k in enumerate(active + (["SET"] if "SET" in data.columns else [])):
    label = "SET Index" if k == "SET" else k
    fig.add_trace(go.Scatter(
        x=data.index, y=cum(data[k]),
        name=label,
        line=dict(color=COLORS[i % len(COLORS)], width=3 if k == "SET" else 2),
        hovertemplate=f"<b>{label}</b><br>%{{x|%d %b %Y}}<br>Return: %{{y:.2f}}%<extra></extra>",
    ))
fig.add_hline(y=0, line_dash="dot", line_color="#8A9BB0", line_width=1)
fig.update_layout(
    paper_bgcolor="white", plot_bgcolor="#F7F9FC", height=400,
    legend=dict(orientation="h", yanchor="bottom", y=-0.3, font_size=12),
    yaxis=dict(ticksuffix="%", gridcolor="#E8EDF3", zeroline=False),
    xaxis=dict(gridcolor="rgba(0,0,0,0)"),
    margin=dict(l=0, r=0, t=10, b=0),
    hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True)

# ── Allocation Pie + Bar Chart ────────────────────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("🥧 Portfolio Allocation")
    fig_pie = px.pie(
        names=active, values=[100/len(active)]*len(active),
        color_discrete_sequence=COLORS[:len(active)], hole=0.38,
    )
    fig_pie.update_traces(textinfo="label+percent", textfont_size=13)
    fig_pie.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=320)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_r:
    st.subheader("🏆 1-Year Return Rankings")
    bar_colors = ["#2ECC71" if r[1]["one_y"] >= 0 else "#E74C3C" for r in ranked]
    fig_bar = go.Figure(go.Bar(
        x=[r[0] for r in ranked],
        y=[r[1]["one_y"] for r in ranked],
        marker_color=bar_colors,
        text=[f"{r[1]['one_y']:+.2f}%" for r in ranked],
        textposition="outside",
    ))
    fig_bar.add_hline(y=0, line_dash="dot", line_color="#8A9BB0")
    fig_bar.update_layout(
        paper_bgcolor="white", plot_bgcolor="#F7F9FC", height=320,
        yaxis=dict(ticksuffix="%", gridcolor="#E8EDF3"),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=0, t=10, b=0), showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Performance Table ─────────────────────────────────────────────────────────
st.subheader("📋 Individual Stock Performance")

rows = [{"Ticker": k, "Company": NAMES.get(k,""), "Last Price (THB)": round(metrics[k]["last"], 2),
         "1Y Return": metrics[k]["one_y"]/100, "YTD Return": metrics[k]["ytd"]/100,
         "vs SET (1Y)": (metrics[k]["one_y"]-set_1y)/100}
        for k in active]
if "SET" in data.columns:
    rows.append({"Ticker":"SET","Company":"SET Index (Benchmark)",
                 "Last Price (THB)":round(data["SET"].iloc[-1],2),
                 "1Y Return":set_1y/100,"YTD Return":set_ytd/100,"vs SET (1Y)":None})

df = pd.DataFrame(rows)

def color_val(v):
    if v is None: return ""
    return f"color: {'#2ECC71' if v >= 0 else '#E74C3C'}; font-weight: 600"

styled = (df.style
    .format({"Last Price (THB)":"{:.2f}","1Y Return":"{:+.2f%}","YTD Return":"{:+.2f%}","vs SET (1Y)":lambda v:"—" if v is None else f"{v:+.2f%}"})
    .applymap(color_val, subset=["1Y Return","YTD Return","vs SET (1Y)"])
)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.caption("All returns in THB · Prices auto-adjusted for splits & dividends · Data: Yahoo Finance")
