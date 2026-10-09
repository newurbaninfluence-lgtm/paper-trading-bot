# Research scorecard (2026-10-09)

Backtest: 500 trading days (2024-10-10 to 2026-10-08), 21002 signals across 2143 stocks. Same rules, fills and slippage as the live bot; candidates picked only from what was known at the open.

All signals together: -0.276R per trade, win rate 42%, t=-33.76.

## Strategies, best to worst

| Strategy | Trades | Per day | Win % | Avg R | Avg R (top 1% removed) | t | 1st half | 2nd half | With news | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| pm_high_break | 665 | 1.33 | 46% | -0.149 | -0.149 | -3.58 | -0.177 | -0.121 | -0.159 | **off**: loses -0.15R/trade over 665 trades |
| hod_break | 665 | 1.33 | 46% | -0.160 | -0.160 | -3.91 | -0.219 | -0.100 | -0.159 | **off**: loses -0.16R/trade over 665 trades |
| orb15 | 1339 | 2.68 | 45% | -0.171 | -0.171 | -5.99 | -0.179 | -0.163 | -0.175 | **off**: loses -0.17R/trade over 1339 trades |
| orb5 | 2264 | 4.53 | 44% | -0.186 | -0.186 | -8.18 | -0.178 | -0.194 | -0.214 | **off**: loses -0.19R/trade over 2264 trades |
| afternoon_hod | 802 | 1.6 | 43% | -0.190 | -0.190 | -5.39 | -0.213 | -0.166 | -0.142 | **off**: loses -0.19R/trade over 802 trades |
| bull_flag | 2228 | 4.46 | 43% | -0.259 | -0.259 | -10.95 | -0.250 | -0.267 | -0.302 | **off**: loses -0.26R/trade over 2228 trades |
| ema_bounce | 5276 | 10.55 | 42% | -0.263 | -0.263 | -16.92 | -0.245 | -0.281 | -0.257 | **off**: loses -0.26R/trade over 5276 trades |
| failed_breakdown | 2548 | 5.1 | 42% | -0.263 | -0.263 | -12.35 | -0.243 | -0.283 | -0.290 | **off**: loses -0.26R/trade over 2548 trades |
| vwap_pullback | 4476 | 8.95 | 38% | -0.429 | -0.429 | -25.31 | -0.440 | -0.419 | -0.436 | **off**: loses -0.43R/trade over 4476 trades |
| eod_squeeze | 739 | 1.48 | 37% | -0.328 | -0.430 | -3.49 | -0.174 | -0.481 | -0.225 | **off**: loses -0.33R/trade over 739 trades |

t above 2 means the edge is very unlikely to be luck; between 1 and 2 is promising; below 1 is noise.

## Trade filter (learned from conditions)

Tested on the most recent 30% of data it never saw: all signals -0.283R vs filtered -0.113R (2543 of 6301 kept). Filter is **OFF (did not beat taking everything)**.

Conditions that matter most (positive = helps, negative = hurts): log_price +0.21, risk_pct +0.13, vwap_pullback -0.13, orb5 -0.11, afternoon_hod +0.08, eod_squeeze -0.08, orb15 -0.07, minute -0.07, failed_breakdown -0.07, bull_flag +0.06

## Where the money goes: edge vs trading costs

Gross R = what the setup earned before slippage/spread. Cost R = round-trip slippage as a share of the risk. A strategy only works when gross beats cost.

| Strategy | Gross R | Cost R | Net R |
|---|---|---|---|
| afternoon_hod | +0.052 | 0.242 | -0.190 |
| bull_flag | +0.051 | 0.309 | -0.259 |
| ema_bounce | +0.083 | 0.345 | -0.263 |
| eod_squeeze | +0.009 | 0.337 | -0.328 |
| failed_breakdown | +0.023 | 0.286 | -0.263 |
| hod_break | +0.038 | 0.197 | -0.160 |
| orb15 | +0.031 | 0.201 | -0.171 |
| orb5 | +0.008 | 0.195 | -0.186 |
| pm_high_break | +0.049 | 0.197 | -0.149 |
| vwap_pullback | +0.047 | 0.476 | -0.429 |

**By stock price**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under $5 | 4336 | +0.018 | 0.558 | -0.540 |
| $5-10 | 3758 | +0.053 | 0.321 | -0.268 |
| $10-20 | 4519 | +0.047 | 0.231 | -0.184 |
| $20-50 | 5695 | +0.055 | 0.247 | -0.192 |
| $50+ | 2694 | +0.066 | 0.262 | -0.196 |

**By stop width**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under 1% | 3376 | +0.118 | 0.542 | -0.424 |
| 1-2% | 7134 | +0.062 | 0.301 | -0.239 |
| 2-3% | 4743 | +0.023 | 0.272 | -0.249 |
| 3%+ | 5749 | +0.006 | 0.264 | -0.258 |

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
