import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Sri Lanka A/L University Admission Analytics", layout="wide")

st.title("Sri Lanka A/L University Admission Analytics Dashboard")
st.markdown("Explore university admission Z-score cutoffs through descriptive, diagnostic, and predictive analytics.")

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

# Ensure CutoffZ is numeric
df['CutoffZ'] = pd.to_numeric(df['CutoffZ'], errors='coerce')

# Tabs for the three layers
tab1, tab2, tab3 = st.tabs(["Layer 1: Descriptive", "Layer 2: Diagnostic", "Layer 3: Student Analytics"])

with tab1:
    st.header("Descriptive Analytics: What Happened?")
    st.markdown("Get a high-level summary of the cutoffs for a specific academic year and district.")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("Select Academic Year", sorted(df["AcademicYear"].unique(), reverse=True))
    with col2:
        selected_district_desc = st.selectbox("Select District", sorted(df["DistrictName"].unique()), key="desc_dist")
        
    df_desc = df[(df["AcademicYear"] == selected_year) & (df["DistrictName"] == selected_district_desc)]
    
    st.subheader(f"Overview for {selected_year} - {selected_district_desc}")
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Courses Offered", df_desc["CourseName"].nunique())
    kpi2.metric("Universities Enrolling", df_desc["UniversityName"].nunique())
    if not df_desc["CutoffZ"].dropna().empty:
        kpi3.metric("Highest Z-Score Cutoff", round(df_desc["CutoffZ"].max(), 4))
    else:
        kpi3.metric("Highest Z-Score Cutoff", "N/A")
        
    st.markdown("### Z-Score Distribution by Course")
    if not df_desc.empty:
        top_courses = df_desc.groupby("CourseName")["CutoffZ"].max().nlargest(20).index
        fig_desc = px.box(
            df_desc[df_desc["CourseName"].isin(top_courses)], 
            x="CourseName", y="CutoffZ", 
            title="Z-Score Spread for Top 20 Most Competitive Courses",
            points="all",
            color="CourseName"
        )
        fig_desc.update_layout(xaxis={'categoryorder':'total descending'}, showlegend=False)
        fig_desc.update_xaxes(tickangle=45)
        st.plotly_chart(fig_desc, width='stretch')
        
        st.markdown("### Dataset Summary")
        st.dataframe(df_desc.dropna(subset=['CutoffZ']).sort_values('CutoffZ', ascending=False), width='stretch')
    else:
        st.info("No data available for this selection.")

with tab2:
    st.header("Diagnostic Analytics: Where and how did cutoffs change?")
    st.markdown("Analyze year-over-year trends and variance in Z-scores for a specific course.")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        selected_course = st.selectbox("Select Course", sorted(df["CourseName"].unique()), key="diag_course")
    with col_d2:
        selected_district = st.selectbox("Select District", sorted(df["DistrictName"].unique()), key="diag_dist")
        
    df_diag = df[(df["CourseName"] == selected_course) & (df["DistrictName"] == selected_district)]
    df_diag = df_diag.dropna(subset=['CutoffZ'])
    
    if not df_diag.empty:
        fig_trend = px.line(
            df_diag.sort_values("AcademicYear"), 
            x="AcademicYear", 
            y="CutoffZ", 
            color="UniversityName",
            markers=True,
            title=f"Z-Score Trends for {selected_course} in {selected_district}"
        )
        st.plotly_chart(fig_trend, width='stretch')
        
        st.subheader("Year-over-Year (YoY) Change Analysis")
        # Pivot to calculate diff
        pivot_df = df_diag.pivot_table(index="AcademicYear", columns="UniversityName", values="CutoffZ").sort_index()
        diff_df = pivot_df.diff()
        
        # Melt back for plotting
        diff_melted = diff_df.reset_index().melt(id_vars="AcademicYear", value_name="Z_Score_Change").dropna()
        
        if not diff_melted.empty:
            fig_diff = px.bar(
                diff_melted,
                x="AcademicYear",
                y="Z_Score_Change",
                color="UniversityName",
                barmode="group",
                title="Year-over-Year Z-Score Variance"
            )
            st.plotly_chart(fig_diff, width='stretch')
            
            st.markdown("### Changes Data")
            st.dataframe(diff_melted.sort_values(by=["AcademicYear", "UniversityName"]), width='stretch')
        else:
            st.info("Not enough sequential data to calculate Year-over-Year changes.")
    else:
        st.info("No data available for this course and district combination.")

with tab3:
    st.header("Student Analytics: Which courses are within reach?")
    st.markdown("Enter your Z-score to see which courses you would have historically qualified for based on past cutoffs.")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        student_district = st.selectbox("Your District", sorted(df["DistrictName"].unique()), key="stu_dist")
    with col_s2:
        student_zscore = st.number_input("Your Z-Score", min_value=-3.0, max_value=4.0, value=1.5, step=0.05)
    with col_s3:
        target_year = st.selectbox("Reference Academic Year", sorted(df["AcademicYear"].unique(), reverse=True), key="stu_year")
        
    df_stu = df[(df["AcademicYear"] == target_year) & (df["DistrictName"] == student_district)]
    df_stu = df_stu.dropna(subset=['CutoffZ'])
    
    if not df_stu.empty:
        df_stu = df_stu.copy()
        df_stu['Margin'] = student_zscore - df_stu['CutoffZ']
        
        def categorize(margin):
            if margin >= 0.1:
                return "Safe (Margin >= +0.1)"
            elif margin >= -0.05:
                return "Borderline (-0.05 to +0.1)"
            else:
                return "Out of Reach"
                
        df_stu['Likelihood'] = df_stu['Margin'].apply(categorize)
        
        reachable_df = df_stu[df_stu['Likelihood'] != "Out of Reach"].sort_values("Margin", ascending=False)
        
        if not reachable_df.empty:
            st.success(f"Found {len(reachable_df)} courses within reach for {target_year} in {student_district} with a Z-Score of {student_zscore}.")
            st.dataframe(
                reachable_df[["CourseName", "UniversityName", "CutoffZ", "Margin", "Likelihood"]],
                width='stretch'
            )
            
            fig_reach = px.scatter(
                reachable_df,
                x="CutoffZ",
                y="CourseName",
                color="Likelihood",
                hover_data=["UniversityName", "Margin"],
                title="Reachable Courses Distribution",
                color_discrete_map={
                    "Safe (Margin >= +0.1)": "green",
                    "Borderline (-0.05 to +0.1)": "orange"
                }
            )
            fig_reach.update_traces(marker=dict(size=10))
            fig_reach.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_reach, width='stretch')
        else:
            st.warning("Based on the reference year, no courses appear to be within reach. Try a lower threshold or different reference year.")
    else:
        st.info("No cutoff data available for the selected year and district.")
