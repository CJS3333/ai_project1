# Streamlit 앱: 지하철 상위 10개 역 (Plotly 인터랙티브)

아래는 Streamlit Cloud에서 바로 동작하는 한 파일짜리 앱 코드(`streamlit_app.py`)와 `requirements.txt` 내용입니다.

---

## streamlit_app.py

```python
# streamlit_app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os

st.set_page_config(page_title="지하철 Top10 시각화", layout="wide")
st.title("📊 지하철 승하차 합계 Top 10 (Plotly)")

@st.cache_data
def load_data(path='/mnt/data/subway.csv'):
    # 파일 경로가 존재하면 로드, 아니면 업로더로 대체
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, encoding='utf-8')
        except Exception:
            df = pd.read_csv(path, encoding='cp949')
    else:
        uploaded = st.file_uploader("CSV 파일 업로드 (subway.csv 형식)", type=['csv'])
        if uploaded is None:
            return None
        try:
            df = pd.read_csv(uploaded, encoding='utf-8')
        except Exception:
            uploaded.seek(0)
            df = pd.read_csv(uploaded, encoding='cp949')
    # 컬럼 정리: 사용일자 -> datetime
    if '사용일자' in df.columns:
        df['사용일자'] = df['사용일자'].astype(str)
        # 일부 값이 YYYYMMDD 형태가 아닐 수 있으므로 안전하게 파싱
        df['date'] = pd.to_datetime(df['사용일자'].str.slice(0,8), format='%Y%m%d', errors='coerce')
    else:
        st.error("CSV에 '사용일자' 컬럼이 없습니다.")
        return None
    # 숫자 컬럼 보정
    for c in ['승차총승객수', '하차총승객수']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
        else:
            st.error(f"CSV에 '{c}' 컬럼이 없습니다.")
            return None
    return df


def make_blue_gradient(n):
    # 첫 색은 빨강, 나머지 n-1개는 파란색 계열 그라데이션
    def lerp(a, b, t):
        return int(a + (b - a) * t)
    # 파란색 시작과 끝(진한 파랑 -> 연한 파랑)
    start = (0, 51, 204)   # #0033cc
    end = (204, 229, 255)  # #cce5ff
    colors = ['#ff0000']
    if n <= 1:
        return colors
    for i in range(n-1):
        t = i / max(1, n-2)
        r = lerp(start[0], end[0], t)
        g = lerp(start[1], end[1], t)
        b = lerp(start[2], end[2], t)
        colors.append(f"#{r:02x}{g:02x}{b:02x}")
    return colors


# load
df = load_data()
if df is None:
    st.info("왼쪽에서 CSV 파일을 업로드하거나, 앱 환경에 '/mnt/data/subway.csv' 파일을 배치하세요.")
    st.stop()

# 사용자 입력: 2025년 10월 안의 날짜만 보여주기
oct2025 = df[(df['date'].dt.year == 2025) & (df['date'].dt.month == 10)]
if oct2025.empty:
    st.warning("데이터에 2025년 10월의 데이터가 없습니다. 전체 날짜에서 선택하세요.")
    available_dates = df['date'].dropna().sort_values().unique()
else:
    available_dates = oct2025['date'].dropna().sort_values().unique()

# 선택 UI
col1, col2 = st.columns([1,1])
with col1:
    selected_date = st.selectbox("🗓 날짜 선택", options=available_dates, format_func=lambda d: d.strftime('%Y-%m-%d'))
with col2:
    lines = df['노선명'].dropna().unique().tolist()
    lines_sorted = sorted(lines)
    selected_line = st.selectbox("🚇 호선 선택", options=['전체'] + lines_sorted)

# 필터링 및 계산
mask = (df['date'] == pd.to_datetime(selected_date))
if selected_line != '전체':
    mask &= (df['노선명'] == selected_line)

filtered = df[mask].copy()
if filtered.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    st.stop()

# 역별 승차+하차 합계 계산
agg = filtered.groupby('역명', as_index=False).agg({
    '승차총승객수': 'sum',
    '하차총승객수': 'sum'
})
agg['합계'] = agg['승차총승객수'] + agg['하차총승객수']
agg_sorted = agg.sort_values('합계', ascending=False).head(10)

# 색 설정
n = len(agg_sorted)
colors = make_blue_gradient(n)

# Plotly 막대그래프
fig = go.Figure()
fig.add_trace(go.Bar(
    x=agg_sorted['역명'][::-1],
    y=agg_sorted['합계'][::-1],
    marker_color=colors[::-1],
    text=agg_sorted['합계'][::-1],
    textposition='auto',
    hovertemplate='<b>%{x}</b><br>합계: %{y}<extra></extra>'
))
fig.update_layout(
    title=f"Top 10 역 - {selected_date.strftime('%Y-%m-%d')} / {'전체' if selected_line=='전체' else selected_line}",
    xaxis_title='',
    yaxis_title='승차+하차 합계',
    margin=dict(l=40, r=40, t=80, b=120),
    height=600
)

# 역명을 가독성 있게 세로로 보여주기
fig.update_xaxes(tickangle= -45)

st.plotly_chart(fig, use_container_width=True)

# 상세 테이블
with st.expander('🔎 결과 테이블 보기'):
    st.dataframe(agg_sorted.reset_index(drop=True))

st.markdown("---")
st.caption('데이터: 업로드한 subway.csv 기준. 앱은 업로드된 파일의 컬럼명이 `사용일자`, `노선명`, `역명`, `승차총승객수`, `하차총승객수` 이어야 정상 동작합니다.')
```

---

## requirements.txt

```
streamlit==1.28.0
pandas>=1.5.0
plotly>=5.15.0
```

---

### 사용법 요약

1. Streamlit Cloud(또는 로컬)에 `streamlit_app.py` 파일을 업로드하세요.
2. `requirements.txt` 도 함께 업로드하여 플러그인 설치를 보장하세요.
3. 앱 실행 후, CSV 파일을 업로드하거나 `/mnt/data/subway.csv` 경로에 파일을 배치하면 됩니다.

필요하면 코드에 기능(예: 날짜 범위 슬라이더, 노선별 색상 커스터마이즈 등)을 추가해줄게!
