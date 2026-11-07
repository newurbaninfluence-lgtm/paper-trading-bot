# Research scorecard (2026-11-07)

Backtest: 521 trading days (2024-10-10 to 2026-11-06), 21962 signals across 2192 stocks. Same rules, fills and slippage as the live bot; candidates picked only from what was known at the open.

All signals together: -0.275R per trade, win rate 42%, t=-34.44.

## Strategies, best to worst

| Strategy | Trades | Per day | Win % | Avg R | Avg R (top 1% removed) | t | 1st half | 2nd half | With news | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| hod_break | 705 | 1.35 | 47% | -0.139 | -0.139 | -3.49 | -0.190 | -0.087 | -0.146 | **off**: loses -0.14R/trade over 705 trades |
| pm_high_break | 699 | 1.34 | 46% | -0.160 | -0.160 | -3.96 | -0.155 | -0.164 | -0.155 | **off**: loses -0.16R/trade over 699 trades |
| orb15 | 1411 | 2.71 | 46% | -0.166 | -0.166 | -5.97 | -0.170 | -0.163 | -0.170 | **off**: loses -0.17R/trade over 1411 trades |
| orb5 | 2385 | 4.58 | 44% | -0.187 | -0.187 | -8.45 | -0.172 | -0.203 | -0.219 | **off**: decay: last 40 live signals avg -0.16R |
| afternoon_hod | 844 | 1.62 | 43% | -0.205 | -0.205 | -5.99 | -0.227 | -0.183 | -0.179 | **off**: decay: last 35 live signals avg -0.48R |
| bull_flag | 2344 | 4.5 | 43% | -0.255 | -0.255 | -11.03 | -0.249 | -0.262 | -0.305 | **off**: decay: last 50 live signals avg -0.17R |
| ema_bounce | 5484 | 10.53 | 42% | -0.261 | -0.261 | -17.12 | -0.249 | -0.273 | -0.260 | **off**: decay: last 50 live signals avg -0.52R |
| failed_breakdown | 2652 | 5.09 | 42% | -0.263 | -0.263 | -12.6 | -0.247 | -0.279 | -0.286 | **off**: loses -0.26R/trade over 2652 trades |
| eod_squeeze | 772 | 1.48 | 37% | -0.318 | -0.416 | -3.52 | -0.141 | -0.496 | -0.222 | **off**: decay: last 50 live signals avg -0.62R |
| vwap_pullback | 4666 | 8.96 | 38% | -0.430 | -0.430 | -25.87 | -0.435 | -0.425 | -0.434 | **off**: decay: last 50 live signals avg -0.36R |

t above 2 means the edge is very unlikely to be luck; between 1 and 2 is promising; below 1 is noise.

## Trade filter (learned from conditions)

Tested on the most recent 30% of data it never saw: all signals -0.279R vs filtered -0.113R (2894 of 6589 kept). Filter is **OFF (did not beat taking everything)**.

Conditions that matter most (positive = helps, negative = hurts): log_price +0.21, vwap_pullback -0.13, risk_pct +0.13, orb5 -0.10, eod_squeeze -0.08, minute -0.07, failed_breakdown -0.07, orb15 -0.06, bull_flag +0.06, afternoon_hod +0.06

## Where the money goes: edge vs trading costs

Gross R = what the setup earned before slippage/spread. Cost R = round-trip slippage as a share of the risk. A strategy only works when gross beats cost.

| Strategy | Gross R | Cost R | Net R |
|---|---|---|---|
| afternoon_hod | +0.040 | 0.244 | -0.205 |
| bull_flag | +0.056 | 0.311 | -0.255 |
| ema_bounce | +0.087 | 0.348 | -0.261 |
| eod_squeeze | +0.019 | 0.337 | -0.318 |
| failed_breakdown | +0.024 | 0.287 | -0.263 |
| hod_break | +0.058 | 0.197 | -0.139 |
| orb15 | +0.036 | 0.202 | -0.166 |
| orb5 | +0.008 | 0.195 | -0.187 |
| pm_high_break | +0.040 | 0.200 | -0.160 |
| vwap_pullback | +0.049 | 0.479 | -0.430 |

**By stock price**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under $5 | 4596 | +0.020 | 0.559 | -0.539 |
| $5-10 | 3918 | +0.054 | 0.323 | -0.269 |
| $10-20 | 4752 | +0.047 | 0.233 | -0.185 |
| $20-50 | 5915 | +0.060 | 0.247 | -0.187 |
| $50+ | 2781 | +0.073 | 0.262 | -0.189 |

**By stop width**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under 1% | 3518 | +0.121 | 0.543 | -0.422 |
| 1-2% | 7468 | +0.064 | 0.302 | -0.238 |
| 2-3% | 4956 | +0.028 | 0.274 | -0.246 |
| 3%+ | 6020 | +0.007 | 0.266 | -0.259 |

## Fixes tested: entry and exit variants

Entry: mkt = market order next bar (current), lim = limit at the signal close, good 3 minutes (no chase). Plan: h2 = half at 1R, rest 2R (current); r3 = all at 3R; tr = half at 1R, trail the rest on the 9 EMA.
Net R below uses the typical measured spread; survivors must also stay positive with the bot's slippage and the worse (75th pct) spread.

Measured quoted spreads at entry (median / 75th pct): under $5 0.46% / 0.69%, $5-10 0.23% / 0.53%, $10-20 0.24% / 0.49%, $20-50 0.24% / 0.44%, $50+ 0.21% / 0.39%. A market order pays about half the spread on the way in and half on the way out.

| Strategy | Entry | Plan | Trades | Fill rate | Gross R | Net R | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|
| hod_break | lim | h2 | 633 | 90% | +0.016 | -0.025 | -0.61 | -0.071 | +0.020 |
| ema_bounce | lim | r3 | 5002 | 91% | +0.058 | -0.032 | -1.26 | -0.033 | -0.031 |
| hod_break | lim | tr | 633 | 90% | +0.010 | -0.038 | -0.97 | -0.064 | -0.012 |
| orb15 | lim | h2 | 1284 | 91% | +0.007 | -0.038 | -1.3 | -0.038 | -0.039 |
| pm_high_break | lim | h2 | 647 | 93% | +0.004 | -0.040 | -0.94 | -0.047 | -0.033 |
| orb15 | lim | tr | 1284 | 91% | +0.004 | -0.049 | -1.74 | -0.066 | -0.032 |
| hod_break | lim | r3 | 633 | 90% | -0.001 | -0.056 | -0.95 | -0.166 | +0.053 |
| afternoon_hod | lim | h2 | 754 | 89% | -0.006 | -0.066 | -1.78 | -0.100 | -0.033 |
| ema_bounce | lim | h2 | 5002 | 91% | +0.006 | -0.068 | -4.24 | -0.060 | -0.076 |
| orb15 | lim | r3 | 1284 | 91% | -0.015 | -0.073 | -1.75 | -0.065 | -0.081 |
| pm_high_break | lim | tr | 647 | 93% | -0.020 | -0.074 | -1.83 | -0.075 | -0.072 |
| afternoon_hod | lim | tr | 754 | 89% | -0.007 | -0.075 | -2.05 | -0.125 | -0.026 |
| bull_flag | lim | r3 | 2105 | 90% | +0.001 | -0.076 | -1.99 | -0.133 | -0.018 |
| hod_break | mkt | h2 | 705 | 100% | +0.026 | -0.078 | -1.98 | -0.116 | -0.040 |
| bull_flag | lim | h2 | 2105 | 90% | -0.019 | -0.081 | -3.34 | -0.086 | -0.076 |

**Survivors (net > +0.05R, t > 2, positive in both halves, 200+ trades): 0** (none yet)

## Path to $20/day

Current 6 accounts replayed over the backtest with every live rule (1 trade/day, price cap, on/off, filter):

| Account | $/day | Days traded | Worst day |
|---|---|---|---|
| $200 | $+0.00 | 0/521 | $0.00 |
| $250 | $+0.00 | 0/521 | $0.00 |
| $350 | $+0.00 | 0/521 | $0.00 |
| $400 | $+0.00 | 0/521 | $0.00 |
| $550 | $+0.00 | 0/521 | $0.00 |
| $1000 | $+0.00 | 0/521 | $0.00 |

**All accounts: $+0.00/day.**
The current setup does not show a positive edge after costs, so more money would only lose faster. Fix the strategy list first.
