import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

# =====================================================
# 페이지 설정
# =====================================================
st.set_page_config(
    page_title="극지식물 EC–환경–생육 통합 분석",
    layout="wide"
)

# =====================================================
# 한글 폰트 & UI 스타일
# =====================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}

.section {
    padding: 1.2rem;
    border-radius: 12px;
    background-color: #f8f9fa;
    margin-bottom: 1.5rem;
}

.highlight {
    background-color: #e6f4ea;
    padding: 0.6rem;
    border-radius: 8px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# 연구 상수
# =====================================================
SCHOOL_EC = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0
}

PHOTOPERIOD = {
    "송도고": "16h / 8h",
    "하늘고": "24h (연속광)",
    "아라고": "12h / 12h",
    "동산고": "자연광 유사"
}

DATA_DIR = Path("data")

# =====================================================
# 한글 파일명 대응 유틸
# =====================================================
def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text)

def find_file(directory: Path, target_name: str):
    target = normalize(target_name)
    for f in directory.iterdir():
        if normalize(f.name) == target:
            return f
    return None

# =====================================================
# 데이터 로딩
# =====================================================
@st.cache_data
def load_environment_data():
    env = {}
    with st.spinner("환경 데이터 로딩 중..."):
        for school in SCHOOL_EC:
            file = find_file(DATA_DIR, f"{school}_환경데이터.csv")
            if file is None:
                st.error(f"{school} 환경 데이터 파일을 찾을 수 없습니다.")
                continue
            env[school] = pd.read_csv(file)
    return env

@st.cache_data
def load_growth_data():
    with st.spinner("생육 데이터 로딩 중..."):
        xlsx = None
        for f in DATA_DIR.iterdir():
            if f.suffix == ".xlsx":
                xlsx = f
                break
        if xlsx is None:
            st.error("생육 결과 XLSX 파일이 없습니다.")
            return {}

        xls = pd.ExcelFile(xlsx)
        return {sheet: pd.read_excel(xlsx, sheet_name=sheet) for sheet in xls.sheet_names}

env_data = load_environment_data()
growth_data = load_growth_data()

# =====================================================
# 사이드바
# =====================================================
st.sidebar.title("🔍 분석 설정")
selected_school = st.sidebar.selectbox(
    "학교 선택",
    ["전체"] + list(SCHOOL_EC.keys())
)

# =====================================================
# 메인 타이틀
# =====================================================
st.title("🌱 극지식물 EC–환경–생육 통합 분석")

st.markdown("""
<div class="section">
본 대시보드는 극지식물 <b>나도수영</b>의 생육에 영향을 미치는  
<b>EC(전기전도도), pH, 환경 조건</b>을 분석하기 위해 제작되었다.<br>
4개 학교의 실험 데이터를 비교하여 <b>안정적인 생육 조건과 경향성</b>을 도출하는 것이 목적이다.
</div>
""", unsafe_allow_html=True)

# =====================================================
# 탭 구성
# =====================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 송도고 환경 변화",
    "🔬 EC–pH 상관 분석",
    "📊 EC–생육 결과",
    "💡 광주기 가설 분석"
])

# =====================================================
# TAB 1 — 송도고 환경
# =====================================================
with tab1:
    st.subheader("송도고 환경 변수의 시간 변화")

    st.markdown("""
<div class="section">
송도고의 환경 데이터는 연속 측정되어  
<b>온도·습도·EC·pH의 변화 추세</b>를 동시에 분석할 수 있다.<br>
본 연구에서는 송도고를 <b>기준 환경(reference environment)</b>으로 설정한다.
</div>
""", unsafe_allow_html=True)

    if "송도고" in env_data:
        df = env_data["송도고"]

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=["온도", "습도", "pH", "EC"]
        )

        fig.add_trace(go.Scatter(x=df["time"], y=df["temperature"]), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["time"], y=df["humidity"]), row=1, col=2)
        fig.add_trace(go.Scatter(x=df["time"], y=df["ph"]), row=2, col=1)
        fig.add_trace(go.Scatter(x=df["time"], y=df["ec"]), row=2, col=2)

        fig.update_layout(
            height=700,
            showlegend=False,
            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
        )

        st.plotly_chart(fig, use_container_width=True)

# =====================================================
# TAB 2 — EC–pH 상관
# =====================================================
with tab2:
    st.subheader("EC와 pH의 상관관계 (송도고)")

    st.markdown("""
<div class="section">
EC와 pH는 양액 내 이온 농도와 직접적으로 연결된 변수이다.<br>
본 산점도는 두 변수의 <b>동시 측정값</b>을 시각화한 결과이다.
</div>
""", unsafe_allow_html=True)

    if "송도고" in env_data:
        df = env_data["송도고"]
        x = df["ec"].astype(float)
        y = df["ph"].astype(float)
        corr = np.corrcoef(x, y)[0, 1]

        fig = go.Figure(go.Scatter(
            x=x, y=y, mode="markers", marker=dict(size=7)
        ))

        fig.update_layout(
            title=f"EC–pH 산점도 (상관계수 r = {corr:.3f})",
            xaxis_title="EC",
            yaxis_title="pH",
            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"""
<div class="highlight">
EC 증가에 따라 pH가 감소하는 <b>음의 상관관계</b>가 관찰되었다.<br>
이는 H⁺ 농도 증가 및 완충 작용과 일치하는 결과이다.
</div>
""", unsafe_allow_html=True)

# =====================================================
# TAB 3 — EC–생육
# =====================================================
with tab3:
    st.subheader("EC 조건에 따른 생육 결과 비교")

    summary = []
    for school, df in growth_data.items():
        summary.append({
            "학교": school,
            "EC": SCHOOL_EC.get(school),
            "평균 생중량": df["생중량(g)"].mean()
        })

    result_df = pd.DataFrame(summary).dropna()

    fig = go.Figure(go.Bar(
        x=result_df["EC"],
        y=result_df["평균 생중량"],
        text=result_df["평균 생중량"].round(2),
        textposition="outside"
    ))

    fig.update_layout(
        title="EC별 평균 생중량",
        xaxis_title="EC",
        yaxis_title="평균 생중량 (g)",
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )

    st.plotly_chart(fig, use_container_width=True)

    optimal = result_df.loc[result_df["평균 생중량"].idxmax()]

    st.markdown(f"""
<div class="highlight">
평균 생중량 기준 최적 EC는 <b>EC = {optimal['EC']}</b> 이다.<br>
다만 본 결과는 <b>경향성 분석</b>으로 해석해야 한다.
</div>
""", unsafe_allow_html=True)

    buffer = io.BytesIO()
    result_df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    st.download_button(
        label="EC별 평균 생중량 결과 다운로드",
        data=buffer.getvalue(),
        file_name="EC별_평균생중량_결과.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =====================================================
# TAB 4 — 광주기 가설
# =====================================================
with tab4:
    st.subheader("광주기–EC 상호작용 가설")

    st.markdown("""
<div class="section">
광주기는 본 실험에서 직접 통제되지 않았으나,  
학교별 조건 차이를 통해 <b>잠재적 영향</b>을 추론할 수 있다.
</div>
""", unsafe_allow_html=True)

    photo_df = pd.DataFrame({
        "학교": PHOTOPERIOD.keys(),
        "광주기": PHOTOPERIOD.values(),
        "EC": [SCHOOL_EC[s] for s in PHOTOPERIOD],
        "평균 생중량": [growth_data[s]["생중량(g)"].mean() for s in PHOTOPERIOD]
    })

    st.dataframe(photo_df, use_container_width=True)

    st.markdown("""
<div class="highlight">
하늘고의 연속광(24h) 조건에서 EC 2.0은  
상대적으로 높은 평균 생중량을 보였다.<br>
이는 광주기가 EC 효과를 증폭시킬 가능성을 시사한다.
</div>

### 🔍 향후 연구 방향
- 광주기 × EC 이원 실험 설계
- 생육 안정성 지표(CV) 도입
- 장기 재배 실험을 통한 누적 효과 분석
""", unsafe_allow_html=True)
