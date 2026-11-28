# Research scorecard (2026-11-28)

Backtest: 535 trading days (2024-10-10 to 2026-11-27), 22601 signals across 2213 stocks. Same rules, fills and slippage as the live bot; candidates picked only from what was known at the open.

All signals together: -0.273R per trade, win rate 42%, t=-34.71.

## Strategies, best to worst

| Strategy | Trades | Per day | Win % | Avg R | Avg R (top 1% removed) | t | 1st half | 2nd half | With news | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| hod_break | 732 | 1.37 | 47% | -0.143 | -0.143 | -3.67 | -0.184 | -0.101 | -0.163 | **off**: loses -0.14R/trade over 732 trades |
| pm_high_break | 722 | 1.35 | 45% | -0.166 | -0.166 | -4.19 | -0.155 | -0.178 | -0.156 | **off**: loses -0.17R/trade over 722 trades |
| orb15 | 1453 | 2.72 | 46% | -0.167 | -0.167 | -6.11 | -0.178 | -0.157 | -0.167 | **off**: decay: last 50 live signals avg -0.34R |
| orb5 | 2451 | 4.58 | 44% | -0.191 | -0.191 | -8.74 | -0.181 | -0.201 | -0.216 | **off**: decay: last 50 live signals avg -0.49R |
| afternoon_hod | 857 | 1.6 | 42% | -0.210 | -0.210 | -6.2 | -0.218 | -0.203 | -0.175 | **off**: decay: last 50 live signals avg -0.54R |
| ema_bounce | 5638 | 10.54 | 43% | -0.255 | -0.255 | -16.93 | -0.248 | -0.263 | -0.259 | **off**: decay: last 50 live signals avg -0.45R |
| bull_flag | 2429 | 4.54 | 43% | -0.256 | -0.256 | -11.25 | -0.251 | -0.261 | -0.304 | **off**: decay: last 50 live signals avg -0.70R |
| failed_breakdown | 2732 | 5.11 | 42% | -0.264 | -0.264 | -12.83 | -0.246 | -0.282 | -0.290 | **off**: decay: last 50 live signals avg -0.30R |
| eod_squeeze | 790 | 1.48 | 37% | -0.307 | -0.402 | -3.46 | -0.143 | -0.471 | -0.216 | **off**: loses -0.31R/trade over 790 trades |
| vwap_pullback | 4797 | 8.97 | 38% | -0.424 | -0.424 | -25.79 | -0.437 | -0.411 | -0.434 | **off**: decay: last 50 live signals avg -0.40R |

t above 2 means the edge is very unlikely to be luck; between 1 and 2 is promising; below 1 is noise.

## Trade filter (learned from conditions)

Tested on the most recent 30% of data it never saw: all signals -0.267R vs filtered -0.108R (2952 of 6781 kept). Filter is **OFF (did not beat taking everything)**.

Conditions that matter most (positive = helps, negative = hurts): log_price +0.21, risk_pct +0.13, orb5 -0.12, vwap_pullback -0.12, minute -0.08, orb15 -0.07, failed_breakdown -0.07, bull_flag +0.06, pm_high_break -0.06, log_pm_rvol +0.05

## Where the money goes: edge vs trading costs

Gross R = what the setup earned before slippage/spread. Cost R = round-trip slippage as a share of the risk. A strategy only works when gross beats cost.

| Strategy | Gross R | Cost R | Net R |
|---|---|---|---|
| afternoon_hod | +0.034 | 0.244 | -0.210 |
| bull_flag | +0.056 | 0.312 | -0.256 |
| ema_bounce | +0.094 | 0.350 | -0.255 |
| eod_squeeze | +0.029 | 0.336 | -0.307 |
| failed_breakdown | +0.024 | 0.288 | -0.264 |
| hod_break | +0.052 | 0.194 | -0.143 |
| orb15 | +0.035 | 0.202 | -0.167 |
| orb5 | +0.005 | 0.196 | -0.191 |
| pm_high_break | +0.033 | 0.199 | -0.166 |
| vwap_pullback | +0.056 | 0.480 | -0.424 |

**By stock price**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under $5 | 4782 | +0.024 | 0.562 | -0.538 |
| $5-10 | 4047 | +0.055 | 0.322 | -0.267 |
| $10-20 | 4882 | +0.054 | 0.232 | -0.178 |
| $20-50 | 6041 | +0.061 | 0.246 | -0.185 |
| $50+ | 2849 | +0.072 | 0.260 | -0.188 |

**By stop width**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under 1% | 3579 | +0.124 | 0.543 | -0.420 |
| 1-2% | 7660 | +0.067 | 0.302 | -0.235 |
| 2-3% | 5134 | +0.033 | 0.276 | -0.242 |
| 3%+ | 6228 | +0.008 | 0.269 | -0.261 |

## Fixes tested: entry and exit variants

Entry: mkt = market order next bar (current), lim = limit at the signal close, good 3 minutes (no chase). Plan: h2 = half at 1R, rest 2R (current); r3 = all at 3R; tr = half at 1R, trail the rest on the 9 EMA.
Net R below uses the typical measured spread; survivors must also stay positive with the bot's slippage and the worse (75th pct) spread.

Measured quoted spreads at entry (median / 75th pct): under $5 0.46% / 0.69%, $5-10 0.23% / 0.53%, $10-20 0.24% / 0.49%, $20-50 0.24% / 0.44%, $50+ 0.21% / 0.39%. A market order pays about half the spread on the way in and half on the way out.

| Strategy | Entry | Plan | Trades | Fill rate | Gross R | Net R | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|
| ema_bounce | lim | r3 | 5135 | 91% | +0.065 | -0.025 | -1.01 | -0.029 | -0.022 |
| hod_break | lim | h2 | 658 | 90% | +0.008 | -0.032 | -0.8 | -0.064 | -0.001 |
| orb15 | lim | h2 | 1324 | 91% | +0.008 | -0.037 | -1.28 | -0.044 | -0.030 |
| hod_break | lim | tr | 658 | 90% | +0.004 | -0.043 | -1.13 | -0.067 | -0.020 |
| orb15 | lim | tr | 1324 | 91% | +0.007 | -0.045 | -1.64 | -0.071 | -0.020 |
| pm_high_break | lim | h2 | 670 | 93% | -0.005 | -0.049 | -1.17 | -0.029 | -0.068 |
| ema_bounce | lim | h2 | 5135 | 91% | +0.012 | -0.062 | -3.93 | -0.059 | -0.066 |
| hod_break | lim | r3 | 658 | 90% | -0.008 | -0.063 | -1.08 | -0.142 | +0.017 |
| afternoon_hod | lim | h2 | 767 | 89% | -0.010 | -0.070 | -1.89 | -0.094 | -0.046 |
| orb15 | lim | r3 | 1324 | 91% | -0.018 | -0.075 | -1.84 | -0.072 | -0.079 |
| bull_flag | lim | r3 | 2180 | 90% | +0.000 | -0.077 | -2.06 | -0.139 | -0.015 |
| afternoon_hod | lim | tr | 767 | 89% | -0.011 | -0.080 | -2.19 | -0.119 | -0.040 |
| bull_flag | lim | h2 | 2180 | 90% | -0.019 | -0.081 | -3.39 | -0.083 | -0.079 |
| pm_high_break | lim | tr | 670 | 93% | -0.031 | -0.084 | -2.14 | -0.064 | -0.105 |
| hod_break | mkt | h2 | 732 | 100% | +0.018 | -0.085 | -2.2 | -0.116 | -0.054 |

**Survivors (net > +0.05R, t > 2, positive in both halves, 200+ trades): 0** (none yet)

## Path to $20/day

Current 6 accounts replayed over the backtest with every live rule (1 trade/day, price cap, on/off, filter):

| Account | $/day | Days traded | Worst day |
|---|---|---|---|
| $200 | $+0.00 | 0/535 | $0.00 |
| $250 | $+0.00 | 0/535 | $0.00 |
| $350 | $+0.00 | 0/535 | $0.00 |
| $400 | $+0.00 | 0/535 | $0.00 |
| $550 | $+0.00 | 0/535 | $0.00 |
| $1000 | $+0.00 | 0/535 | $0.00 |

**All accounts: $+0.00/day.**
The current setup does not show a positive edge after costs, so more money would only lose faster. Fix the strategy list first.
