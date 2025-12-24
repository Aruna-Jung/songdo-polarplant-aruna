import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

# =====================================================
# 기본 설정
# =====================================================
st.set_page_config(
    page_title="극지식물 EC–환경–생육 통합 분석",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# 연구 상수 (보고서 기준)
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
# 유틸: 한글 파일명 대응
# =====================================================
def nfc(text):
    return unicodedata.normalize("NFC", text)

def find_file(directory: Path, target_name: str):
    target = nfc(target_name)
    for f in directory.iterdir():
        if nfc(f.name) == target:
            return f
    return None

# =====================================================
# 데이터 로딩
# =====================================================
@st.cache_data
def load_environment():
    data = {}
    with st.spinner("환경 데이터 로딩 중..."):
        for school in SCHOOL_EC:
            path = find_file(DATA_DIR, f"{school}_환경데이터.csv")
            if path is None:
                st.error(f"{school} 환경 데이터 파일 없음")
                continue
            data[school] = pd.read_csv(path)
    return data

@st.cache_data
def load_growth():
    with st.spinner("생육 데이터 로딩 중..."):
        xlsx = None
        for f in DATA_DIR.iterdir():
            if f.suffix == ".xlsx":
                xlsx = f
                break
        if xlsx is None:
            st.error("생육 결과 XLSX 파일 없음")
            return {}

        xls = pd.ExcelFile(xlsx)
        return {s: pd.read_excel(xlsx, sheet_name=s) for s in xls.sheet_names}

env = load_environment()
growth = load_growth()

# =====================================================
# 사이드바
# =====================================================
st.sidebar.title("분석 설정")
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
    "🌡️ 환경 데이터",
    "📊 EC–생육 정량 분석",
    "💡 광주기 확장 가설"
])

# =====================================================
# TAB 1 — 연구 개요
# =====================================================
with tab1:
    st.subheader("연구 배경 및 설계")

    st.markdown("""
본 연구는 극지식물 **나도수영**의 생육에 영향을 미치는 환경 요인 중  
**EC(Electrical Conductivity)**의 역할을 정량적으로 분석하는 것을 목표로 한다.

EC는 생육을 직접 결정하는 단일 원인이 아니라,  
**pH·온도·습도·광주기와 상호작용하며 생육 안정성을 조절하는 조건 변수**로 가정하였다.

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
모든 학교에서 EC는 시간에 따라 증가하고,  
pH는 완만히 감소하는 공통 경향을 보였다.

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
            "EC(실측)": df["ec"].mean(),
            "EC(목표)": SCHOOL_EC[s]
        })

    avg_df = pd.DataFrame(avg_rows)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 온도", "평균 습도", "평균 pH", "목표 EC vs 실측 EC"]
    )

    for _, r in avg_df.iterrows():
        fig.add_bar(x=[r["학교"]], y=[r["온도"]], row=1, col=1)
        fig.add_bar(x=[r["학교"]], y=[r["습도"]], row=1, col=2)
        fig.add_bar(x=[r["학교"]], y=[r["pH"]], row=2, col=1)
        fig.add_bar(x=[r["학교"]], y=[r["EC(실측)"]], row=2, col=2)
        fig.add_scatter(
            x=[r["학교"]],
            y=[r["EC(목표)"]],
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
    st.subheader("EC 조건별 생육 결과 비교")

    calc = []
    for s, df in growth.items():
        calc.append({
            "학교": s,
            "EC": SCHOOL_EC[s],
            "평균 생중량": df["생중량(g)"].mean(),
            "표준편차": df["생중량(g)"].std(),
            "평균 잎 수": df["잎 수(장)"].mean(),
            "평균 지상부 길이": df["지상부 길이(mm)"].mean(),
            "개체수": len(df)
        })

    calc_df = pd.DataFrame(calc)
    best = calc_df.loc[calc_df["평균 생중량"].idxmax()]

    st.markdown(f"""
### 📌 핵심 결과 해석

- 평균 생중량이 가장 큰 EC 조건은 **EC = {best['EC']}** 이었다.
- 그러나 해당 조건에서는 개체 간 **편차(표준편차)** 또한 크게 나타났다.
- 이는 EC가 생육의 최대치를 결정하기보다는  
  **생육 가능 범위의 상한선**을 규정하는 변수임을 시사한다.
""")

    fig_bar = px.bar(
        calc_df,
        x="EC",
        y="평균 생중량",
        error_y="표준편차",
        text_auto=".2f",
        title="EC별 평균 생중량 (±표준편차)"
    )
    fig_bar.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # -------------------------------
    # 직접 회귀 계산
    # -------------------------------
    merged = []
    for s, df in growth.items():
        temp = df.copy()
        temp["EC"] = SCHOOL_EC[s]
        merged.append(temp)

    merged_df = pd.concat(merged)

    x = merged_df["잎 수(장)"].astype(float)
    y = merged_df["생중량(g)"].astype(float)

    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept

    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot

    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter(
        x=x,
        y=y,
        mode="markers",
        marker=dict(size=7, color="rgba(0,0,150,0.5)"),
        name="개별 개체"
    ))
    fig_scatter.add_trace(go.Scatter(
        x=x,
        y=y_pred,
        mode="lines",
        line=dict(color="red", width=3),
        name="회귀선"
    ))

    fig_scatter.update_layout(
        title="잎 수 vs 생중량 (직접 계산한 탐색적 회귀)",
        xaxis_title="잎 수 (장)",
        yaxis_title="생중량 (g)",
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
        annotations=[dict(
            x=0.02, y=0.98, xref="paper", yref="paper",
            text=f"회귀식: y = {slope:.3f}x + {intercept:.3f}<br>R² = {r2:.3f}",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.8)"
        )]
    )

    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("""
📌 본 회귀 분석은 잎 수 단일 변수를 사용한 **탐색적 분석**으로,  
예측 모델이 아닌 **경향성 파악용**으로 해석하는 것이 적절하다.
""")

# =====================================================
# TAB 4 — 광주기 가설
# =====================================================
with tab4:
    st.subheader("광주기–EC 상호작용 가설")

    st.markdown("""
광주기는 본 실험에서 직접 통제 변수로 설정되지는 않았으나,  
학교별 조건 차이가 EC 효과를 증폭 또는 완충했을 가능성이 있다.

특히 하늘고의 연속광 조건에서는  
EC 2.0이 상대적으로 높은 평균 생중량을 보였다.
""")

    photo_df = pd.DataFrame({
        "학교": PHOTOPERIOD.keys(),
        "광주기": PHOTOPERIOD.values(),
        "EC": [SCHOOL_EC[s] for s in PHOTOPERIOD],
        "평균 생중량": [growth[s]["생중량(g)"].mean() for s in PHOTOPERIOD]
    })

    st.dataframe(photo_df, use_container_width=True)

    st.markdown("""
### 🔍 향후 연구 확장
- 광주기 × EC 이원 분산 분석
- 생육 안정성 지표(CV) 도입
- 장기 생육 실험으로 누적 효과 분석
""")
