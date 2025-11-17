# streamlit_app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

st.set_page_config(page_title="Subway Top10", layout="wide")
st.title("지하철 승하차 합계 Top 10")

@st.cache_data
def load_data(path='/mnt/data/subway.csv'):
    if os.path.exists(path):
        # try utf-8 first, then cp949
        try:
            df = pd.read_csv(path, encoding='utf-8')
        except Exception:
            df = pd.read_csv(path, encoding='cp949')
    else:
        uploaded = st.file_uploader("Upload CSV (subway.csv)", type=['csv'])
        if uploaded is None:
            return None
        try:
            df = pd.read_csv(uploaded, encoding='utf-8')
        except Exception:
            uploaded.seek(0)
            df = pd.read_csv(uploaded, encoding='cp949')

    # required columns check
    required = ['사용일자', '노선명', '역명', '승차총승객수', '하차총승객수']
    for c in required:
        if c not in df.columns:
            raise ValueError(f"CSV missing required column: {c}")

    # parse date
    df['사용일자'] = df['사용일자'].astype(str)
    df['date'] = pd.to_datetime(df['사용일자'].str.slice(0,8), format='%Y%m%d', errors='coerce')

    # numeric conversion
    df['승차총승객수'] = pd.to_numeric(df['승차총승객수'], errors='coerce').fillna(0).astype(int)
    df['하차총승객수'] = pd.to_numeric(df['하차총승객수'], errors='coerce').fillna(0).astype(int)

    return df

def make_blue_gradient(n):
    # first red, rest blue gradient
    if n <= 0:
        return []
    colors = ['#ff0000']
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

# load data
try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 로드 중 오류: {e}")
    st.stop()

if df is None:
    st.info("CSV 파일을 업로드하거나 /mnt/data/subway.csv 경로에 파일을 두세요.")
    st.stop()

# limit dates to Oct 2025 if present, otherwise all dates
oct_mask = (df['date'].dt.year == 2025) & (df['date'].dt.month == 10)
if oct_mask.any():
    date_choices = df.loc[oct_mask, 'date'].dropna().sort_values().unique()
else:
    date_choices = df['date'].dropna().sort_values().unique()

if len(date_choices) == 0:
    st.error("처리 가능한 날짜가 데이터에 없습니다.")
    st.stop()

selected_date = st.selectbox("날짜 선택", options=date_choices, format_func=lambda d: d.strftime('%Y-%m-%d'))
lines = sorted(df['노선명'].dropna().unique().tolist())
selected_line = st.selectbox("호선 선택", options=['전체'] + lines)

mask = df['date'] == pd.to_datetime(selected_date)
if selected_line != '전체':
    mask = mask & (df['노선명'] == selected_line)

filtered = df.loc[mask].copy()
if filtered.empty:
    st.warning("선택 조건에 해당하는 데이터가 없습니다.")
    st.stop()

agg = filtered.groupby('역명', as_index=False).agg({'승차총승객수': 'sum', '하차총승객수': 'sum'})
agg['합계'] = agg['승차총승객수'] + agg['하차총승객수']
top10 = agg.sort_values('합계', ascending=False).head(10).reset_index(drop=True)

n = len(top10)
colors = make_blue_gradient(n)
# reverse for plotting so largest at top if horizontal, but we'll use vertical with rotated ticks
fig = go.Figure()
fig.add_trace(go.Bar(
    x=top10['역명'],
    y=top10['합계'],
    marker_color=colors
))
fig.update_layout(
    title=f"Top 10 역 - {selected_date.strftime('%Y-%m-%d')} / {selected_line}",
    xaxis_tickangle=-45,
    yaxis_title="승차+하차 합계",
    height=600,
    margin=dict(l=40, r=40, t=80, b=150)
)

st.plotly_chart(fig, use_container_width=True)

with st.expander("결과 테이블"):
    st.dataframe(top10)
