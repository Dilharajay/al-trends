# Power BI Dashboard Layout Guide: A/L Trends & Cutoff Analysis

This document outlines the design, layout, and visual structure for the Power BI dashboard, heavily inspired by the project's interactive Streamlit application. It leverages the advanced DAX measures built into the `.tmdl` Semantic Model.

---

## Global Elements (Persistent Across Pages)
- **Header**: Title (e.g., "Sri Lanka A/L University Cutoff Trends") with a clean, academic theme (Dark Blues, Whites, and Grays).
- **Filter Pane (Left Sidebar)**:
  - **Academic Year**: Dropdown or List (e.g., `dim_year[AcademicYear]`).
  - **Exam Year**: Hidden filter if needed, but primarily driven by Academic Year.
  - **Course Stream**: Dropdown (e.g., `dim_combination[stream]`).

---

## Page 1: National Overview & Competitiveness
**Purpose**: Provide a high-level executive summary of the hardest courses and universities to enter, tracking national demand and seating capacity.

### Visuals
1. **KPI Cards (Top Row)**:
   - **Available Courses**: `[Available Courses]`
   - **Total Intake**: `[Total Intake]`
   - **Overall Median Z-Score**: `MEDIAN(fact_cutoffs[CutoffZ])`
   - **Highest Z-Score**: `[Max Cutoff Z]`

2. **Top 10 Most Competitive Courses (Horizontal Bar Chart)**:
   - **Y-Axis**: `dim_course[CourseName]`
   - **X-Axis**: `[Competitiveness Index]`
   - **Tooltip**: `[Average Cutoff Z]`, `[Cutoff Volatility]`, `[Competitiveness Band]`
   - *Design Tip*: Apply conditional formatting using `[Competitiveness Band]` (e.g., Red for "Extremely competitive", Yellow for "Moderate").

3. **Fastest Rising & Falling Courses YoY (Tornado Chart or Clustered Bar)**:
   - **Y-Axis**: `dim_course[CourseName]`
   - **X-Axis**: `[YoY Cutoff Change]`
   - *Design Tip*: Highlight positive changes (cutoffs getting harder) in Red/Orange, and negative changes in Green/Blue.

4. **University Intake Distribution (Tree Map or Pie Chart)**:
   - **Category**: `dim_university[UniversityName]`
   - **Values**: `[Total Intake]`

---

## Page 2: Course & University Deep Dive
**Purpose**: Allow users to select a specific course (e.g., Medicine, Engineering) and analyze how its cutoffs vary across different universities and historical years.

### Page-Specific Slicer
- **Course Name**: Searchable Dropdown Slicer (`dim_course[CourseName]`).

### Visuals
1. **University Comparison (Matrix Table)**:
   - **Rows**: `dim_university[UniversityName]`
   - **Values**: `[Average Cutoff Z]`, `[Total Intake]`, `[Cutoff Volatility]`, `[Volatility Level]`
   - *Design Tip*: Use Data Bars conditional formatting on the `[Average Cutoff Z]` column.

2. **Historical Trend (Line Chart)**:
   - **X-Axis**: `dim_year[AcademicYear]`
   - **Y-Axis**: `[Average Cutoff Z]`
   - **Legend**: `dim_university[UniversityName]`
   - *Behavior*: When a course is selected in the slicer, this line chart shows how the cutoff for that exact course trended at different universities over the last 8 years.

3. **District Disparity (Box and Whisker Chart - Custom Visual)**:
   - **Category**: `dim_district[DistrictName]`
   - **Values**: `fact_cutoffs[CutoffZ]`
   - *Purpose*: Shows the spread of Z-scores for the selected course across all districts, highlighting the massive impact of district quotas.

---

## Page 3: Student Eligibility Analyzer
**Purpose**: Replicate the Streamlit "Student Analyzer" tool. A student inputs their expected Z-Score, and the dashboard dynamically color-codes all historical cutoffs to show where they would have been accepted.

### Page-Specific Slicer (What-If Parameter)
- **Your Expected Z-Score**: Slider Slicer using `'Student Analyzer'[Student Z-Score]`.

### Visuals
1. **Dynamic Eligibility Landscape (Scatter Plot)**:
   - **X-Axis**: `fact_cutoffs[CutoffZ]`
   - **Y-Axis**: `dim_course[CourseName]`
   - **Legend (Color)**: `[Eligibility Likelihood]` (DAX Measure)
   - **Tooltips**: `dim_university[UniversityName]`, `dim_district[DistrictName]`, `[Student Margin]`
   - *Design Tip*: Hardcode the legend colors exactly like Streamlit:
     - **Safe**: Green
     - **Possible**: Blue
     - **Competitive**: Orange
     - **Unlikely**: Red
   - *Feature*: Add an X-Axis Constant Line bound to the measure `[Selected Student Z-Score]` so the student sees a vertical line representing their score intersecting the historical cutoffs.

2. **Feasible Options (Table Visual)**:
   - **Filters on Visual**: Set `[Eligibility Likelihood]` to *is not* "Unlikely".
   - **Columns**: `dim_course[CourseName]`, `dim_university[UniversityName]`, `dim_district[DistrictName]`, `fact_cutoffs[CutoffZ]`, `[Eligibility Likelihood]`, `[Student Margin]`.
   - *Sort*: By `[Student Margin]` Descending.

---

## Page 4: Methodology & Limitations
**Purpose**: Provide clarity on how the metrics are calculated and warn against treating historical cutoffs as deterministic predictions.

### Visuals
1. **Text Boxes**:
   - **Competitiveness Index Explanation**: Detail how it normalizes Z-scores and penalizes volatility.
   - **NQC Handling**: Explain that "Not Qualified for Course" is handled strictly and excluded from arithmetic averages.
   - **Limitations Alert**: A highlighted warning box emphasizing that Z-scores depend dynamically on year-specific candidate performance and national demand. 

---
**Implementation Note for Developer**: 
Ensure that all relationships are active in the Model View (e.g., `fact_course_intake` connected to `dim_course` and `dim_year`). All measures listed above (e.g., `[Competitiveness Index]`, `[Eligibility Likelihood]`, `[YoY Cutoff Change]`) are fully pre-built in the `.tmdl` semantic model and are ready to be dragged onto the canvas.
