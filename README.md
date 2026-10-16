# Redispatch in Germany: is the cost of grid congestion really falling?

**In one sentence:** when the power grid is overloaded, operators order some power plants down and others up (redispatch); this project measures what that has cost since 2022 and tests whether the congestion behind it is shrinking.

Live page: `docs/index.html` (GitHub Pages, folder `/docs`). Live explorer for Hugging Face Spaces: `space/`. Power BI package: `powerbi/`.

## 1. Problem

Germany's wind is mostly in the north and its demand in the south and west, so power lines get overloaded. Grid operators fix this with redispatch and the bill is paid by electricity customers. Politicians and the press say the bill is falling. A grid-investment committee needs to know two different things: is the **bill** falling, and is the **problem** (the amount of power moved) getting smaller? Only the second one says whether more grid is needed.

Who could use the answer: a regulator's analyst, an investment committee, an energy journalist (plausible uses, not tested with real users).

## 2. Dataset

| Source | Content | Licence |
|---|---|---|
| SMARD, Bundesnetzagentur | monthly redispatch volume (GWh) and cost (million EUR), July 2022 to April 2026 (46 months); hourly generation by source | "Bundesnetzagentur / SMARD.de", CC BY 4.0 |
| Netztransparenz (the four transmission operators) | 51,443 individual redispatch measures from 31 December 2023 to 8 September 2026 (longer than the monthly series): operator, direction, plant type, energy | check the terms at the source before reuse |

Files: `data/raw/`. `src/fetch_smard_generation.py` downloads the generation file again.

## 3. How I solved it

1. Compute cost per MWh (cost divided by volume) for every month.
2. Compare each month with the same month one year earlier, so winter peaks do not distort the picture.
3. Test whether the changes are real with a bootstrap range and a rank test, because 46 months is a short series.
4. Split the measures by ordering operator, by direction (reduce or increase output) and by plant type.
5. Compare monthly redispatch volume with wind generation (13 overlapping months).

## 4. Findings

- **The bill peaked at 348.8 million EUR in January 2023.** April 2026 was 136.5 million, 60.9 percent lower. A fairer comparison: the average of the last 12 months (126.4 million) is 38.4 percent below the 2023 average (205.2 million).
- **The cost per MWh has really fallen:** median 128.5 EUR (2022) to 68.4 (2025). Year on year it changes by −11.6 percent (95 percent range −18.6 to −4.1). Theil-Sen slope −11.7 EUR per MWh per year (range −15.4 to −8.2), Kendall tau −0.53.
- **The volume has not clearly changed:** year on year +8.6 percent (range −5.4 to +22.3), Kendall tau 0.01 (p = 0.93). The same for total cost: −0.8 percent (range −17.8 to +19.4). With 34 comparable months the data cannot distinguish flat from about ±20 percent.
- **So the case for investment rests on the volume, which has not clearly fallen**, not on the cost, which has.
- **TenneT DE ordered 47.5 percent** of the redispatched energy (27,091 GWh), Amprion 25.7, 50Hertz 13.9, TransnetBW 13.0 (all measures up to 8 September 2026).
- **Wind and redispatch volume move together** (13 months, correlation 0.75, bootstrap range 0.31 to 0.96): likely a real link, poorly pinned down.
- Average monthly reductions rose from 1,199 GWh (first 24 months) to 1,309 (last 12); increases fell from 771 to 603.

## 5. Models and methods used

No machine-learning model: this is a descriptive and statistical analysis, chosen on purpose. The question is about trends and uncertainty, not prediction.

- Year-on-year percentage change with a **bootstrap** confidence interval (3,000 resamples).
- **Kendall tau** rank test and **Theil-Sen** robust slope for monotonic trends.
- Pearson and Spearman correlation with a bootstrap range for the wind link.

## 6. Technical documentation

- Cost per MWh = `cost (million EUR) × 1e6 / (volume (GWh) × 1e3)`.
- Operator totals use `GESAMTE_ARBEIT_MWH` (German decimal comma) grouped by `ANWEISENDER_UENB`.
- Wind = onshore plus offshore hourly generation summed per month; the first, partial month is dropped.
- Year-on-year uses each month against the same month 12 months earlier (34 pairs).
- Seeds: bootstrap 42 (wind) and 7 (trend).
- Reproduce: `pip install -r requirements.txt` then `python src/build_results.py` (writes `reports/results.json`, `docs/data.js`) and `python src/export_powerbi.py`.
- Limits: 46 months, partial first and last years; cost as reported by the source, not checked against operator accounts; the investment recommendation of the original report is an interpretation, not a cost-benefit study; the operator table starts in 2024.
- The original coursework report (D3 charts) is `reports/original_d3_report.html`. Its reduction/increase figures (1,215→1,300 and 810→635) differ from the fixed-window figures above, because the windows differ.

## 7. Output

- Static project page with five charts and the trend table: `docs/index.html`.
- A Hugging Face Space app to explore metric, years and operators: `space/`.
- Power BI package: star-schema CSVs (`powerbi/data/`), DAX measures (`powerbi/measures.dax`), theme and a build guide. **The DAX is untested** because I could not run Power BI Desktop. Building the report yourself is the next step.
- Machine-readable results: `reports/results.json`.

## 8. Deployment

**Live (Hugging Face static Spaces):** https://huggingface.co/spaces/malliksmrity/grid-sim-env (simulation) and https://huggingface.co/spaces/malliksmrity/redispatch-explorer (explorer)

**Simulation environment (simulation/):** GridSimEnv resolves a north-south congestion in a real wind hour at minimum cost, graded against a linear-programme optimum. The wind series is real; the two-zone grid, line limit and prices are stylised assumptions. A naive largest-plant-first rule scores 0.71 over 500 hours. Live Gradio app, Space-ready, not yet deployed. n8n workflow in utomation/n8n/ (SMARD live feed tested, n8n itself untested).

| What | How | Status |
|---|---|---|
| Static page | GitHub Pages, branch + folder `/docs` | needs enabling |
| Live explorer | Hugging Face Space (Gradio), folder `space/`, steps in `space/README.md` | not deployed (needs your account) |
| Container | `Dockerfile` runs `src/build_results.py` | written, not built |
| CI | `.github/workflows/ci.yml` re-runs the script on every push | written, not yet run on GitHub |
| Process | `PROCESS.md`: backlog, definition of done | plan, not past experience |

## Coursework and extensions

Coursework (module M512 Data Visualization, Gisma): the analysis and the D3 report. Extended afterwards: recomputation script, trend tests, wind interval, Chart.js page, Power BI package, Space app. Check your university's rules before publishing coursework (your college has approved publishing, results pending).

Smrity Mallik, MSc AI and Data Science (Gisma, Berlin), B.Eng. Mechanical Engineering. GitHub: github.com/malliksmrity. LinkedIn: linkedin.com/in/smritymallik.
