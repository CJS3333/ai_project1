import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------------------------------------------------
# 1. 데이터 로드 및 전처리
# ----------------------------------------------------------------------

# 파일 경로 (Streamlit 배포 시 같은 폴더에 있어야 함)
FILE_PATH = "countriesMBTI_16types.csv"

@st.cache_data
def load_data(path):
    """CSV 파일을 로드하고 결측치를 처리합니다."""
    try:
        df = pd.read_csv(path)
        # 'Country' 열이 있는지 확인
        if 'Country' not in df.columns:
            st.error("데이터에 'Country' 열이 없습니다. 파일 형식을 확인해주세요.")
            return None
        
        # 'Country' 열을 인덱스로 설정
        df = df.set_index('Country')
        
        # 데이터프레임의 모든 값이 0과 1 사이인지 확인 (MBTI 비율 데이터의 유효성 검사)
        if not ((df >= 0).all().all() and (df <= 1).all().all()):
            st.warning("MBTI 비율 데이터가 0과 1 사이에 있지 않은 값이 포함되어 있을 수 있습니다.")
            
        return df
    except FileNotFoundError:
        st.error(f"파일을 찾을 수 없습니다: {path}. 파일 이름과 경로를 확인해주세요.")
        return None
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return None

# 데이터 로드
df_mbti = load_data(FILE_PATH)

# 데이터가 성공적으로 로드되지 않았으면 앱 실행 중단
if df_mbti is None:
    st.stop()

# ----------------------------------------------------------------------
# 2. Plotly 그래프 생성 함수
# ----------------------------------------------------------------------

def create_mbti_bar_chart(df: pd.DataFrame, country_name: str):
    """
    선택된 국가의 MBTI 비율 막대 그래프를 생성합니다.
    1등은 빨간색, 2등부터는 파란색 그라데이션을 적용합니다.
    """
    if country_name not in df.index:
        st.warning(f"데이터에서 국가 '{country_name}'를 찾을 수 없습니다.")
        return go.Figure()

    # 1. 데이터 추출 및 정렬
    country_data = df.loc[country_name].sort_values(ascending=False)
    
    # MBTI 유형 이름 (x축)
    mbti_types = country_data.index.tolist()
    # 비율 값 (y축)
    ratios = country_data.values
    
    # 2. 색상 설정 (요청사항 반영)
    
    # 총 막대 개수
    n_bars = len(ratios)
    
    # 색상 리스트 초기화
    colors = []
    
    # 1등은 빨간색 (High contrast red)
    colors.append('rgb(220, 20, 60)') 
    
    # 2등부터는 파란색 그라데이션 적용
    # 'Blues' 컬러 스케일 (Plotly 기본 스케일) 사용. 
    # 2등(가장 진한 파랑)부터 끝(가장 옅은 파랑)으로
    
    # 파란색 그라데이션 생성 (2등부터 n등까지)
    # n_bars - 1 개의 색이 필요 (1등 제외)
    blue_scale = px.colors.sequential.Blues[1:] 
    
    # 필요한 색상 개수에 맞게 조정
    if n_bars > 1:
        # 색상 그라데이션을 2등부터 n등까지 순서대로 할당
        for i in range(1, n_bars):
             # Plotly에서 색상 인덱스는 0부터 시작하고, 2등은 index 1이므로
             # n_bars가 16일 때 15개 (1부터 15)의 색이 필요
             # Blues 스케일의 길이는 보통 10개이므로, 
             # 여기서는 단순화를 위해 Blue 계열의 단일 색상을 사용하거나,
             # 필요 시 더 긴 스케일을 생성해야 함.
             # 여기서는 **2등이 가장 진한 파랑**이고 **비율이 낮아질수록 흐려지는** 단순한 그라데이션을 사용합니다.
            
             # Blue 그라데이션 (2등부터 가장 옅은 파란색으로)
             # i: 1, 2, ..., n_bars-1
             # 색상 밝기: (1 - (i-1) / (n_bars - 2)) * 0.5 + 0.3 (약간의 조정)
             # hsv to rgb 변환을 Streamlit에서 직접 할 수 없으므로, Plotly의 'Blues' 스케일을 활용합니다.
             
            # Plotly Blues 스케일은 일반적으로 밝기 순서로 정렬되어 있습니다.
            # 가장 어두운 파랑 (두 번째 막대)에서 가장 밝은 파랑 (마지막 막대)으로
            
            # 1등은 이미 할당했으므로, 2등부터 마지막까지의 색상을 할당
            blue_idx = i - 1
            
            # 파란색 그라데이션 범위를 2등부터 마지막까지 부드럽게 매핑
            # 2등 막대(i=1) -> 진한 파랑, 마지막 막대(i=n_bars-1) -> 옅은 파랑
            # 2등을 위한 인덱스 계산 (0에서 15-2=13 사이)
            
            # 파랑색 농도를 비율에 따라 계산 (2등부터)
            # 2등의 비율과 가장 낮은 비율의 차이를 기반으로 그라데이션 적용
            
            # 여기서는 편의상 Plotly가 제공하는 'Blues' 스케일의 가장 진한 톤(idx 1)부터 시작하여 
            # 나머지 막대에 순차적으로 할당합니다.
            
            # 주의: Plotly의 색상 스케일은 길이가 정해져 있으므로, 16개 색상을 모두 커버하기 위해
            # 충분히 긴 스케일을 사용하거나 보간해야 합니다.
            # 여기서는 Plotly의 'deep' 파란색을 사용하여 그라데이션을 수동으로 생성하겠습니다.
            
            ratio_norm = (ratios[i] - ratios[n_bars-1]) / (ratios[1] - ratios[n_bars-1] + 1e-9)
            
            # HSL 색상 (Hue=240(파랑), Saturation=100%, Lightness=50%에서 85%로)
            # Lightness가 높을수록 옅은 색입니다. ratio_norm이 높을수록 진한 색이 되어야 합니다.
            # Lightness = 80 - ratio_norm * 30 (80%에서 50% 사이)
            L = 50 + (1 - ratio_norm) * 30
            colors.append(f'hsl(220, 70%, {L}%)')
            
        
    # 3. 그래프 객체 생성
    fig = go.Figure(data=[
        go.Bar(
            x=mbti_types,
            y=ratios,
            marker_color=colors,
            text=[f'{r*100:.2f}%' for r in ratios], # 막대 위에 비율 텍스트 표시
            textposition='outside' # 텍스트 위치
        )
    ])

    # 4. 레이아웃 설정
    fig.update_layout(
        title={
            'text': f'**{country_name}**의 MBTI 유형별 비율',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24, 'color': 'black'}
        },
        xaxis_title="MBTI 유형 (비율 순 정렬)",
        yaxis_title="비율",
        yaxis_tickformat='.1%', # y축 포맷을 퍼센트로
        height=600,
        template="plotly_white", # 깔끔한 배경
        uniformtext_minsize=8, 
        uniformtext_mode='hide'
    )
    
    # 막대 그래프가 0부터 시작하도록 Y축 설정
    fig.update_yaxes(range=[0, country_data.max() * 1.1])


    return fig

# ----------------------------------------------------------------------
# 3. Streamlit 앱 인터페이스
# ----------------------------------------------------------------------

st.set_page_config(
    page_title="국가별 MBTI 비율 분석",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌍 국가별 MBTI 비율 분석 (90개국)")
st.markdown("---")

# 국가 선택 드롭다운 (사이드바)
available_countries = sorted(df_mbti.index.tolist())

st.sidebar.header("국가 선택")
selected_country = st.sidebar.selectbox(
    "데이터를 확인할 국가를 선택하세요:",
    available_countries,
    index=available_countries.index('South Korea') if 'South Korea' in available_countries else 0
)

# 그래프 생성 및 표시
if selected_country:
    st.subheader(f"선택 국가: {selected_country}")
    
    # 그래프 생성
    fig = create_mbti_bar_chart(df_mbti, selected_country)
    
    # Streamlit에 Plotly 그래프 표시
    st.plotly_chart(fig, use_container_width=True)
    
    # 하위 데이터 테이블 표시 (선택 사항)
    st.markdown("### 📊 상세 비율 데이터")
    
    # 선택된 국가의 데이터를 비율 순으로 정렬
    country_data_sorted = df_mbti.loc[selected_country].sort_values(ascending=False)
    
    # 100을 곱하고 소수점 2자리로 포맷
    formatted_data = (country_data_sorted * 100).round(2).reset_index()
    formatted_data.columns = ['MBTI 유형', '비율 (%)']

    # 비율에 따라 색상 하이라이트 적용 (Streamlit의 자체 스타일링)
    def highlight_max(s):
        is_max = s == s.max()
        # 1등 비율 셀만 빨간색으로 하이라이트
        return ['background-color: #ffcccc' if v else '' for v in is_max]
    
    st.dataframe(
        formatted_data.style.apply(highlight_max, subset=['비율 (%)']),
        use_container_width=True
    )
    
    st.caption("비율은 소수점 둘째 자리에서 반올림하여 퍼센트로 표시됩니다.")
    
# ----------------------------------------------------------------------
# 4. 데이터 출처 및 정보
# ----------------------------------------------------------------------

st.markdown("---")
st.sidebar.markdown("""
### 정보
이 앱은 사용자가 선택한 국가의 MBTI 유형별 비율을 보여줍니다.
- **데이터 출처**: 사용자 업로드 파일 (`countriesMBTI_16types.csv`)
- **개발**: Gemini
""")

# ----------------------------------------------------------------------
