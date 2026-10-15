# Build the Power BI report (about 60 to 90 minutes)

Why this exists: the project page is a static Chart.js page. Power BI is what many German employers use for reporting, so this folder prepares a clean data model and measures. **I could not open Power BI Desktop while preparing this, so the DAX in `measures.dax` and these steps are untested. Building the report yourself is the point: you will be able to explain every number.**

Tool: Power BI Desktop (free, Windows). Do not publish to the Power BI service with your university account without checking the rules.

## 1. Load the data
1. Home, Get data, Text/CSV. Load `data/fact_monthly.csv`, `data/dim_month.csv`, `data/fact_operator_monthly.csv`. Accept the detected types.
2. In each table set `month` to the Date type.

## 2. Model (star schema)
1. Model view. Drag `dim_month[month]` onto `fact_monthly[month]` and onto `fact_operator_monthly[month]`. Both: many to one, single direction.
2. Mark `dim_month` as the date table (Table tools, Mark as date table, column `month`).

## 3. Measures
Create each measure in `measures.dax` with Modeling, New measure. Check each one against `reports/results.json`:
- Latest month cost 136.48 and peak 348.8 (decline about 60.9 percent).
- Cost per MWh for 2025 as a yearly figure: compare with the project page (median is shown there, a ratio of sums differs slightly).
- TenneT DE share of operator energy for Jan 2024 to Apr 2026 will differ from the README (47.5 percent) because the operator table does not cover 2022 and 2023.

## 4. Pages
Page 1 "Cost": column and line chart (month on the axis, Total Cost and Cost 12M Average), cards (Latest Month Cost, Decline From Peak %).
Page 2 "Volume": line chart of Total Volume (GWh) by month; clustered columns of reductions versus increases.
Page 3 "Operators": bar chart of Operator Energy by operator, slicer on `energy_type` and `direction`.
Give each visual a plain title that states the finding, as on the project page. View, Themes, Browse for themes, `theme.json`.

## 5. Before you show it
- Add a text box with the data source and licence (SMARD, CC BY 4.0; Netztransparenz).
- Export a PDF for your application. Keep the `.pbix` private unless you have checked licences.
