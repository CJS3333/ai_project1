import streamlit as st
import pandas as pd
from pathlib import Path

# -----------------------------------------------
# Plotly import (safe)
# -----------------------------------------------
try:
    import plotly.graph_objects as go
except Exception:
    st.set_page_config(page_title="MBTI by Country", layout="wide")
    st.title("🌍 MBTI Distribution by Country — Interactive Chart")
    st.error(
        "필수 패키지 'plotly'가 설치되어 있지 않습니다.\n"
        "프로젝트 루트에 requirements.txt 파일을 아래 내용으로 추가하세요:\n\n"
        "streamlit==1.28.0\n"
        "pandas>=1.5.0\n"
        "plotly>=5.15.0\n\n"
        "추가 후 Streamlit Cloud에서 'Manage app → Redeploy' 를 눌러주세요."
    )
    st.stop()

# -----------------------------------------------
# App Title
# -----------------------------------------------
st.set_page_config(page_title="MBTI Country Analysis", layout="wide")
st.title("🌍 국가별 MBTI 분포 대시보드")
st.write("인터랙티브 Plotly 그래프 + Streamlit UI")

# -----------------------------------------------
# Load CSV
# -----------------------------------------------
DATA_PATH = "countriesMBTI_16types.csv"

if not Path(DATA_PATH).exists():
    st.error(f"CSV 파일을 찾을 수 없습니다: {DATA_PATH}")
    st.stop()

try:
    df = pd.read_csv(DATA_PATH)
except Exception as e:
    st.error("CSV 로드 중 오류 발생: " + str(e))
    st.stop()

# -----------------------------------------------
# Validate MBTI columns
# -----------------------------------------------
MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP",
]

# 존재하는 MBTI 열만 필터
mbti_cols = [c for c in MBTI_TYPES if c in df.columns]

if not mbti_cols:
    st.error("데이터에 MBTI 타입 컬럼이 없습니다.")
    st.stop()

# -----------------------------------------------
# Sidebar – 국가 선택
# -----------------------------------------------
country_list = df["country"].dropna().unique().tolist()
selected_country = st.sidebar.selectbox("국가 선택", country_list)

# 선택된 국가 데이터만 추출
row = df[df["country"] == selected_country].iloc[0]

# MBTI 비율 dict
values = {t: row[t] for t in mbti_cols}

# -----------------------------------------------
# Normalize & Sort
# -----------------------------------------------
# 값이 모두 0이면 경고
if sum(values.values()) == 0:
    st.warning(f"{selected_country}의 MBTI 데이터가 모두 0입니다.")
    st.stop()

# 내림차순 정렬
sorted_items = sorted(values.items(), key=lambda x: x[1], reverse=True)
labels = [x[0] for x in sorted_items]
vals = [x[1] for x in sorted_items]

# -----------------------------------------------
# Color scheme: 1등 빨강, 2등부터 파랑 → 밝은 파랑 그라데이션
# -----------------------------------------------
colors = []
for i, _ in enumerate(vals):
    if i == 0:
        # 1등 빨간색
        colors.append("rgb(255, 80, 80)")
    else:
        # 나머지는 파랑 → 밝은 파랑
        # index가 커질수록 150 → 220 정도로 밝아짐
        blue_strength = min(220, 150 + i * 5)
        colors.append(f"rgb(80, 80, {blue_strength})")

# -----------------------------------------------
# Plotly Bar Chart
# -----------------------------------------------
fig = go.Figure(
    data=[
        go.Bar(
            x=labels,
            y=vals,
            marker_color=colors,
            text=[f"{v}%" for v in vals],
            textposition="outside",
        )
    ]
)

fig.update_layout(
    title=f"{selected_country} — MBTI 분포",
    xaxis_title="MBTI 타입",
    yaxis_title="비율 (%)",
    height=650,
    margin=dict(l=40, r=40, t=80, b=80),
)

# -----------------------------------------------
# Display
# -----------------------------------------------
st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------
# Data Table 보기 옵션
# -----------------------------------------------
with st.expander("📄 원본 데이터 보기"):
    st.dataframe(df)
