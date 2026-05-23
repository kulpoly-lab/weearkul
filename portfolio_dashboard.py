"""
Portfolio Dashboard – Investment Trend Analysis
Run with:  pip install streamlit plotly yfinance pandas  &&  streamlit run portfolio_dashboard.py
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Portfolio Dashboard", page_icon="📈", layout="wide")

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card{background:#0D2137;border-radius:10px;padding:16px 20px;text-align:center;margin-bottom:8px}
.metric-val{font-size:1.6rem;font-weight:700;color:#C9A84C}
.metric-lbl{font-size:.8rem;color:#8A9BB0;margin-top:2px}
h1{color:#0D2137!important}
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
FULL_NAMES = {
    "SITHAI": "Srithai Superware",
    "LH":     "Land & Houses",
    "LHK":    "Lohakit Metal",
    "PT":     "Premier Technology",
    "QH":     "Quality Houses",
    "TISCO":  "TISCO Financial",
}
COLORS = ["#3498DB","#E74C3C","#2ECC71","#9B59B6","#F39C12","#1ABC9C","#C9A84C"]

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data():
    end   = datetime.today()
    start = end - timedelta(days=365)
    all_tickers = list(TICKERS.values()) + ["^SET.BK"]
    raw = yf.download(all_tickers, start=start, end=end, auto_adjust=True, progress=False)["Close"]
    raw = raw.ffill().dropna(how="all")
    return raw

# ── Main ──────────────────────────────────────────────────────────────────────
st.title("Portfolio Dashboard · Investment Trend Analysis")
st.caption(f"Data as of {datetime.today().strftime('%d %B %Y')} · Source: Yahoo Finance")

with st.spinner("Fetching market data…"):
    data = load_data()

# Map to friendly names
col_map = {v: k for k, v in TICKERS.items()}
col_map["^SET.BK"] = "SET"
data.columns = [col_map.get(c, c) for c in data.columns]

stocks = list(TICKERS.keys())

# ── Calculate returns ─────────────────────────────────────────────────────────
def cum_ret(series):
    return (series / series.iloc[0] - 1) * 100

def one_y_ret(series):
    return (series.iloc[-1] / series.iloc[0] - 1) * 100

def ytd_ret(series):
    ytd_data = series[series.index.year >= datetime.today().year]
    if len(ytd_data) < 2:
        return 0.0
    return (ytd_data.iloc[-1] / ytd_data.iloc[0] - 1) * 100

set_1y  = one_y_ret(data["SET"]) if "SET" in data.columns else 0
set_ytd = ytd_ret(data["SET"])   if "SET" in data.columns else 0

metrics = {}
for k in stocks:
    if k in data.columns:
        metrics[k] = {
            "last":  data[k].iloc[-1],
            "one_y": one_y_ret(data[k]),
            "ytd":   ytd_ret(data[k]),
        }

ranked = sorted(metrics.items(), key=lambda x: x[1]["one_y"], reverse=True)
avg_port = sum(m["one_y"] for _,m in metrics.items()) / len(metrics) if metrics else 0

# ── KPI Row ───────────────────────────────────────────────────────────────────
c1,c2,c3,c4,c5 = st.columns(5)
def metric(col, label, value, color="#C9A84C"):
    col.markdown(f"""<div class="metric-card">
        <div class="metric-val" style="color:{color}">{value}</div>
        <div class="metric-lbl">{label}</div></div>""", unsafe_allow_html=True)

metric(c1, "Holdings", "6")
metric(c2, "SET Index 1Y", f"{set_1y:+.2f}%", "#2ECC71" if set_1y>=0 else "#E74C3C")
metric(c3, f"Best: {ranked[0][0]}", f"{ranked[0][1]['one_y']:+.2f}%", "#2ECC71")
metric(c4, f"Worst: {ranked[-1][0]}", f"{ranked[-1][1]['one_y']:+.2f}%", "#E74C3C")
metric(c5, "Portfolio vs SET", f"{avg_port-set_1y:+.2f}%", "#2ECC71" if (avg_port-set_1y)>=0 else "#E74C3C")

st.divider()

# ── Cumulative Return Chart ───────────────────────────────────────────────────
st.subheader("Cumulative Return vs SET Index (1 Year)")
fig_line = go.Figure()
for i, k in enumerate(stocks + ["SET"]):
    if k in data.columns:
        label = "SET Index" if k == "SET" else k
        fig_line.add_trace(go.Scatter(
            x=data.index, y=cum_ret(data[k]),
            name=label, line=dict(color=COLORS[i], width=3 if k=="SET" else 2),
            hovertemplate=f"{label}: %{{y:.2f}}%<extra></extra>"
        ))
fig_line.add_hline(y=0, line_dash="dash", line_color="#8A9BB0", line_width=1)
fig_line.update_layout(
    paper_bgcolor="#FFFFFF", plot_bgcolor="#F7F9FC",
    legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    yaxis=dict(ticksuffix="%", gridcolor="#E8EDF3"),
    xaxis=dict(gridcolor="rgba(0,0,0,0)"),
    margin=dict(l=0,r=0,t=10,b=0), height=380,
)
st.plotly_chart(fig_line, use_container_width=True)

# ── Allocation + Bar ──────────────────────────────────────────────────────────
col_pie, col_bar = st.columns(2)

with col_pie:
    st.subheader("Portfolio Allocation (Equal Weight)")
    fig_pie = px.pie(names=stocks, values=[100/6]*6, color_discrete_sequence=COLORS[:6], hole=0.35)
    fig_pie.update_traces(textinfo="label+percent", textfont_size=13)
    fig_pie.update_layout(showlegend=False, margin=dict(l=0,r=0,t=10,b=0), height=300)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_bar:
    st.subheader("1-Year Return Rankings")
    rk_keys = [r[0] for r in ranked]
    rk_vals = [r[1]["one_y"] for r in ranked]
    bar_colors = ["#2ECC71" if v>=0 else "#E74C3C" for v in rk_vals]
    fig_bar = go.Figure(go.Bar(x=rk_keys, y=rk_vals, marker_color=bar_colors, text=[f"{v:+.2f}%" for v in rk_vals], textposition="outside"))
    fig_bar.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#F7F9FC",
        yaxis=dict(ticksuffix="%", gridcolor="#E8EDF3"),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        margin=dict(l=0,r=0,t=10,b=0), height=300, showlegend=False)
    fig_bar.add_hline(y=0, line_dash="dash", line_color="#8A9BB0")
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Performance Table ─────────────────────────────────────────────────────────
st.subheader("Individual Stock Performance")
rows = []
for k in stocks:
    if k in metrics:
        m = metrics[k]
        rows.append({
            "Ticker": k, "Company": FULL_NAMES[k],
            "Last Price (THB)": round(m["last"], 2),
            "1Y Return": f"{m['one_y']:+.2f}%",
            "YTD Return": f"{m['ytd']:+.2f}%",
            "vs SET (1Y)": f"{m['one_y']-set_1y:+.2f}%",
        })
if "SET" in data.columns:
    rows.append({"Ticker":"SET","Company":"SET Index (Benchmark)",
        "Last Price (THB)":round(data["SET"].iloc[-1],2),
        "1Y Return":f"{set_1y:+.2f}%","YTD Return":f"{set_ytd:+.2f}%","vs SET (1Y)":"—"})

df = pd.DataFrame(rows)

def highlight_row(row):
    if row["Ticker"] == "SET":
        return ["background-color:#0D2137;color:#C9A84C;font-weight:bold"]*len(row)
    return [""]*len(row)

def color_ret(val):
    if isinstance(val, str) and val not in ("—",""):
        try:
            n = float(val.replace("+","").replace("%",""))
            return f"color:{'#2ECC71' if n>=0 else '#E74C3C'};font-weight:600"
        except: pass
    return ""

styled = df.style.apply(highlight_row, axis=1)\
    .applymap(color_ret, subset=["1Y Return","YTD Return","vs SET (1Y)"])\
    .set_properties(**{"text-align":"center"})\
    .set_properties(subset=["Ticker","Company"], **{"text-align":"left"})

st.dataframe(styled, use_container_width=True, hide_index=True)
st.caption(f"All returns in THB · Data sourced from Yahoo Finance · {datetime.today().strftime('%d %B %Y')}")
