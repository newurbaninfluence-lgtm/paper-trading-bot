# Research scorecard (2026-10-31)

Backtest: 516 trading days (2024-10-10 to 2026-10-30), 21730 signals across 2181 stocks. Same rules, fills and slippage as the live bot; candidates picked only from what was known at the open.

All signals together: -0.276R per trade, win rate 42%, t=-34.35.

## Strategies, best to worst

| Strategy | Trades | Per day | Win % | Avg R | Avg R (top 1% removed) | t | 1st half | 2nd half | With news | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| hod_break | 692 | 1.34 | 47% | -0.137 | -0.137 | -3.41 | -0.201 | -0.072 | -0.149 | **off**: loses -0.14R/trade over 692 trades |
| pm_high_break | 688 | 1.33 | 46% | -0.160 | -0.160 | -3.93 | -0.171 | -0.150 | -0.157 | **off**: loses -0.16R/trade over 688 trades |
| orb15 | 1401 | 2.72 | 46% | -0.167 | -0.167 | -5.99 | -0.175 | -0.160 | -0.173 | **off**: loses -0.17R/trade over 1401 trades |
| orb5 | 2360 | 4.57 | 44% | -0.190 | -0.190 | -8.54 | -0.170 | -0.210 | -0.220 | **off**: loses -0.19R/trade over 2360 trades |
| afternoon_hod | 835 | 1.62 | 43% | -0.199 | -0.199 | -5.79 | -0.228 | -0.170 | -0.170 | **off**: loses -0.20R/trade over 835 trades |
| bull_flag | 2311 | 4.48 | 43% | -0.254 | -0.254 | -10.91 | -0.251 | -0.257 | -0.305 | **off**: decay: last 42 live signals avg -0.41R |
| ema_bounce | 5430 | 10.52 | 42% | -0.261 | -0.261 | -17.03 | -0.250 | -0.272 | -0.259 | **off**: loses -0.26R/trade over 5430 trades |
| failed_breakdown | 2634 | 5.1 | 42% | -0.263 | -0.263 | -12.58 | -0.250 | -0.277 | -0.287 | **off**: loses -0.26R/trade over 2634 trades |
| eod_squeeze | 760 | 1.47 | 36% | -0.328 | -0.428 | -3.59 | -0.156 | -0.501 | -0.227 | **off**: decay: last 48 live signals avg -0.70R |
| vwap_pullback | 4619 | 8.95 | 38% | -0.432 | -0.432 | -25.86 | -0.434 | -0.430 | -0.437 | **off**: decay: last 50 live signals avg -0.45R |

t above 2 means the edge is very unlikely to be luck; between 1 and 2 is promising; below 1 is noise.

## Trade filter (learned from conditions)

Tested on the most recent 30% of data it never saw: all signals -0.279R vs filtered -0.117R (2938 of 6520 kept). Filter is **OFF (did not beat taking everything)**.

Conditions that matter most (positive = helps, negative = hurts): log_price +0.21, risk_pct +0.13, vwap_pullback -0.13, orb5 -0.11, eod_squeeze -0.09, failed_breakdown -0.07, minute -0.07, afternoon_hod +0.07, bull_flag +0.06, orb15 -0.06

## Where the money goes: edge vs trading costs

Gross R = what the setup earned before slippage/spread. Cost R = round-trip slippage as a share of the risk. A strategy only works when gross beats cost.

| Strategy | Gross R | Cost R | Net R |
|---|---|---|---|
| afternoon_hod | +0.045 | 0.245 | -0.199 |
| bull_flag | +0.056 | 0.310 | -0.254 |
| ema_bounce | +0.086 | 0.347 | -0.261 |
| eod_squeeze | +0.010 | 0.338 | -0.328 |
| failed_breakdown | +0.023 | 0.287 | -0.263 |
| hod_break | +0.060 | 0.197 | -0.137 |
| orb15 | +0.034 | 0.202 | -0.167 |
| orb5 | +0.005 | 0.195 | -0.190 |
| pm_high_break | +0.038 | 0.198 | -0.160 |
| vwap_pullback | +0.047 | 0.478 | -0.432 |

**By stock price**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under $5 | 4533 | +0.020 | 0.558 | -0.538 |
| $5-10 | 3882 | +0.051 | 0.323 | -0.271 |
| $10-20 | 4692 | +0.044 | 0.232 | -0.188 |
| $20-50 | 5878 | +0.061 | 0.247 | -0.186 |
| $50+ | 2745 | +0.070 | 0.262 | -0.192 |

**By stop width**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under 1% | 3485 | +0.116 | 0.543 | -0.427 |
| 1-2% | 7384 | +0.064 | 0.302 | -0.238 |
| 2-3% | 4901 | +0.029 | 0.273 | -0.244 |
| 3%+ | 5960 | +0.005 | 0.266 | -0.261 |

## Fixes tested: entry and exit variants

Entry: mkt = market order next bar (current), lim = limit at the signal close, good 3 minutes (no chase). Plan: h2 = half at 1R, rest 2R (current); r3 = all at 3R; tr = half at 1R, trail the rest on the 9 EMA.
Net R below uses the typical measured spread; survivors must also stay positive with the bot's slippage and the worse (75th pct) spread.

Measured quoted spreads at entry (median / 75th pct): under $5 0.46% / 0.69%, $5-10 0.23% / 0.53%, $10-20 0.24% / 0.49%, $20-50 0.24% / 0.44%, $50+ 0.21% / 0.39%. A market order pays about half the spread on the way in and half on the way out.

| Strategy | Entry | Plan | Trades | Fill rate | Gross R | Net R | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|
| hod_break | lim | h2 | 623 | 90% | +0.023 | -0.017 | -0.42 | -0.085 | +0.050 |
| hod_break | lim | tr | 623 | 90% | +0.017 | -0.030 | -0.77 | -0.076 | +0.015 |
| ema_bounce | lim | r3 | 4953 | 91% | +0.059 | -0.031 | -1.22 | -0.032 | -0.030 |
| orb15 | lim | h2 | 1276 | 91% | +0.009 | -0.037 | -1.25 | -0.042 | -0.032 |
| pm_high_break | lim | h2 | 637 | 93% | +0.006 | -0.038 | -0.89 | -0.047 | -0.030 |
| hod_break | lim | r3 | 623 | 90% | +0.012 | -0.043 | -0.72 | -0.177 | +0.091 |
| orb15 | lim | tr | 1276 | 91% | +0.006 | -0.047 | -1.64 | -0.070 | -0.023 |
| afternoon_hod | lim | h2 | 746 | 89% | +0.002 | -0.059 | -1.56 | -0.103 | -0.015 |
| afternoon_hod | lim | tr | 746 | 89% | +0.001 | -0.068 | -1.83 | -0.128 | -0.007 |
| ema_bounce | lim | h2 | 4953 | 91% | +0.005 | -0.069 | -4.26 | -0.060 | -0.077 |
| pm_high_break | lim | tr | 637 | 93% | -0.019 | -0.073 | -1.8 | -0.074 | -0.073 |
| bull_flag | lim | r3 | 2075 | 90% | +0.003 | -0.074 | -1.92 | -0.134 | -0.014 |
| hod_break | mkt | h2 | 692 | 100% | +0.029 | -0.075 | -1.87 | -0.133 | -0.016 |
| orb15 | lim | r3 | 1276 | 91% | -0.017 | -0.075 | -1.8 | -0.068 | -0.081 |
| bull_flag | lim | h2 | 2075 | 90% | -0.017 | -0.079 | -3.23 | -0.083 | -0.075 |

**Survivors (net > +0.05R, t > 2, positive in both halves, 200+ trades): 0** (none yet)

## Path to $20/day

Current 6 accounts replayed over the backtest with every live rule (1 trade/day, price cap, on/off, filter):

| Account | $/day | Days traded | Worst day |
|---|---|---|---|
| $200 | $+0.00 | 0/516 | $0.00 |
| $250 | $+0.00 | 0/516 | $0.00 |
| $350 | $+0.00 | 0/516 | $0.00 |
| $400 | $+0.00 | 0/516 | $0.00 |
| $550 | $+0.00 | 0/516 | $0.00 |
| $1000 | $+0.00 | 0/516 | $0.00 |

**All accounts: $+0.00/day.**
The current setup does not show a positive edge after costs, so more money would only lose faster. Fix the strategy list first.
