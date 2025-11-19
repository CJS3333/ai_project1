import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.title("💉 서울시 코로나19 백신 접종 데이터 시각화")

st.write("CSV 파일을 업로드해주세요.")

uploaded = st.file_uploader("CSV 업로드", type=["csv"])

# -----------------------------
# CSV LOAD
# -----------------------------
@st.cache_data
def load_csv(file):
    try:
        return pd.read_csv(file, encoding="utf-8")
    except:
        return pd.read_csv(file, encoding="cp949")

if uploaded:
    df = load_csv(uploaded)

    st.success("파일 불러오기 성공! 👌")
    st.dataframe(df.head())

    # 날짜 처리
    if "접종일" in df.columns:
        df["접종일"] = pd.to_datetime(df["접종일"], errors="coerce")

    # -----------------------------
    # 비율 컬럼만 추출
    # -----------------------------
    rate_cols = ["1차접종률(%)", "2차접종률(%)", "3차접종률(%)"]

    df_rates = df[rate_cols].mean().sort_values(ascending=False)
    df_rates = df_rates.reset_index()
    df_rates.columns = ["접종차수", "접종률"]

    # -----------------------------
    # 색상 설정 (1등=빨강, 나머지=파랑 그라데이션)
    # -----------------------------
    colors = []
    for i in range(len(df_rates)):
        if i == 0:
            colors.append("red")
        else:
            blue_value = int(200 + (i * 20))   # 파랑 → 밝은 파랑 그라데이션
            blue_value = min(255, blue_value)
            colors.append(f"rgb(0,0,{blue_value})")

    # -----------------------------
    # Plotly 막대그래프
    # -----------------------------
    fig = px.bar(
        df_rates,
        x="접종차수",
        y="접종률",
        text="접종률",
    )

    fig.update_traces(marker_color=colors, texttemplate="%{text:.2f}%")
    fig.update_layout(
        title="💉 접종률 비교 (1등=빨강 / 나머지=파랑 그라데이션)",
        xaxis_title="접종 차수",
        yaxis_title="접종률 (%)",
        template="plotly_white",
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("CSV를 업로드하면 그래프가 표시됩니다.")

