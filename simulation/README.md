---
title: GridSimEnv
sdk: gradio
sdk_version: 6.30.0
app_file: app.py
pinned: false
---

# GridSimEnv: resolve a grid congestion at minimum cost

A simulation environment on real hourly wind data (SMARD, 12,961 hours). In each hour the market schedule sends more power from the north to the south than the line can carry. The agent redispatches: reduce generation in the north and increase it by the same amount in the south, at minimum cost.

- **Tools:** `reset(hour)`, `get_situation()`, `check_plan(plan)`, `submit_plan(plan)`.
- **Grade:** optimal cost divided by your cost (1.0 = optimal), 0 if the plan breaks a rule. The optimum is solved as a linear programme (scipy).
- **Assumptions (stylised, not calibrated to real plant prices):** a two-zone grid, the north exports 20 percent of German wind, the line carries 72 percent of the scheduled flow, six plants with assumed prices. Wind curtailment is the most expensive option (120 EUR/MW) because curtailed wind is compensated.
- **Real:** the wind series.

Files: `grid_env.py`, `evaluate.py` (writes `results.json`), `app.py` (live app), `smard_generation_hourly.csv`.

## Deploy (you do this, with your own Hugging Face account)

1. Create a new Space: SDK Gradio, free CPU.
2. Clone it and copy everything from this `simulation/` folder into it.
3. `git add . && git commit -m "first version" && git push`.

Run locally: `pip install -r requirements.txt` then `python app.py`.