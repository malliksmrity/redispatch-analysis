"""GridSimEnv: live simulation. Resolve a real wind hour's grid congestion at minimum cost."""
import json
from pathlib import Path

import gradio as gr
import pandas as pd

import grid_env as g

ENV = g.GridSimEnv()
RES = json.loads((Path(__file__).resolve().parent / "results.json").read_text(encoding="utf-8"))
OPTIONS = list(g.DOWN) + list(g.UP)


def load(hour):
    s = ENV.reset(int(hour))
    rows = [["reduce in the north", k, v["max_MW"], v["price"]] for k, v in s["down_options"].items()] + [["increase in the south", k, v["max_MW"], v["price"]] for k, v in s["up_options"].items()]
    head = (f"{s['hour']} UTC. German wind {s['german_wind_MW']} MW. The scheduled flow north to south is {s['scheduled_flow_MW']} MW but the line carries {s['line_limit_MW']} MW. "
            f"You must redispatch at least {s['must_redispatch_MW']} MW, balanced between north and south.")
    return head, pd.DataFrame(rows, columns=["side", "option", "max MW", "price EUR/MW"])


def submit(*mw):
    plan = dict(zip(OPTIONS, mw))
    chk = ENV.check_plan(plan)
    if not chk["valid"]:
        return "Plan not valid: " + "; ".join(chk["errors"]), ""
    r = ENV.submit_plan(plan)
    return f"Valid. Cost {r['cost_EUR']:,} EUR, optimum {r['optimal_cost_EUR']:,} EUR. Score {r['reward']} (1.0 = optimal).", json.dumps(r["optimal_plan"], indent=1)


with gr.Blocks(title="GridSimEnv") as demo:
    gr.Markdown("# GridSimEnv: resolve a grid congestion at minimum cost\nThe wind data is real (SMARD, hourly). The two-zone grid, the line limit and the prices are a **stylised assumption**, "
                "so the problem has a provable optimum (solved as a linear programme). Code: github.com/malliksmrity/redispatch-analysis")
    hour = gr.Slider(0, len(ENV.h) - 1, value=100, step=1, label="Hour (index into 12,961 real hours)")
    b0 = gr.Button("Load this hour")
    sit, tbl = gr.Textbox(label="Situation"), gr.Dataframe()
    b0.click(load, hour, [sit, tbl])
    sl = [gr.Slider(0, 3000, value=0, step=10, label=f"{k} (MW)") for k in OPTIONS]
    b1 = gr.Button("Submit plan")
    res, opt = gr.Textbox(label="Result"), gr.Textbox(label="Optimal plan (shown after you submit)")
    b1.click(submit, sl, [res, opt])
    gr.Markdown(f"**Over {RES['hours']} random real hours:** the naive 'largest plant first' rule scores {RES['policies']['naive rule (largest plant first)']['mean_score']}, a cheapest-first rule 1.0 "
                f"(mean cost {RES['policies']['naive rule (largest plant first)']['mean_cost_EUR']:,} against {RES['policies']['cheapest first (the optimum)']['mean_cost_EUR']:,} EUR per hour).")
if __name__ == "__main__":
    demo.launch()
