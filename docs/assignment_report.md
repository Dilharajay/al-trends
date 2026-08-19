# Assignment Title: Analyzing G.C.E. Advanced Level University Cutoffs and District Disparities in Sri Lanka

**Student Name:** [Insert Name]  
**Registration Number:** [Insert Registration Number]  

---

## 1. Introduction to the Selected Sri Lankan Problem

Admission to state-funded universities in Sri Lanka is highly competitive. The University Grants Commission (UGC) determines admissions using a student's Z-score alongside a district quota system designed to maintain regional equity. 

While the UGC publishes these cutoff marks annually, they are released as static PDF documents. This format makes it nearly impossible for students, teachers, or researchers to analyze historical trends, compare cutoffs across different universities, or clearly see how the district quota system impacts specific courses. Because the data is locked in PDFs, stakeholders lack the tools needed to make informed decisions. This project solves that problem by extracting the historical data and building an interactive dashboard.

## 2. Reason for Selecting the Problem

I chose this problem because university admission causes significant stress for Sri Lankan students. They often have to guess their chances based on isolated cutoffs from a single previous year, which can lead to poor choices when ordering their university preferences. 

Additionally, the district quota system is frequently debated. By putting the historical data into a structured database, we can actually measure and visualize the exact Z-score differences between urban and rural districts for courses like Medicine or Engineering. This shifts the conversation from anecdotal assumptions to empirical facts.

## 3. Data Sources Used

The analysis uses official data published by the University Grants Commission spanning from the 2018/2019 academic year to 2025/2026. The sources include:

* **Cutoff Publications:** Annual PDFs containing the minimum Z-score required for every course across all 25 districts.
* **Intake Capacity Records:** Documents showing the total number of seats allocated for each course at each university.
* **UNICODES Mapping Directory:** The official UGC codebook used to standardize course names (e.g., "001" for Medicine) and university names.

## 4. Brief Explanation of Data Cleaning and Preparation

Extracting tabular data from the UGC PDFs required a custom ETL pipeline written in Python. The main challenges and steps included:

* **PDF Extraction:** The raw documents are landscape-oriented with nested, poorly aligned tables. I used the `pymupdf` library to map the spatial coordinates of the text, allowing the script to properly align the headers with the data columns.
* **Standardizing Names:** University and course names often had slight spelling variations across different years. I matched all extracted names to the official UGC UNICODES directory to assign them immutable IDs.
* **Handling NQC:** Many cells contain "NQC" (Not Qualified for Course). I kept this as a distinct text status rather than converting it to zero. Converting it to zero would have ruined the mathematical averages when calculating Z-score trends later.
* **Data Modeling:** I structured the clean data into a Star Schema with fact tables for cutoffs and intakes, and dimension tables for courses, universities, districts, and years.
* **Power BI Integration:** The database was exported to SQLite and Parquet formats. I then built a Power BI Semantic Model using DAX to calculate custom metrics, like the standard deviation of cutoffs over time.

## 5. Screenshots of the Power BI Dashboard

*(Note for submission: Insert your actual screenshots below.)*

* **Figure 1: National Overview**  
  *[Insert Screenshot]*  
  *Caption: Shows national KPIs, total seat capacities, and ranks the most competitive courses.*

* **Figure 2: Historical Trends**  
  *[Insert Screenshot]*  
  *Caption: Tracks Z-score changes for a selected course across different universities over the last eight years.*

* **Figure 3: District Disparity**  
  *[Insert Screenshot]*  
  *Caption: Box plots showing how minimum Z-scores vary across the 25 administrative districts for high-demand fields.*

* **Figure 4: Student Eligibility Analyzer**  
  *[Insert Screenshot]*  
  *Caption: An interactive tool where a student inputs their Z-score to see which courses and universities historically match their results.*

## 6. Key Findings and Insights

Analyzing the modeled data revealed several clear patterns in the admission system:

* **Severe District Disparities:** The quota system creates massive entry gaps. For Medicine, students from the Colombo district face cutoff scores that are drastically higher than students applying from districts like Mullaitivu or Nuwara Eliya. The dashboard visualizations show how tight the bottleneck is for urban candidates.
* **Concentrated Demand:** A very small number of disciplines—mainly Medicine, Engineering, and IT—drive the highest Z-scores nationwide. 
* **Risky Volatility in Tech Courses:** Newer technology and specialized management degrees show high standard deviations in their cutoffs. Their requirements bounce up and down heavily from year to year. Students relying on a single previous year's cutoff for these courses face a high risk of rejection.
* **Stagnant Seat Capacity:** While the Z-scores required for competitive courses have crept upward over the years, the intake capacity for those specific top-tier courses has remained relatively flat. The system is getting harder to enter simply because supply is not matching the inflating demand.

## 7. Recommendations or Possible Solutions

1. **Interactive Tools for Students:** The Ministry of Higher Education should replace static PDF releases with a public, interactive database. If students could input their scores and see historical probabilities like the Student Analyzer built here, it would significantly reduce anxiety and poor preference ordering.
2. **Reviewing Quota Percentages:** Policymakers can use the district disparity data to evaluate if the current quota weights still make sense. The data can help determine if the penalty on high-performing urban students is proportionate to the actual infrastructural gaps in rural schools today.
3. **Expanding Specific Intakes:** Universities should track the volatility and upward trends of specific courses to decide where to build new infrastructure. Courses that show consecutive years of rising cutoffs need immediate seat expansion.

## 8. Conclusion

This project took eight years of disconnected government PDFs and turned them into a structured database and an interactive dashboard. By writing custom Python scripts to parse the files and using Power BI to visualize the results, it solves a real problem for Sri Lankan students. The final tool makes it easy to explore admission trends, exposes the reality of the district quota system, and provides a clear example of how open data can improve the university application process.

## 9. References

1. University Grants Commission of Sri Lanka. (n.d.). *University Admissions - Cutoff Marks & Intake Summaries*. Retrieved from https://www.ugc.ac.lk/
2. Kimball, R., & Ross, M. (2013). *The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling* (3rd ed.). Wiley.
3. McKinney, W. (2022). *Python for Data Analysis: Data Wrangling with pandas, NumPy, and Jupyter* (3rd ed.). O'Reilly Media.

## 10. Unlisted YouTube Video Link

**Video Presentation:** [Insert Unlisted YouTube URL Here]
