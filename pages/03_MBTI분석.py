# streamlit_mbti_app.py
"""
Streamlit app: MBTI by Country (interactive Plotly bar chart)
- Upload a CSV or the app will try to load './countriesMBTI_16types.csv' if present.
- Select a country -> show MBTI distribution as a Plotly bar chart.
- Chart styling: 1st place = red, others = blue -> fading gradient (lighter blues for lower ranks).
- Provides a downloadable requirements.txt content.

How to run on Streamlit Cloud:
1. Create a new app, paste this file as 'streamlit_app.py' (or keep filename).
2. Add a file 'requirements.txt' with the contents provided by the download button, or use the included download button in the app to get it.

"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import io

st.set_page_config(page_title='MBTI by Country', layout='wide')

st.title('🌍 MBTI Distribution by Country — Interactive Plotly Chart')
st.markdown('업로드한 CSV 파일에서 각 국가의 MBTI 분포를 확인합니다. 파일이 없으면 앱 상단의 업로더로 업로드하세요.')

# Try to load local CSV if available (useful when deploying with the file included)
default_path = Path('./countriesMBTI_16types.csv')

uploaded_file = st.file_uploader('CSV 파일 업로드 (countriesMBTI_16types.csv 형식)', type=['csv'])

if uploaded_file is None and default_path.exists():
    try:
        df = pd.read_csv(default_path)
        st.success(f'로컬 파일 {default_path} 로드 완료')
    except Exception as e:
        st.error('로컬 파일 로드 실패: ' + str(e))
        df = None
elif uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success('업로드 파일 로드 완료')
    except Exception as e:
        st.error('업로드 파일 로드 실패: ' + str(e))
        df = None
else:
    df = None

if df is None:
    st.info('CSV 파일을 업로드하거나 프로젝트 루트에 countriesMBTI_16types.csv 파일을 넣어주세요.')
    st.stop()

# Ensure 'Country' column exists
if 'Country' not in df.columns:
    st.error("CSV에 'Country' 열이 없습니다. 파일을 확인하세요.")
    st.stop()

# Identify MBTI columns (all columns except 'Country')
mbti_cols = [c for c in df.columns if c != 'Country']

# Basic validation: check there are 16 MBTI cols
if len(mbti_cols) < 10:
    st.warning('MBTI 열 수가 적습니다. 올바른 파일인지 확인하세요.')

# Sidebar - Country select
with st.sidebar:
    st.header('옵션')
    country = st.selectbox('국가 선택', options=sorted(df['Country'].unique()))
    show_table = st.checkbox('원시 데이터 표 보기', value=False)
    normalize = st.checkbox('값을 0-1로 정규화 (합 = 1)', value=True)

row = df.loc[df['Country'] == country]
if row.empty:
    st.error('선택한 국가의 데이터가 없습니다.')
    st.stop()

row = row.iloc[0]

# Extract MBTI values
types = mbti_cols
values = [float(row[t]) for t in types]

if normalize:
    s = sum(values)
    if s > 0:
        values = [v / s for v in values]

# Create a dataframe for plotting sorted by value
plot_df = pd.DataFrame({'MBTI': types, 'Value': values}).sort_values('Value', ascending=False).reset_index(drop=True)

# Build colors: 1st = red, others = blue gradient (from deep to lighter)
def hex_from_rgb(r,g,b):
    return '#{:02x}{:02x}{:02x}'.format(int(r), int(g), int(b))

n = len(plot_df)
colors = []
# red for first
colors.append('#e02424')  # vivid red

# base blue (Plotly default-ish)
base_blue = (31, 119, 180)  # rgb
lightest_blue = (200, 220, 245)

if n > 1:
    for i in range(1, n):
        # interpolation factor from 0 -> 1 as i goes 1..n-1
        if n-2 > 0:
            t = (i-1) / (n-2)
        else:
            t = 0
        r = base_blue[0] + (lightest_blue[0] - base_blue[0]) * t
        g = base_blue[1] + (lightest_blue[1] - base_blue[1]) * t
        b = base_blue[2] + (lightest_blue[2] - base_blue[2]) * t
        colors.append(hex_from_rgb(r, g, b))

# Plotly bar chart
fig = go.Figure(data=[go.Bar(
    x=plot_df['MBTI'],
    y=plot_df['Value'],
    marker=dict(color=colors),
    text=[f"{v:.2%}" for v in plot_df['Value']],
    textposition='auto',
    hovertemplate='<b>%{x}</b><br>비율: %{y:.4f}<extra></extra>'
)])

fig.update_layout(
    title=f'{country} 의 MBTI 분포 (상위부터)',
    xaxis_title='MBTI 유형',
    yaxis_title='비율',
    template='simple_white',
    margin=dict(l=40, r=40, t=80, b=40),
    height=520
)

# Show dataframe and figure
col1, col2 = st.columns([1,2])
with col1:
    st.subheader('상위 MBTI 목록')
    st.table(plot_df.head(10))
    if show_table:
        st.subheader('원시 데이터')
        st.dataframe(df[df['Country']==country].T)

with col2:
    st.plotly_chart(fig, use_container_width=True)

# Provide requirements.txt content and download button
requirements = """streamlit
pandas
plotly
"""

st.markdown('---')
st.subheader('requirements.txt')
st.code(requirements)
st.download_button('requirements.txt 다운로드', data=requirements, file_name='requirements.txt', mime='text/plain')

st.markdown("\n---\n앱에 문제가 생기면 CSV 파일의 컬럼명(특히 'Country')과 값이 숫자(또는 비율)인지 확인하세요.")
