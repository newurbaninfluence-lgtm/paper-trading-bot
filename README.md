# Paper trading bot

Paper-only day-trading system. No real money. Runs on GitHub Actions; mirrors trades into an Alpaca **paper** account.

| File | What it is |
|---|---|
| `core.py` | Strategies, features, slippage and trade management, shared by live bot and backtester |
| `bot.py` | Live bot: 6 accounts ($200–$1,000), 1 trade/account/day, 1% risk, Alpaca paper bracket orders |
| `research.py` | Backtester on years of Alpaca minute data, trade filter (model.json), strategy on/off list, $20/day plan |
| `report.py` | Daily report (`reports/DATE.md`) and spreadsheet (`reports/Paper Bot Live.xlsx`) |
| `journal.csv` | Every closed live trade |
| `signals.csv` | Every signal the bot saw (taken or not) with conditions and real outcome |
| `research/scorecard.md` | Latest backtest scorecard and path to $20/day |
| `briefs/DATE.md` | Morning market brief from outlets across the political spectrum |

Workflows: `paper-bot` (market days), `research` (Saturdays, or run manually).
