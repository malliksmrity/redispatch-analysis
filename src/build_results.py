"""Recompute the headline numbers of the redispatch analysis from the raw CSVs.

Inputs (data/raw/): volume-and-associated-co.csv (SMARD monthly volume in GWh and cost in million EUR),
Redispatch_Daten.csv (Netztransparenz, one row per measure), smard_generation_hourly.csv,
redispatch-by-direction.csv, redispatch-by-plant-type.csv.

Run from the repo root:  python src/build_results.py
Writes reports/results.json and docs/data.js (loaded by docs/index.html).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def month_index(df):
    df["date"] = pd.to_datetime(df["Month"], format="%b %Y")
    return df.sort_values("date").reset_index(drop=True)


def main():
    vc = month_index(pd.read_csv(RAW / "volume-and-associated-co.csv", encoding="utf-8-sig"))
    vc = vc.rename(columns={"Volume of energy": "gwh", "Costs": "cost_m"})
    vc["eur_per_mwh"] = vc["cost_m"] * 1e6 / (vc["gwh"] * 1e3)  # million EUR per GWh -> EUR per MWh
    vc["avg12"] = vc["cost_m"].rolling(12, min_periods=12).mean()
    peak = vc.loc[vc["cost_m"].idxmax()]
    last = vc.iloc[-1]
    vc["year"] = vc["date"].dt.year
    unit = vc.groupby("year")["eur_per_mwh"].agg(["median", "count"]).round(1)
    yearly = vc.groupby("year")[["cost_m", "gwh"]].sum().round(1)

    # robustness: decline measured against averages, not against the single peak month
    last12 = vc.tail(12)["cost_m"].mean()
    y2023 = vc[vc.year == 2023]["cost_m"].mean()

    # operators (51,443 measures)
    rd = pd.read_csv(RAW / "Redispatch_Daten.csv", sep=";", encoding="utf-8-sig")
    rd["mwh"] = rd["GESAMTE_ARBEIT_MWH"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)
    by_op = (rd.groupby("ANWEISENDER_UENB")["mwh"].sum() / 1000).round(0).sort_values(ascending=False)
    op_share = (by_op / by_op.sum()).round(3)

    # direction and plant type, earliest vs latest period
    dr = month_index(pd.read_csv(RAW / "redispatch-by-direction.csv", encoding="utf-8-sig"))
    early = dr[dr.date < "2024-07-01"].head(24)
    recent = dr.tail(12)
    pt = month_index(pd.read_csv(RAW / "redispatch-by-plant-type.csv", encoding="utf-8-sig"))

    # wind vs redispatch volume, overlapping months only
    g = pd.read_csv(RAW / "smard_generation_hourly.csv", parse_dates=["timestamp_utc"])
    g["wind"] = g[["Wind onshore", "Wind offshore"]].sum(axis=1, min_count=1)
    gm = g.dropna(subset=["wind"]).set_index("timestamp_utc")["wind"].resample("MS").sum() / 1000  # GWh
    gm = gm[gm > 0]
    both = pd.concat([gm.rename("wind_gwh"), vc.set_index("date")["gwh"].rename("redispatch_gwh")], axis=1, sort=True).dropna()
    both = both.iloc[1:]  # first month is partial in the SMARD file
    pear = float(both["wind_gwh"].corr(both["redispatch_gwh"]))
    spear = float(both["wind_gwh"].corr(both["redispatch_gwh"], method="spearman"))
    rng = np.random.default_rng(42)
    boots = [both.sample(len(both), replace=True, random_state=int(s)).corr().iloc[0, 1] for s in rng.integers(0, 10**6, 2000)]
    ci = np.nanpercentile(boots, [2.5, 97.5])

    out = {
        "months": int(len(vc)), "first_month": vc.Month.iloc[0], "last_month": vc.Month.iloc[-1], "n_measures": int(len(rd)),
        "peak": {"month": peak.Month, "cost_m": float(peak.cost_m)},
        "latest": {"month": last.Month, "cost_m": float(last.cost_m)},
        "decline_from_peak_pct": round(float((1 - last.cost_m / peak.cost_m) * 100), 1),
        "robustness": {"avg_cost_last_12_months_m": round(float(last12), 1), "avg_cost_2023_m": round(float(y2023), 1),
                       "decline_avg_2023_to_last12_pct": round(float((1 - last12 / y2023) * 100), 1)},
        "median_eur_per_mwh_by_year": {int(k): float(v) for k, v in unit["median"].items()},
        "months_per_year": {int(k): int(v) for k, v in unit["count"].items()},
        "yearly_totals": {int(k): {"cost_m": float(r.cost_m), "gwh": float(r.gwh)} for k, r in yearly.iterrows()},
        "energy_by_operator_gwh": {k: float(v) for k, v in by_op.items()}, "operator_share": {k: float(v) for k, v in op_share.items()},
        "volume_range_gwh": [float(vc.gwh.min()), float(vc.gwh.max())],
        "direction_avg_monthly_gwh": {"first_24_months": {c: round(float(early[c].mean()), 0) for c in ["Reductions", "Increases"]},
                                      "last_12_months": {c: round(float(recent[c].mean()), 0) for c in ["Reductions", "Increases"]}},
        "wind_vs_redispatch": {"months": int(len(both)), "pearson": round(pear, 2), "spearman": round(spear, 2),
                               "bootstrap_95ci_pearson": [round(float(ci[0]), 2), round(float(ci[1]), 2)]},
    }
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    page = dict(out, monthly={"month": vc.Month.tolist(), "cost_m": vc.cost_m.round(1).tolist(), "avg12": vc.avg12.round(1).where(vc.avg12.notna(), None).tolist(),
                              "gwh": vc.gwh.round(0).tolist(), "eur_per_mwh": vc.eur_per_mwh.round(1).tolist(), "year": vc.year.tolist()},
                direction={"month": dr.Month.tolist(), "reductions": dr.Reductions.round(0).tolist(), "increases": dr.Increases.round(0).tolist()},
                plant={"month": pt.Month.tolist(), "conventional": pt["Conventional power plant"].round(0).tolist(), "renewable": pt["Renewable sources"].round(0).tolist()},
                wind={"month": [d.strftime("%b %Y") for d in both.index], "wind_gwh": both.wind_gwh.round(0).tolist(), "redispatch_gwh": both.redispatch_gwh.round(0).tolist()})
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "data.js").write_text("window.PAGE_DATA = " + json.dumps(page) + ";\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
