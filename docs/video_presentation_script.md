# Video Presentation Script: A/L Cutoffs & District Disparities
**Target Length:** 6-7 minutes (approx. 900 words)  
**Speaking Pace:** Relaxed, conversational  

---

**[0:00 - 1:00] Introduction & The Problem**

**[Camera: Full face visible, looking directly at the lens]**

Hello everyone. My name is [Your Name], and my registration number is [Your Registration Number]. Today, I'm going to walk you through my Power BI project analyzing Sri Lanka's G.C.E. Advanced Level university admission cutoffs. 

If you grew up in Sri Lanka, you already know how stressful university admissions can be. The University Grants Commission, or UGC, uses a combination of Z-scores and a district quota system to allocate seats. 

The problem is that the UGC publishes this data as static PDF documents every year. Because the data is locked in these PDFs, students can't easily track trends over time. They have to guess their chances based on a single past year, which leads to poor decisions when they rank their university preferences. Also, because the data isn't interactive, it's hard to clearly see how the district quota system actually impacts different regions. 

To fix this, I decided to extract eight years of historical data and build an interactive dashboard to make the admission process transparent.

**[1:00 - 2:30] Data Sources & Preparation**

**[Camera: Shrink to a small corner frame. Main screen shows the raw PDFs, then the Python code, then the Power BI model view]**

All the data comes directly from the official UGC website. I downloaded the annual Cutoff Publications from 2018 to 2026, the official Seat Allocation documents, and the UNICODES directory to map the exact course and university names.

Getting data out of PDFs is messy. I wrote a custom ETL pipeline in Python using the `pymupdf` library. The raw tables were landscape-oriented and often misaligned, so my script used spatial coordinates to match the headers to the data columns. 

One major cleaning step was handling "NQC", which stands for Not Qualified for Course. I deliberately kept NQC as a text label instead of converting it to a zero. If I had used zeroes, it would have ruined the mathematical averages for the Z-score trends later on. 

After cleaning, I structured the data into a Kimball Star Schema. The fact tables hold the cutoffs and intake numbers, while the dimension tables hold the courses, universities, districts, and years. Finally, I loaded it into Power BI using the Tabular Model Definition Language, or TMDL, where I wrote custom DAX measures to calculate standard deviations and competitiveness indexes.

**[2:30 - 5:30] Power BI Dashboard Walkthrough**

**[Screen Recording: Open the Power BI Dashboard to Page 1]**

Let's look at the dashboard. 

On this first page, the National Overview, we have the high-level KPIs at the top showing available courses and total intake. Below that, this horizontal bar chart ranks the top 10 most competitive courses in the country based on a custom DAX measure I built. 

**[Screen Recording: Click on Page 2 (Course & University Deep Dive)]**

Moving to the second page, we can dive into specific courses. If I select "Medicine" from the slicer here, the line chart instantly updates to show how the Z-score requirement has shifted over the last eight years across different universities. You can see the exact intake capacity for Medicine at the University of Colombo versus Peradeniya right next to it. 

**[Screen Recording: Click on Page 3 (District Disparities)]**

Page three is where we see the impact of the district quotas. This box plot shows the spread of minimum Z-scores across all 25 districts for high-demand fields. Notice how wide the gap is. If you hover over Colombo, you see the threshold is significantly higher than rural districts like Nuwara Eliya. This visually proves how tight the bottleneck is for urban candidates.

**[Screen Recording: Click on Page 4 (Student Eligibility Analyzer)]**

Finally, page four is the Student Eligibility Analyzer. I built a "What-If" parameter in Power BI that lets a student input their expected Z-score using this slider. 

Watch what happens when I move the slider to 1.8. The scatter plot dynamically color-codes all historical cutoffs. Green means a safe bet, blue is possible, and red is unlikely. Instead of guessing, a student can immediately see exactly which universities and courses historically match their performance.

**[5:30 - 6:30] Key Findings & Recommendations**

**[Camera: Full face visible again]**

Analyzing this data brought up a few clear insights. 

First, the district disparity is severe. The quota system effectively creates completely different entry standards depending on your home address, which puts massive pressure on urban students. 

Second, I noticed a huge risk factor in newer technology and specialized management courses. My DAX measures flagged these as "High Volatility." Their cutoffs bounce up and down wildly from year to year. Students relying on just last year's cutoff for these courses are taking a massive risk. 

Based on these findings, I have a few recommendations:
1. The Ministry of Higher Education needs to replace their static PDFs with a public, interactive database like this one. It would drastically reduce student anxiety.
2. Policymakers should use this modeled data to review the quota weights and ensure they still make sense for modern school infrastructures.
3. Universities should track the volatility of specific tech courses and immediately expand seat capacity where demand is consistently spiking.

**[6:30 - 7:00] Conclusion**

Overall, this project shows how data engineering and business intelligence can solve a real-world problem. By un-trapping data from PDFs, we can give students the clarity they need for their futures, and give administrators the insights they need to run a fair admission system.

Thank you for watching.

---
*(Note: After recording, upload the video to YouTube, set the visibility to "Unlisted", and paste the link into Section 10 of your PDF report before submission.)*
