import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io
import numpy as np

# =====================================================
# 기본 설정
# =====================================================
st.set_page_config(
    page_title="극지식물 EC–생육 상관 분석 플랫폼",
    layout="wide"
)

# 한글 폰트
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# 연구 상수 정의 (보고서 기준)
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
    "동산고": "자연광 근접"
}

SCHOOL_COLOR = {
    "송도고": "#4C72B0",
    "하늘고": "#55A868",
    "아라고": "#C44E52",
    "동산고": "#8172B2"
}

DATA_DIR = Path("data")

# =====================================================
# 파일 유틸
# =====================================================
def nfc(text):
    return unicodedata.normalize("NFC", text)

def find_file(directory: Path, filename: str):
    target = nfc(filename)
    for f in directory.iterdir():
        if nfc(f.name) == target:
            return f
    return None

# =====================================================
# 데이터 로딩
# =====================================================
@st.cache_data
def load_env():
    data = {}
    with st.spinner("환경 데이터 로딩 중…"):
        for school in SCHOOL_EC:
            path = find_file(DATA_DIR, f"{school}_환경데이터.csv")
            if path is None:
                st.error(f"{school} 환경 데이터 누락")
                continue
            df = pd.read_csv(path)
            data[school] = df
    return data

@st.cache_data
def load_growth():
    with st.spinner("생육 결과 로딩 중…"):
        xlsx = None
        for f in DATA_DIR.iterdir():
            if f.suffix == ".xlsx":
                xlsx = f
                break
        if xlsx is None:
            st.error("생육 결과 XLSX 없음")
            return {}

        xls = pd.ExcelFile(xlsx)
        return {sheet: pd.read_excel(xlsx, sheet_name=sheet) for sheet in xls.sheet_names}

env = load_env()
growth = load_growth()

# =====================================================
# 사이드바
# =====================================================
st.sidebar.title("분석 옵션")
school_sel = st.sidebar.selectbox(
    "학교 선택",
    ["전체"] + list(SCHOOL_EC.keys())
)

# =====================================================
# 제목
# =====================================================
st.title("🌱 극지식물 EC–환경–생육 통합 분석 대시보드")

# =====================================================
# 탭 구성
# =====================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📖 연구 개요",
    "🌡️ 환경 데이터 해석",
    "📊 EC–생육 정량 분석",
    "💡 광주기 확장 가설"
])

# =====================================================
# TAB 1 — 연구 개요
# =====================================================
with tab1:
    st.subheader("연구 설계 개요")

    st.markdown("""
본 연구는 극지식물 **나도수영**의 생육을 결정하는 주요 환경 변수 중  
**EC(Electrical Conductivity)**가 생육에 미치는 영향을 정량적으로 분석한다.

특히 EC를 단독 원인이 아닌,  
**pH·온도·습도·광주기와 상호작용하는 조건 변수**로 가정하였다.

송도고의 환경 조건은 변동성이 작고 연속 측정이 가능했기 때문에  
본 연구에서는 이를 **비교 기준(reference environment)**으로 설정하였다.
""")

    overview = pd.DataFrame({
        "학교": SCHOOL_EC.keys(),
        "EC 조건": SCHOOL_EC.values(),
        "광주기": [PHOTOPERIOD[s] for s in SCHOOL_EC],
        "개체 수": [len(growth.get(s, [])) for s in SCHOOL_EC]
    })

    st.dataframe(overview, use_container_width=True)

# =====================================================
# TAB 2 — 환경 데이터
# =====================================================
with tab2:
    st.subheader("환경 변수의 공통 경향과 학교별 차이")

    st.markdown("""
모든 학교에서 EC는 시간에 따라 점진적으로 증가하고,  
pH는 완만히 감소하는 **공통 경향**을 보였다.

이는 양액 내 이온 축적과 이에 따른 H⁺ 농도 증가가  
동시에 발생했을 가능성을 시사한다.
""")

    avg_rows = []
    for s, df in env.items():
        avg_rows.append({
            "학교": s,
            "온도": df["temperature"].mean(),
            "습도": df["humidity"].mean(),
            "pH": df["ph"].mean(),
            "EC": df["ec"].mean(),
            "EC 목표": SCHOOL_EC[s]
        })

    avg_df = pd.DataFrame(avg_rows)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "평균 온도",
            "평균 습도",
            "평균 pH",
            "목표 EC vs 실측 EC"
        ]
    )

    for _, r in avg_df.iterrows():
        c = SCHOOL_COLOR[r["학교"]]
        fig.add_bar(x=[r["학교"]], y=[r["온도"]], row=1, col=1, marker_color=c)
        fig.add_bar(x=[r["학교"]], y=[r["습도"]], row=1, col=2, marker_color=c)
        fig.add_bar(x=[r["학교"]], y=[r["pH"]], row=2, col=1, marker_color=c)
        fig.add_bar(x=[r["학교"]], y=[r["EC"]], row=2, col=2, marker_color=c)
        fig.add_scatter(
            x=[r["학교"]],
            y=[r["EC 목표"]],
            mode="markers",
            marker=dict(symbol="line-ew-open", size=20, color="black"),
            row=2, col=2
        )

    fig.update_layout(
        height=720,
        showlegend=False,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )

    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# TAB 3 — EC–생육 정량 분석
# =====================================================
with tab3:
    st.subheader("EC 조건에 따른 생육 결과의 정량 비교")

    calc_rows = []
    for s, df in growth.items():
        calc_rows.append({
            "학교": s,
            "EC": SCHOOL_EC[s],
            "평균 생중량": df["생중량(g)"].mean(),
            "표준편차": df["생중량(g)"].std(),
            "평균 잎 수": df["잎 수(장)"].mean(),
            "평균 지상부 길이": df["지상부 길이(mm)"].mean()
        })

    calc_df = pd.DataFrame(calc_rows)

    best_row = calc_df.loc[calc_df["평균 생중량"].idxmax()]

    st.markdown(f"""
### 📌 핵심 결과 해석

- 평균 생중량이 가장 큰 EC 조건은 **EC = {best_row['EC']}** 이었다.
- 다만 해당 EC에서는 **개체 간 편차(표준편차)** 또한 크게 나타났다.
- 이는 EC가 최대 생육량보다는 **생육 가능 범위의 상한선**을 정의하며,  
  안정성은 다른 환경 변수의 영향을 강하게 받음을 시사한다.
""")

    fig_bar = px.bar(
        calc_df,
        x="EC",
        y="평균 생중량",
        error_y="표준편차",
        color="학교",
        title="EC별 평균 생중량 (±표준편차)",
        text_auto=".2f"
    )
    fig_bar.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("상관관계 탐색 (Exploratory)")

    merged = []
    for s, df in growth.items():
        tmp = df.copy()
        tmp["학교"] = s
        tmp["EC"] = SCHOOL_EC[s]
        merged.append(tmp)

    merged_df = pd.concat(merged)

    fig_scatter = px.scatter(
        merged_df,
        x="잎 수(장)",
        y="생중량(g)",
        color="EC",
        trendline="ols",
        title="잎 수 vs 생중량 (경향 탐색)"
    )
    fig_scatter.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# =====================================================
# TAB 4 — 광주기 확장 가설
# =====================================================
with tab4:
    st.subheader("광주기(Photoperiod)와 EC 상호작용 가설")

    st.markdown("""
본 연구에서는 광주기를 직접 통제 변수로 설정하지는 않았으나,  
학교별 광주기 차이가 EC 효과의 **증폭 또는 완충 변수**로 작용했을 가능성을 고려하였다.

특히 하늘고의 경우 연속광(24h) 조건에서  
EC 2.0이 상대적으로 높은 평균 생중량을 보였으며,  
이는 **광합성 시간 증가가 중간 EC 조건에서 효율적으로 작용했을 가능성**을 시사한다.
""")

    photo_df = pd.DataFrame({
        "학교": PHOTOPERIOD.keys(),
        "광주기": PHOTOPERIOD.values(),
        "EC": [SCHOOL_EC[s] for s in PHOTOPERIOD],
        "평균 생중량": [
            growth[s]["생중량(g)"].mean() for s in PHOTOPERIOD
        ]
    })

    st.dataframe(photo_df, use_container_width=True)

    st.markdown("""
### 🔍 향후 연구 확장 제안
- 광주기를 독립 변수로 통제한 반복 실험
- EC × 광주기 이원 분산 분석(ANOVA)
- 생육 안정성 지표(변동계수, CV) 도입
""")
