# Assignment Title: A Data-Driven Analysis of G.C.E. Advanced Level University Cutoff Trends and District Disparities in Sri Lanka

**Student Name:** [Insert Name]  
**Registration Number:** [Insert Registration Number]  

---

## 1. Introduction to the Selected Sri Lankan Problem

The transition from secondary education to state-funded higher education in Sri Lanka operates under an exceptionally competitive paradigm. The University Grants Commission (UGC) of Sri Lanka governs admissions using a dual-criteria mechanism: candidate performance, quantified via a standardized Z-score, and a complex district-based quota system designed to promote regional equity. 

Despite the critical nature of these cutoff thresholds, the historical data governing them is disseminated as fragmented, static PDF documents. This dissemination method inherently obscures long-term trends, obfuscates the true competitiveness of specific academic programs, and prevents a transparent evaluation of the district quota system's impact. Consequently, stakeholders—ranging from prospective undergraduates to educational policymakers—are deprived of the aggregate analytical visibility required to make informed, data-driven decisions. This project addresses this critical gap by engineering an automated data extraction pipeline and an interactive Business Intelligence (BI) dashboard to democratize access to historical university admission data.

## 2. Reason for Selecting the Problem

The rationale for investigating this specific domain is twofold, encompassing both socioeconomic and technical imperatives:

1. **Socioeconomic and Psychological Impact:** University admission in Sri Lanka is a high-stakes juncture that dictates future socioeconomic mobility. The current opacity surrounding historical cutoff fluctuations forces students to rely on anecdotal evidence when finalizing their university preferences, leading to significant psychological distress and sub-optimal academic placements. An interactive analytical tool mitigates this by providing empirical predictability.
2. **Evaluation of Policy Efficacy:** The district quota system has been a subject of continuous academic and public debate regarding its balance of equity versus meritocracy. By modeling this data dimensionally, it becomes possible to empirically visualize and quantify the exact magnitude of district-level disparities across highly coveted degrees (e.g., Medicine and Engineering), thereby providing a foundation for objective policy review.

## 3. Data Sources Used

The empirical foundation of this analysis relies exclusively on official datasets published by the University Grants Commission (UGC) of Sri Lanka. To ensure longitudinal validity, the data spans multiple academic years (2018/2019 through 2025/2026). The specific source vectors include:

* **Historical Cutoff Publications (COP):** Annual UGC PDF releases containing the minimum Z-score requirements for every course across all 25 administrative districts.
* **Intake Capacity Records (SEATS):** Official documentation detailing the total seating capacity allocated per course, per university, for corresponding academic years.
* **UGC UNICODES Mapping Directory:** The authoritative registry used to standardize the nomenclature of academic programs via 3-digit Course Codes (e.g., "001" for Medicine) and alphabetical University Codes (e.g., "A" for University of Colombo).

## 4. Brief Explanation of Data Cleaning and Preparation

The transformation of unstructured PDF reports into a query-optimized analytical model necessitated a robust ETL (Extract, Transform, Load) pipeline, developed utilizing Python. The methodology strictly adhered to standard data engineering principles:

* **Heuristic Data Extraction:** The raw documents possessed complex, landscape-oriented, nested tables with varying alignment. The `pymupdf` library was employed to programmatically navigate the document hierarchy, utilizing spatial coordinate mapping to accurately extract tabular data and resolve misalignments caused by rotated text bounding boxes.
* **Entity Standardization and Resolution:** Raw text extractions frequently contained typographical variations of university and course names across different years. A mapping layer was developed utilizing the UGC UNICODES directory to reliably bind disparate string values to their official, immutable identifiers.
* **Anomalous Data Handling (NQC):** The dataset prominently features "Not Qualified for Course" (NQC) designations. In the cleaning phase, it was paramount to preserve NQC as a distinct categorical state rather than coercing it to a numerical zero, as doing so would critically skew the arithmetic means and standard deviations of the historical cutoffs.
* **Dimensional Modeling:** The cleansed data was structured into a Kimball-style Star Schema, comprising fact tables (`fact_cutoffs`, `fact_course_intake`) and associated dimensions (`dim_course`, `dim_university`, `dim_district`, `dim_year`).
* **Semantic Layer Integration:** The relational schema was exported to SQLite and Parquet formats. Subsequently, an advanced Power BI Semantic Model was constructed using Tabular Model Definition Language (TMDL). Complex Data Analysis Expressions (DAX) were engineered to dynamically calculate advanced metrics, including Z-score Volatility (Standard Deviation) and a normalized Competitiveness Index.

## 5. Screenshots of the Power BI Dashboard

*(Note for submission: Replace the placeholder text below with high-resolution screenshots demonstrating the interactive features of your Power BI dashboard.)*

* **Figure 1: Executive Overview and National Competitiveness**  
  *[Insert Screenshot]*  
  *Caption: A macro-level view detailing national KPIs, total intake capacities, and a ranking of the top 10 most competitive courses based on the normalized Competitiveness Index.*

* **Figure 2: Course-Specific Historical Trends and Intake Volume**  
  *[Insert Screenshot]*  
  *Caption: A drill-through analysis of a selected course, plotting year-over-year Z-score fluctuations via line charts and comparing university-specific seat allocations.*

* **Figure 3: District Disparity Analysis**  
  *[Insert Screenshot]*  
  *Caption: Box-and-whisker distributions illustrating the variance in minimum Z-score requirements across the 25 administrative districts for high-demand disciplines.*

* **Figure 4: The Student Eligibility Analyzer**  
  *[Insert Screenshot]*  
  *Caption: An interactive "What-If" parameter tool allowing prospective candidates to input a hypothetical Z-score and dynamically visualize their probability of admission (Safe, Possible, Competitive, Unlikely) across historical contexts.*

## 6. Key Findings and Insights

The multidimensional analysis yielded several statistically significant insights regarding the dynamics of Sri Lankan university admissions:

* **Quantifiable District Disparities:** The data starkly illuminates the profound impact of the district quota system. For elite programs such as Medicine (Course Code: 001), the inter-district variance is extreme. Candidates operating within the Colombo district frequently face cutoff thresholds exponentially higher than those in less urbanized districts (e.g., Mullaitivu or Nuwara Eliya). While this fulfills the policy's objective of regional equity, the visualization highlights the intense bottleneck placed on urban merit candidates.
* **Oligopoly of Academic Demand:** A Pareto distribution is evident in course competitiveness. A minute fraction of disciplines—predominantly Medicine, Engineering, and emerging IT degrees—monopolize the highest national Z-scores. 
* **Cutoff Volatility as a Risk Factor:** Longitudinal analysis identified "High Volatility" courses—typically specialized management or newer technology degrees. These courses exhibit high standard deviations in their year-over-year cutoffs. This volatility poses a significant risk to applicants who treat previous-year cutoffs as static guarantees, emphasizing the danger of isolated data interpretation.
* **Stagnation of Capacity Against Inflationary Performance:** By cross-referencing `fact_cutoffs` with `fact_course_intake`, the analysis reveals that while candidate performance (and consequently, cutoff thresholds) experiences upward inflationary pressure in competitive districts, the corresponding seating capacity expands at a disproportionately slower rate, compounding systemic admission pressures.

## 7. Recommendations and Possible Solutions

Based on the empirical findings, the following systemic and localized recommendations are proposed:

1. **Deployment of Predictive Analytical Tooling:** The Ministry of Higher Education should transition away from static PDF disclosures and implement an interactive, public-facing intelligence portal akin to the Student Analyzer developed in this project. Providing probabilistic admission modeling would dramatically reduce student anxiety and optimize the preference-selection process.
2. **Data-Driven Quota Recalibration:** The stark variances visualized in the district disparity analysis suggest an urgent need for policy review. Policymakers should utilize longitudinal clustering algorithms to periodically reassess whether the current district quota percentages accurately reflect modern infrastructural disparities, or if they require recalibration to prevent undue penalty to high-performing cohorts.
3. **Targeted Infrastructural Expansion:** Universities should utilize "Volatility" metrics as leading indicators for academic demand. Courses exhibiting rapid, sustained spikes in cutoff requirements should be prioritized for immediate resource allocation and seating capacity expansion to absorb national demand efficiently.

## 8. Conclusion

This project successfully operationalized decades of fragmented, unstructured government data into a cohesive, interactive Business Intelligence solution. By employing rigorous data engineering methodologies—from heuristic PDF extraction to advanced dimensional modeling—the inherently opaque landscape of Sri Lankan university admissions was rendered transparent. The resulting analytical framework not only empowers prospective undergraduates with critical, actionable intelligence for their academic planning but also provides educational administrators with a macro-level diagnostic instrument to evaluate the efficacy, fairness, and systemic pressures of the prevailing admission infrastructure.

## 9. References

1. University Grants Commission of Sri Lanka. (n.d.). *University Admissions - Cutoff Marks & Intake Summaries*. Retrieved from [https://www.ugc.ac.lk/](https://www.ugc.ac.lk/)
2. Kimball, R., & Ross, M. (2013). *The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling* (3rd ed.). Wiley.
3. McKinney, W. (2022). *Python for Data Analysis: Data Wrangling with pandas, NumPy, and Jupyter* (3rd ed.). O'Reilly Media.
4. Microsoft Corporation. (n.d.). *Data Analysis Expressions (DAX) Reference*. Retrieved from [https://learn.microsoft.com/en-us/dax/](https://learn.microsoft.com/en-us/dax/)

## 10. Unlisted YouTube Video Link

**Video Presentation:** [Insert Unlisted YouTube URL Here]

---
*Generated for academic submission.*
