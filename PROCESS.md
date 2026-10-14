# How I plan the next work (Scrum-style)

This is the plan for the next sprints of **redispatch-analysis**. It is a planned way of working for a one-person project, not a record of past team work.

## Working agreement
- Sprint: one week. Sprint goal: one backlog item finished, with its numbers in `reports/` and the README.
- Planning on Monday (pick items), review on Friday (open the project page, check the numbers), a short retrospective note in the commit log.
- Board: one GitHub issue per backlog item, columns To do, In progress, Done (GitHub Projects).
- Branches: `main` stays working; each item gets its own branch and a pull request.

## Definition of done
1. The script runs in a fresh virtual environment from `requirements.txt`.
2. Every number in the README and on the page matches `reports/`.
3. The project page opens without console errors and works on a phone.
4. No secrets or personal data in the files or history.
5. Limits are stated next to the result.

## Product backlog
| # | User story | Acceptance |
|---|---|---|
| 1 | As a committee member, I want a Power BI report, so that I can filter by operator and year. | Report built from powerbi/ following BUILD_GUIDE.md, PDF exported. |
| 2 | As an analyst, I want operator data back to 2022, so that operator shares cover the whole period. | Operator table from July 2022. |
| 3 | As an analyst, I want a regional view, so that investment priorities are not only by operator. | Measures by region or plant, with a map or table. |
