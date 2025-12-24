import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from pathlib import Path
import unicodedata
import io

# ======================================================
# 기본 설정
# ======================================================
st.set_page_config(
    page_title="극지식물 EC–환경–생육 통합 분석",
    layout="wide"
)

# ======================================================
# 한글 폰트 + 다크/라이트 UI 완전 대응 CSS
# ======================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}

/* 공통 카드 */
.section {
    padding: 1.3rem;
    border-radius: 14px;
    margin-bottom: 1.5rem;
    line-height: 1.65;
}

/* 라이트 모드 */
[data-theme="light"] .section {
    background-color: #f8f9fa;
    color: #212529;
}

/* 다크 모드 */
[data-theme="dark"] .section {
    background-color: #1e1e1e;
    color: #f1f3f5;
    border: 1px solid #2f2f2f;
}

/* 강조 박스 */
.highlight {
    padding: 0.8rem;
    border-radius: 10px;
    font-weight: 600;
}

/* 라이트 */
[data-theme="light"] .highlight {
    background-color: #e6f4ea;
    color: #1b4332;
}

/* 다크 */
[data-theme="dark"] .highlight {
    background-color: #12372a;
    color: #d8f3dc;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# 데이터 경로 탐색 (NFC/NFD 완전 대응)
# ======================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def normalize(text):
    return unicodedata.normalize("NFC", text)

def find_file(keyword):
    for file in DATA_DIR.iterdir():
        if normalize(keyword) in normalize(file.name):
            return file
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
<b>EC(전기전도도), pH, 환경 요인, 광주기</b>를 종합적으로 분석한다.  
학교별로 상이한 EC 조건을 비교하여 <b>최적 생육 구간</b>을 도출하는 것을 목표로 한다.
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
        송도고의 온도, 습도, EC, pH는 시간에 따라 연속적으로 측정되었다.  
        이를 통해 환경 변수 간 <b>동시 변화 양상</b>을 관찰할 수 있다.
        </div>
        """, unsafe_allow_html=True)

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=["온도", "습도", "EC", "pH"]
        )

        fig.add_trace(go.Scatter(x=df["time"], y=df["temperature"], name="온도"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["time"], y=df["humidity"], name="습도"), row=1, col=2)
        fig.add_trace(go.Scatter(x=df["time"], y=df["ec"], name="EC"), row=2, col=1)
        fig.add_trace(go.Scatter(x=df["time"], y=df["ph"], name="pH"), row=2, col=2)

        fig.update_layout(
            height=600,
            showlegend=False,
            font=dict(family="Malgun Gothic")
        )

        st.plotly_chart(fig, use_container_width=True)

# ======================================================
# TAB 2: EC–pH 상관 분석
# ======================================================
with tab2:
    if df is None:
        st.error("데이터가 없습니다.")
    else:
        st.markdown("""
        <div class="section">
        EC 증가에 따라 pH가 감소하는 <b>강한 음의 상관관계</b>가 관찰된다.  
        이는 용액 내 이온 농도 증가가 H⁺ 농도 변화와 연동되기 때문이다.
        </div>
        """, unsafe_allow_html=True)

        fig_scatter = px.scatter(
            df,
            x="ec",
            y="ph",
            trendline="lowess",
            title="EC–pH 상관관계"
        )

        fig_scatter.update_layout(font=dict(family="Malgun Gothic"))
        st.plotly_chart(fig_scatter, use_container_width=True)

# ======================================================
# TAB 3: EC–생육 결과
# ======================================================
with tab3:
    growth = load_growth_data()
    if growth is None:
        st.error("생육 결과 데이터가 없습니다.")
    else:
        records = []
        ec_map = {
            "송도고": 1.0,
            "하늘고": 2.0,
            "아라고": 4.0,
            "동산고": 8.0
        }

        for school, df_g in growth.items():
            records.append({
                "학교": school,
                "EC": ec_map.get(school),
                "평균 생중량": df_g["생중량(g)"].mean()
            })

        result_df = pd.DataFrame(records)

        st.markdown("""
        <div class="section">
        EC가 지나치게 높아질 경우 삼투 스트레스로 인해 생중량이 감소한다.  
        <b>하늘고(EC 2.0)</b> 조건에서 가장 안정적인 생육 결과가 나타난다.
        </div>
        """, unsafe_allow_html=True)

        fig_bar = px.bar(
            result_df,
            x="학교",
            y="평균 생중량",
            color="EC",
            title="EC 조건별 평균 생중량 비교"
        )
        fig_bar.update_layout(font=dict(family="Malgun Gothic"))
        st.plotly_chart(fig_bar, use_container_width=True)

        buffer = io.BytesIO()
        result_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            data=buffer,
            file_name="EC별_평균생중량_결과.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ======================================================
# TAB 4: 광주기 가설 분석
# ======================================================
with tab4:
    st.markdown("""
    <div class="section">
    <b>광주기(빛의 조사 시간)</b>는 식물의 발아 및 생장 조절 호르몬에 직접적인 영향을 미친다.  
    극지 환경에서는 긴 일조 시간에 적응한 식물이  
    <b>일정 임계값 이상의 광주기</b>에서 생장 효율이 급격히 증가할 가능성이 있다.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="highlight">
    🔬 향후 실험 제안  
    - EC 조건 고정  
    - 광주기 8h / 12h / 16h 비교  
    - 생중량 + 잎 수 + 생장률 동시 측정
    </div>
    """, unsafe_allow_html=True)
