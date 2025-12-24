import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

# ===============================
# 페이지 설정
# ===============================
st.set_page_config(
    page_title="극지식물 EC–환경–생육 통합 분석",
    layout="wide"
)

# ===============================
# 한글 폰트
# ===============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# 상수
# ===============================
SCHOOL_EC = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0
}

DATA_DIR = Path("data")

# ===============================
# 파일명 정규화
# ===============================
def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text)

def find_file(directory: Path, target_name: str):
    target = normalize(target_name)
    for f in directory.iterdir():
        if normalize(f.name) == target:
            return f
    return None

# ===============================
# 데이터 로딩
# ===============================
@st.cache_data
def load_environment_data():
    env = {}
    with st.spinner("환경 데이터 로딩 중..."):
        for school in SCHOOL_EC.keys():
            file = find_file(DATA_DIR, f"{school}_환경데이터.csv")
            if file is None:
                st.error(f"{school} 환경 데이터 파일을 찾을 수 없습니다.")
                continue
            env[school] = pd.read_csv(file)
    return env

@st.cache_data
def load_growth_data():
    with st.spinner("생육 데이터 로딩 중..."):
        xlsx_file = None
        for f in DATA_DIR.iterdir():
            if f.suffix == ".xlsx":
                xlsx_file = f
                break

        if xlsx_file is None:
            st.error("생육 결과 XLSX 파일이 없습니다.")
            return {}

        xls = pd.ExcelFile(xlsx_file)
        data = {}
        for sheet in xls.sheet_names:
            data[sheet] = pd.read_excel(xlsx_file, sheet_name=sheet)
        return data

env_data = load_environment_data()
growth_data = load_growth_data()

# ===============================
# 사이드바
# ===============================
st.sidebar.title("학교 선택")
selected_school = st.sidebar.selectbox(
    "학교",
    ["전체"] + list(SCHOOL_EC.keys())
)

# ===============================
# 제목
# ===============================
st.title("🌱 극지식물 EC–환경–생육 통합 분석")

# ===============================
# 탭
# ===============================
tab1, tab2, tab3 = st.tabs([
    "📈 송도고 환경 변화",
    "🔬 EC–pH 상관 분석",
    "📊 예상 생중량 계산"
])

# ===============================
# TAB 1
# ===============================
with tab1:
    st.subheader("송도고 온도 · 습도 · pH · EC 변화")

    if "송도고" not in env_data:
        st.error("송도고 환경 데이터가 없습니다.")
    else:
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

# ===============================
# TAB 2
# ===============================
with tab2:
    st.subheader("EC와 pH의 상관관계 (송도고 기준)")

    if "송도고" not in env_data:
        st.error("송도고 환경 데이터가 없습니다.")
    else:
        df = env_data["송도고"]

        x = df["ec"].astype(float)
        y = df["ph"].astype(float)

        corr = np.corrcoef(x, y)[0, 1]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x, y=y, mode="markers", marker=dict(size=7)
        ))

        fig.update_layout(
            title=f"EC–pH 산점도 (상관계수 r = {corr:.3f})",
            xaxis_title="EC",
            yaxis_title="pH",
            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
        )

        st.plotly_chart(fig, use_container_width=True)

# ===============================
# TAB 3
# ===============================
with tab3:
    st.subheader("EC 조건에 따른 예상 생중량")

    summary = []
    for school, df in growth_data.items():
        summary.append({
            "학교": school,
            "EC": SCHOOL_EC.get(school, np.nan),
            "평균 생중량": df["생중량(g)"].mean()
        })

    result_df = pd.DataFrame(summary).dropna()

    fig = go.Figure()
    fig.add_trace(go.Bar(
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
### 📌 계산 결과
- 평균 생중량 기준 최적 EC는 **EC = {optimal['EC']}**  
- 본 값은 실험 데이터를 이용한 **경향성 결과**이다.
""")

    # ✅ 다운로드 (완전 안정)
    buffer = io.BytesIO()
    result_df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    st.download_button(
        label="EC별 평균 생중량 결과 다운로드",
        data=buffer.getvalue(),   # 🔥 핵심 수정
        file_name="EC별_평균생중량_결과.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
