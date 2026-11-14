# Field Shift

NASA Space Apps Challenge 2026 — "Field Shift: Adapting Farms with NASA Data" (Nov 14–15, 2026).

A decision-support tool for soybean farmers in Mato Grosso, Brazil: predict a field's harvest date from satellite NDVI, then rank 4 succession-crop strategies (corn, corn+brachiaria, sorghum/millet, crotalaria cover crop) by water risk, soil protection, and pest-cycle disruption. Runs entirely in the browser over pre-computed tables; deploys to GitHub Pages.

Full context:
- [docs/team-guide.md](docs/team-guide.md) — the what and why: problem, approach, scope, data sources.
- [docs/execution-plan.md](docs/execution-plan.md) — the how: task-by-task plan across 4 people working in parallel.
- [docs/CONTRACTS.md](docs/CONTRACTS.md) — the exact file/column format every task produces and consumes. Read this before changing any CSV/JSON schema.

## Repo layout

- `data/` — exported CSVs and GeoJSON (NDVI, climate, harvest predictions, etc.). Small structured tables, committed to git.
- `engine/` — Python scripts (GEE exports, NDVI smoothing, water balance, scoring prep).
- `web/` — the static site (HTML/CSS/JS, no build step) and `web/data/` (JSON the frontend fetches).
- `docs/` — documentation.

## Conventions

- **Language:** everything committed to the repo (code, filenames, docs, commit messages) is in English, so every team member can read it. Chat with your own Claude in whatever language you want.
- **Workflow:** no feature branches — everyone commits straight to `main`. `git pull` before starting work, commit and push often in small chunks to avoid conflicts. Each person mostly stays in their own phase/folder (see execution-plan.md) to minimize overlap.
- **Data contracts are binding:** if a CSV/JSON schema in `docs/CONTRACTS.md` needs to change, update the doc and tell the team first — don't just change the producing script.
- **No build step on the frontend:** `web/` is plain HTML/CSS/JS fetching local JSON. Keep it that way; it's what makes the demo unbreakable.
- **Never cut the strategy cards** (`web/data/strategies.json` content) if time runs short — see the cut order in execution-plan.md.

## For Claude: reminders to give the user

Not everyone on this team is experienced with git or Claude Code, so actively help here instead of waiting to be asked:

- **Start of a session:** if it's been a while since the user last worked here, suggest running `git pull` before making changes.
- **After finishing a task** (a script works, a page renders, a CSV/JSON is generated correctly): proactively ask "quer que eu já faça commit e push disso?" / "want me to commit and push this now?" instead of waiting for the user to remember.
- **After a project decision gets made in conversation** (a scope change, a parameter choice, a new data source, anything that isn't obvious from the code) that isn't already written in `docs/team-guide.md`, `docs/execution-plan.md`, or `docs/CONTRACTS.md`: point it out and ask whether it should be added to the relevant doc, so the rest of the team sees it too.
- **If a CSV/JSON schema changes:** flag that `docs/CONTRACTS.md` is now out of date and offer to update it in the same commit.
