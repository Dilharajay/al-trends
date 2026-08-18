import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Sri Lanka A/L Cutoffs", layout="wide")

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
        f.AllIslandMerit
    FROM fact_cutoffs f
    JOIN dim_course c ON f.CourseID = c.CourseID
    JOIN dim_university u ON f.UniversityID = u.UniversityID
    JOIN dim_district d ON f.DistrictID = d.DistrictID
    """
    df = pd.read_sql(query, conn)
    
    query_bridge = """
    SELECT b.CourseID, c.CourseName, b.combination_id, d.stream, d.subject_1, d.subject_2, d.subject_3
    FROM bridge_course_combination b
    JOIN dim_combination d ON b.combination_id = d.combination_id
    JOIN dim_course c ON b.CourseID = c.CourseID
    """
    try:
        bridge_df = pd.read_sql(query_bridge, conn)
        # Create a display name for the combinations
        bridge_df['Combo_Display'] = bridge_df['combination_id'] + " (" + bridge_df['stream'] + "): " + bridge_df['subject_1'] + ", " + bridge_df['subject_2'] + ", " + bridge_df['subject_3']
    except Exception:
        bridge_df = pd.DataFrame()
        
    conn.close()
    
    df['CutoffZ'] = pd.to_numeric(df['CutoffZ'], errors='coerce')
    
    # Load seats
    seats_path = Path("data/bronze/csv/available_seats.csv")
    if seats_path.exists():
        seats_df = pd.read_csv(seats_path)
        df = df.merge(seats_df, on=["AcademicYear", "CourseName"], how="left")
    else:
        df["Seats"] = np.nan
        
    # Calculate Volatility & Competitiveness for each Course
    stats = df.dropna(subset=['CutoffZ']).groupby('CourseName')['CutoffZ'].agg(['mean', 'std', 'min', 'max']).reset_index()
    stats['std'] = stats['std'].fillna(0)
    stats['Volatility'] = pd.cut(stats['std'], bins=[-1, 0.05, 0.15, float('inf')], labels=['Low', 'Medium', 'High'])
    
    # Simple Competitiveness Index (0-100)
    max_z = stats['mean'].max()
    min_z = stats['mean'].min()
    if pd.notna(max_z) and pd.notna(min_z) and max_z > min_z:
        stats['Normalized Z'] = (stats['mean'] - min_z) / (max_z - min_z) * 100
        stats['Competitiveness'] = stats['Normalized Z'] - (stats['std'] * 10)
        stats['Competitiveness'] = stats['Competitiveness'].clip(0, 100)
    else:
        stats['Competitiveness'] = 50
        
    stats['Competitiveness_Band'] = pd.cut(
        stats['Competitiveness'], 
        bins=[-1, 25, 50, 75, 90, 100], 
        labels=['Lower historical cutoff', 'Moderate', 'Competitive', 'Highly competitive', 'Extremely competitive']
    )
    
    df = df.merge(stats[['CourseName', 'Volatility', 'Competitiveness', 'Competitiveness_Band']], on="CourseName", how="left")
    
    return df, stats, bridge_df

df, course_stats, bridge_df = load_data()

st.sidebar.title("SRI LANKA A/L CUTOFFS")
page = st.sidebar.radio("Navigation", [
    "Overview", 
    "Course Explorer", 
    "District Analysis", 
    "Historical Trends", 
    "Student Analyzer", 
    "Methodology"
])

if page == "Overview":
    st.title("National Overview")
    st.markdown("High-level summary of the Sri Lankan A/L University Admission Cutoffs.")
    
    sel_year = st.selectbox("Academic Year", sorted(df["AcademicYear"].unique(), reverse=True))
    d_year = df[df["AcademicYear"] == sel_year]
    d_valid = d_year.dropna(subset=['CutoffZ'])
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Universities", d_year["UniversityName"].nunique())
    col2.metric("Degree Programmes", d_year["CourseName"].nunique())
    col3.metric("Districts", d_year["DistrictName"].nunique())
    
    if not d_valid.empty:
        col4.metric("Highest Z-Score", round(d_valid["CutoffZ"].max(), 4))
        col5.metric("Median Z-Score", round(d_valid["CutoffZ"].median(), 4))
        
        st.subheader("Top 10 Most Competitive Courses")
        top_courses = d_valid.groupby("CourseName")["CutoffZ"].max().nlargest(10).reset_index()
        fig_bar = px.bar(top_courses, x="CutoffZ", y="CourseName", orientation='h', title="Highest Cutoffs by Course")
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, width='stretch')
        
        st.subheader("Average Cutoff by Academic Year")
        trend_all = df.dropna(subset=['CutoffZ']).groupby("AcademicYear")["CutoffZ"].mean().reset_index()
        fig_line = px.line(trend_all.sort_values("AcademicYear"), x="AcademicYear", y="CutoffZ", markers=True)
        st.plotly_chart(fig_line, width='stretch')
        
        st.subheader("Average Cutoff by District")
        dist_avg = d_valid.groupby("DistrictName")["CutoffZ"].mean().reset_index().sort_values("CutoffZ", ascending=False)
        fig_dist = px.bar(dist_avg, x="DistrictName", y="CutoffZ", color="CutoffZ", color_continuous_scale="Viridis")
        st.plotly_chart(fig_dist, width='stretch')
    else:
        st.warning("No valid Z-scores for this year.")

elif page == "Course Explorer":
    st.title("Course Explorer")
    st.markdown("Find a specific degree and analyze its historical trend.")
    
    col1, col2, col3 = st.columns(3)
    courses = sorted(df["CourseName"].unique())
    default_course = "MEDICINE" if "MEDICINE" in courses else ("ENGINEERING" if "ENGINEERING" in courses else courses[0])
    default_index = courses.index(default_course) if default_course in courses else 0
    
    selected_course = col1.selectbox("Select Course", courses, index=default_index)
    selected_dist = col2.selectbox("Select District", ["All"] + sorted(df["DistrictName"].unique()))
    
    d_course_all_unis = df[df["CourseName"] == selected_course]
    available_unis = sorted(d_course_all_unis["UniversityName"].unique())
    selected_unis = col3.multiselect("Select Universities", available_unis, default=available_unis)
    
    d_course = d_course_all_unis[d_course_all_unis["UniversityName"].isin(selected_unis)]
    if selected_dist != "All":
        d_course = d_course[d_course["DistrictName"] == selected_dist]
        
    st.subheader(f"Historical Trend for {selected_course}")
    d_course_clean = d_course.dropna(subset=['CutoffZ']).sort_values("AcademicYear")
    
    if not d_course_clean.empty:
        if selected_dist == "All":
            d_course_agg = d_course_clean.groupby(["AcademicYear", "UniversityName"])["CutoffZ"].mean().reset_index()
            fig = px.line(
                d_course_agg,
                x="AcademicYear", y="CutoffZ", color="UniversityName", markers=True,
                title="Average Cutoff across All Districts"
            )
        else:
            fig = px.line(
                d_course_clean,
                x="AcademicYear", y="CutoffZ", color="UniversityName", markers=True,
                title=f"Cutoff for {selected_dist} District"
            )
        st.plotly_chart(fig, width='stretch')
        
        st.subheader("Cross-Tabulation (Pivot)")
        pivot = d_course.pivot_table(index=["UniversityName", "DistrictName"], columns="AcademicYear", values="CutoffZ")
        st.dataframe(pivot, width='stretch')
    else:
        st.info("No Z-score data available.")

elif page == "District Analysis":
    st.title("District Analysis")
    
    st.subheader("District Competitiveness Matrix")
    sel_courses = st.multiselect("Select Courses for Matrix", sorted(df["CourseName"].unique()), default=["Medicine", "Engineering", "Computer Science", "Physical Science", "Management"] if "Medicine" in df["CourseName"].values else sorted(df["CourseName"].unique())[:5])
    sel_year_dist = st.selectbox("Academic Year", sorted(df["AcademicYear"].unique(), reverse=True))
    
    d_mat = df[(df["AcademicYear"] == sel_year_dist) & (df["CourseName"].isin(sel_courses))].dropna(subset=['CutoffZ'])
    if not d_mat.empty:
        matrix = d_mat.pivot_table(index="DistrictName", columns="CourseName", values="CutoffZ", aggfunc='mean')
        st.dataframe(matrix.style.background_gradient(cmap='YlOrRd', axis=None), width='stretch')
    
    st.markdown("---")
    st.subheader("Compare Two Districts")
    c1, c2 = st.columns(2)
    dist_a = c1.selectbox("District A", sorted(df["DistrictName"].unique()), index=0)
    dist_b = c2.selectbox("District B", sorted(df["DistrictName"].unique()), index=1 if len(df["DistrictName"].unique())>1 else 0)
    
    if dist_a and dist_b:
        da = df[(df["AcademicYear"] == sel_year_dist) & (df["DistrictName"] == dist_a)].groupby("CourseName")["CutoffZ"].mean()
        db = df[(df["AcademicYear"] == sel_year_dist) & (df["DistrictName"] == dist_b)].groupby("CourseName")["CutoffZ"].mean()
        comp = pd.DataFrame({dist_a: da, dist_b: db}).dropna()
        comp['Difference'] = comp[dist_a] - comp[dist_b]
        st.dataframe(comp.sort_values('Difference', ascending=False), width='stretch')

elif page == "Historical Trends":
    st.title("Historical Trends & Volatility")
    
    st.subheader("Cutoff Volatility & Competitiveness")
    st.markdown("Every course is analyzed for mean cutoff, variance (volatility), and an overall Competitiveness Index (0-100).")
    st.dataframe(course_stats[['CourseName', 'mean', 'min', 'max', 'Volatility', 'Competitiveness_Band']].sort_values('mean', ascending=False), width='stretch')
    
    st.markdown("---")
    st.subheader("Fastest Rising & Falling Courses (YoY)")
    sel_uni = st.selectbox("Select University", ["All"] + sorted(df["UniversityName"].unique()))
    
    d_trend = df.dropna(subset=['CutoffZ'])
    if sel_uni != "All":
        d_trend = d_trend[d_trend["UniversityName"] == sel_uni]
        
    pivot_trend = d_trend.pivot_table(index=["CourseName", "UniversityName"], columns="ExamYear", values="CutoffZ", aggfunc='mean')
    
    years = sorted(d_trend["ExamYear"].unique())
    if len(years) >= 2:
        y1, y2 = years[-2], years[-1]
        pivot_trend['Absolute Change'] = pivot_trend[y2] - pivot_trend[y1]
        pivot_trend['Percentage Change (%)'] = (pivot_trend['Absolute Change'] / pivot_trend[y1]) * 100
        
        res = pivot_trend[[y1, y2, 'Absolute Change', 'Percentage Change (%)']].dropna().sort_values('Percentage Change (%)', ascending=False)
        
        c1, c2 = st.columns(2)
        c1.markdown(f"**Fastest Rising ( {y1} -> {y2} )**")
        c1.dataframe(res.head(10), width='stretch')
        
        c2.markdown(f"**Fastest Falling ( {y1} -> {y2} )**")
        c2.dataframe(res.tail(10).sort_values('Percentage Change (%)'), width='stretch')
    else:
        st.info("Need at least 2 exam years of data to compute trends.")

elif page == "Student Analyzer":
    st.title("Historical Eligibility / Competitiveness Indicator")
    st.markdown("Explore historically competitive courses based on your Z-score. **Note:** The UGC cutoff is year-dependent and influenced by candidate performance and demand. This tool is an indicator of historical eligibility, not a guarantee of future admission.")
    
    c1, c2, c3, c4 = st.columns(4)
    stu_dist = c1.selectbox("Your District", sorted(df["DistrictName"].unique()))
    stu_z = c2.number_input("Your Z-score", min_value=-4.0, max_value=4.0, value=1.5, step=0.01)
    ref_year = c3.selectbox("Reference Year", sorted(df["AcademicYear"].unique(), reverse=True))
    
    # Subject combination slicer
    combo_options = ["All Courses"]
    if not bridge_df.empty:
        combo_options.extend(sorted(bridge_df['Combo_Display'].unique()))
    
    stu_combo = c4.selectbox("Subject Combination", combo_options)
    
    d_stu = df[(df["AcademicYear"] == ref_year) & (df["DistrictName"] == stu_dist)].dropna(subset=['CutoffZ']).copy()
    
    # Filter by subject combination if specific one is selected
    if stu_combo != "All Courses" and not bridge_df.empty:
        allowed_courses = bridge_df[bridge_df['Combo_Display'] == stu_combo]['CourseName'].unique()
        d_stu = d_stu[d_stu['CourseName'].isin(allowed_courses)]
    
    if not d_stu.empty:
        d_stu['Difference'] = stu_z - d_stu['CutoffZ']
        
        def assess(diff):
            if diff >= 0.1: return "Safe"
            if diff >= -0.05: return "Possible"
            if diff >= -0.2: return "Competitive"
            return "Unlikely"
            
        d_stu['Assessment'] = d_stu['Difference'].apply(assess)
        
        res = d_stu[['CourseName', 'UniversityName', 'CutoffZ', 'Difference', 'Assessment', 'Seats']].sort_values('Difference', ascending=False)
        
        st.subheader("Your Eligibility Landscape")
        
        color_map = {"Safe": "green", "Possible": "blue", "Competitive": "orange", "Unlikely": "red"}
        fig = px.scatter(res, x="CutoffZ", y="CourseName", color="Assessment", color_discrete_map=color_map, hover_data=["UniversityName", "Difference"])
        fig.add_vline(x=stu_z, line_dash="dash", line_color="black", annotation_text="Your Z-Score")
        st.plotly_chart(fig, width='stretch')
        
        st.dataframe(res.style.map(lambda v: f"color: {color_map.get(v, 'black')}", subset=['Assessment']), width='stretch')
    else:
        st.info("No data available for the selected reference year.")

elif page == "Methodology":
    st.title("Methodology & Data Pipeline")
    st.markdown("""
    ### Data Pipeline
    1. **UGC PDFs**: Official university cutoff documents.
    2. **Python Extraction**: Parsing using `pymupdf` to extract tables accurately.
    3. **Cleaning & Standardization**: District, Course, and University names are normalized. 
    4. **NQC Handling**: "Not Qualified for Course" (NQC) values are retained as a status string (`CutoffStatus`) alongside numerical Z-scores (stored as NULL for NQC), ensuring NQC is strictly differentiated from a Z-score of 0.
    5. **Database**: Exported to a star-schema SQLite/Parquet model for BI integration.
    
    ### Analytical Metrics
    - **Cutoff Volatility**: The standard deviation of a course's cutoff over available years.
    - **Competitiveness Index**: A normalized, custom metric (0-100) combining historical mean cutoff and stability. This is an exploratory indicator, not an official UGC measure.
    
    ### Important Limitations
    The UGC states that the minimum Z-score required for a given course is year-specific and depends directly on candidate performance and national demand. 
    **Do not use this dashboard to deterministically predict university entry.** It is designed solely to investigate how cutoffs have behaved across Sri Lanka over time.
    """)
