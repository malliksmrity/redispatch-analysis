"""Export a small star schema for Power BI Desktop (free) into powerbi/data/.

Tables
  dim_month.csv             one row per month (key = first day of the month)
  fact_monthly.csv          SMARD monthly volume, cost, reductions, increases, plant types
  fact_operator_monthly.csv Netztransparenz measures summed per month, operator, direction, energy type
                            (the measure list only covers January 2024 to April 2026)

Run from the repo root:  python src/export_powerbi.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "powerbi" / "data"


def monthly(name):
    df = pd.read_csv(RAW / name, encoding="utf-8-sig")
    df["month"] = pd.to_datetime(df["Month"], format="%b %Y")
    return df.drop(columns="Month").set_index("month")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    vc = monthly("volume-and-associated-co.csv").rename(columns={"Volume of energy": "volume_gwh", "Costs": "cost_million_eur"})
    dr = monthly("redispatch-by-direction.csv").rename(columns={"Reductions": "reductions_gwh", "Increases": "increases_gwh"})
    pt = monthly("redispatch-by-plant-type.csv").rename(columns={"Conventional power plant": "conventional_gwh", "Renewable sources": "renewable_gwh"})
    fm = vc.join(dr).join(pt).reset_index()
    fm.to_csv(OUT / "fact_monthly.csv", index=False, date_format="%Y-%m-%d")

    months = pd.DataFrame({"month": pd.date_range(fm.month.min(), fm.month.max(), freq="MS")})
    months["year"] = months.month.dt.year
    months["month_number"] = months.month.dt.month
    months["month_name"] = months.month.dt.strftime("%b")
    months["year_month"] = months.month.dt.strftime("%Y-%m")
    months.to_csv(OUT / "dim_month.csv", index=False, date_format="%Y-%m-%d")

    rd = pd.read_csv(RAW / "Redispatch_Daten.csv", sep=";", encoding="utf-8-sig")
    rd["mwh"] = rd["GESAMTE_ARBEIT_MWH"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)
    rd["month"] = pd.to_datetime(rd["BEGINN_DATUM"], format="%d.%m.%Y").dt.to_period("M").dt.to_timestamp()
    fo = (rd.groupby(["month", "ANWEISENDER_UENB", "RICHTUNG", "PRIMAERENERGIEART"], as_index=False)["mwh"].sum()
          .rename(columns={"ANWEISENDER_UENB": "operator", "RICHTUNG": "direction", "PRIMAERENERGIEART": "energy_type", "mwh": "energy_mwh"}))
    fo = fo[fo.month.isin(months.month)]
    fo["energy_mwh"] = fo["energy_mwh"].round(1)
    fo.to_csv(OUT / "fact_operator_monthly.csv", index=False, date_format="%Y-%m-%d")
    print({"fact_monthly": len(fm), "dim_month": len(months), "fact_operator_monthly": len(fo)})
    print("operator rows by first month:", fo.month.min().date(), "to", fo.month.max().date())


if __name__ == "__main__":
    main()
