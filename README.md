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
| `options_lab.py` | Options pattern finder: SPY/QQQ + big names, ATM calls/puts at real Alpaca option prices, 0DTE vs weekly -> `research/options_patterns.md` |
| `markets_lab.py` | Crypto + forex pattern finder (1h / 4h / daily): hunt on older data, exam on newer data -> `research/crypto_*`, `research/forex_*` |
| `crypto_dl.py`, `fx_dl.py` | Data downloaders (Alpaca crypto bars; Dukascopy FX candles) |

Workflows: `paper-bot` (market days), `research` (Saturdays, or run manually), `labs` (options/crypto/forex pattern finders: Saturdays, or commit a change to `.trigger/labs`).

Lab rule: a pattern is only worth paper trading if it is strong on the hunt period AND still makes money after costs on the exam period it never saw.
