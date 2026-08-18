# Power BI Model Relationships Guide

This guide explains how to configure the AL Trends dataset in Power BI using a star schema.

## Tables to import

Import from either:

- `data/bronze/csv/` (CSV files), or
- `data/bronze/parquet/` (Parquet files), or
- `data/bronze/db/al_cutoffs.db` (SQLite)

Expected tables:

- `fact_cutoffs`
- `dim_course`
- `dim_university`
- `dim_district`
- `dim_year`

## Recommended model layout

Use `fact_cutoffs` as the center fact table and connect all dimensions to it.

Relationships:

1. `dim_course[CourseID]` -> `fact_cutoffs[CourseID]`
2. `dim_university[UniversityID]` -> `fact_cutoffs[UniversityID]`
3. `dim_district[DistrictID]` -> `fact_cutoffs[DistrictID]`
4. `dim_year[AcademicYear]` -> `fact_cutoffs[AcademicYear]`

Relationship settings:

- Cardinality: One-to-many (`1:*`) from dimension to fact
- Cross-filter direction: Single (dimension -> fact)
- Active relationship: Yes

## Why `AcademicYear` for dim_year

`dim_year` contains one row per academic cycle and `fact_cutoffs` already stores `AcademicYear`, so this is the cleanest join key for time slicing in reports.

## Data type checks in Power BI

Before building visuals, confirm these data types:

- `fact_cutoffs[CutoffZ]`: Decimal number
- `fact_cutoffs[ExamYear]`: Whole number
- `fact_cutoffs[Page]`: Whole number
- `fact_cutoffs[AllIslandMerit]`: True/False
- `fact_cutoffs[AptitudeTest]`: True/False
- `fact_cutoffs[PublicationDate]`: Date
- `dim_year[PublicationDate]`: Date

## Suggested calculated columns/measures

### Helpful measure: available-only average

```DAX
Average Cutoff Z (Available) =
CALCULATE(
    AVERAGE(fact_cutoffs[CutoffZ]),
    fact_cutoffs[CutoffStatus] = "AVAILABLE"
)
```

### Helpful measure: NQC count

```DAX
NQC Count =
CALCULATE(
    COUNTROWS(fact_cutoffs),
    fact_cutoffs[CutoffStatus] = "NQC"
)
```

### Helpful measure: Available records

```DAX
Available Records =
CALCULATE(
    COUNTROWS(fact_cutoffs),
    fact_cutoffs[CutoffStatus] = "AVAILABLE"
)
```

## Visual setup checklist

- Add slicers for:
  - `dim_year[AcademicYear]`
  - `dim_course[CourseName]`
  - `dim_university[UniversityName]`
  - `dim_district[DistrictName]`
- Use `CutoffStatus` to filter out non-numeric records when needed.
- Prefer dimension fields in axes/legends (not fact text fields) to avoid duplicated labels.

## Common issues and fixes

1. Duplicate labels in visuals:
- Use dimension columns (`dim_*`) rather than text columns in `fact_cutoffs`.

2. Wrong averages:
- Filter `CutoffStatus = "AVAILABLE"`.

3. Time slicer not filtering:
- Verify active relationship between `dim_year[AcademicYear]` and `fact_cutoffs[AcademicYear]`.

4. Missing rows after filters:
- Confirm relationship direction is single and cardinality is `1:*`.

## Quick validation query (Power BI DAX Studio optional)

```DAX
EVALUATE
SUMMARIZECOLUMNS(
    dim_year[AcademicYear],
    "Rows", COUNTROWS(fact_cutoffs),
    "Available", CALCULATE(COUNTROWS(fact_cutoffs), fact_cutoffs[CutoffStatus] = "AVAILABLE"),
    "NQC", CALCULATE(COUNTROWS(fact_cutoffs), fact_cutoffs[CutoffStatus] = "NQC")
)
```
