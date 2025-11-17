# Streamlit 앱: 지하철 상위 10개 역 (Plotly 인터랙티브)

아래는 Streamlit Cloud에서 바로 동작하는 한 파일짜리 앱 코드(`streamlit_app.py`)와 `requirements.txt` 내용입니다. (위젯을 캐시된 함수 안에서 호출하는 문제를 해결한 버전입니다.)

---

## streamlit_app.py

```python
# streamlit_app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

st.set_page_config(page_title="지하철 Top10", layout="wide")
st.title("📊 지하철 승하차 합계 Top 10 (Plotly)")

# ---------------------------
# 캐시된 데이터 로드 함수들 (위젯 없음)
# ---------------------------
@st.cache_data
def load_data_from_path(path):
    # path는 파일 시스템 경로
    # 인코딩 시도: utf-8 -> cp949
    df = None
    try:
        df = pd.read_csv(path, encoding='utf-8')
    except Exception:
        df = pd.read_csv(path, encoding='cp949')
    return _postprocess(df)

@st.cache_data
def load_data_from_bytes(bytes_io):
    # 업로더에서 받은 바이너리(또는 io.BytesIO)
    try:
        df = pd.read_csv(bytes_io, encoding='utf-8')
    except Exception:
        bytes_io.seek(0)
        df = pd.read_csv(bytes_io, encoding='cp949')
    return _postprocess(df)

def _postprocess(df):
    # 컬럼 필수 확인
    required = ['사용일자', '노선명', '역명', '승차총승객수', '하차총승객수']
    for c in required:
        if c not in df.columns:
            raise ValueError(f"CSV에 필요한 컬럼이 없습니다: {c}")

    # 사용일자 -> datetime
    df['사용일자'] = df['사용일자'].astype(str)
    df['date'] = pd.to_datetime(df['사용일자'].str.slice(0,8), format='%Y%m%d', errors='coerce')

    # 숫자 컬럼 변환
    df['승차총승객수'] = pd.to_numeric(df['승차총승객수'], errors='coerce').fillna(0).astype(int)
    df['하차총승객수'] = pd.to_numeric(df['하차총승객수'], errors='coerce').fillna(0).astype(int)

    return df

# ---------------------------
# 파일 로드 (위젯은 캐시된 함수 바깥에서 사용)
# ---------------------------
# 우선 앱 내부 경로에서 자동 로드 시도
default_path = '/mnt/data/subway.csv'
loaded_df = None
if os.path.exists(default_path):
    try:
        loaded_df = load_data_from_path(default_path)
    except Exception as e:
        st.error(f"기본 경로에서 데이터 로드 실패: {e}")

# 파일 업로더 위젯은 캐시 함수 밖에 둠 (경고 해결)
uploaded = st.file_uploader("Upload CSV (subway.csv)", type=['csv'])
if uploaded is not None:
    try:
        loaded_df = load_data_from_bytes(uploaded)
    except Exception as e:
        st.error(f"업로드 파일 로드 실패: {e}")

if loaded_df is None:
    st.info("왼쪽에서 CSV를 업로드하거나 앱 환경에 '/mnt/data/subway.csv' 파일을 배치하세요.")
    st.stop()

df = loaded_df

# ---------------------------
# UI: 날짜(2025년 10월 중 하루)와 호선 선택
# ---------------------------
# 2025년 10월 날짜 목록 우선 제공
oct_mask = (df['date'].dt.year == 2025) & (df['date'].dt.month == 10)
if oct_mask.any():
    date_choices = df.loc[oct_mask, 'date'].dropna().sort_values().unique()
else:
    date_choices = df['date'].dropna().sort_values().unique()

if len(date_choices) == 0:
    st.error("데이터에 선택 가능한 날짜가 없습니다.")
    st.stop()

selected_date = st.selectbox("🗓 날짜 선택 (2025-10- 중 선택 가능)", options=date_choices, format_func=lambda d: d.strftime('%Y-%m-%d'))
lines = sorted(df['노선명'].dropna().unique().tolist())
selected_line = st.selectbox("🚇 호선 선택", options=['전체'] + lines)

# ---------------------------
# 필터링 및 집계
# ---------------------------
mask = df['date'] == pd.to_datetime(selected_date)
if selected_line != '전체':
    mask &= (df['노선명'] == selected_line)

filtered = df[mask].copy()
if filtered.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    st.stop()

agg = filtered.groupby('역명', as_index=False).agg({
    '승차총승객수': 'sum',
    '하차총승객수': 'sum'
})
agg['합계'] = agg['승차총승객수'] + agg['하차총승객수']
agg_sorted = agg.sort_values('합계', ascending=False).head(10).reset_index(drop=True)

# ---------------------------
# 색상: 1등 빨강, 나머지는 파란색 그라데이션(점점 연해짐)
# ---------------------------
def make_blue_gradient(n):
    if n <= 0:
        return []
    colors = ['#ff0000']
    if n == 1:
        return colors
    start = (0, 51, 204)   # 진한 파랑 #0033cc
    end = (204, 229, 255)  # 연한 파랑 #cce5ff
    for i in range(n-1):
        t = i / max(1, n-2)
        r = int(start[0] + (end[0] - start[0]) * t)
        g = int(start[1] + (end[1] - start[1]) * t)
        b = int(start[2] + (end[2] - start[2]) * t)
        colors.append(f"#{r:02x}{g:02x}{b:02x}")
    return colors

n = len(agg_sorted)
colors = make_blue_gradient(n)

# Plotly 막대그래프 (가독성을 위해 내림차순으로 표시)
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
    title=f"Top 10 역 - {pd.to_datetime(selected_date).strftime('%Y-%m-%d')} / {'전체' if selected_line=='전체' else selected_line}",
    xaxis_title='',
    yaxis_title='승차+하차 합계',
    margin=dict(l=40, r=40, t=80, b=120),
    height=600
)
fig.update_xaxes(tickangle=-45)

st.plotly_chart(fig, use_container_width=True)

with st.expander('🔎 결과 테이블 보기'):
    st.dataframe(agg_sorted)

st.markdown("---")
st.caption('데이터: 업로드한 subway.csv 기준. 컬럼명: 사용일자, 노선명, 역명, 승차총승객수, 하차총승객수')
```

---

## requirements.txt

```
streamlit==1.28.0
pandas>=1.5.0
plotly>=5.15.0
```

---

### 변경 요약

* `st.file_uploader` 같은 위젯을 **캐시된 함수 밖**으로 옮겨 `CachedWidgetWarning` 문제 해결.
* 데이터 읽기/전처리 함수는 `@st.cache_data`로 유지하되, 내부에 위젯 호출을 전혀 넣지 않았음.
* 그래프 색상은 요청하신 대로 1위는 빨강, 나머지는 파란색 그라데이션(연해짐)으로 설정.

앱 파일을 이 코드로 교체한 뒤 재배포하면 경고/오류는 사라질 거예요. 추가로 로그에서 다른 오류가 보이면 그 내용(민감정보 제외)을 붙여넣어 주세요.
