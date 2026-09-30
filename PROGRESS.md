# Night build progress

The site lives in `website/`. Run it with `python3 website/serve.py` and open http://localhost:8765.
Work happens on branch `night-build`; the restore point is `ae9dd2c` on `worktree-complete-training`.
NIGHT_PLAN.md has the architecture.

| Step | Status | Notes |
|---|---|---|
| Plan and progress files | done | |
| Foundation | in progress | |
| Springboard | not started | |
| Glass | not started | |
| Ferro | not started | |
| Amber | not started | |
| Instrument | not started | |
| Trading | not started | |
| Polish and morning report | not started | |

## Log

- Saved the design canvases and outputs in commit `ae9dd2c`, then created the `night-build` branch.
- Wrote NIGHT_PLAN.md. Timings: one price takes 0.2 ms, a 46-strike smile 0.5 ms, and 20,000-path Monte Carlo 10 ms, so the model page reprices live through the local server.

## If this session stops

1. Read NIGHT_PLAN.md and this table.
2. `git log --oneline night-build` shows the last milestone.
3. The next step is the first row that isn't marked done.
