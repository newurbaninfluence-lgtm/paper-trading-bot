# Research scorecard (2026-10-24)

Backtest: 511 trading days (2024-10-10 to 2026-10-23), 21458 signals across 2170 stocks. Same rules, fills and slippage as the live bot; candidates picked only from what was known at the open.

All signals together: -0.277R per trade, win rate 42%, t=-34.26.

## Strategies, best to worst

| Strategy | Trades | Per day | Win % | Avg R | Avg R (top 1% removed) | t | 1st half | 2nd half | With news | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| hod_break | 680 | 1.33 | 47% | -0.147 | -0.147 | -3.62 | -0.215 | -0.079 | -0.157 | **off**: loses -0.15R/trade over 680 trades |
| pm_high_break | 678 | 1.33 | 46% | -0.154 | -0.154 | -3.76 | -0.188 | -0.121 | -0.164 | **off**: loses -0.15R/trade over 678 trades |
| orb15 | 1377 | 2.69 | 45% | -0.173 | -0.173 | -6.15 | -0.181 | -0.165 | -0.178 | **off**: loses -0.17R/trade over 1377 trades |
| orb5 | 2332 | 4.56 | 44% | -0.190 | -0.190 | -8.48 | -0.176 | -0.204 | -0.220 | **off**: loses -0.19R/trade over 2332 trades |
| afternoon_hod | 817 | 1.6 | 43% | -0.192 | -0.192 | -5.53 | -0.225 | -0.160 | -0.152 | **off**: loses -0.19R/trade over 817 trades |
| bull_flag | 2273 | 4.45 | 43% | -0.251 | -0.251 | -10.7 | -0.258 | -0.244 | -0.300 | **off**: loses -0.25R/trade over 2273 trades |
| failed_breakdown | 2615 | 5.12 | 42% | -0.264 | -0.264 | -12.55 | -0.248 | -0.280 | -0.287 | **off**: loses -0.26R/trade over 2615 trades |
| ema_bounce | 5370 | 10.51 | 42% | -0.265 | -0.265 | -17.21 | -0.249 | -0.280 | -0.261 | **off**: decay: last 50 live signals avg -0.15R |
| eod_squeeze | 750 | 1.47 | 36% | -0.328 | -0.429 | -3.54 | -0.180 | -0.476 | -0.226 | **off**: loses -0.33R/trade over 750 trades |
| vwap_pullback | 4566 | 8.94 | 38% | -0.432 | -0.432 | -25.77 | -0.437 | -0.428 | -0.436 | **off**: decay: last 36 live signals avg -0.70R |

t above 2 means the edge is very unlikely to be luck; between 1 and 2 is promising; below 1 is noise.

## Trade filter (learned from conditions)

Tested on the most recent 30% of data it never saw: all signals -0.292R vs filtered -0.128R (2913 of 6438 kept). Filter is **OFF (did not beat taking everything)**.

Conditions that matter most (positive = helps, negative = hurts): log_price +0.21, vwap_pullback -0.13, risk_pct +0.13, orb5 -0.11, eod_squeeze -0.09, afternoon_hod +0.08, orb15 -0.07, minute -0.07, bull_flag +0.07, failed_breakdown -0.07

## Where the money goes: edge vs trading costs

Gross R = what the setup earned before slippage/spread. Cost R = round-trip slippage as a share of the risk. A strategy only works when gross beats cost.

| Strategy | Gross R | Cost R | Net R |
|---|---|---|---|
| afternoon_hod | +0.050 | 0.243 | -0.192 |
| bull_flag | +0.059 | 0.310 | -0.251 |
| ema_bounce | +0.082 | 0.347 | -0.265 |
| eod_squeeze | +0.011 | 0.339 | -0.328 |
| failed_breakdown | +0.023 | 0.287 | -0.264 |
| hod_break | +0.051 | 0.197 | -0.147 |
| orb15 | +0.029 | 0.202 | -0.173 |
| orb5 | +0.006 | 0.196 | -0.190 |
| pm_high_break | +0.044 | 0.198 | -0.154 |
| vwap_pullback | +0.045 | 0.478 | -0.432 |

**By stock price**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under $5 | 4490 | +0.022 | 0.558 | -0.536 |
| $5-10 | 3819 | +0.047 | 0.322 | -0.275 |
| $10-20 | 4632 | +0.042 | 0.232 | -0.189 |
| $20-50 | 5803 | +0.059 | 0.247 | -0.188 |
| $50+ | 2714 | +0.071 | 0.262 | -0.192 |

**By stop width**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under 1% | 3437 | +0.117 | 0.543 | -0.425 |
| 1-2% | 7273 | +0.061 | 0.302 | -0.241 |
| 2-3% | 4854 | +0.028 | 0.273 | -0.245 |
| 3%+ | 5894 | +0.004 | 0.266 | -0.262 |

## Fixes tested: entry and exit variants

Entry: mkt = market order next bar (current), lim = limit at the signal close, good 3 minutes (no chase). Plan: h2 = half at 1R, rest 2R (current); r3 = all at 3R; tr = half at 1R, trail the rest on the 9 EMA.
Net R below uses the typical measured spread; survivors must also stay positive with the bot's slippage and the worse (75th pct) spread.

Measured quoted spreads at entry (median / 75th pct): under $5 0.46% / 0.69%, $5-10 0.23% / 0.53%, $10-20 0.24% / 0.49%, $20-50 0.24% / 0.44%, $50+ 0.21% / 0.39%. A market order pays about half the spread on the way in and half on the way out.

| Strategy | Entry | Plan | Trades | Fill rate | Gross R | Net R | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|
| hod_break | lim | h2 | 611 | 90% | +0.013 | -0.028 | -0.67 | -0.080 | +0.023 |
| pm_high_break | lim | h2 | 629 | 93% | +0.012 | -0.032 | -0.75 | -0.052 | -0.013 |
| ema_bounce | lim | r3 | 4901 | 91% | +0.052 | -0.038 | -1.52 | -0.039 | -0.038 |
| orb15 | lim | h2 | 1252 | 91% | +0.003 | -0.042 | -1.43 | -0.043 | -0.042 |
| hod_break | lim | tr | 611 | 90% | +0.006 | -0.042 | -1.04 | -0.076 | -0.008 |
| orb15 | lim | tr | 1252 | 91% | +0.002 | -0.051 | -1.77 | -0.073 | -0.028 |
| afternoon_hod | lim | h2 | 730 | 89% | +0.003 | -0.057 | -1.49 | -0.091 | -0.023 |
| hod_break | lim | r3 | 611 | 90% | -0.005 | -0.061 | -1.0 | -0.165 | +0.043 |
| afternoon_hod | lim | tr | 730 | 89% | +0.003 | -0.064 | -1.72 | -0.119 | -0.010 |
| pm_high_break | lim | tr | 629 | 93% | -0.014 | -0.068 | -1.65 | -0.081 | -0.054 |
| bull_flag | lim | r3 | 2042 | 90% | +0.007 | -0.069 | -1.8 | -0.143 | +0.004 |
| ema_bounce | lim | h2 | 4901 | 91% | +0.002 | -0.072 | -4.43 | -0.062 | -0.081 |
| afternoon_hod | lim | r3 | 730 | 89% | +0.004 | -0.074 | -1.49 | -0.109 | -0.039 |
| bull_flag | lim | h2 | 2042 | 90% | -0.014 | -0.076 | -3.09 | -0.084 | -0.068 |
| orb15 | lim | r3 | 1252 | 91% | -0.024 | -0.081 | -1.93 | -0.071 | -0.091 |

**Survivors (net > +0.05R, t > 2, positive in both halves, 200+ trades): 0** (none yet)

## Path to $20/day

Current 6 accounts replayed over the backtest with every live rule (1 trade/day, price cap, on/off, filter):

| Account | $/day | Days traded | Worst day |
|---|---|---|---|
| $200 | $+0.00 | 0/511 | $0.00 |
| $250 | $+0.00 | 0/511 | $0.00 |
| $350 | $+0.00 | 0/511 | $0.00 |
| $400 | $+0.00 | 0/511 | $0.00 |
| $550 | $+0.00 | 0/511 | $0.00 |
| $1000 | $+0.00 | 0/511 | $0.00 |

**All accounts: $+0.00/day.**
The current setup does not show a positive edge after costs, so more money would only lose faster. Fix the strategy list first.
