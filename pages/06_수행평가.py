# --- 파일 로드 안전 처리: pages/06_수행평가.py에 이 블록으로 대체하세요.
from pathlib import Path
import pandas as pd
import streamlit as st

CSV_FILENAME = "Seoul Metropolitan City_COVID-19 Vaccination Status.csv"

# pages/ 에서 실행될 때 repo root의 파일을 가리키는 안전한 후보 경로들
possible_paths = [
    # pages 폴더의 한 단계 위(레포 루트)에 있을 경우
    Path(__file__).resolve().parents[1] / CSV_FILENAME,
    # 이 세션/환경에서 보였던 절대 경로 (주의: Cloud에선 보장되지 않음)
    Path("/mnt/data") / CSV_FILENAME,
    # 현재 작업 디렉토리에서 직접 찾기
    Path(CSV_FILENAME),
    Path("./data") / CSV_FILENAME,
]

def read_csv_if_exists(path_obj):
    """경로가 있으면 인코딩 순서대로 읽어 반환, 없으면 None."""
    if not path_obj or not path_obj.exists():
        return None, None
    for enc in ["cp949", "utf-8", "euc-kr", "latin1"]:
        try:
            df = pd.read_csv(path_obj, encoding=enc)
            return df, enc
        except Exception:
            continue
    return None, None

# 1) 후보 경로 탐색
df = None
used_path = None
used_enc = None
for p in possible_paths:
    d, enc = read_csv_if_exists(p)
    if d is not None:
        df = d
        used_path = str(p)
        used_enc = enc
        break

# 2) 못 찾으면 업로더로 처리
if df is None:
    st.warning("레포/서버에서 CSV를 찾지 못했습니다. 아래에서 CSV 파일을 업로드해주세요.")
    uploaded = st.file_uploader("CSV 파일 업로드", type=["csv"])
    if uploaded is None:
        st.stop()  # 업로드가 없으면 앱을 더 이상 진행하지 않음
    # 업로드된 파일은 pandas로 직접 시도
    success = False
    for enc in [None, "cp949", "utf-8", "euc-kr", "latin1"]:
        try:
            if enc is None:
                df = pd.read_csv(uploaded)
            else:
                uploaded.seek(0)
                df = pd.read_csv(uploaded, encoding=enc)
            used_path = "uploaded_file"
            used_enc = enc or "pandas-detect"
            success = True
            break
        except Exception:
            continue
    if not success:
        st.error("업로드한 파일을 읽지 못했습니다. 다른 인코딩(예: cp949)으로 저장된 CSV인지 확인하세요.")
        st.stop()

st.success(f"데이터 로드 성공 — 소스: {used_path} (encoding={used_enc})")
# 이후 기존 코드에서 df를 그대로 사용하시면 됩니다.
