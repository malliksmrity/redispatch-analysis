# Redispatch in Germany: cost and volume of grid congestion management, 2022 to 2026

Analyzes monthly redispatch data to test whether costs and volumes are really changing, and includes a small congestion-management simulation and a Power BI model.

Live demos: https://huggingface.co/spaces/malliksmrity/grid-sim-env and https://huggingface.co/spaces/malliksmrity/redispatch-explorer


## 1. Problem
When the grid cannot carry the scheduled flow, operators pay plants to change output (redispatch). Monthly costs swing widely, so the question is whether cost and volume show a real trend or are just noise.

## 2. Data
Monthly redispatch figures from SMARD / Netztransparenz, July 2022 to April 2026 (46 months): volume (GWh), cost (million EUR), reductions and increases, and volumes by operator. The simulation uses real hourly German wind generation (SMARD, 12,961 hours).

## 3. Approach
1. Clean and aggregate monthly data; compute cost per MWh.
2. Test trends with Kendall's tau and Theil-Sen slopes.
3. Bootstrap year-on-year changes for 95 % ranges.
4. Build a star-schema model for Power BI with DAX measures.
5. Simulate one congested hour (north-south flow above the line limit), grading plans against the linear-programme optimum.

## 4. Results
| Quantity | Change per year | 95 % range |
|---|---|---|
| Cost per MWh | −11.6 % | −18.6 to −4.1 % |
| Volume | +8.6 % | −5.4 to +22.3 % |
| Total cost | −0.8 % | −17.8 to +19.4 % |

Cost per MWh fell with reasonable confidence; the volume and total-cost changes cannot be told apart from zero. The peak month (348.8 million EUR) against the latest month (136.5 million EUR) looks like a 61 % fall, but that compares two single months and is not a trend estimate.

Simulation (500 real wind hours): a naive largest-plant-first rule scores 0.71 against the optimum (1.0).

## 5. Technical notes
- Cost per MWh = total cost / total volume, so months are weighted by volume.
- Optimum: cheapest-first dispatch on each side equals the linear-programme solution for this two-zone problem; the grid, line limit (72 % of the scheduled flow), plant limits and prices are stylised assumptions.
- Power BI project in `powerbi/project_with_report/`: all 10 DAX measures reproduce the pandas values in `powerbi/expected_values.csv`.
- Reproduce: `pip install -r requirements.txt`, then `python src/build_results.py`.

## 6. Limitations
- 46 months only, so trend ranges are wide.
- Cost depends on prices and events not modelled here.
- The simulation grid is a teaching model; only the wind series is real.
- The Power BI report is a single overview page.

## 7. Deployment
| Item | Status |
|---|---|
| Static page (GitHub Pages, `/docs`) | live |
| Hugging Face static Spaces (grid simulator, explorer) | live |
| Power BI project | opens in Power BI Desktop; measures verified |
| CI (GitHub Actions) | passing |

Smrity Mallik, MSc AI and Data Science (Gisma, Berlin), B.Eng. Mechanical Engineering.

