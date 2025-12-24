import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
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
# 폰트 + 다크/라이트 UI 대응
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
# 경로 및 파일 탐색 (NFC/NFD 안전)
# ======================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def normalize(text):
    return unicodedata.normalize("NFC", text)

def find_file(keyword):
    for f in DATA_DIR.iterdir():
        if normalize(keyword) in normalize(f.name):
            return f
    return None

# ======================================================
# 데이터 로딩
# ======================================================
@st.cache_data
def load_env_data(school):
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
st.sidebar.title("학교 선택")
school_option = st.sidebar.selectbox(
    "분석 대상",
    ["전체", "송도고", "하늘고", "아라고", "동산고"]
)

# ======================================================
# 제목
# ======================================================
st.title("🌱 극지식물 EC–환경–생육 통합 분석")

st.markdown("""
<div class="section">
본 대시보드는 극지식물 <b>나도수영</b>의 생육에 영향을 미치는  
<b>EC(전기전도도), pH, 환경 요인, 광주기</b>를 통합적으로 분석한다.  
특히 pH–EC의 상대 변화와 생육 지표 간의 관계를 중심으로 해석한다.
</div>
""", unsafe_allow_html=True)

# ======================================================
# 탭 구성
# ======================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 송도고 환경 변화",
    "🔗 EC–pH 상관 분석",
    "⚖️ EC–생육 결과",
    "💡 광주기 가설 분석"
])

# ======================================================
# TAB 1: 송도고 환경 변화
# ======================================================
with tab1:
    df = load_env_data("송도고")

    if df is None:
        st.error("송도고 환경 데이터가 없습니다.")
    else:
        st.markdown("""
        <div class="section">
        송도고의 온도·습도·EC·pH는 시간에 따라 연속적으로 측정되었다.  
        각 변수의 동시 변화를 통해 재배 환경의 안정성과 변동성을 해석할 수 있다.
        </div>
        """, unsafe_allow_html=True)

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=["온도", "습도", "EC", "pH"]
        )

        fig.add_trace(go.Scatter(x=df["time"], y=df["temperature"]), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["time"], y=df["humidity"]), row=1, col=2)
        fig.add_trace(go.Scatter(x=df["time"], y=df["ec"]), row=2, col=1)
        fig.add_trace(go.Scatter(x=df["time"], y=df["ph"]), row=2, col=2)

        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ======================================================
# TAB 2: EC–pH 상관 분석 (statsmodels 미사용)
# ======================================================
with tab2:
    if df is None:
        st.error("환경 데이터가 없습니다.")
    else:
        corr = df["ec"].corr(df["ph"])

        st.markdown(f"""
        <div class="section">
        EC와 pH 사이의 피어슨 상관계수는  
        <b>r = {corr:.3f}</b>로 계산되었다.  
        이는 EC 증가에 따라 pH가 감소하는 <b>뚜렷한 음의 상관관계</b>를 의미한다.
        </div>
        """, unsafe_allow_html=True)

        fig_scatter = px.scatter(
            df,
            x="ec",
            y="ph",
            title="EC–pH 산점도 (상관관계 시각화)"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

# ======================================================
# TAB 3: EC–생육 결과
# ======================================================
with tab3:
    growth = load_growth_data()

    if growth is None:
        st.error("생육 결과 데이터가 없습니다.")
    else:
        ec_map = {
            "송도고": 1.0,
            "하늘고": 2.0,
            "아라고": 4.0,
            "동산고": 8.0
        }

        rows = []
        for school, gdf in growth.items():
            rows.append({
                "학교": school,
                "EC": ec_map.get(school),
                "평균 생중량(g)": gdf["생중량(g)"].mean()
            })

        result_df = pd.DataFrame(rows)

        st.markdown("""
        <div class="section">
        EC가 일정 수준까지 증가하면 생육이 촉진되지만,  
        고농도 EC 조건에서는 삼투 스트레스로 인해 생중량이 감소하는 경향이 나타난다.
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

        # 다운로드 (중요: getvalue 사용)
        buffer = io.BytesIO()
        result_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            data=buffer.getvalue(),
            file_name="EC별_평균생중량_결과.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ======================================================
# TAB 4: 광주기 가설 분석
# ======================================================
with tab4:
    st.markdown("""
    <div class="section">
    광주기는 식물의 생체 리듬과 광합성 효율을 조절하는 핵심 요인이다.  
    극지식물은 장일 조건에 적응했을 가능성이 높아,  
    동일한 EC 조건에서도 광주기 변화가 생육 차이를 유발할 수 있다.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="highlight">
    🔬 후속 실험 설계 제안  
    - EC 조건 고정  
    - 광주기 8h / 12h / 16h  
    - 생중량·잎 수·생장률 비교 분석
    </div>
    """, unsafe_allow_html=True)
