# app.py — Streamlit 앱 (파일 경로 유무에 따라 유연하게 처리)
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Seoul COVID-19 Vaccination Status")
st.title("Seoul Metropolitan City — COVID-19 Vaccination Status")
st.markdown("앱에서 레포/서버 경로에 CSV가 없으면 아래 업로드 위젯을 사용하세요.")

PREFERRED_PATHS = [
    "/mnt/data/Seoul Metropolitan City_COVID-19 Vaccination Status.csv",
    "./Seoul Metropolitan City_COVID-19 Vaccination Status.csv",
    "./data/Seoul Metropolitan City_COVID-19 Vaccination Status.csv",
    "./seoul_vaccination_status.csv",
    "./data/seoul_vaccination_status.csv"
]

@st.cache_data
def try_read_csv_from_paths(paths):
    for p in paths:
        try:
            # 시도 인코딩 목록
            for enc in ["utf-8", "cp949", "euc-kr", "latin1"]:
                try:
                    df = pd.read_csv(p, encoding=enc)
                    return df, p, enc
                except Exception:
                    continue
        except FileNotFoundError:
            continue
    return None, None, None

df, used_path, used_enc = try_read_csv_from_paths(PREFERRED_PATHS)

if df is None:
    st.warning("앱에서 지정한 경로에서 CSV를 찾지 못했습니다. 아래 업로더로 파일을 올려주세요.")
    uploaded = st.file_uploader("CSV 파일 업로드", type=["csv"])
    if uploaded is not None:
        # pandas는 uploaded 파일 객체를 직접 읽을 수 있습니다.
        # 인코딩 실패 가능성을 대비해 순차 시도
        success = False
        try:
            df = pd.read_csv(uploaded)
            used_enc = "pandas-detect"
            used_path = "uploaded_file"
            success = True
        except Exception:
            try:
                uploaded.seek(0)
                df = pd.read_csv(uploaded, encoding="cp949")
                used_enc = "cp949"
                used_path = "uploaded_file"
                success = True
            except Exception as e:
                st.error(f"업로드한 파일을 읽는 데 실패했습니다: {e}")
        if not success:
            st.stop()
    else:
        st.info("CSV 파일이 필요합니다. 레포에 파일을 추가하거나 여기 업로드하세요.")
        st.stop()

st.success(f"데이터 로드 성공 — 소스: {used_path} (encoding={used_enc})")
st.subheader("데이터 샘플 (상위 10행)")
st.dataframe(df.head(10))

st.subheader("컬럼 정보")
st.write(df.dtypes.to_frame('dtype'))

# '차수' 관련 컬럼 자동탐지
dose_cols = [c for c in df.columns if any(x in c for x in ['1차','2차','3차','차수','접종','당일'])]
dose_cols += [c for c in df.columns if any(x in c.lower() for x in ['1st','2nd','3rd','dose']) and c not in dose_cols]
dose_cols = list(dict.fromkeys(dose_cols))

dose_totals = {}
if dose_cols:
    for c in dose_cols:
        s = pd.to_numeric(df[c], errors='coerce').fillna(0)
        dose_totals[c] = float(s.sum())
else:
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    for c in numeric_cols[:3]:
        dose_totals[c] = float(df[c].sum())

dose_df = pd.DataFrame.from_dict(dose_totals, orient='index', columns=['total']).reset_index().rename(columns={'index':'dose'})
total_sum = dose_df['total'].sum() if dose_df['total'].sum() else 1
dose_df['proportion'] = dose_df['total'] / total_sum
dose_df = dose_df.sort_values('total', ascending=False).reset_index(drop=True)

# 색상: 1등 빨강, 나머지 파랑 그라데이션
colors = []
if not dose_df.empty:
    max_total = dose_df['total'].max()
    for val in dose_df['total']:
        if val == max_total:
            colors.append('red')
        else:
            intensity = 0.3 + 0.7 * (val / max_total) if max_total>0 else 0.3
            blue_level = int(255 * intensity)
            colors.append(f'rgb(0,0,{blue_level})')

st.subheader("차수별 총합 & 비율")
st.dataframe(dose_df)

st.subheader("비율 막대그래프")
fig_prop = px.bar(dose_df, x='dose', y='proportion', text=dose_df['proportion'].apply(lambda x: f"{x:.2%}"))
fig_prop.update_traces(marker_color=colors, textposition='outside')
st.plotly_chart(fig_prop, use_container_width=True)

st.subheader("차수별 접종 총합 그래프")
fig_total = px.bar(dose_df, x='dose', y='total', text=dose_df['total'].apply(lambda x: f"{int(x):,}"))
fig_total.update_traces(marker_color=colors, textposition='outside')
st.plotly_chart(fig_total, use_container_width=True)

st.markdown('---')
st.subheader('원본 데이터 다운로드')
st.download_button('CSV 다운로드', df.to_csv(index=False).encode('utf-8-sig'), file_name='seoul_vaccination_status.csv', mime='text/csv')
