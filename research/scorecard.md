# Research scorecard (2026-11-21)

Backtest: 531 trading days (2024-10-10 to 2026-11-20), 22391 signals across 2213 stocks. Same rules, fills and slippage as the live bot; candidates picked only from what was known at the open.

All signals together: -0.274R per trade, win rate 42%, t=-34.68.

## Strategies, best to worst

| Strategy | Trades | Per day | Win % | Avg R | Avg R (top 1% removed) | t | 1st half | 2nd half | With news | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| hod_break | 721 | 1.36 | 47% | -0.141 | -0.141 | -3.6 | -0.183 | -0.099 | -0.160 | **off**: loses -0.14R/trade over 721 trades |
| pm_high_break | 712 | 1.34 | 46% | -0.157 | -0.157 | -3.93 | -0.155 | -0.159 | -0.156 | **off**: loses -0.16R/trade over 712 trades |
| orb15 | 1436 | 2.7 | 46% | -0.166 | -0.166 | -6.04 | -0.176 | -0.157 | -0.165 | **off**: decay: last 50 live signals avg -0.17R |
| orb5 | 2429 | 4.57 | 44% | -0.189 | -0.189 | -8.61 | -0.175 | -0.203 | -0.217 | **off**: decay: last 50 live signals avg -0.49R |
| afternoon_hod | 856 | 1.61 | 42% | -0.210 | -0.210 | -6.2 | -0.218 | -0.203 | -0.175 | **off**: decay: last 50 live signals avg -0.56R |
| bull_flag | 2400 | 4.52 | 43% | -0.250 | -0.250 | -10.92 | -0.255 | -0.245 | -0.303 | **off**: decay: last 50 live signals avg -0.63R |
| ema_bounce | 5586 | 10.52 | 42% | -0.261 | -0.261 | -17.27 | -0.245 | -0.277 | -0.260 | **off**: decay: last 50 live signals avg -0.68R |
| failed_breakdown | 2712 | 5.11 | 42% | -0.263 | -0.263 | -12.73 | -0.243 | -0.283 | -0.290 | **off**: loses -0.26R/trade over 2712 trades |
| eod_squeeze | 788 | 1.48 | 37% | -0.314 | -0.410 | -3.54 | -0.140 | -0.487 | -0.216 | **off**: loses -0.31R/trade over 788 trades |
| vwap_pullback | 4751 | 8.95 | 38% | -0.427 | -0.427 | -25.87 | -0.434 | -0.420 | -0.434 | **off**: decay: last 50 live signals avg -0.62R |

t above 2 means the edge is very unlikely to be luck; between 1 and 2 is promising; below 1 is noise.

## Trade filter (learned from conditions)

Tested on the most recent 30% of data it never saw: all signals -0.271R vs filtered -0.107R (2921 of 6718 kept). Filter is **OFF (did not beat taking everything)**.

Conditions that matter most (positive = helps, negative = hurts): log_price +0.21, risk_pct +0.13, vwap_pullback -0.13, orb5 -0.11, failed_breakdown -0.08, minute -0.07, bull_flag +0.07, orb15 -0.07, eod_squeeze -0.06, log_pm_rvol +0.05

## Where the money goes: edge vs trading costs

Gross R = what the setup earned before slippage/spread. Cost R = round-trip slippage as a share of the risk. A strategy only works when gross beats cost.

| Strategy | Gross R | Cost R | Net R |
|---|---|---|---|
| afternoon_hod | +0.034 | 0.244 | -0.210 |
| bull_flag | +0.061 | 0.311 | -0.250 |
| ema_bounce | +0.088 | 0.349 | -0.261 |
| eod_squeeze | +0.023 | 0.336 | -0.314 |
| failed_breakdown | +0.025 | 0.288 | -0.263 |
| hod_break | +0.054 | 0.195 | -0.141 |
| orb15 | +0.035 | 0.201 | -0.166 |
| orb5 | +0.007 | 0.196 | -0.189 |
| pm_high_break | +0.042 | 0.199 | -0.157 |
| vwap_pullback | +0.053 | 0.480 | -0.427 |

**By stock price**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under $5 | 4710 | +0.021 | 0.561 | -0.540 |
| $5-10 | 4022 | +0.055 | 0.322 | -0.267 |
| $10-20 | 4847 | +0.051 | 0.232 | -0.181 |
| $20-50 | 6000 | +0.060 | 0.247 | -0.186 |
| $50+ | 2812 | +0.073 | 0.262 | -0.188 |

**By stop width**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under 1% | 3565 | +0.124 | 0.544 | -0.419 |
| 1-2% | 7605 | +0.065 | 0.302 | -0.238 |
| 2-3% | 5072 | +0.033 | 0.275 | -0.242 |
| 3%+ | 6149 | +0.006 | 0.268 | -0.262 |

## Fixes tested: entry and exit variants

Entry: mkt = market order next bar (current), lim = limit at the signal close, good 3 minutes (no chase). Plan: h2 = half at 1R, rest 2R (current); r3 = all at 3R; tr = half at 1R, trail the rest on the 9 EMA.
Net R below uses the typical measured spread; survivors must also stay positive with the bot's slippage and the worse (75th pct) spread.

Measured quoted spreads at entry (median / 75th pct): under $5 0.46% / 0.69%, $5-10 0.23% / 0.53%, $10-20 0.24% / 0.49%, $20-50 0.24% / 0.44%, $50+ 0.21% / 0.39%. A market order pays about half the spread on the way in and half on the way out.

| Strategy | Entry | Plan | Trades | Fill rate | Gross R | Net R | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|
| hod_break | lim | h2 | 649 | 90% | +0.011 | -0.030 | -0.73 | -0.064 | +0.004 |
| ema_bounce | lim | r3 | 5091 | 91% | +0.060 | -0.031 | -1.23 | -0.025 | -0.036 |
| orb15 | lim | h2 | 1308 | 91% | +0.009 | -0.036 | -1.23 | -0.034 | -0.038 |
| pm_high_break | lim | h2 | 660 | 93% | +0.007 | -0.038 | -0.89 | -0.026 | -0.049 |
| hod_break | lim | tr | 649 | 90% | +0.006 | -0.042 | -1.07 | -0.063 | -0.020 |
| orb15 | lim | tr | 1308 | 91% | +0.007 | -0.045 | -1.61 | -0.062 | -0.028 |
| hod_break | lim | r3 | 649 | 90% | -0.003 | -0.058 | -0.99 | -0.148 | +0.031 |
| ema_bounce | lim | h2 | 5091 | 91% | +0.006 | -0.068 | -4.27 | -0.056 | -0.080 |
| bull_flag | lim | r3 | 2153 | 90% | +0.006 | -0.071 | -1.89 | -0.127 | -0.016 |
| afternoon_hod | lim | h2 | 766 | 89% | -0.010 | -0.071 | -1.91 | -0.094 | -0.047 |
| pm_high_break | lim | tr | 660 | 93% | -0.019 | -0.072 | -1.81 | -0.058 | -0.086 |
| orb15 | lim | r3 | 1308 | 91% | -0.017 | -0.074 | -1.8 | -0.063 | -0.085 |
| bull_flag | lim | h2 | 2153 | 90% | -0.013 | -0.075 | -3.11 | -0.084 | -0.065 |
| afternoon_hod | lim | tr | 766 | 89% | -0.012 | -0.080 | -2.2 | -0.119 | -0.042 |
| hod_break | mkt | h2 | 721 | 100% | +0.021 | -0.082 | -2.11 | -0.113 | -0.052 |

**Survivors (net > +0.05R, t > 2, positive in both halves, 200+ trades): 0** (none yet)

## Path to $20/day

Current 6 accounts replayed over the backtest with every live rule (1 trade/day, price cap, on/off, filter):

| Account | $/day | Days traded | Worst day |
|---|---|---|---|
| $200 | $+0.00 | 0/531 | $0.00 |
| $250 | $+0.00 | 0/531 | $0.00 |
| $350 | $+0.00 | 0/531 | $0.00 |
| $400 | $+0.00 | 0/531 | $0.00 |
| $550 | $+0.00 | 0/531 | $0.00 |
| $1000 | $+0.00 | 0/531 | $0.00 |

**All accounts: $+0.00/day.**
The current setup does not show a positive edge after costs, so more money would only lose faster. Fix the strategy list first.
