# Redispatch in Germany: is the cost of grid congestion really falling?

**In one sentence:** when the power grid is overloaded, operators order some power plants down and others up (redispatch); this project looks at what that has cost since 2022 and whether the underlying congestion is shrinking.

Project page (charts, plain language): `docs/index.html`, served with GitHub Pages once Pages is enabled for the `/docs` folder.

## The question

Is redispatch getting cheaper because congestion is easing, or only because each unit is cheaper to handle? And what does that mean for a decision on grid investment?

## Who could benefit, and how

A grid-investment committee, a regulator's analyst or an energy journalist could use the charts to separate "the bill is lower" from "the problem is smaller" (plausible, not tested with a real user).

## Data and licence

- SMARD (Bundesnetzagentur): monthly volume (GWh) and cost (million EUR), generation by source. Credit: "Bundesnetzagentur | SMARD.de", licence CC BY 4.0.
- Netztransparenz (the four German transmission operators): list of 51,443 individual redispatch measures.
- Period: July 2022 to April 2026 (46 months). Files are in `data/raw/`. `src/fetch_smard_generation.py` downloads the hourly generation file again.
- Please check the current licence terms at both sources before reusing the data.

## How it works

1. Read monthly cost and volume. Divide to get euros per MWh.
2. Sum the individual measures by the grid operator that ordered them.
3. Compare reductions and increases, and conventional and renewable plants.
4. Compare monthly wind generation with redispatch volume for the months where both exist.

## Results

From `python src/build_results.py`, saved in `reports/results.json`.

- Monthly cost peaked at 348.8 million EUR in January 2023. April 2026 was 136.5 million (60.9 percent lower).
- A fairer comparison: the average of the last 12 months (126.4 million) is 38.4 percent below the 2023 average (205.2 million).
- Median cost per MWh by year: 128.5 (2022, 6 months), 91.5, 78.1, 68.4 (2025), 61.1 (2026, 4 months).
- Monthly volume stays between 715.9 and 3,493.7 GWh with no steady decline.
- TenneT DE ordered 27,091 GWh, 47.5 percent of the total. Amprion 14,661, 50Hertz 7,921, TransnetBW 7,413.
- Average reductions per month: 1,199 GWh in the first 24 months and 1,309 in the last 12. Increases: 771 and 603.
- Wind generation and redispatch volume, 13 overlapping months: correlation 0.75 (Spearman 0.76). A bootstrap 95 percent interval is 0.31 to 0.96, so the link is likely positive but poorly pinned down.

## Limitations

- 46 months, partial first and last years.
- Cost figures are as reported by the source and were not checked against operator accounts.
- The investment recommendation in the original report is an interpretation, not a cost-benefit study.
- The original report quoted reductions rising from about 1,215 to 1,300 GWh and increases falling from 810 to 635. Using the fixed windows above the numbers are 1,199 to 1,309 and 771 to 603. The direction is the same, the exact figures differ with the window chosen.

## How to run

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python src/build_results.py     # writes reports/results.json and docs/data.js
```

Open `docs/index.html` in a browser. `reports/original_d3_report.html` is the first version of the report, with D3 charts.

## What is coursework and what I extended

- Coursework (module M512 Data Visualization, Gisma): the analysis and the D3 report in `reports/original_d3_report.html` and `reports/chart-lib.js`.
- Extended afterwards: the recomputation script, the 12-month-average comparison, the wind correlation interval, and the Chart.js page. The submitted file with my student ID in its name is not part of this repository.
- Check your university's rules before publishing coursework.

## For technical readers

- Cost per MWh = `cost (million EUR) * 1e6 / (volume (GWh) * 1e3)`.
- Operator totals use `GESAMTE_ARBEIT_MWH` (German decimal comma) grouped by `ANWEISENDER_UENB`.
- Wind = onshore plus offshore hourly generation summed per month. The first, partial month is dropped. Bootstrap: 2,000 resamples of the 13 months, seed 42.

## Power BI package (untested in Power BI)

`powerbi/` holds a small star schema (`python src/export_powerbi.py`), DAX measures, a theme and a build guide. I could not run Power BI Desktop, so the measures are untested. The operator table covers only January 2024 to April 2026 (one measure on 31 December 2023 is included).

## Repository layout

```
data/raw/    SMARD and Netztransparenz CSV files
src/         build_results.py, export_powerbi.py, fetch_smard_generation.py
powerbi/     data/ (star schema CSVs), measures.dax, theme.json, BUILD_GUIDE.md
reports/     results.json, original_d3_report.html, chart-lib.js
docs/        static project page
```

Smrity Mallik, MSc AI and Data Science (Gisma, Berlin), B.Eng. Mechanical Engineering.
GitHub: github.com/malliksmrity. LinkedIn: linkedin.com/in/smritymallik.

## Process and automation

- `PROCESS.md`: backlog, definition of done and sprint rhythm for the next work (a plan, not past experience).
- `.github/workflows/ci.yml`: GitHub Actions check (written here, not yet run on GitHub).
- `Dockerfile`: container for the main script (not built or tested yet).
