import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from pathlib import Path
import unicodedata
import io

# ===============================
# 기본 설정
# ===============================
st.set_page_config(
    page_title="극지식물 최적 EC 농도 연구",
    layout="wide"
)

# 한글 폰트 (Streamlit)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# 상수 정의
# ===============================
SCHOOL_EC = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0
}

SCHOOL_COLOR = {
    "송도고": "#4C72B0",
    "하늘고": "#55A868",
    "아라고": "#C44E52",
    "동산고": "#8172B2"
}

DATA_DIR = Path("data")

# ===============================
# 유틸 함수
# ===============================
def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFC", text)

def find_file_by_name(directory: Path, target_name: str):
    target_norm = normalize_text(target_name)
    for file in directory.iterdir():
        if normalize_text(file.name) == target_norm:
            return file
    return None

# ===============================
# 데이터 로딩
# ===============================
@st.cache_data
def load_environment_data():
    env_data = {}
    with st.spinner("환경 데이터 로딩 중..."):
        for school in SCHOOL_EC.keys():
            filename = f"{school}_환경데이터.csv"
            file_path = find_file_by_name(DATA_DIR, filename)
            if file_path is None:
                st.error(f"{filename} 파일을 찾을 수 없습니다.")
                continue
            df = pd.read_csv(file_path)
            env_data[school] = df
    return env_data

@st.cache_data
def load_growth_data():
    with st.spinner("생육 데이터 로딩 중..."):
        xlsx_path = None
        for file in DATA_DIR.iterdir():
            if file.suffix == ".xlsx":
                xlsx_path = file
                break
        if xlsx_path is None:
            st.error("생육 결과 XLSX 파일을 찾을 수 없습니다.")
            return {}

        xls = pd.ExcelFile(xlsx_path)
        growth_data = {}
        for sheet in xls.sheet_names:
            growth_data[sheet] = pd.read_excel(xls, sheet_name=sheet)
        return growth_data

env_data = load_environment_data()
growth_data = load_growth_data()

# ===============================
# 사이드바
# ===============================
st.sidebar.title("학교 선택")
selected_school = st.sidebar.selectbox(
    "분석할 학교",
    ["전체"] + list(SCHOOL_EC.keys())
)

# ===============================
# 제목
# ===============================
st.title("🌱 극지식물 최적 EC 농도 연구")

# ===============================
# 탭 구성
# ===============================
tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# ===============================
# TAB 1 : 실험 개요
# ===============================
with tab1:
    st.subheader("연구 배경 및 목적")

    st.markdown("""
본 연구는 극지식물 **나도수영**의 생육에 영향을 미치는 환경 요인 중  
**EC(Electrical Conductivity)** 농도의 역할을 탐구하는 것을 목적으로 한다.

EC는 생육을 직접 결정하는 단일 인자라기보다,  
**pH·온도·습도와 상호작용하며 생육 안정성을 조절하는 조건 변수**로 작용한다.

본 대시보드는 송도고 환경을 기준(reference environment)으로 설정하여  
학교별 EC 조건에 따른 생육 결과를 **상대적으로 해석**한다.
""")

    summary_df = pd.DataFrame({
        "학교": SCHOOL_EC.keys(),
        "EC 목표": SCHOOL_EC.values(),
        "개체수": [
            len(growth_data.get(s, [])) for s in SCHOOL_EC.keys()
        ]
    })
    st.dataframe(summary_df, use_container_width=True)

    total_plants = sum(summary_df["개체수"])
    avg_temp = pd.concat(env_data.values())["temperature"].mean()
    avg_hum = pd.concat(env_data.values())["humidity"].mean()

    st.metric("총 개체수", f"{total_plants} 개체")
    st.metric("평균 온도", f"{avg_temp:.2f} ℃")
    st.metric("평균 습도", f"{avg_hum:.2f} %")
    st.metric("경향상 최적 EC", "2.0 (하늘고)")

# ===============================
# TAB 2 : 환경 데이터
# ===============================
with tab2:
    st.subheader("학교별 환경 평균 비교")

    avg_env = []
    for school, df in env_data.items():
        avg_env.append({
            "학교": school,
            "온도": df["temperature"].mean(),
            "습도": df["humidity"].mean(),
            "pH": df["ph"].mean(),
            "EC": df["ec"].mean()
        })
    avg_env_df = pd.DataFrame(avg_env)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 온도", "평균 습도", "평균 pH", "목표 EC vs 실측 EC"]
    )

    for school in avg_env_df["학교"]:
        color = SCHOOL_COLOR[school]
        row = avg_env_df[avg_env_df["학교"] == school].iloc[0]

        fig.add_bar(x=[school], y=[row["온도"]], row=1, col=1, marker_color=color)
        fig.add_bar(x=[school], y=[row["습도"]], row=1, col=2, marker_color=color)
        fig.add_bar(x=[school], y=[row["pH"]], row=2, col=1, marker_color=color)
        fig.add_bar(x=[school], y=[row["EC"]], row=2, col=2, marker_color=color)

    fig.update_layout(
        height=700,
        showlegend=False,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)

    if selected_school != "전체":
        df = env_data[selected_school]
        st.subheader(f"{selected_school} 환경 시계열")

        fig_line = px.line(
            df,
            x="time",
            y=["temperature", "humidity", "ec"],
            labels={"value": "측정값", "time": "시간"},
            title="시간에 따른 환경 변화"
        )
        fig_line.add_hline(
            y=SCHOOL_EC[selected_school],
            line_dash="dash",
            annotation_text="목표 EC"
        )
        fig_line.update_layout(
            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
        )
        st.plotly_chart(fig_line, use_container_width=True)

        with st.expander("환경 데이터 원본"):
            st.dataframe(df)
            buffer = io.BytesIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                data=buffer,
                file_name=f"{selected_school}_환경데이터.csv",
                mime="text/csv"
            )

# ===============================
# TAB 3 : 생육 결과
# ===============================
with tab3:
    st.subheader("EC 조건별 생육 결과 분석")

    growth_summary = []
    for school, df in growth_data.items():
        growth_summary.append({
            "학교": school,
            "EC": SCHOOL_EC.get(school, None),
            "평균 생중량": df["생중량(g)"].mean(),
            "평균 잎 수": df["잎 수(장)"].mean(),
            "평균 지상부 길이": df["지상부 길이(mm)"].mean(),
            "개체수": len(df)
        })

    growth_df = pd.DataFrame(growth_summary)

    best_ec = growth_df.loc[growth_df["평균 생중량"].idxmax(), "EC"]

    st.metric("경향상 최적 EC", f"{best_ec}")

    fig_bar = px.bar(
        growth_df,
        x="EC",
        y="평균 생중량",
        color="학교",
        title="EC별 평균 생중량 비교",
        text_auto=".2f"
    )
    fig_bar.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    fig_box = px.box(
        pd.concat(growth_data.values(), keys=growth_data.keys(), names=["학교"]),
        x="학교",
        y="생중량(g)",
        title="학교별 생중량 분포"
    )
    fig_box.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig_box, use_container_width=True)

    with st.expander("생육 데이터 원본"):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            for school, df in growth_data.items():
                df.to_excel(writer, sheet_name=school, index=False)
        buffer.seek(0)

        st.download_button(
            data=buffer,
            file_name="학교별_생육결과.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
