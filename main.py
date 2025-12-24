import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

# ======================================================
# 페이지 설정
# ======================================================
st.set_page_config(
    page_title="극지식물 EC–환경–생육 통합 분석",
    layout="wide"
)

# ======================================================
# 한글 폰트 + 다크/라이트 모드 대응 CSS
# ======================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}

.section {
    padding: 1.2rem;
    border-radius: 14px;
    margin-bottom: 1.5rem;
    line-height: 1.65;
}

[data-theme="light"] .section {
    background-color: #f8f9fa;
    color: #212529;
}

[data-theme="dark"] .section {
    background-color: #1e1e1e;
    color: #f1f3f5;
    border: 1px solid #2f2f2f;
}

.highlight {
    padding: 0.8rem;
    border-radius: 10px;
    font-weight: 600;
}

[data-theme="light"] .highlight {
    background-color: #e6f4ea;
    color: #1b4332;
}

[data-theme="dark"] .highlight {
    background-color: #12372a;
    color: #d8f3dc;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# 경로 설정
# ======================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# ======================================================
# NFC/NFD 안전 파일 탐색
# ======================================================
def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text)

def find_file(keyword: str):
    if not DATA_DIR.exists():
        return None

    for file in DATA_DIR.iterdir():
        if normalize(keyword) in normalize(file.name):
            return file
    return None

# ======================================================
# 데이터 로딩
# ======================================================
@st.cache_data
def load_env_data(school: str):
    file = find_file(f"{school}_환경데이터")
    if file is None:
        return None
    return pd.read_csv(file)

@st.cache_data
def load_growth_data():
    file = find_file("생육결과데이터")
    if file is None:
        return None
    return pd.read_excel(file, sheet_name=None)

# ======================================================
# 사이드바
# ======================================================
st.sidebar.title("분석 설정")
school_option = st.sidebar.selectbox(
    "학교 선택",
    ["송도고", "하늘고", "아라고", "동산고"]
)

# ======================================================
# 제목
# ======================================================
st.title("🌱 극지식물 EC–환경–생육 통합 분석")

st.markdown("""
<div class="section">
본 대시보드는 극지식물 <b>나도수영</b>의 생육에 영향을 미치는  
<b>EC(전기전도도), pH, 환경 요인, 광주기</b>를 통합적으로 분석한다.  
특히 EC–pH의 상관관계와 EC 조건에 따른 생육 차이를 중심으로 해석한다.
</div>
""", unsafe_allow_html=True)

# ======================================================
# 탭 구성
# ======================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 환경 변화 (송도고)",
    "🔗 EC–pH 상관 분석",
    "⚖️ EC–생육 결과 비교",
    "💡 광주기 가설"
])

# ======================================================
# TAB 1: 송도고 환경 변화
# ======================================================
with tab1:
    df_env = load_env_data("송도고")

    if df_env is None:
        st.error("송도고 환경 데이터를 찾을 수 없습니다.")
    else:
        st.markdown("""
        <div class="section">
        송도고의 온도, 습도, EC, pH는 시간에 따라 연속적으로 측정되었다.  
        이를 통해 환경 변수 간 동시 변화 양상을 관찰할 수 있다.
        </div>
        """, unsafe_allow_html=True)

        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=["온도", "습도", "EC", "pH"]
        )

        fig.add_trace(go.Scatter(x=df_env["time"], y=df_env["temperature"]), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_env["time"], y=df_env["humidity"]), row=1, col=2)
        fig.add_trace(go.Scatter(x=df_env["time"], y=df_env["ec"]), row=2, col=1)
        fig.add_trace(go.Scatter(x=df_env["time"], y=df_env["ph"]), row=2, col=2)

        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ======================================================
# TAB 2: EC–pH 상관 분석
# ======================================================
with tab2:
    if df_env is None:
        st.error("환경 데이터가 없습니다.")
    else:
        corr = df_env["ec"].corr(df_env["ph"])

        st.markdown(f"""
        <div class="section">
        EC와 pH 사이의 피어슨 상관계수는  
        <b>r = {corr:.3f}</b>로 계산되었다.  
        이는 EC가 증가할수록 pH가 감소하는 음의 상관관계를 의미한다.
        </div>
        """, unsafe_allow_html=True)

        fig_scatter = px.scatter(
            df_env,
            x="ec",
            y="ph",
            title="EC–pH 산점도"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

# ======================================================
# TAB 3: EC–생육 결과 비교
# ======================================================
with tab3:
    growth_data = load_growth_data()

    if growth_data is None:
        st.error("생육 결과 데이터를 찾을 수 없습니다.")
    else:
        ec_map = {
            "송도고": 1.0,
            "하늘고": 2.0,
            "아라고": 4.0,
            "동산고": 8.0
        }

        rows = []
        for school, gdf in growth_data.items():
            if "생중량(g)" not in gdf.columns:
                continue

            rows.append({
                "학교": school,
                "EC": ec_map.get(school, None),
                "평균 생중량(g)": gdf["생중량(g)"].mean()
            })

        result_df = pd.DataFrame(rows)

        st.markdown("""
        <div class="section">
        EC가 증가함에 따라 생육이 촉진되다가,  
        고농도 EC 조건에서는 삼투 스트레스로 인해 생중량이 감소하는 경향을 보인다.
        </div>
        """, unsafe_allow_html=True)

        fig_bar = px.bar(
            result_df,
            x="학교",
            y="평균 생중량(g)",
            color="EC",
            title="EC 조건별 평균 생중량 비교"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # 다운로드 (완전 안전)
        buffer = io.BytesIO()
        result_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            label="📥 EC별 평균 생중량 결과 다운로드",
            data=buffer.getvalue(),
            file_name="EC별_평균생중량_결과.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ======================================================
# TAB 4: 광주기 가설
# ======================================================
with tab4:
    st.markdown("""
    <div class="section">
    광주기는 식물의 광합성 효율과 생체 리듬을 조절하는 핵심 변수이다.  
    극지식물은 장일 환경에 적응했을 가능성이 높으며,  
    동일한 EC 조건에서도 광주기 차이가 생육 결과에 영향을 줄 수 있다.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="highlight">
    🔬 후속 실험 제안  
    • EC 조건 고정  
    • 광주기 8h / 12h / 16h 비교  
    • 생중량·잎 수·생장률 동시 분석
    </div>
    """, unsafe_allow_html=True)
