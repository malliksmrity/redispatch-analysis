"""GridSimEnv: resolve a north-south grid congestion at minimum cost (a stylised redispatch problem).

STYLISED, NOT CALIBRATED TO REAL PLANT PRICES. What is real: the hourly wind generation, taken from SMARD
(data/raw/smard_generation_hourly.csv). What is assumed: a two-zone grid, the north exports to the south over one line, the
line limit, the plants and their redispatch prices. The point is the decision problem and a provable optimum, as in the
real operators' task.

Situation for one hour: the north has wind plus a conventional fleet; the market schedule sends `flow` MW over the line, which
is above its limit. The operator must cut the flow to the limit by redispatch:
  - reduce generation in the north (conventional plants, or wind curtailment, which is the most expensive because curtailed wind is compensated), and
  - increase generation in the south by the same amount (gas peakers, a reserve plant).
Every MW reduced in the north is replaced one for one in the south. Prices (EUR per MW of redispatch, per hour) are stylised.
The cheapest feasible plan is the linear-programming optimum (solved with scipy), so a plan is graded against it.

API: reset(hour_index) / get_situation() / check_plan(plan) / submit_plan(plan); plan = dict of MW per option.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.optimize import linprog

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "smard_generation_hourly.csv"
if not RAW.exists():
    RAW = Path(__file__).resolve().parent / "smard_generation_hourly.csv"

# redispatch options: name, zone, max MW, price EUR per MW (stylised assumption)
DOWN = {"North wind curtailment": (None, 120.0), "North lignite plant": (1500.0, 95.0), "North gas plant": (900.0, 80.0)}
UP = {"South gas peaker": (1400.0, 140.0), "South hard-coal reserve": (1000.0, 110.0), "South hydro/pumped storage": (600.0, 75.0)}
LINE_LIMIT_SHARE = 0.72   # the line can carry 72 percent of the scheduled flow (assumption)
SCALE = 0.20              # the modelled north exports 20 percent of Germany's wind (assumption)


def load_hours():
    d = pd.read_csv(RAW, parse_dates=["timestamp_utc"])
    d["wind"] = d[["Wind onshore", "Wind offshore"]].sum(axis=1, min_count=1)
    d = d.dropna(subset=["wind"]).reset_index(drop=True)
    return d


class GridSimEnv:
    def __init__(self):
        self.h = load_hours()
        self.i = 0

    def reset(self, hour_index: int):
        self.i = int(hour_index) % len(self.h)
        r = self.h.iloc[self.i]
        self.flow = float(r.wind) * SCALE            # scheduled flow north to south, MW
        self.limit = self.flow * LINE_LIMIT_SHARE
        self.excess = self.flow - self.limit         # MW that must be redispatched
        return self.get_situation()

    def get_situation(self):
        wind = float(self.h.iloc[self.i].wind)
        return {"hour": str(self.h.iloc[self.i].timestamp_utc), "german_wind_MW": round(wind), "scheduled_flow_MW": round(self.flow), "line_limit_MW": round(self.limit),
                "must_redispatch_MW": round(self.excess, 1),
                "down_options": {k: {"max_MW": (round(self.flow) if v[0] is None else v[0]), "price": v[1]} for k, v in DOWN.items()},
                "up_options": {k: {"max_MW": v[0], "price": v[1]} for k, v in UP.items()},
                "rule": "total reduction in the north must equal total increase in the south, and both must be at least the excess"}

    def _caps(self):
        return {**{k: (self.flow if v[0] is None else v[0]) for k, v in DOWN.items()}, **{k: v[0] for k, v in UP.items()}}

    def check_plan(self, plan: dict):
        caps, errs = self._caps(), []
        down = sum(plan.get(k, 0.0) for k in DOWN)
        up = sum(plan.get(k, 0.0) for k in UP)
        for k, v in plan.items():
            if k not in caps:
                errs.append(f"unknown option {k}")
            elif v < -1e-6 or v > caps[k] + 1e-6:
                errs.append(f"{k}: {v:.0f} MW outside 0..{caps[k]:.0f}")
        if abs(down - up) > 1.0:
            errs.append(f"reduction ({down:.0f} MW) and increase ({up:.0f} MW) must balance")
        if down < self.excess - 1.0:
            errs.append(f"flow still {self.excess - down:.0f} MW over the limit")
        price = {**{k: v[1] for k, v in DOWN.items()}, **{k: v[1] for k, v in UP.items()}}
        cost = sum(plan.get(k, 0.0) * price[k] for k in plan if k in price)
        return {"valid": not errs, "errors": errs, "cost_EUR": round(cost)}

    def optimum(self):
        names = list(DOWN) + list(UP)
        price = [DOWN[k][1] for k in DOWN] + [UP[k][1] for k in UP]
        caps = self._caps()
        A_eq = [[1.0] * len(DOWN) + [-1.0] * len(UP)]
        A_ub = [[-1.0] * len(DOWN) + [0.0] * len(UP)]  # total reduction >= excess
        res = linprog(price, A_ub=A_ub, b_ub=[-self.excess], A_eq=A_eq, b_eq=[0.0], bounds=[(0, caps[k]) for k in names], method="highs")
        return {"plan": {k: round(float(x), 1) for k, x in zip(names, res.x) if x > 1e-6}, "cost_EUR": round(float(res.fun))}

    def submit_plan(self, plan: dict):
        c, o = self.check_plan(plan), self.optimum()
        if not c["valid"]:
            return {"reward": 0.0, "valid": False, "errors": c["errors"], "optimal_cost_EUR": o["cost_EUR"]}
        score = float(np.clip(o["cost_EUR"] / c["cost_EUR"], 0, 1)) if c["cost_EUR"] > 0 else 1.0
        return {"reward": round(score, 3), "valid": True, "cost_EUR": c["cost_EUR"], "optimal_cost_EUR": o["cost_EUR"], "optimal_plan": o["plan"]}


# --- baseline policies ---------------------------------------------------------------------------
def naive_plan(env: GridSimEnv):
    """Cut the first (largest) conventional plant and replace with the first peaker: what a quick rule might do."""
    ex = env.excess
    d = {"North lignite plant": min(ex, 1500.0)}
    rest = ex - d["North lignite plant"]
    if rest > 0:
        d["North gas plant"] = min(rest, 900.0)
        rest -= d["North gas plant"]
    if rest > 0:
        d["North wind curtailment"] = rest
    up, rem = {}, ex
    for k in ("South gas peaker", "South hard-coal reserve", "South hydro/pumped storage"):
        x = min(rem, UP[k][0]); up[k] = x; rem -= x
        if rem <= 0:
            break
    return {**d, **up}


def greedy_plan(env: GridSimEnv):
    """Cheapest-first on each side: the optimum for this problem (shown so the grade is understood)."""
    return env.optimum()["plan"]
