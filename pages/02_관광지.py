import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

st.set_page_config(page_title="서울 인기 관광지 Top 10 (외국인 선호)", layout="wide")

st.title("🇰🇷 서울 인기 관광지 Top 10 (외국인 선호)")
st.caption("Folium 지도로 보는 위치 — Streamlit Cloud에서 바로 실행 가능")

# Top 10 places (commonly favored by international visitors)
spots = [
    {
        "name": "경복궁 (Gyeongbokgung Palace)",
        "lat": 37.5796, "lon": 126.9770,
        "desc": "조선의 법궁. 근정전, 경회루가 유명하며 한복 체험과 함께 많이 방문합니다."
    },
    {
        "name": "북촌한옥마을 (Bukchon Hanok Village)",
        "lat": 37.5826, "lon": 126.9830,
        "desc": "전통 한옥이 밀집한 마을로 골목 산책과 사진 촬영 명소."
    },
    {
        "name": "명동 쇼핑거리 (Myeongdong Shopping Street)",
        "lat": 37.5636, "lon": 126.9850,
        "desc": "코스메틱과 길거리 음식으로 유명한 대표 쇼핑 거리."
    },
    {
        "name": "남산 N서울타워 (N Seoul Tower)",
        "lat": 37.5512, "lon": 126.9882,
        "desc": "서울 전경을 조망할 수 있는 랜드마크 전망대."
    },
    {
        "name": "인사동 문화거리 (Insadong)",
        "lat": 37.5740, "lon": 126.9853,
        "desc": "전통 공예품과 갤러리, 찻집이 모여 있는 문화 거리."
    },
    {
        "name": "홍대거리 (Hongdae / Hongik Univ. Area)",
        "lat": 37.5563, "lon": 126.9220,
        "desc": "스트리트 퍼포먼스, 클럽, 카페, 개성 있는 상점이 즐비한 젊음의 거리."
    },
    {
        "name": "동대문디자인플라자 DDP (Dongdaemun Design Plaza)",
        "lat": 37.5667, "lon": 127.0094,
        "desc": "자하 하디드가 설계한 아이코닉 건축물. 전시·패션·야시장과 가깝습니다."
    },
    {
        "name": "롯데월드타워 & 석촌호수 (Lotte World Tower & Seokchon Lake)",
        "lat": 37.5130, "lon": 127.1025,
        "desc": "555m 초고층 전망과 석촌호수 산책로, 쇼핑·엔터테인먼트 집약지."
    },
    {
        "name": "광장시장 (Gwangjang Market)",
        "lat": 37.5701, "lon": 127.0001,
        "desc": "빈대떡·마약김밥 등 길거리 음식으로 유명한 재래시장."
    },
    {
        "name": "청계천 (Cheonggyecheon Stream)",
        "lat": 37.5690, "lon": 126.9789,
        "desc": "도심 속 산책로. 야간 조명이 아름답고 광화문·종로와 인접."
    },
]

# Sidebar controls
st.sidebar.header("표시 설정")
default_center = [37.5665, 126.9780]  # 서울 시청 인근
zoom = st.sidebar.slider("초기 확대(Zoom)", min_value=10, max_value=16, value=12)
use_cluster = st.sidebar.checkbox("마커 클러스터 사용", value=True)
selected = st.sidebar.multiselect(
    "보여줄 장소 선택 (미선택 시 전체)",
    options=[s["name"] for s in spots],
    default=[s["name"] for s in spots],
)

# Initialize map
m = folium.Map(location=default_center, zoom_start=zoom, tiles="CartoDB positron", control_scale=True)

if use_cluster:
    cluster = MarkerCluster(name="관광지").add_to(m)
else:
    cluster = m  # add markers directly to map

# Add markers
for s in spots:
    if selected and s["name"] not in selected:
        continue
    popup_html = f"""
    <div style='min-width:220px'>
        <h4 style='margin:0 0 6px 0'>{s["name"]}</h4>
        <p style='margin:0'>{s["desc"]}</p>
        <hr style='margin:6px 0'>
        <small>위치: {s["lat"]:.4f}, {s["lon"]:.4f}</small>
    </div>
    """
    folium.CircleMarker(
        location=[s["lat"], s["lon"]],
        radius=7,
        weight=2,
        fill=True,
        fill_opacity=0.8,
        tooltip=s["name"],
        color="#2b8a3e",
    ).add_to(cluster)
    folium.Marker(
        location=[s["lat"], s["lon"]],
        tooltip=s["name"],
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(icon="star", prefix="fa"),
    ).add_to(cluster)

folium.LayerControl().add_to(m)

# Render map
st_data = st_folium(m, width="100%", height=650)

st.markdown("---")
st.subheader("사용 방법")
st.markdown(
    """
1) 이 저장소를 Streamlit Cloud에 업로드하거나, \
**`app.py`와 `requirements.txt`** 두 파일을 업로드하세요.  
2) 앱 엔트리 포인트는 기본값(`app.py`)이면 됩니다.  
3) 실행 후 사이드바에서 확대/축소, 클러스터, 표시에 포함할 장소를 조절할 수 있어요.
"""
)

st.caption("© 서울 좌표는 공개 자료를 참고한 대략값으로, 현장과 오차가 있을 수 있습니다.")
