# Streamlit app for visualizing Seoul COVID-19 Vaccination Status
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Seoul COVID-19 Vaccination Status")

st.title("Seoul Metropolitan City — COVID-19 Vaccination Status")
st.markdown("Uploaded dataset: **Seoul Metropolitan City_COVID-19 Vaccination Status.csv**")

@st.cache_data
def load_data(path):
    return pd.read_csv(path, encoding="cp949")

df = load_data("/mnt/data/Seoul Metropolitan City_COVID-19 Vaccination Status.csv")

st.subheader("데이터 샘플 (상위 10행)")
st.dataframe(df.head(10))

st.subheader("컬럼 정보")
st.write(df.dtypes.to_frame('dtype'))

# Detected dose-related columns
# (자동탐지된 컬럼명은 로컬에서 미리 계산되어 스트림릿에서 사용됩니다.)
dose_cols = ['당일 1차접종자 수', '1차접종 누계', '당일 2차접종자 수', '2차접종 누계', '당일 3차접종자 수', '3차접종 누계', '당일 4차접종자 수', '4차접종 누계']

if dose_cols:
    st.subheader("차수별 총합 & 비율")
    dose_totals = {
        '1차접종 누계': 17686735713.0,
        '2차접종 누계': 4372836883.0,
        '3차접종 누계': 2450391133.0,
        '4차접종 누계': 316008378.0,
        '동절기접종 누계': 172585921.0,
        '당일 2차접종자 수': 8055902.0,
        '당일 1차접종자 수': 7859336.0,
        '당일 3차접종자 수': 5911976.0
    }
    dose_df = pd.DataFrame.from_dict(dose_totals, orient='index', columns=['total']).reset_index().rename(columns={'index':'dose'})
    dose_df['proportion'] = dose_df['total'] / dose_df['total'].sum()
    st.dataframe(dose_df)

    st.subheader("비율 막대그래프")
    fig_prop = px.bar(dose_df.sort_values('total', ascending=False), x='dose', y='proportion', text=dose_df['proportion'].apply(lambda x: f"{x:.2%}"))
    colors = ['red', 'rgb(0,0,255)', 'rgb(0,0,200)', 'rgb(0,0,120)', 'rgb(0,0,80)', 'rgb(0,0,60)', 'rgb(0,0,40)', 'rgb(0,0,30)']
    fig_prop.update_traces(marker_color=colors, textposition='outside')
    st.plotly_chart(fig_prop, use_container_width=True)

    st.subheader("차수별 접종 총합 그래프")
    fig_total = px.bar(dose_df.sort_values('total', ascending=False), x='dose', y='total', text=dose_df['total'].apply(lambda x: f"{int(x):,}"))
    fig_total.update_traces(marker_color=colors, textposition='outside')
    st.plotly_chart(fig_total, use_container_width=True)
else:
    st.info("데이터에서 '1차','2차','3차' 관련 컬럼을 자동으로 찾지 못했습니다. 컬럼명을 확인해주세요.")

st.markdown('---')
st.subheader('원본 데이터 다운로드')
st.download_button('CSV 다운로드', df.to_csv(index=False).encode('utf-8-sig'), file_name='seoul_vaccination_status.csv', mime='text/csv')
# app.py — Streamlit 앱 (파일 경로 유무에 따라 유연하게 처리)
import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO, BytesIO

st.set_page_config(layout="wide", page_title="Seoul COVID-19 Vaccination Status")

st.title("Seoul Metropolitan City — COVID-19 Vaccination Status")
st.markdown("앱에서 CSV 파일을 찾을 수 없으면 아래 업로드 위젯을 사용하세요.")

# 기본으로 시도할 경로들 (배포 시 레포 루트에 파일을 넣어둘 경우 유용)
PREFERRED_PATHS = [
    "/mnt/data/Seoul Metropolitan City_COVID-19 Vaccination Status.csv",
    "./Seoul Metropolitan City_COVID-19 Vaccination Status.csv",
    "./data/Seoul Metropolitan City_COVID-19 Vaccination Status.csv"
]

@st.cache_data
def try_read_csv_from_paths(paths):
    for p in paths:
        try:
            # cp949/euc-kr/utf-8 순으로 자동 시도
            for enc in ["utf-8", "cp949", "euc-kr", "latin1"]:
                try:
                    df = pd.read_csv(p, encoding=enc)
                    return df, p, enc
                except Exception:
                    continue
        except FileNotFoundError:
            continue
    return None, None, None

# 1) 먼저 레포/서버상의 경로로 시도
df, used_path, used_enc = try_read_csv_from_paths(PREFERRED_PATHS)

# 2) 없으면 사용자에게 업로드 받음
uploaded = None
if df is None:
    st.warning("앱에서 미리 지정한 경로에서 CSV를 찾지 못했습니다. 아래에 파일을 업로드해주세요.")
    uploaded = st.file_uploader("CSV 파일 업로드 (예: Seoul Metropolitan City_COVID-19 Vaccination Status.csv)", type=["csv"])
    if uploaded is not None:
        # uploaded는 UploadedFile 객체 (BytesIO)
        # 인코딩 문제에 대비해 먼저 bytes -> try decode
        try:
            # pandas는 바이트 스트림을 바로 받을 수 있음
            df = pd.read_csv(uploaded)
            used_enc = "pandas-detect"
            used_path = "uploaded_file"
        except Exception:
            # 업로드된 파일을 cp949로 시도
            uploaded.seek(0)
            try:
                df = pd.read_csv(uploaded, encoding="cp949")
                used_enc = "cp949"
                used_path = "uploaded_file"
            except Exception as e:
                st.error(f"업로드한 파일을 읽는 데 실패했습니다: {e}")
                st.stop()
    else:
        st.info("CSV 파일이 필요합니다. 레포에 파일을 추가하거나 위 업로더로 업로드하세요.")
        st.stop()

# 여기까지 도달하면 df는 유효
st.success(f"데이터 로드 성공 — 소스: {used_path} (encoding={used_enc})")
st.subheader("데이터 샘플 (상위 10행)")
st.dataframe(df.head(10))

st.subheader("컬럼 정보")
st.write(df.dtypes.to_frame('dtype'))

# 자동으로 '차수' 관련 컬럼 탐지
dose_cols = [c for c in df.columns if any(x in c for x in ['1차','2차','3차','차수','접종','당일'])]
# 영어/다른 표기 fallback
dose_cols += [c for c in df.columns if any(x in c.lower() for x in ['1st','2nd','3rd','dose']) and c not in dose_cols]
dose_cols = list(dict.fromkeys(dose_cols))

# 집계
dose_totals = {}
if dose_cols:
    for c in dose_cols:
        s = pd.to_numeric(df[c], errors='coerce').fillna(0)
        dose_totals[c] = float(s.sum())
else:
    # 숫자형 컬럼에서 상위 3개를 임의로 사용(데이터마다 다름)
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    for i, c in enumerate(numeric_cols[:3]):
        dose_totals[c] = float(df[c].sum())

import pandas as pd
dose_df = pd.DataFrame.from_dict(dose_totals, orient='index', columns=['total']).reset_index().rename(columns={'index':'dose'})
total_sum = dose_df['total'].sum() if dose_df['total'].sum() else 1
dose_df['proportion'] = dose_df['total'] / total_sum
dose_df = dose_df.sort_values('total', ascending=False).reset_index(drop=True)

# 색상: 1등 빨간, 나머지 파랑 그라데이션
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
