import streamlit as st
import pandas as pd
import plotly.express as px

# Streamlit 페이지 설정
st.set_page_config(
    page_title="서울시 코로나19 백신 접종 현황 분석",
    layout="wide"
)

## ----------------------------------------------------
## 1. 데이터 로드 및 전처리 함수 (개선됨)
## ----------------------------------------------------
@st.cache_data
def load_data(file_path):
    """
    CSV 파일을 로드하고 필요한 전처리를 수행합니다.
    - 복잡한 try-except 대신 errors='coerce'를 사용하여 범위 날짜를 제거합니다.
    """
    try:
        # 파일은 루트 폴더에 있다고 가정
        df = pd.read_csv(file_path, encoding='cp949') 
    except UnicodeDecodeError:
        # cp949로 실패하면 utf-8 시도
        df = pd.read_csv(file_path, encoding='utf-8')
    
    # 컬럼명 정리 및 필요한 컬럼만 선택
    vax_cols = [
        '접종일',
        '당일 1차접종자 수', 
        '당일 2차접종자 수', 
        '당일 3차접종자 수',
        '1차접종률(%)',
        '2차접종률(%)',
        '3차접종률(%)'
    ]
    df_clean = df[vax_cols].copy()

    # 1. 접종일 컬럼에서 특수 문자 제거 (예: '(2023.08.20.~08.26.)' -> '2023.08.20.08.26.')
    df_clean['접종일'] = df_clean['접종일'].astype(str).str.replace(r'[~()]', '', regex=True)
    
    # 2. 날짜 형식으로 변환 시도. 변환 실패(범위 데이터) 시 NaT(Not a Time)으로 만듦
    df_clean['접종일'] = pd.to_datetime(df_clean['접종일'], format='%Y.%m.%d', errors='coerce')
    
    # 3. NaT (범위 데이터)를 포함하는 행을 제거 (단일 날짜 데이터만 남김)
    df_clean.dropna(subset=['접종일'], inplace=True)
    
    return df_clean

# 데이터 로드
DATA_FILE = "Seoul Metropolitan City_COVID-19 Vaccination Status.csv"
df_vax = load_data(DATA_FILE)


## ----------------------------------------------------
## 2. 시각화 및 분석 함수
## ----------------------------------------------------

def plot_vax_count(df):
    """
    1차, 2차, 3차 접종 합계를 비교하는 막대 그래프를 생성합니다.
    """
    st.markdown("### 📊 차수별 총 접종자 수 비교 (1차, 2차, 3차)")
    st.caption("기간 동안의 당일 접종자 수를 합산하여 차수별 접종 규모를 비교합니다.")
    
    # 1차, 2차, 3차 접종자 수 합계 계산
    total_1st = df['당일 1차접종자 수'].sum()
    total_2nd = df['당일 2차접종자 수'].sum()
    total_3rd = df['당일 3차접종자 수'].sum()
    
    vax_totals = pd.DataFrame({
        '접종 차수': ['1차', '2차', '3차'],
        '총 접종자 수': [total_1st, total_2nd, total_3rd]
    }).sort_values(by='총 접종자 수', ascending=False)
    
    # 가장 많이 접종한 차수 찾기 (색상 조건)
    max_vax_rank = vax_totals.iloc[0]['접종 차수']
    
    # 1등(최고 접종 수)을 빨간색으로, 나머지는 파란색 그라데이션
    if max_vax_rank == '1차':
        color_discrete_sequence=['red', 'blue', 'darkblue']
    elif max_vax_rank == '2차':
        color_discrete_sequence=['blue', 'red', 'darkblue']
    else: # 3차
        color_discrete_sequence=['blue', 'darkblue', 'red']
    
    # Plotly 막대 그래프 생성
    fig = px.bar(
        vax_totals,
        x='접종 차수',
        y='총 접종자 수',
        text='총 접종자 수',
        title='COVID-19 차수별 총 접종자 수',
        color='접종 차수',
        color_discrete_sequence=color_discrete_sequence,
        category_orders={"접종 차수": vax_totals['접종 차수'].tolist()}, # 정렬 유지
        labels={'총 접종자 수': '총 접종자 수 (명)'}
    )
    
    fig.update_traces(texttemplate='%{text:,.0f}명', textposition='outside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    fig.update_layout(xaxis_title=None, yaxis_title=None, showlegend=False)
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.success(f"**가장 많이 접종한 차수:** **{vax_totals.iloc[0]['접종 차수']}** ({vax_totals.iloc[0]['총 접종자 수']:,.0f}명)")
    st.markdown("---")


def plot_vax_rate_over_time(df):
    """
    1차, 2차, 3차 접종률을 시간 경과에 따라 비교하는 꺾은선 그래프를 생성합니다.
    """
    st.markdown("### 📈 1차, 2차, 3차 누적 접종률 변화 추이")
    st.caption("시간에 따른 누적 접종률(%)의 변화를 보여줍니다. 데이터의 특성상 접종률은 계속 증가하는 추세를 보입니다.")
    
    # Plotly 꺾은선 그래프 생성
    fig = px.line(
        df,
        x='접종일',
        y=['1차접종률(%)', '2차접종률(%)', '3차접종률(%)'],
        title='차수별 누적 접종률 변화',
        labels={'value': '접종률 (%)', 'variable': '접종 차수'},
    )

    fig.update_layout(
        xaxis_title=None,
        yaxis_title="접종률 (%)",
        hovermode="x unified",
        legend_title="접종 차수"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")


## ----------------------------------------------------
## 3. 메인 Streamlit 앱 실행
## ----------------------------------------------------
st.title("🇰🇷 서울시 COVID-19 백신 접종 현황 분석")
st.markdown("이 앱은 서울시 백신 접종 데이터를 기반으로 차수별 접종 현황을 시각화합니다.")

if not df_vax.empty:
    st.dataframe(df_vax.head(), caption="데이터 미리보기 (전처리된 상위 5개 행)")
    
    # 9번 요청: 1차, 2차, 3차 중 가장 많이 접종한 차수 그래프
    plot_vax_count(df_vax)
    
    # 5, 6번 요청: 비율(접종률) 그래프
    plot_vax_rate_over_time(df_vax)
    
else:
    st.error("데이터 파일을 로드하거나 처리하는 데 문제가 발생했습니다. 파일 경로 및 인코딩을 확인해 주세요.")
