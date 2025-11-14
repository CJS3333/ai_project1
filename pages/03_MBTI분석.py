# streamlit_app.py
"""
Streamlit app: MBTI by Country (interactive Plotly bar chart)
- 파일명: streamlit_app.py (Streamlit Cloud에서 자동으로 인식됩니다)
- 사용법: 프로젝트 루트에 countriesMBTI_16types.csv 파일을 두거나, 앱에서 CSV를 업로드하세요.
- 의존성: streamlit, pandas, plotly
"""

import streamlit as st
import sys
from pathlib import Path

# 안전하게 plotly import 처리: 설치되어 있지 않다면 사용자에게 안내하고 중단
try:
    import plotly.graph_objects as go
except Exception:
    st.set_page_config(page_title='MBTI by Country', layout='wide')
    st.title('🌍 MBTI Distribution by Country — Interactive Plotly Chart')
    st.error(
        "필수 패키지 'plotly'가 설치되어 있지 않아 앱을 실행할 수 없습니다.\n\n"
        "해결 방법:\n"
        "1) 프로젝트 루트에 다음 내용을 포함한 `requirements.txt` 파일을 추가하세요:\n\n"
        "   streamlit==1.28.0\n"
        "   pandas>=1.5.0\n"
        "   plotly>=5.15.0\n\n"
        "2) Streamlit Cloud에 배포한 경우 앱 페이지의 'Manage app' → 'Redeploy' 또는 'Restart'를 눌러 재배포하세요.\n"
        "   (로컬) 터미널에서: pip install -r requirements.txt\n\n"
        "설치 후 앱을 다시 열면 정상 동작합니다."
    )
    st.stop()

import pandas as pd

st.set_page_config(page_title='MBTI by Country', layout='wide')
st.title('🌍 MBTI Distribution by Country — Interactive Plotly Chart')
st.markdown('CSV 파일을 업로드하거나 프로젝트 루트에 `countriesMBTI_16types.csv` 파일을 넣어주세요.')

# Canonical MBTI order (preferential ordering if present in CSV)
MBTI_ORDER = ['INFJ','ISFJ','INTP','ISFP','ENTP','INFP','ENTJ','ISTP','INTJ','ESFP','ESTJ','ENFP','ESTP','ISTJ','ENFJ','ESFJ']

# Load CSV (uploader or local file if present)
def load_csv():
    default_path = Path('./countriesMBTI_16types.csv')
    uploaded = st.file_uploader('CSV 파일 업로드', type=['csv'])
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            st.success('업로드 파일 로드 완료')
            return df
        except Exception as e:
            st.error(f'업로드 파일 로드 실패: {e}')
            return None
    elif default_path.exists():
        try:
            df = pd.read_csv(default_path)
            st.success(f'로컬 파일 {default_path} 로드 완료')
            return df
        except Exception as e:
            st.error(f'로컬 파일 로드 실패: {e}')
            return None
    else:
        return None

df = load_csv()
if df is None:
    st.info('CSV 파일을 업로드하거나 루트에 countriesMBTI_16types.csv 파일을 넣어주세요.')
    st.stop()

# Validate Country column
if 'Country' not in df.columns:
    st.error("CSV에 'Country' 열이 없습니다. 파일을 확인하세요.")
    st.stop()

# Detect MBTI columns present (keep canonical order)
present_mbti = [t for t in MBTI_ORDER if t in df.columns]
other_mbti = [c for c in df.columns if c != 'Country' and c not in present_mbti]
mbti_cols = present_mbti + other_mbti

if len(mbti_cols) < 4:
    st.warning('MBTI로 보이는 열이 아주 적습니다. 파일을 올바르게 준비했는지 확인하세요.')

# Sidebar controls
with st.sidebar:
    st.header('옵션')
    country = st.selectbox('국가 선택', options=sorted(df['Country'].unique()))
    normalize = st.checkbox('값을 0-1로 정규화 (합 = 1)', value=True)
    show_raw = st.checkbox('원시 데이터 보기', value=False)

row_df = df.loc[df['Country'] == country]
if row_df.empty:
    st.error('선택한 국가의 데이터가 없습니다.')
    st.stop()

row = row_df.iloc[0]

# Safely extract numeric values for each MBTI column we detected
types = mbti_cols
values = []
for t in types:
    try:
        v = float(row[t])
    except Exception:
        v = 0.0
    values.append(v)

# Normalization
if normalize:
    s = sum(values)
    if s > 0:
        values = [v / s for v in values]

plot_df = pd.DataFrame({'MBTI': types, 'Value': values}).sort_values('Value', ascending=False).reset_index(drop=True)

# Color generation: first = red, remaining = blue gradient
def clamp(x, lo=0, hi=255):
    return max(lo, min(hi, int(round(x))))

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(clamp(rgb[0]), clamp(rgb[1]), clamp(rgb[2]))

n = len(plot_df)
colors = []
if n == 0:
    st.error('플롯할 MBTI 데이터가 없습니다.')
    st.stop()

# vivid red for #1
colors.append('#e02424')

# Base and light blue endpoints
base_blue = (31, 119, 180)
light_blue = (200, 220, 245)
if n > 1:
    steps = n - 1
    for i in range(1, n):
        t = (i - 1) / max(1, steps - 1)  # 0..1
        r = base_blue[0] + (light_blue[0] - base_blue[0]) * t
        g = base_blue[1] + (light_blue[1] - base_blue[1]) * t
        b = base_blue[2] + (light_blue[2] - base_blue[2]) * t
        colors.append(rgb_to_hex((r, g, b)))

# Build Plotly figure
fig = go.Figure()
fig.add_trace(go.Bar(
    x=plot_df['MBTI'],
    y=plot_df['Value'],
    marker_color=colors,
    text=[f"{v:.2%}" for v in plot_df['Value']],
    textposition='outside',
    hovertemplate='<b>%{x}</b><br>비율: %{y:.6f}<extra></extra>'
))

fig.update_layout(
    title=f'{country} 의 MBTI 분포 (상위부터)',
    xaxis_title='MBTI 유형',
    yaxis_title='비율',
    template='simple_white',
    margin=dict(l=40, r=40, t=80, b=40),
    height=560
)

# Display
col1, col2 = st.columns([1,2])
with col1:
    st.subheader('상위 MBTI 목록')
    st.table(plot_df.head(12))
    if show_raw:
        st.subheader('원시 데이터 (해당 국가)')
        st.dataframe(row_df.T)
with col2:
    st.plotly_chart(fig, use_container_width=True)

# requirements download
requirements = """streamlit==1.28.0
pandas>=1.5.0
plotly>=5.15.0
"""
st.markdown('---')
st.subheader('requirements.txt')
st.code(requirements)
st.download_button('requirements.txt 다운로드', data=requirements, file_name='requirements.txt', mime='text/plain')

st.markdown('\n---\n문제가 계속되면 발생한 에러 메시지를 그대로 알려주세요. 바로 도와드릴게요.')
