# pages/06_수행평가.py — 파일 읽기 부분을 이 코드로 대체하세요.
import streamlit as st
import pandas as pd
import os
from pathlib import Path

st.set_page_config(layout="wide")

# 1) 파일명(정확히 맞춰야 합니다)
CSV_FILENAME = "Seoul Metropolitan City_COVID-19 Vaccination Status.csv"

# 2) 가능한 경로들 (pages/ 에서 실행될 때를 고려)
possible_paths = [
    # 1) 앱 루트(레포 루트)에 있는 경우 (pages 폴더에서 한 단계 위)
    Path(__file__).resolve().parents[1] / CSV_FILENAME,
    # 2) 절대경로 (세션에서 파일이 있던 경로)
    Path("/mnt/data") / CSV_FILENAME,
    # 3) 현재 작업 디렉토리 (안전장치)
    Path(CSV_FILENAME),
    Path("./data") / CSV_FILENAME,
]

@st.cache_data
def load_data():
    last_exc = None
    for p in possible_paths:
        try:
            if p.exists():
                # 여러 인코딩 순차 시도
                for enc in ["utf-8", "cp949", "euc-kr", "latin1"]:
                    try:
                        df = pd.read_csv(p, encoding=enc)
                        return df, str(p), enc
                    except Exception:
                        continue
            else:
                # p might be a str path if constructed differently
                continue
        except Exception as e:
            last_exc = e
            continue
    # 못 찾으면 None 반환 (호출부에서 업로더로 처리)
    return None, None, None

# 실제 로딩 시도
df, used_path, used_enc = load_data()
if df is None:
    st.warning("레포/서버에서 CSV를 찾지 못했습니다. 아래에서 CSV 파일을 업로드해주세요.")
    uploaded = st.file_uploader("CSV 파일 업로드", type=["csv"])
    if uploaded is None:
        st.stop()
    # 업로드된 파일 읽기 (인코딩 시도)
    success = False
    for enc in [None, "cp949", "euc-kr", "utf-8", "latin1"]:
        try:
            if enc is None:
                df = pd.read_csv(uploaded)
            else:
                uploaded.seek(0)
                df = pd.read_csv(uploaded, encoding=enc)
            used_enc = enc or "pandas-detect"
            used_path = "uploaded_file"
            success = True
            break
        except Exception:
            continue
    if not success:
        st.error("업로드한 파일을 읽는 데 실패했습니다. 다른 인코딩(또는 CSV 포맷)을 확인하세요.")
        st.stop()

st.success(f"데이터 로드 성공 — 소스: {used_path} (encoding={used_enc})")

# 이후 df를 기존 코드대로 사용하면 됩니다.
