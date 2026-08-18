import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="AL Z-Score Dashboard", layout="wide")

st.title("Sri Lanka A/L Z-Score Trends Dashboard")

# Load Data
@st.cache_data
def load_data():
    conn = sqlite3.connect("data/bronze/db/al_cutoffs.db")
    query = """
    SELECT 
        f.AcademicYear,
        f.ExamYear,
        c.CourseName,
        u.UniversityName,
        d.DistrictName,
        f.CutoffZ,
        f.CutoffStatus,
        f.AllIslandMerit,
        f.AptitudeTest
    FROM fact_cutoffs f
    JOIN dim_course c ON f.CourseID = c.CourseID
    JOIN dim_university u ON f.UniversityID = u.UniversityID
    JOIN dim_district d ON f.DistrictID = d.DistrictID
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("Filters")
selected_year = st.sidebar.multiselect("Academic Year", df["AcademicYear"].unique(), default=df["AcademicYear"].unique())
selected_course = st.sidebar.selectbox("Course", sorted(df["CourseName"].unique()))
selected_district = st.sidebar.selectbox("District", sorted(df["DistrictName"].unique()))

# Filter Data
filtered_df = df[
    (df["AcademicYear"].isin(selected_year)) & 
    (df["CourseName"] == selected_course) &
    (df["DistrictName"] == selected_district)
]

filtered_df = filtered_df[filtered_df["CutoffZ"].notnull()]

# Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Z-Score Trends for {selected_course} in {selected_district} District")
    if not filtered_df.empty:
        fig = px.line(
            filtered_df, 
            x="AcademicYear", 
            y="CutoffZ", 
            color="UniversityName",
            markers=True,
            title="Trend over Academic Years"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No Z-Score data available for the selected filters (Data might be NQC or Missing).")

with col2:
    st.subheader("Data Summary")
    st.dataframe(filtered_df[["AcademicYear", "UniversityName", "CutoffZ"]].sort_values("AcademicYear", ascending=False), use_container_width=True)

st.markdown("---")
st.subheader("Explore the complete dataset")
st.dataframe(df.head(100))
