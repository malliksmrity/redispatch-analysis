# n8n workflow: weekly live grid summary

`weekly_grid_summary.json` is an importable n8n workflow: every week it pulls the newest German onshore wind data from the SMARD live feed (checked: the feed answers and has the structure the workflow expects), computes the mean and maximum, and asks an AI model for a three-sentence plain-language reading.

**Status: not run in n8n.** I could not run n8n here. The JavaScript steps were tested on sample data; the SMARD addresses were tested live; the n8n node settings were written from the node documentation and may need small fixes after import.

## Use it
1. Install n8n (cloud, or `npx n8n` with Node.js) and open it.
2. Workflows, Import from file, choose `weekly_grid_summary.json`.
3. Open the "Anthropic chat model" node and add **your own** Anthropic credential (an API key you create yourself; never put it in the file).
4. Run once manually, then activate. Add a node after the summary (email, Slack, a file) to send it somewhere.

Ideas for later (not built): refresh `docs/data.js` automatically, watch new Bundestag speeches through the DIP API, or send weld photos to a vision model.