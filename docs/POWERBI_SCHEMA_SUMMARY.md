# Power BI Schema Summary

This project exposes a star-schema model designed for Power BI and similar BI tools.

## Fact table

### fact_cutoffs

This is the central fact table. One row represents a single cutoff value for a course at a university in a district for a given academic year.

Columns:

- AcademicYear: text
- ExamYear: integer
- PublicationDate: text (ISO date)
- CourseID: text
- CourseName: text
- UniversityID: text
- UniversityName: text
- DistrictID: text
- DistrictName: text
- CutoffZ: float/null
- CutoffStatus: text
  - AVAILABLE
  - NQC
  - MISSING
  - UNPARSED:<raw value>
- AllIslandMerit: boolean
- AptitudeTest: boolean
- Page: integer
- SourceFile: text

Recommended usage:

- Use this as the main fact table in Power BI.
- Create measures such as:
  - Average CutoffZ
  - Count of Available Cutoffs
  - Count of NQC values
  - Minimum/Maximum CutoffZ by course or district

## Dimension tables

### dim_course

Unique course dimension.

Columns:

- CourseID: text (primary key)
- CourseName: text

Relationships:

- `dim_course[CourseID]` -> `fact_cutoffs[CourseID]`

### dim_university

Unique university dimension.

Columns:

- UniversityID: text (primary key)
- UniversityName: text

Relationships:

- `dim_university[UniversityID]` -> `fact_cutoffs[UniversityID]`

### dim_district

District dimension based on official Sri Lankan district names used in the source document.

Columns:

- DistrictID: text (primary key)
- DistrictName: text

Relationships:

- `dim_district[DistrictID]` -> `fact_cutoffs[DistrictID]`

### dim_year

Year dimension for the publication cycle.

Columns:

- YearID: text (primary key)
- AcademicYear: text
- ExamYear: integer
- PublicationDate: text

Relationships:

- `dim_year[AcademicYear]` -> `fact_cutoffs[AcademicYear]`

Note: because the fact table stores `AcademicYear` and `ExamYear` directly, a relationship on `AcademicYear` is practical for slicers, but a custom relationship on `ExamYear` is also possible if needed.

## Relationship model

Use the following one-to-many relationships in Power BI:

- `dim_course` -> `fact_cutoffs` on `CourseID`
- `dim_university` -> `fact_cutoffs` on `UniversityID`
- `dim_district` -> `fact_cutoffs` on `DistrictID`
- `dim_year` -> `fact_cutoffs` on `AcademicYear`

This creates a star schema with a single fact table and four supporting dimensions.

## Data quality notes

- `CutoffZ` is stored as null for `NQC` and other non-numeric statuses.
- `CutoffStatus` captures the actual extraction outcome and helps separate valid values from missing or unparsed data.
- `AllIslandMerit` and `AptitudeTest` are preserved as boolean indicators from the source document.
- `SourceFile` and `Page` help trace the original PDF and page of extraction for auditing.
- University names are standardized before bronze writes to reduce duplicates from layout/OCR variations.
- Example canonical mappings include:
  - `Eastern University -Trincomalee Campus` -> `Eastern University - Trincomalee Campus`
  - `Trincomalee Campus, Eastern University, Sri Lanka` -> `Eastern University - Trincomalee Campus`
  - `Institute of Indigenous Medicine` / `Gampaha Wickramaarachchi Ayurveda Institute` -> `The Gampaha Wickramarachchi University of Indigenous Medicine, Sri Lanka`

## Suggested Power BI visuals

Useful starting visuals:

- Matrix: District by Course, showing average `CutoffZ`
- Bar chart: University ranking by average cutoff
- Line chart: trend by `ExamYear` or `AcademicYear`
- KPI cards:
  - Average cutoff
  - Count of available scores
  - Count of NQC entries
- Slicer filters:
  - CourseName
  - UniversityName
  - DistrictName
  - AcademicYear
  - AllIslandMerit
  - AptitudeTest

## Example DAX measures

```DAX
Average Cutoff Z =
AVERAGE(fact_cutoffs[CutoffZ])

Available Cutoffs =
CALCULATE(
    COUNTROWS(fact_cutoffs),
    fact_cutoffs[CutoffStatus] = "AVAILABLE"
)

NQC Count =
CALCULATE(
    COUNTROWS(fact_cutoffs),
    fact_cutoffs[CutoffStatus] = "NQC"
)
```

## Output folder

The generated files are located in:

```text
data/bronze/
  fact_cutoffs.csv
  dim_course.csv
  dim_university.csv
  dim_district.csv
  dim_year.csv
  al_cutoffs.db
  fact_cutoffs.parquet
  dim_course.parquet
  dim_university.parquet
  dim_district.parquet
  dim_year.parquet
```

This output is ready for direct import into Power BI.
