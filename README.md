# Paper trading bot

Paper-only day-trading bot. No broker connection, no real orders. Runs on GitHub Actions every market day.

- 6 paper accounts ($200, $250, $350, $400, $550, $1,000), 3 strategies each, 1 trade per account per day, 1% risk per trade.
- Fills: next 1-minute bar open + $0.02 slippage; stops fill $0.02 worse.
- `bot3.log`: play-by-play. `journal.csv`: every closed trade. `state.pkl`: hand-off between morning and afternoon runs.
- Replay a past day: `python bot3.py replay 2026-10-08 SKYD,BORR`
