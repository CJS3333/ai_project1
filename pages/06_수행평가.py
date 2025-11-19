import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 데이터 로드 및 전처리
@st.cache_data
def load_data(file_path):
    try:
        # 한국어 인코딩(cp949)으로 파일 로드 시도
        df = pd.read_csv(file_path, encoding='cp949')
    except UnicodeDecodeError:
        # 실패 시, 다른 흔한 인코딩(utf-8)으로 다시 시도
        df = pd.read_csv(file_path, encoding='utf-8')
    return df

def process_data(df):
    # 가장 마지막 행 (최신 누계 데이터)만 사용
    latest_data = df.iloc[0]

    # 1차, 2차, 3차 접종 누계 인원 추출
    # 누계 인원이 없으면 0으로 처리 (혹시 모를 에러 방지)
    data = {
        '차수': ['1차 접종 누계', '2차 접종 누계', '3차 접종 누계'],
        '누계 인원': [
            latest_data.get('1차접종 누계', 0),
            latest_data.get('2차접종 누계', 0),
            latest_data.get('3차접종 누계', 0)
        ]
    }
    
    # 데이터프레임 생성
    df_chart = pd.DataFrame(data)
    
    # 3차 접종이 중간에 누락된 경우를 대비해 NaN을 0으로 채우고 정수형으로 변환
    df_chart['누계 인원'] = df_chart['누계 인원'].fillna(0).astype(int)
    
    return df_chart

# 2. Plotly 그래프 생성
def create_chart(df_chart):
    # 가장 많이 접종한 차수 찾기
    max_count = df_chart['누계 인원'].max()
    
    # 색상 할당: 가장 많은 값은 빨간색, 나머지는 파란색 그라데이션
    color_map = []
    
    # 파란색 계열 색상 설정 (높을수록 진하게)
    blue_scale = ['#aed8e6', '#71b7e6', '#2d7dc5'] 

    # '누계 인원' 기준으로 정렬 후, 가장 큰 값은 'red', 나머지는 blue_scale 순서대로 할당
    df_sorted = df_chart.sort_values(by='누계 인원', ascending=False).reset_index(drop=True)
    
    # 색상 리스트 생성
    chart_colors = {}
    blue_index = 0
    
    for index, row in df_sorted.iterrows():
        차수 = row['차수']
        인원 = row['누계 인원']
        
        if 인원 == max_count and 인원 > 0:
            chart_colors[차수] = '#FF4B4B' # Streamlit Red
        elif blue_index < len(blue_scale):
            chart_colors[차수] = blue_scale[blue_index]
            blue_index += 1
        else:
            chart_colors[차수] = '#cccccc' # 기타 색상

    # 3. Plotly 막대 그래프 생성
    fig = px.bar(
        df_chart, 
        x='차수', 
        y='누계 인원', 
        color='차수', # '차수'별로 색상을 다르게 설정
        color_discrete_map=chart_colors, # 위에서 정의한 색상 맵 적용
        title='차수별 COVID-19 백신 접종 누계 인원 비교',
        labels={'차수': '백신 접종 차수', '누계 인원': '접종 누계 인원 수'},
        text='누계 인원' # 막대 위에 값 표시
    )

    # 그래프 레이아웃 커스터마이징
    fig.update_layout(
        xaxis_title='백신 접종 차수',
        yaxis_title='누계 인원 (명)',
        legend_title='접종 차수',
        hovermode="x unified"
    )

    # 텍스트 포맷팅 (정수형에 쉼표 추가)
    fig.update_traces(texttemplate='%{y:,s}', textposition='outside')
    fig.update_yaxes(tickformat=',.') # Y축 값 쉼표 처리

    return fig

# 4. Streamlit 앱 실행 함수
def run_app():
    st.title("💉 COVID-19 백신 접종 데이터 분석")
    st.markdown("---")
    
    # 파일 경로 지정 (Streamlit Cloud 환경에서는 현재 디렉토리에 파일이 있어야 함)
    file_path = 'COVID.csv'

    try:
        df = load_data(file_path)
        
        # 1차, 2차, 3차 접종 누계 데이터 준비
        df_chart = process_data(df)
        
        st.subheader("최신 기준 1, 2, 3차 접종 누계 인원 비교")
        
        # 그래프 생성 및 표시
        fig = create_chart(df_chart)
        st.plotly_chart(fig, use_container_width=True)

        # 요약 정보 표시
        max_vaccine = df_chart.loc[df_chart['누계 인원'].idxmax()]
        st.info(
            f"**💡 분석 결과:**\n\n"
            f"**{max_vaccine['차수']}**에 **{max_vaccine['누계 인원']:,}명**으로 가장 많은 인원이 접종했습니다."
        )

        st.markdown("---")
        st.subheader("데이터 미리보기 (최신 5개 항목)")
        st.dataframe(df.head(), use_container_width=True)

    except FileNotFoundError:
        st.error(f"'{file_path}' 파일을 찾을 수 없습니다. Streamlit Cloud에 파일을 업로드했는지 확인해주세요.")
    except Exception as e:
        st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    run_app()
