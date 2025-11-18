# streamlit_app_plotly.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(layout="centered", page_title="Vaccination Rates - Plotly")

CSV_NAME = "Seoul Metropolitan City_COVID-19 Vaccination Status.csv"

@st.cache_data
def load_csv(path):
    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding='cp949')
    except Exception as e:
        st.error(f"파일을 불러오는 중 오류가 발생했습니다: {e}")
        return None

st.title("서울시 코로나19 접종 비율 (Plotly 인터랙티브 막대그래프)")
st.markdown("가장 최신 날짜 기준으로 접종 비율(%)을 막대그래프로 표시합니다. 업로드하거나 기본 파일을 사용하세요.")

uploaded = st.file_uploader("CSV 파일 업로드 (선택)", type="csv")
if uploaded is not None:
    df = load_csv(uploaded)
else:
    data_path = Path(CSV_NAME)
    if not data_path.exists():
        st.warning(f"기본 CSV 파일이 서버에 없습니다. 업로드하거나 '{CSV_NAME}' 를 프로젝트 루트에 놓아주세요.")
        st.stop()
    df = load_csv(str(data_path))

if df is None:
    st.stop()

st.subheader("원본 데이터 미리보기")
st.dataframe(df.head(50))

# 날짜 열 자동 탐지
date_col = None
for col in df.columns:
    if any(k in col.lower() for k in ['date','접종일','일자','날짜','연도','기준']):
        date_col = col
        break
if date_col is None:
    # try to find a parseable column
    for col in df.columns:
        parsed = pd.to_datetime(df[col], errors='coerce')
        if parsed.notna().sum() / len(df) > 0.6:
            date_col = col
            break

if date_col:
    try:
        df[date_col + "_parsed"] = pd.to_datetime(df[date_col], errors='coerce')
        latest_row = df.loc[df[date_col + "_parsed"].idxmax()]
        latest_date = df[date_col + "_parsed"].max().date()
    except Exception:
        latest_row = df.iloc[-1]
        latest_date = None
else:
    latest_row = df.iloc[-1]
    latest_date = None

# 퍼센트 컬럼 검출: '률' 또는 '%' 또는 'rate' 포함
pct_cols = [c for c in df.columns if ('률' in c) or ('%' in c) or ('rate' in c.lower())]
# 일부 데이터셋은 "1차접종률(%)"처럼 명확히 되어 있으므로 우선 pct_cols 사용
if not pct_cols:
    st.error("데이터에서 '접종률' 계열의 컬럼을 찾지 못했습니다. 컬럼명에 '률' 또는 '%' 등이 포함되어 있는지 확인해 주세요.")
    st.stop()

# 최신 행에서 값 읽어서 정리
items = []
for c in pct_cols:
    val = latest_row.get(c, None)
    if pd.isna(val):
        continue
    # 문자열에 '%'가 포함된 경우 제거
    if isinstance(val, str) and '%' in val:
        try:
            vnum = float(val.replace('%','').replace(',','').strip())
        except:
            vnum = None
    else:
        try:
            vnum = float(val)
        except:
            vnum = None
    if vnum is not None:
        items.append((c, vnum))

if not items:
    st.error("선택된 퍼센트 컬럼에서 유효한 숫자 값을 찾을 수 없습니다.")
    st.stop()

plot_df = pd.DataFrame(items, columns=['label','value']).sort_values('value', ascending=False).reset_index(drop=True)

# 색상 세팅: 1등은 레드, 나머지는 블루 그라데이션 (투명도 차이로 표현)
red = "rgba(208,4,41,1)"  # 진한 빨강
base_blue_rgb = (2,62,138)
n_other = len(plot_df) - 1
blue_colors = []
if n_other > 0:
    # i=0 -> 가장 진한(투명도 높음) , i increase -> 점점 투명해짐
    for i in range(n_other):
        # alpha 범위: 0.95 -> 0.35 (대략)
        if n_other == 1:
            alpha = 0.8
        else:
            alpha = 0.95 - (i * (0.60 / (n_other - 1)))
        blue_colors.append(f"rgba({base_blue_rgb[0]},{base_blue_rgb[1]},{base_blue_rgb[2]},{alpha:.2f})")
colors = [red] + blue_colors

# Plotly 막대그래프 생성
fig = go.Figure(go.Bar(
    x=plot_df['label'],
    y=plot_df['value'],
    marker=dict(color=colors),
    text=[f"{v:.2f}%" for v in plot_df['value']],
    textposition='auto',
    hovertemplate="%{x}<br>비율: %{y:.2f}%<extra></extra>"
))
title = "접종 비율 비교 (가장 최신일자 기준)"
if latest_date is not None:
    title += f" — {latest_date.isoformat()}"
fig.update_layout(title=title, yaxis_title="비율 (%)", xaxis_title="접종 구분", template="simple_white")

st.plotly_chart(fig, use_container_width=True)

st.markdown("### 데이터 및 그래프 설명")
st.write("- 그래프는 데이터에서 `률`, `%`, 또는 `rate`가 컬럼명에 포함된 컬럼을 찾아 최신(가장 최근) 행의 값을 표시합니다.")
st.write("- 색상: 값이 가장 큰 항목을 빨간색으로 강조하고, 나머지는 파란색 계열로 투명도를 달리해 그라데이션처럼 보이게 했습니다.")
