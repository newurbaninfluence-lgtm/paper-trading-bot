# Research scorecard (2026-10-09)

Backtest: 500 trading days (2024-10-10 to 2026-10-08), 21082 signals across 2143 stocks. Same rules, fills and slippage as the live bot; candidates picked only from what was known at the open.

All signals together: -801086168.709R per trade, win rate 42%, t=-1.0.

## Strategies, best to worst

| Strategy | Trades | Per day | Win % | Avg R | Avg R (top 1% removed) | t | 1st half | 2nd half | With news | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| pm_high_break | 665 | 1.33 | 46% | -0.149 | -0.149 | -3.58 | -0.177 | -0.121 | -0.159 | **off**: loses -0.15R/trade over 665 trades |
| hod_break | 665 | 1.33 | 46% | -0.160 | -0.160 | -3.91 | -0.219 | -0.100 | -0.159 | **off**: loses -0.16R/trade over 665 trades |
| orb15 | 1341 | 2.68 | 45% | -0.181 | -0.181 | -6.16 | -0.197 | -0.164 | -0.186 | **off**: loses -0.18R/trade over 1341 trades |
| orb5 | 2264 | 4.53 | 44% | -0.186 | -0.186 | -8.18 | -0.178 | -0.194 | -0.214 | **off**: loses -0.19R/trade over 2264 trades |
| afternoon_hod | 802 | 1.6 | 43% | -0.190 | -0.190 | -5.39 | -0.213 | -0.166 | -0.142 | **off**: loses -0.19R/trade over 802 trades |
| bull_flag | 2228 | 4.46 | 43% | -0.259 | -0.259 | -10.95 | -0.250 | -0.267 | -0.302 | **off**: loses -0.26R/trade over 2228 trades |
| failed_breakdown | 2550 | 5.1 | 42% | -0.267 | -0.267 | -12.41 | -0.251 | -0.284 | -0.298 | **off**: loses -0.27R/trade over 2550 trades |
| ema_bounce | 5281 | 10.56 | 42% | -0.270 | -0.270 | -16.45 | -0.248 | -0.293 | -0.258 | **off**: loses -0.27R/trade over 5281 trades |
| eod_squeeze | 739 | 1.48 | 37% | -0.328 | -0.430 | -3.49 | -0.174 | -0.481 | -0.225 | **off**: loses -0.33R/trade over 739 trades |
| vwap_pullback | 4547 | 9.09 | 37% | -3714206862.718 | -3714206862.718 | -1.0 | -0.477 | -7426780388.608 | -0.462 | **off**: loses -3714206862.72R/trade over 4547 trades |

t above 2 means the edge is very unlikely to be luck; between 1 and 2 is promising; below 1 is noise.

## Trade filter (learned from conditions)

Tested on the most recent 30% of data it never saw: all signals -0.294R vs filtered -0.116R (2558 of 6325 kept). Filter is **OFF (did not beat taking everything)**.

Conditions that matter most (positive = helps, negative = hurts): log_price +0.21, vwap_pullback -0.14, risk_pct +0.13, orb5 -0.11, afternoon_hod +0.09, eod_squeeze -0.08, orb15 -0.08, minute -0.07, failed_breakdown -0.07, bull_flag +0.06

## Path to $20/day

Current 6 accounts replayed over the backtest with every live rule (1 trade/day, price cap, on/off, filter):

| Account | $/day | Days traded | Worst day |
|---|---|---|---|
| $200 | $+0.00 | 0/500 | $0.00 |
| $250 | $+0.00 | 0/500 | $0.00 |
| $350 | $+0.00 | 0/500 | $0.00 |
| $400 | $+0.00 | 0/500 | $0.00 |
| $550 | $+0.00 | 0/500 | $0.00 |
| $1000 | $+0.00 | 0/500 | $0.00 |

**All accounts: $+0.00/day.**
The current setup does not show a positive edge after costs, so more money would only lose faster. Fix the strategy list first.
