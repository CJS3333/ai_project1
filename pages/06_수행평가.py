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
