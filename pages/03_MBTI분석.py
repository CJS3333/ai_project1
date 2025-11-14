import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os # 파일 경로 처리를 위해 os 모듈 추가

# -----------------------------------------------------------------------------
# 1. 데이터 로드 (파일 경로 수정)
# -----------------------------------------------------------------------------
# 파일이 상위 폴더(루트)에 있으므로, 상대 경로를 '../countriesMBTI_16types.csv'로 설정합니다.
FILE_PATH = '../countriesMBTI_16types.csv'

@st.cache_data
def load_data(path):
    """
    지정된 경로에서 데이터프레임을 로드합니다.
    Streamlit Cloud 환경에서는 상위 폴더 접근이 가능합니다.
    """
    try:
        df = pd.read_csv(path)
        return df
    except FileNotFoundError:
        st.error(f"⚠️ **파일을 찾을 수 없습니다.** 경로를 확인해 주세요: `{path}`")
        # 데이터가 없는 경우를 대비해 빈 DataFrame 반환
        return pd.DataFrame()

df_mbti = load_data(FILE_PATH)

# 데이터가 성공적으로 로드되지 않았으면 실행 중지
if df_mbti.empty:
    st.stop()


# -----------------------------------------------------------------------------
# 2. Streamlit 레이아웃 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="🌎 국가별 MBTI 분포 시각화",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🗺️ 국가별 MBTI 16가지 유형 분포 분석")
st.markdown("---")

# -----------------------------------------------------------------------------
# 3. 사이드바 (사용자 입력)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 국가 선택 드롭다운
    countries = sorted(df_mbti['Country'].unique().tolist())
    
    # 초기값 설정 (가장 첫 번째 국가 또는 'South Korea'가 있다면 그것으로 설정)
    initial_index = countries.index('South Korea') if 'South Korea' in countries else 0
    
    selected_country = st.selectbox(
        "**국가를 선택하세요** 👇",
        options=countries,
        index=initial_index
    )

st.markdown(f"## 📊 {selected_country}의 MBTI 유형별 비율")
st.write(f"선택된 **{selected_country}** 국가의 MBTI 16가지 유형별 분포를 막대 그래프로 시각화합니다.")

# -----------------------------------------------------------------------------
# 4. 데이터 가공 및 그래프 생성 함수
# -----------------------------------------------------------------------------

def create_mbti_bar_chart(df, country):
    """
    선택된 국가의 MBTI 비율 막대 그래프를 생성하고 색상을 적용합니다.
    1등: 빨간색, 2등부터: 파란색 그라데이션 적용
    """
    
    # 1. 선택된 국가의 데이터 추출 및 가공
    country_data = df[df['Country'] == country].drop(columns=['Country']).T
    country_data.columns = ['Proportion']
    country_data = country_data.reset_index().rename(columns={'index': 'MBTI_Type'})
    
    # 2. 비율을 기준으로 내림차순 정렬
    country_data = country_data.sort_values(by='Proportion', ascending=False).reset_index(drop=True)
    
    # 3. 색상 매핑 로직
    
    # 기본 색상 설정 (Plotly Colorscales 'Blues_r' 사용)
    BLUE_SCALE = px.colors.sequential.Blues_r
    RED_COLOR = '#E41A1C' # 1등 색상 (빨간색)
    
    # 1등 색상을 먼저 추가
    color_list = [RED_COLOR] 
    
    # 2등부터 16등까지의 데이터
    other_proportions = country_data['Proportion'].iloc[1:]
    n_others = len(other_proportions)
    
    if n_others > 0:
        min_val = other_proportions.min()
        max_val = other_proportions.max()
        
        # 비율을 0과 1 사이로 정규화
        if max_val == min_val:
            # 비율이 모두 같은 경우, 중간 밝기의 파란색을 사용
            normalized_proportions = [0.5] * n_others
        else:
            # 비율이 높을수록 어두운 파란색이 되도록 정규화
            normalized_proportions = (other_proportions - min_val) / (max_val - min_val)
        
        # 정규화된 값에 따라 파란색 그라데이션 적용
        # Plotly의 colorscale은 0에 가까울수록 밝고, 1에 가까울수록 어둡습니다.
        blue_colors = [px.colors.sample_colorscale(BLUE_SCALE, p)[0] for p in np.array(normalized_proportions)]
        color_list.extend(blue_colors)
        
    # 색상 리스트를 데이터프레임에 추가
    country_data['Color'] = color_list
    
    # 4. Plotly Bar Chart 생성
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=country_data['MBTI_Type'],
        y=country_data['Proportion'],
        marker_color=country_data['Color'], 
        text=[f'{p:.2%}' for p in country_data['Proportion']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>비율: %{y:.2%}<extra></extra>',
    ))

    # 5. 레이아웃 설정
    fig.update_layout(
        title={
            'text': f"**{country}**의 MBTI 비율 순위",
            'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top'
        },
        xaxis_title="MBTI 유형 (비율 순)",
        yaxis_title="비율 (Proportion)",
        yaxis_tickformat=".0%",
        height=600,
        template="plotly_white"
    )
    
    fig.update_xaxes(tickangle=45)

    return fig

# -----------------------------------------------------------------------------
# 5. Streamlit 앱 실행
# -----------------------------------------------------------------------------
if selected_country:
    # 그래프 생성 및 Streamlit에 표시
    mbti_fig = create_mbti_bar_chart(df_mbti, selected_country)
    st.plotly_chart(mbti_fig, use_container_width=True)

    # 데이터 미리보기
    st.markdown("---")
    st.subheader("📚 데이터 미리보기 (선택 국가)")
    
    display_data = df_mbti[df_mbti['Country'] == selected_country].T.reset_index()
    display_data.columns = ['MBTI 유형', '비율']
    display_data = display_data.iloc[1:].sort_values(by='비율', ascending=False)
    
    # 비율을 보기 쉽게 백분율로 포맷팅
    display_data['비율 (%)'] = (display_data['비율'] * 100).map('{:.2f}%'.format)
    st.dataframe(display_data[['MBTI 유형', '비율 (%)']].reset_index(drop=True), hide_index=True)
