import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

# =====================================================
# 기본 설정
# =====================================================
st.set_page_config(
    page_title="🌱 극지식물 최적 EC 농도 연구",
    layout="wide"
)

# =====================================================
# 한글 폰트
# =====================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

PLOTLY_FONT = dict(
    family="Malgun Gothic, Apple SD Gothic Neo, Noto Sans KR, sans-serif"
)

# =====================================================
# 유니코드 정규화
# =====================================================
def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text)

# =====================================================
# 학교 메타 정보 (기준 테이블)
# =====================================================
school_ec = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0
}

schools = list(school_ec.keys())

def extract_school_name(text: str) -> str | None:
    """파일명/시트명에서 학교명 추출"""
    for school in schools:
        if school in text:
            return school
    return None

# =====================================================
# 데이터 로딩
# =====================================================
@st.cache_data
def load_environment_data(data_dir: Path):
    result = {}
    for f in data_dir.iterdir():
        if f.suffix.lower() == ".csv":
            key = normalize(f.stem)
            df = pd.read_csv(f)
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
            school = extract_school_name(key)
            if school:
                result[school] = df
    return result


@st.cache_data
def load_growth_data(xlsx_path: Path):
    excel = pd.ExcelFile(xlsx_path)
    result = {}
    for sheet in excel.sheet_names:
        key = normalize(sheet)
        school = extract_school_name(key)
        if school:
            result[school] = excel.parse(sheet)
    return result

# =====================================================
# 경로 및 데이터 로딩
# =====================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

with st.spinner("📂 데이터 로딩 중..."):
    try:
        env_data = load_environment_data(DATA_DIR)
        growth_xlsx = next(f for f in DATA_DIR.iterdir() if f.suffix == ".xlsx")
        growth_data = load_growth_data(growth_xlsx)
    except Exception as e:
        st.error(f"데이터 로딩 실패: {e}")
        st.stop()

# =====================================================
# 사이드바
# =====================================================
selected_school = st.sidebar.selectbox(
    "학교 선택",
    ["전체"] + schools
)

# =====================================================
# 제목
# =====================================================
st.title("🌱 극지식물 최적 EC 농도 연구")

tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# =====================================================
# TAB 1 : 실험 개요
# =====================================================
with tab1:
    st.subheader("연구 배경 및 목적")
    st.write(
        "서로 다른 EC 조건에서 극지식물의 생육 반응을 비교하여 "
        "최적의 양액 EC 농도를 도출한다."
    )

    meta = []
    for school in schools:
        meta.append({
            "학교명": school,
            "EC 목표": school_ec[school],
            "개체수": len(growth_data.get(school, []))
        })

    st.dataframe(pd.DataFrame(meta), use_container_width=True)

    total_plants = sum(len(df) for df in growth_data.values())
    avg_temp = pd.concat(env_data.values())["temperature"].mean()
    avg_hum = pd.concat(env_data.values())["humidity"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 개체수", total_plants)
    c2.metric("평균 온도(°C)", f"{avg_temp:.2f}")
    c3.metric("평균 습도(%)", f"{avg_hum:.2f}")
    c4.metric("최적 EC", "2.0 ⭐ (하늘고)")

# =====================================================
# TAB 2 : 환경 데이터
# =====================================================
with tab2:
    st.subheader("학교별 환경 평균 비교")

    rows = []
    for school, df in env_data.items():
        rows.append({
            "학교": school,
            "온도": df["temperature"].mean(),
            "습도": df["humidity"].mean(),
            "pH": df["ph"].mean(),
            "실측 EC": df["ec"].mean(),
            "목표 EC": school_ec[school]
        })

    summary = pd.DataFrame(rows)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 온도", "평균 습도", "평균 pH", "목표 EC vs 실측 EC"]
    )

    fig.add_bar(x=summary["학교"], y=summary["온도"], row=1, col=1)
    fig.add_bar(x=summary["학교"], y=summary["습도"], row=1, col=2)
    fig.add_bar(x=summary["학교"], y=summary["pH"], row=2, col=1)
    fig.add_bar(x=summary["학교"], y=summary["실측 EC"], name="실측 EC", row=2, col=2)
    fig.add_bar(x=summary["학교"], y=summary["목표 EC"], name="목표 EC", row=2, col=2)

    fig.update_layout(height=700, font=PLOTLY_FONT)
    st.plotly_chart(fig, use_container_width=True)

    if selected_school != "전체":
        df = env_data[selected_school]
        st.subheader(f"{selected_school} 환경 시계열")

        for col in ["temperature", "humidity", "ec"]:
            fig_line = px.line(df, x="time", y=col, title=col)
            if col == "ec":
                fig_line.add_hline(y=school_ec[selected_school], line_dash="dash")
            fig_line.update_layout(font=PLOTLY_FONT)
            st.plotly_chart(fig_line, use_container_width=True)

    with st.expander("📄 환경 데이터 원본"):
        for school, df in env_data.items():
            st.markdown(f"**{school}**")
            st.dataframe(df, use_container_width=True)

            buffer = io.BytesIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)

            st.download_button(
                label=f"⬇️ {school} 환경 데이터 CSV 다운로드",
                data=buffer,
                file_name=f"{school}_환경데이터.csv",
                mime="text/csv",
                key=f"env_{school}"
            )

# =====================================================
# TAB 3 : 생육 결과
# =====================================================
with tab3:
    stats = []
    for school, df in growth_data.items():
        stats.append({
            "학교": school,
            "EC": school_ec[school],
            "평균 생중량": df["생중량(g)"].mean(),
            "평균 잎 수": df["잎 수(장)"].mean(),
            "평균 지상부 길이": df["지상부 길이(mm)"].mean(),
            "개체수": len(df)
        })

    stat_df = pd.DataFrame(stats)
    best = stat_df.loc[stat_df["평균 생중량"].idxmax()]

    st.metric("🥇 최적 EC", f"{best['EC']} ({best['학교']})")

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 생중량", "평균 잎 수", "평균 지상부 길이", "개체수"]
    )

    fig.add_bar(x=stat_df["학교"], y=stat_df["평균 생중량"], row=1, col=1)
    fig.add_bar(x=stat_df["학교"], y=stat_df["평균 잎 수"], row=1, col=2)
    fig.add_bar(x=stat_df["학교"], y=stat_df["평균 지상부 길이"], row=2, col=1)
    fig.add_bar(x=stat_df["학교"], y=stat_df["개체수"], row=2, col=2)

    fig.update_layout(height=700, font=PLOTLY_FONT)
    st.plotly_chart(fig, use_container_width=True)

    merged = []
    for school, df in growth_data.items():
        tmp = df.copy()
        tmp["학교"] = school
        merged.append(tmp)
    merged_df = pd.concat(merged)

    fig_box = px.box(
        merged_df, x="학교", y="생중량(g)",
        title="학교별 생중량 분포"
    )
    fig_box.update_layout(font=PLOTLY_FONT)
    st.plotly_chart(fig_box, use_container_width=True)

    with st.expander("📄 생육 데이터 전체 다운로드"):
        buffer = io.BytesIO()
        merged_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            label="⬇️ 전체 생육 결과 XLSX 다운로드",
            data=buffer,
            file_name="전체_생육결과.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
