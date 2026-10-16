"""Score plans in GridSimEnv over 500 random real wind hours.  Run: python simulation/evaluate.py   (writes results.json)"""
import json
from pathlib import Path

import numpy as np

import grid_env as g

env = g.GridSimEnv()
rng = np.random.default_rng(42)
hours = rng.choice(len(env.h), 500, replace=False)
rows = {"naive rule (largest plant first)": [], "cheapest first (the optimum)": []}
for i in hours:
    env.reset(i)
    if env.excess <= 0:
        continue
    rows["naive rule (largest plant first)"].append(env.submit_plan(g.naive_plan(env)))
    rows["cheapest first (the optimum)"].append(env.submit_plan(g.greedy_plan(env)))
out = {"hours": int(len(rows["naive rule (largest plant first)"])), "assumption": "stylised two-zone grid and prices, see grid_env.py", "policies": {}}
for k, v in rows.items():
    r = [x["reward"] for x in v]
    c = [x.get("cost_EUR", 0) for x in v if x["valid"]]
    out["policies"][k] = {"valid_share": round(float(np.mean([x["valid"] for x in v])), 3), "mean_score": round(float(np.mean(r)), 3), "mean_cost_EUR": round(float(np.mean(c)))}
out["mean_excess_MW"] = round(float(np.mean([env.reset(i)["must_redispatch_MW"] for i in hours])), 0)
(Path(__file__).resolve().parent / "results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))