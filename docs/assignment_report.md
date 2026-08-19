# Assignment Title: Data-Driven Analysis of Sri Lankan G.C.E. Advanced Level University Cutoff Trends

**Student Name:** [Your Name]  
**Registration Number:** [Your Registration Number]  

---

## 1. Introduction to the Selected Sri Lankan Problem
The transition from secondary education to state-funded higher education in Sri Lanka is highly competitive. The University Grants Commission (UGC) utilizes a complex Z-score system combined with a district quota mechanism to allocate limited university seats. However, historical cutoff data is typically published as static, isolated PDF documents. This fragmentation makes it incredibly difficult for students, educators, and policymakers to track historical trends, understand true course competitiveness, and gauge the impact of district-level disparities. The lack of an aggregated, interactive analytical tool leaves students guessing their eligibility likelihood, often leading to poor stream or course preferences.

## 2. Reason for Selecting the Problem
I selected this problem because university admission is a high-stakes, life-altering event for Sri Lankan youth. The current system's opacity causes immense stress and uncertainty. By transforming decades of static, unstructured UGC data into a dynamic analytical model, we can democratize access to this critical information. A data-driven dashboard allows students to make informed, realistic choices about their academic futures, and it exposes the stark realities of the district quota system, fostering transparent discussions about educational equity in Sri Lanka.

## 3. Data Sources Used
The analysis relies entirely on official, publicly available data published by the University Grants Commission (UGC) of Sri Lanka:
* **Historical Cutoff Documents:** Official UGC PDF releases containing Z-score cutoffs across 25 districts spanning academic years from 2018/2019 to 2025/2026.
* **Seat Allocation Data:** Official UGC Intake PDFs detailing the total seating capacity (seats available) for each course per academic year.
* **UGC UNICODES Mapping:** The official mapping document used to standardise the distinct Course Codes (e.g., "001" for Medicine) and University Codes (e.g., "A" for University of Colombo).

## 4. Brief Explanation of Data Cleaning or Preparation
The data preparation pipeline was built using Python and automated via an MLOps-ready framework. Key steps included:
1. **PDF Parsing & Table Extraction:** Utilized `pymupdf` and `pdfplumber` to accurately scrape highly nested tables from landscape-oriented PDFs.
2. **Column Misalignment Correction:** Implemented fuzzy-matching algorithms to dynamically align headers with data columns, circumventing issues caused by rotated text bounding boxes in the raw PDFs.
3. **Data Normalization:** Standardized course names, university names, and mapped them to their official 3-digit UGC Course Codes and alphabetical University Codes.
4. **Handling Edge Cases (NQC):** "Not Qualified for Course" (NQC) entries were strictly preserved as categorical statuses rather than being converted to zeroes, ensuring accurate arithmetic averages.
5. **Star Schema Modeling:** Transformed the cleaned data into a dimensional Star Schema (`dim_course`, `dim_university`, `dim_district`, `dim_year`, `fact_cutoffs`, `fact_course_intake`).
6. **Semantic Modeling:** Exported the schema to SQLite and Parquet, and built an advanced Power BI Semantic Model using the TMDL (Tabular Model Definition Language) format, featuring custom DAX measures for calculating Volatility and Competitiveness.

## 5. Screenshots of the Power BI Dashboard

*(Please insert your actual dashboard screenshots here before submitting)*

* **Figure 1: National Overview & Competitiveness**  
  `[Insert Screenshot showing the Top 10 Competitive Courses and High-level KPIs]`
  
* **Figure 2: Course & University Deep Dive**  
  `[Insert Screenshot showing YoY Line Charts and Intake distributions]`
  
* **Figure 3: District Disparities**  
  `[Insert Screenshot showing the Boxplot of Z-scores across the 25 districts]`
  
* **Figure 4: Student Eligibility Analyzer**  
  `[Insert Screenshot showing the What-If Parameter evaluating a specific student Z-Score]`

## 6. Key Findings and Insights
* **Extreme District Disparity:** The district quota system drastically shifts entry requirements. For high-demand courses like Medicine, the Z-score required from the Colombo district is significantly higher than that required from rural districts like Nuwara Eliya or Mullaitivu, visualizing the stark reality of the quota weighting.
* **Oligopoly of Demand:** A massive concentration of competitiveness exists in just a few fields—primarily Medicine, Engineering, and cutting-edge IT/Technology courses. These courses exhibit the highest median Z-scores globally.
* **High Cutoff Volatility:** Newer technology and specialized management courses show "High Volatility," meaning their cutoffs fluctuate wildly year-over-year as their popularity suddenly spikes among candidates, making them risky choices for borderline students.
* **Capacity Stagnation:** Despite rising candidate performance (evidenced by creeping Z-score trends in certain districts), the intake seat capacity (`fact_course_intake`) for top-tier universities remains relatively flat, intensifying competition each year.

## 7. Recommendations or Possible Solutions
1. **Interactive Guidance Portals:** The Ministry of Education should adopt dynamic dashboards similar to this project, retiring static PDFs. Students should be able to input their expected Z-scores and instantly see historically safe or risky courses.
2. **Re-evaluating District Quotas:** Policymakers can utilize the district-disparity visualizations to review whether the current quota percentages still accurately reflect infrastructural disadvantages, or if they are unduly punishing high-performing students in urban centers.
3. **Targeted Capacity Expansion:** Universities should align their infrastructure expansion with the "Volatility" metrics—courses that show rapid, sustained spikes in cutoff Z-scores require immediate intake capacity expansion to meet national demand.

## 8. Conclusion
This project successfully bridged the gap between fragmented government data and actionable educational intelligence. By applying modern data extraction, dimensional modeling, and interactive Power BI visualizations, the historical UGC cutoff data was transformed into a powerful Student Analyzer and Competitiveness tracker. The resulting dashboard not only assists prospective undergraduates in making realistic career choices but also serves as a macro-level diagnostic tool for observing the immense pressures and disparities inherent in the Sri Lankan state university admission system.

## 9. References
1. University Grants Commission (UGC) Sri Lanka. (n.d.). *University Admissions - Cutoff Marks*. Retrieved from [UGC Official Website](https://www.ugc.ac.lk/)
2. Python Software Foundation. (n.d.). *Python Language Reference*. Retrieved from https://www.python.org/
3. Microsoft. (n.d.). *Data Analysis Expressions (DAX) Reference*. Retrieved from https://learn.microsoft.com/en-us/dax/
4. *PyMuPDF Documentation*. (n.d.). Retrieved from https://pymupdf.readthedocs.io/

## 10. Unlisted YouTube Video Link
**Video Presentation:** `[Insert your unlisted YouTube URL here]`

---
*Generated for academic submission.*
