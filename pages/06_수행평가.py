import streamlit as st
import pandas as pd
import plotly.express as px

# Streamlit 페이지 설정
st.set_page_config(
    page_title="서울시 코로나19 백신 접종 현황 분석",
    layout="wide"
)

## ----------------------------------------------------
## 1. 데이터 로드 및 전처리 함수
## ----------------------------------------------------
@st.cache_data
def load_data(file_path):
    """
    CSV 파일을 로드하고 필요한 전처리를 수행합니다.
    """
    try:
        # 파일은 루트 폴더에 있다고 가정
        df = pd.read_csv(file_path, encoding='cp949') 
    except UnicodeDecodeError:
        # cp949로 실패하면 utf-8 시도
        df = pd.read_csv(file_path, encoding='utf-8')
    
    # 컬럼명 정리 및 필요한 컬럼만 선택
    # 당일 접종자 수 컬럼
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

    # 접종일이 범위인 행은 건너뛰고, 단일 날짜만 사용하여 시계열 분석을 단순화
    df_clean['접종일'] = df_clean['접종일'].astype(str).str.replace(r'[~()]', '', regex=True)
    df_clean = df_clean[~df_clean['접종일'].str.contains(r'\.')].copy()
    
    # 날짜 형식으로 변환 시 오류 발생 행 제거 (예: 주간 데이터)
    try:
        df_clean['접종일'] = pd.to_datetime(df_clean['접종일'], format='%Y.%m.%d')
    except:
        # 날짜 변환이 안되는 행을 제외하고 다시 시도 (주간 데이터 제외)
        df_clean = df_clean[df_clean['접종일'].str.match(r'\d{4}\.\d{2}\.\d{2}')].copy()
        df_clean['접종일'] = pd.to_datetime(df_clean['접종일'], format='%Y.%m.%d')
        
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
    max_vax = vax_totals['총 접종자 수'].max()
    color_map = {
        '1차': 'blue', '2차': 'blue', '3차': 'blue'
    }
    
    # 1등(최고 접종 수)을 빨간색으로, 나머지는 파란색 그라데이션
    if vax_totals.iloc[0]['접종 차수'] == '1차':
        color_map['1차'] = 'red'
        color_discrete_sequence=['red', 'blue', 'darkblue']
    elif vax_totals.iloc[0]['접종 차수'] == '2차':
        color_map['2차'] = 'red'
        color_discrete_sequence=['blue', 'red', 'darkblue']
    else:
        color_map['3차'] = 'red'
        color_discrete_sequence=['blue', 'darkblue', 'red']
    
    # Plotly 막대 그래프 생성
    fig = px.bar(
        vax_totals,
        x='접종 차수',
        y='총 접종자 수',
        text='총 접종자 수',
        title='COVID-19 차수별 총 접종자 수',
        color='접종 차수',
