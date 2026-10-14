"""Redispatch in Germany: explore cost, volume and operators (SMARD and Netztransparenz data)."""
import matplotlib
matplotlib.use("Agg")
import gradio as gr
import matplotlib.pyplot as plt
import pandas as pd

fm = pd.read_csv("fact_monthly.csv", parse_dates=["month"])
fo = pd.read_csv("fact_operator_monthly.csv", parse_dates=["month"])
fm["eur_per_mwh"] = fm["cost_million_eur"] * 1000 / fm["volume_gwh"]
METRICS = {"Monthly cost (million EUR)": "cost_million_eur", "Monthly volume (GWh)": "volume_gwh", "Cost per MWh (EUR)": "eur_per_mwh",
           "Reductions (GWh)": "reductions_gwh", "Increases (GWh)": "increases_gwh"}


def show(metric, year_from, year_to, rolling):
    d = fm[(fm.month.dt.year >= year_from) & (fm.month.dt.year <= year_to)]
    col = METRICS[metric]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6))
    a1.bar(d["month"], d[col], width=25, color="#cfe3e6", edgecolor="#0b5d6b")
    if rolling:
        a1.plot(fm["month"], fm[col].rolling(12).mean(), color="black", linewidth=1.5, label="12-month average")
        a1.set_xlim(d.month.min(), d.month.max())
        a1.legend(fontsize=8)
    a1.set_title(metric, fontsize=10)
    op = fo[(fo.month.dt.year >= year_from) & (fo.month.dt.year <= year_to)].groupby("operator")["energy_mwh"].sum().sort_values() / 1000
    a2.barh(op.index, op.values, color="#0b5d6b")
    a2.set_title("Energy by ordering operator (GWh; operator data starts 2024)", fontsize=10)
    fig.tight_layout()
    peak = fm.loc[fm.cost_million_eur.idxmax()]
    text = (f"Peak month: {peak.month:%b %Y}, {peak.cost_million_eur:.0f} million EUR. Latest: {fm.cost_million_eur.iloc[-1]:.0f} million EUR. "
            "Volume has no steady downward trend.")
    return text, fig


demo = gr.Interface(show, [gr.Dropdown(list(METRICS), value="Monthly cost (million EUR)", label="Metric"), gr.Slider(2022, 2026, value=2022, step=1, label="From year"),
                           gr.Slider(2022, 2026, value=2026, step=1, label="To year"), gr.Checkbox(value=True, label="Show 12-month average")],
                    [gr.Textbox(label="Headline"), gr.Plot()], title="Redispatch in Germany",
                    description="Data: SMARD (CC BY 4.0) and Netztransparenz. Code: github.com/malliksmrity/redispatch-analysis")
if __name__ == "__main__":
    demo.launch()
