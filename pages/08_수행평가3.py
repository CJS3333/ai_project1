import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --------------------------------------------------------------------------------
# 1. 데이터 로드 및 전처리
# --------------------------------------------------------------------------------

@st.cache_data
def load_data():
    """데이터를 로드하고 필요한 전처리 수행"""
    # Streamlit Cloud 환경을 고려하여 파일 이름만 지정 (루트 폴더를 작업 디렉토리로 가정)
    try:
        # 경로 수정: 'COVID.csv'
        df = pd.read_csv('COVID.csv') 
    except FileNotFoundError:
        # 오류 발생 시 빈 DataFrame 반환 (Streamlit에서 오류 메시지는 이미 확인했으므로 제거)
        return pd.DataFrame() 

    # '접종일' 컬럼 정리 및 날짜 형식으로 변환 (주간 데이터는 첫째 날짜 사용)
    df['접종일'] = df['접종일'].astype(str).str.replace(r'\(|\)', '', regex=True)
    df['접종일'] = df['접종일'].apply(lambda x: x.split('~')[0].strip())
    df['접종일'] = pd.to_datetime(df['접종일'], format='%Y.%m.%d', errors='coerce')

    # 불필요한 행(NaN이 많은 행) 및 순번 컬럼 제거
    df = df.dropna(subset=['접종일']).reset_index(drop=True)
    df = df.drop(columns=['순번'], errors='ignore')

    # 수치형 컬럼 변환 (콤마 제거 후 숫자 타입으로)
    numeric_cols = [col for col in df.columns if '누계' in col or '접종자 수' in col or '접종대상자' in col]
    for col in numeric_cols:
        df[col] = df[col].astype(str).str.replace(',', '', regex=False).replace('', '0', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 3차, 4차, 동절기 접종률 컬럼은 NaN이 많으므로 0으로 채움
    df = df.fillna(0)

    return df

df = load_data()

# --------------------------------------------------------------------------------
# 2. Streamlit 앱 구성
# --------------------------------------------------------------------------------

if not df.empty:
    st.set_page_config(layout="wide")
    st.title("💉 COVID-19 백신 접종 현황 분석 ")

    st.markdown("---")

    # --- 2.1. Plotly 시계열 그래프 (1차 접종률) ---
    st.header("1. 📉 1차 접종률 추이 (Plotly 그래프)")
    
    fig_line = px.line(
        df, 
        x='접종일', 
        y='1차접종률(%)', 
        title='기간별 1차 접종률 변화',
        labels={'1차접종률(%)': '1차 접종률 (%)', '접종일': '접종일자'},
        color_discrete_sequence=['#2C7BB6'] # 진한 파란색
    )
    fig_line.update_traces(mode='lines+markers', marker=dict(size=4))
    fig_line.update_layout(xaxis_title="접종일", yaxis_title="1차접종률 (%)")
    st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("---")

    # --- 2.2. 접종률 비교 막대 그래프 (비율) ---
    st.header("2. 📊 접종 완료율 비교 (최종 데이터 기준)")

    # 가장 최근 날짜의 접종률 데이터 추출
    # 데이터가 순번이 높은 순서(최신)부터 시작한다고 가정
    latest_data = df.iloc[0] 

    # 1차, 2차, 3차, 4차, 동절기 접종률을 비교
    rates_data = {
        '차수': ['1차 접종률', '2차 접종률', '3차 접종률', '4차 접종률', '동절기 접종률'],
        '접종률 (%)': [
            latest_data.get('1차접종률(%)', 0), 
            latest_data.get('2차접종률(%)', 0), 
            latest_data.get('3차접종률(%)', 0), 
            latest_data.get('4차접종률(%)', 0),
            latest_data.get('동절기접종률(%)', 0)
        ]
    }
    rates_df = pd.DataFrame(rates_data)

    # 1등 찾기
    top_rate_idx = rates_df['접종률 (%)'].idxmax()

    # 색상 설정 (1등: 빨강, 나머지는 파란색 그라데이션)
    def get_color(row):
        if row.name == top_rate_idx:
            return '#FF0000' # 빨간색
        else:
            # 파란색 계열 그라데이션 (값에 따라 색상 명도 조정)
            if row['차수'] == '1차 접종률': return '#2C7BB6' # 진한 파랑
            if row['차수'] == '2차 접종률': return '#7FBCD2'
            if row['차수'] == '3차 접종률': return '#B3E2CD'
            if row['차수'] == '4차 접종률': return '#FDC086' # 4차는 주황 계열로 분리
            return '#F0F9E8' # 동절기 (가장 연한 색)

    rates_df['색상'] = rates_df.apply(get_color, axis=1)

    fig_bar_rate = go.Figure(data=[
        go.Bar(
            x=rates_df['차수'],
            y=rates_df['접종률 (%)'],
            marker_color=rates_df['색상']
        )
    ])
    fig_bar_rate.update_layout(
        title='최신 데이터 기준, 백신 차수별 접종률 (%)',
        xaxis_title="접종 차수",
        yaxis_title="접종률 (%)",
        yaxis_range=[0, rates_df['접종률 (%)'].max() * 1.1]
    )
    st.plotly_chart(fig_bar_rate, use_container_width=True)

    st.markdown("---")

    # --- 2.3. 1차/2차/3차 누계 접종자 수 비교 ---
    st.header("3. 🔢 1차/2차/3차 접종 누계 비교 (가장 많이 접종한 차수)")

    # 1차, 2차, 3차의 최종 누계 값만 추출
    final_cumulative = pd.DataFrame({
        '차수': ['1차 접종 누계', '2차 접종 누계', '3차 접종 누계'],
        '누계 접종자 수': [
            latest_data.get('1차접종 누계', 0), 
            latest_data.get('2차접종 누계', 0), 
            latest_data.get('3차접종 누계', 0)
        ]
    }).sort_values(by='누계 접종자 수', ascending=False).reset_index(drop=True)

    # 1등 찾기
    top_cumulative_idx = final_cumulative['누계 접종자 수'].idxmax()

    # 색상 설정 (1등: 빨강, 나머지는 파란색 그라데이션)
    def get_cumulative_color(row):
        if row.name == top_cumulative_idx:
            return '#FF0000' # 빨간색
        else:
            # 파란색 계열 그라데이션
            if row['차수'] == '1차 접종 누계': return '#2C7BB6'
            if row['차수'] == '2차 접종 누계': return '#7FBCD2'
            return '#B3E2CD'

    final_cumulative['색상'] = final_cumulative.apply(get_cumulative_color, axis=1)

    fig_bar_cumul = go.Figure(data=[
        go.Bar(
            x=final_cumulative['차수'],
            y=final_cumulative['누계 접종자 수'],
            marker_color=final_cumulative['색상']
        )
    ])
    fig_bar_cumul.update_layout(
        title='1차, 2차, 3차 누계 접종자 수 비교',
        xaxis_title="접종 차수",
        yaxis_title="누계 접종자 수",
        yaxis_tickformat = ',.0f' # 숫자 콤마 표시
    )
    st.plotly_chart(fig_bar_cumul, use_container_width=True)

    st.markdown("---")

    # --- 2.4. 데이터 테이블 표시 ---
    st.header("4. 📋 원본 데이터 (최신 100개)")
    st.dataframe(df.head(100), use_container_width=True)
