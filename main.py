import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="극지식물 최적 EC 농도 연구",
    layout="wide"
)

# 한글 폰트 (Streamlit UI)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 유틸: 한글 파일명 안전 비교
# -----------------------------
def normalize_name(name: str) -> str:
    return unicodedata.normalize("NFC", name)

# -----------------------------
# 데이터 로딩
# -----------------------------
@st.cache_data
def load_environment_data(data_dir: Path):
    env_data = {}
    for file in data_dir.iterdir():
        if file.suffix.lower() == ".csv":
            norm_name = normalize_name(file.stem)
            df = pd.read_csv(file)
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
            env_data[norm_name] = df
    return env_data


@st.cache_data
def load_growth_data(xlsx_path: Path):
    buffer = pd.ExcelFile(xlsx_path)
    data = {}
    for sheet in buffer.sheet_names:
        norm_sheet = normalize_name(sheet)
        df = buffer.parse(sheet)
        data[norm_sheet] = df
    return data


# -----------------------------
# 파일 탐색
# -----------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

with st.spinner("📂 데이터 로딩 중..."):
    try:
        env_data = load_environment_data(DATA_DIR)
        growth_xlsx = next(
            f for f in DATA_DIR.iterdir()
            if f.suffix == ".xlsx"
        )
        growth_data = load_growth_data(growth_xlsx)
    except Exception as e:
        st.error(f"데이터 로딩 실패: {e}")
        st.stop()

# -----------------------------
# 메타 정보
# -----------------------------
school_ec = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0
}

school_colors = {
    "송도고": "#1f77b4",
    "하늘고": "#2ca02c",
    "아라고": "#ff7f0e",
    "동산고": "#d62728"
}

# -----------------------------
# 사이드바
# -----------------------------
schools = ["전체"] + list(school_ec.keys())
selected_school = st.sidebar.selectbox("학교 선택", schools)

# -----------------------------
# 제목
# -----------------------------
st.title("🌱 극지식물 최적 EC 농도 연구")

# =============================
# TAB 구성
# =============================
tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# ======================================================
# TAB 1 : 실험 개요
# ======================================================
with tab1:
    st.subheader("연구 배경 및 목적")
    st.write(
        "본 연구는 서로 다른 EC 조건에서 극지식물의 생육 반응을 비교하여 "
        "최적의 양액 EC 농도를 도출하는 것을 목표로 한다."
    )

    meta_rows = []
    for school, ec in school_ec.items():
        meta_rows.append({
            "학교명": school,
            "EC 목표": ec,
            "개체수": len(growth_data.get(school, [])),
            "색상": school_colors[school]
        })

    meta_df = pd.DataFrame(meta_rows)
    st.dataframe(meta_df, use_container_width=True)

    total_plants = sum(len(df) for df in growth_data.values())
    avg_temp = pd.concat(env_data.values())["temperature"].mean()
    avg_hum = pd.concat(env_data.values())["humidity"].mean()
    optimal_ec = 2.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 개체수", f"{total_plants}")
    c2.metric("평균 온도(°C)", f"{avg_temp:.2f}")
    c3.metric("평균 습도(%)", f"{avg_hum:.2f}")
    c4.metric("최적 EC", "2.0 ⭐")

# ======================================================
# TAB 2 : 환경 데이터
# ======================================================
with tab2:
    st.subheader("학교별 환경 데이터 비교")

    summary_rows = []
    for school, df in env_data.items():
        summary_rows.append({
            "학교": school,
            "온도": df["temperature"].mean(),
            "습도": df["humidity"].mean(),
            "pH": df["ph"].mean(),
            "EC": df["ec"].mean(),
            "목표 EC": school_ec.get(school)
        })

    summary_df = pd.DataFrame(summary_rows)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 온도", "평균 습도", "평균 pH", "목표 EC vs 실측 EC"]
    )

    fig.add_bar(x=summary_df["학교"], y=summary_df["온도"], row=1, col=1)
    fig.add_bar(x=summary_df["학교"], y=summary_df["습도"], row=1, col=2)
    fig.add_bar(x=summary_df["학교"], y=summary_df["pH"], row=2, col=1)

    fig.add_bar(x=summary_df["학교"], y=summary_df["EC"], name="실측 EC", row=2, col=2)
    fig.add_bar(x=summary_df["학교"], y=summary_df["목표 EC"], name="목표 EC", row=2, col=2)

    fig.update_layout(
        height=700,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )

    st.plotly_chart(fig, use_container_width=True)

    if selected_school != "전체":
        df = env_data[selected_school]

        st.subheader(f"{selected_school} 시계열 변화")
        for col in ["temperature", "humidity", "ec"]:
            fig_line = px.line(df, x="time", y=col, title=col)
            if col == "ec":
                fig_line.add_hline(y=school_ec[selected_school], line_dash="dash")
            fig_line.update_layout(
                font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
            )
            st.plotly_chart(fig_line, use_container_width=True)

    with st.expander("📄 환경 데이터 원본"):
        for school, df in env_data.items():
            st.write(school)
            st.dataframe(df)
            buffer = io.BytesIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                data=buffer,
                file_name=f"{school}_환경데이터.csv",
                mime="text/csv"
            )

# ======================================================
# TAB 3 : 생육 결과
# ======================================================
with tab3:
    st.subheader("EC별 생육 결과 분석")

    growth_summary = []
    for school, df in growth_data.items():
        growth_summary.append({
            "학교": school,
            "EC": school_ec[school],
            "평균 생중량": df["생중량(g)"].mean(),
            "평균 잎 수": df["잎 수(장)"].mean(),
            "평균 지상부 길이": df["지상부 길이(mm)"].mean(),
            "개체수": len(df)
        })

    gs_df = pd.DataFrame(growth_summary)

    best = gs_df.loc[gs_df["평균 생중량"].idxmax()]
    st.metric("🥇 최적 EC (평균 생중량 최대)", f"{best['EC']}")

    fig_bar = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 생중량", "평균 잎 수", "평균 지상부 길이", "개체수"]
    )

    fig_bar.add_bar(x=gs_df["학교"], y=gs_df["평균 생중량"], row=1, col=1)
    fig_bar.add_bar(x=gs_df["학교"], y=gs_df["평균 잎 수"], row=1, col=2)
    fig_bar.add_bar(x=gs_df["학교"], y=gs_df["평균 지상부 길이"], row=2, col=1)
    fig_bar.add_bar(x=gs_df["학교"], y=gs_df["개체수"], row=2, col=2)

    fig_bar.update_layout(
        height=700,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    merged = []
    for school, df in growth_data.items():
        temp = df.copy()
        temp["학교"] = school
        merged.append(temp)
    merged_df = pd.concat(merged)

    fig_box = px.box(
        merged_df,
        x="학교",
        y="생중량(g)",
        title="학교별 생중량 분포"
    )
    fig_box.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig_box, use_container_width=True)

    fig_scatter1 = px.scatter(
        merged_df, x="잎 수(장)", y="생중량(g)", color="학교",
        title="잎 수 vs 생중량"
    )
    fig_scatter2 = px.scatter(
        merged_df, x="지상부 길이(mm)", y="생중량(g)", color="학교",
        title="지상부 길이 vs 생중량"
    )

    st.plotly_chart(fig_scatter1, use_container_width=True)
    st.plotly_chart(fig_scatter2, use_container_width=True)

    with st.expander("📄 생육 데이터 원본 다운로드"):
        buffer = io.BytesIO()
        merged_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        st.download_button(
            data=buffer,
            file_name="전체_생육결과.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
