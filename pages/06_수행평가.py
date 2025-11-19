# Streamlit app for visualizing Seoul COVID-19 Vaccination Status
# This version does NOT require you to add the CSV to the repo — it will try server paths first
# and then fall back to an upload widget so visitors can run the app without repo changes.

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Seoul COVID-19 Vaccination Status")
st.title("Seoul Metropolitan City — COVID-19 Vaccination Status (Uploader-friendly)")
st.write("앱이 자동으로 서버 경로에서 파일을 찾지 못하면, 아래 업로더로 파일을 올려 실행할 수 있습니다.")

# If the app is running in the same session where the user previously uploaded
# or we have access to a sandbox path, we attempt those paths first.
# The uploaded file (from your earlier session) exists at this path in this environment:
DEFAULT_LOCAL_PATH = "/mnt/data/Seoul Metropolitan City_COVID-19 Vaccination Status.csv"

PREFERRED_PATHS = [
    DEFAULT_LOCAL_PATH,
    "./Seoul Metropolitan City_COVID-19 Vaccination Status.csv",
    "./data/Seoul Metropolitan City_COVID-19 Vaccination Status.csv",
    "./seoul_vaccination_status.csv",
]

@st.cache_data
def try_read_csv_from_paths(paths):
    for p in paths:
        try:
            for enc in ["utf-8", "cp949", "euc-kr", "latin1"]:
                try:
                    df = pd.read_csv(p, encoding=enc)
                    return df, p, enc
                except Exception:
                    continue
        except FileNotFoundError:
            continue
    return None, None, None

# 1) Try paths
df, used_path, used_enc = try_read_csv_from_paths(PREFERRED_PATHS)

# 2) If not found, show uploader
if df is None:
    st.warning("CSV 파일을 자동으로 찾지 못했습니다. 아래에서 파일을 업로드하세요 (한 번 업로드하면 앱이 바로 동작합니다).")
    uploaded = st.file_uploader("CSV 파일 업로드 (예: Seoul Metropolitan City_COVID-19 Vaccination Status.csv)", type=["csv"])
    if uploaded is not None:
        # Try reading uploaded file with pandas; try common encodings
        success = False
        for enc in [None, 'cp949', 'euc-kr', 'utf-8', 'latin1']:
            try:
                if enc is None:
                    df = pd.read_csv(uploaded)
                else:
                    uploaded.seek(0)
                    df = pd.read_csv(uploaded, encoding=enc)
                used_enc = enc or 'pandas-detect'
                used_path = 'uploaded_file'
                success = True
                break
            except Exception:
                continue
        if not success:
            st.error('업로드한 CSV 파일을 읽지 못했습니다. 다른 인코딩으로 저장된 파일일 수 있습니다.')
            st.stop()
    else:
        st.info('CSV 파일을 업로드하거나 앱 소스(레포)에 파일을 추가하세요. 업로드가 가장 간단합니다.')
        st.stop()

st.success(f"데이터 로드 성공 — 소스: {used_path} (encoding={used_enc})")

st.subheader("데이터 샘플 (상위 10행)")
st.dataframe(df.head(10))

st.subheader("컬럼 정보")
st.write(df.dtypes.to_frame('dtype'))

# 자동으로 '차수' 관련 컬럼 탐지
dose_cols = [c for c in df.columns if any(x in c for x in ['1차','2차','3차','차수','접종','당일'])]
# 영어 표기 탐지
dose_cols += [c for c in df.columns if any(x in c.lower() for x in ['1st','2nd','3rd','dose']) and c not in dose_cols]
dose_cols = list(dict.fromkeys(dose_cols))

# 집계
dose_totals = {}
if dose_cols:
    for c in dose_cols:
        s = pd.to_numeric(df[c], errors='coerce').fillna(0)
        dose_totals[c] = float(s.sum())
else:
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    for c in numeric_cols[:3]:
        dose_totals[c] = float(df[c].sum())

import pandas as pd
dose_df = pd.DataFrame.from_dict(dose_totals, orient='index', columns=['total']).reset_index().rename(columns={'index':'dose'})
# 안전장치: 총합이 0이면 1로 대체(비율 계산 시)
total_sum = dose_df['total'].sum() if dose_df['total'].sum() else 1
dose_df['proportion'] = dose_df['total'] / total_sum
dose_df = dose_df.sort_values('total', ascending=False).reset_index(drop=True)

# 색상: 1등 빨강, 나머지는 파랑 그라데이션
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
