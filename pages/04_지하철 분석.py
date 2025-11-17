# streamlit_app.py
# ASCII-only safe version to avoid encoding/syntax issues
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

st.set_page_config(page_title="Subway Top10 Safe", layout="wide")
st.title("Subway: Top 10 Stations (safe mode)")

@st.cache_data
def load_csv_from_path(path):
    # try utf-8 then cp949
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except Exception:
        df = pd.read_csv(path, encoding="cp949")
    return postprocess(df)

@st.cache_data
def load_csv_from_fileobj(fileobj):
    # fileobj: uploaded file-like
    try:
        df = pd.read_csv(fileobj, encoding="utf-8")
    except Exception:
        fileobj.seek(0)
        df = pd.read_csv(fileobj, encoding="cp949")
    return postprocess(df)

def postprocess(df):
    required = ["사용일자", "노선명", "역명", "승차총승객수", "하차총승객수"]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"Missing column: {c}")

    df["사용일자"] = df["사용일자"].astype(str)
    df["date"] = pd.to_datetime(df["사용일자"].str.slice(0,8),
                                format="%Y%m%d", errors="coerce")
    df["승차총승객수"] = pd.to_numeric(df["승차총승객수"], errors="coerce").fillna(0).astype(int)
    df["하차총승객수"] = pd.to_numeric(df["하차총승객수"], errors="coerce").fillna(0).astype(int)
    return df

# load default path first
default_path = "/mnt/data/subway.csv"
df = None
if os.path.exists(default_path):
    try:
        df = load_csv_from_path(default_path)
    except Exception as e:
        st.error("Failed to load default csv: " + str(e))

# file uploader (widget is outside cached functions)
uploaded = st.file_uploader("Upload subway.csv", type=["csv"])
if uploaded is not None:
    try:
        df = load_csv_from_fileobj(uploaded)
    except Exception as e:
        st.error("Failed to load uploaded file: " + str(e))

if df is None:
    st.info("Place subway.csv at /mnt/data/ or upload via the uploader.")
    st.stop()

# restrict to Oct 2025 if exists
oct_mask = (df["date"].dt.year == 2025) & (df["date"].dt.month == 10)
if oct_mask.any():
    dates = df.loc[oct_mask, "date"].dropna().sort_values().unique()
else:
    dates = df["date"].dropna().sort_values().unique()

if len(dates) == 0:
    st.error("No valid dates found in data.")
    st.stop()

selected_date = st.selectbox("Select date (prefer Oct 2025)", options=dates,
                             format_func=lambda d: d.strftime("%Y-%m-%d"))
lines = sorted(df["노선명"].dropna().unique().tolist())
selected_line = st.selectbox("Select line", options=["All"] + lines)

mask = df["date"] == pd.to_datetime(selected_date)
if selected_line != "All":
    mask = mask & (df["노선명"] == selected_line)

filtered = df.loc[mask].copy()
if filtered.empty:
    st.warning("No data for the selected filters.")
    st.stop()

agg = filtered.groupby("역명", as_index=False).agg({"승차총승객수": "sum", "하차총승객수": "sum"})
agg["합계"] = agg["승차총승객수"] + agg["하차총승객수"]
top10 = agg.sort_values("합계", ascending=False).head(10).reset_index(drop=True)

def make_colors(n):
    if n <= 0:
        return []
    colors = ["#ff0000"]
    if n == 1:
        return colors
    start = (0, 51, 204)
    end = (204, 229, 255)
    for i in range(n-1):
        t = i / max(1, n-2)
        r = int(start[0] + (end[0] - start[0]) * t)
        g = int(start[1] + (end[1] - start[1]) * t)
        b = int(start[2] + (end[2] - start[2]) * t)
        colors.append(f"#{r:02x}{g:02x}{b:02x}")
    return colors

n = len(top10)
colors = make_colors(n)

fig = go.Figure()
fig.add_trace(go.Bar(
    x=top10["역명"][::-1],
    y=top10["합계"][::-1],
    marker_color=colors[::-1],
    text=top10["합계"][::-1],
    textposition="auto",
))
fig.update_layout(title=f"Top10 on {selected_date.strftime('%Y-%m-%d')} / {selected_line}",
                  xaxis_tickangle=-45, yaxis_title="Sum", height=600)
st.plotly_chart(fig, use_container_width=True)

with st.expander("Table"):
    st.dataframe(top10)
