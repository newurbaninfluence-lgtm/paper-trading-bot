# Research scorecard (2026-10-17)

Backtest: 506 trading days (2024-10-10 to 2026-10-16), 21225 signals across 2151 stocks. Same rules, fills and slippage as the live bot; candidates picked only from what was known at the open.

All signals together: -0.279R per trade, win rate 42%, t=-34.25.

## Strategies, best to worst

| Strategy | Trades | Per day | Win % | Avg R | Avg R (top 1% removed) | t | 1st half | 2nd half | With news | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| pm_high_break | 667 | 1.32 | 46% | -0.150 | -0.150 | -3.61 | -0.180 | -0.119 | -0.159 | **off**: loses -0.15R/trade over 667 trades |
| hod_break | 672 | 1.33 | 46% | -0.152 | -0.152 | -3.74 | -0.218 | -0.087 | -0.159 | **off**: loses -0.15R/trade over 672 trades |
| orb15 | 1357 | 2.68 | 45% | -0.173 | -0.173 | -6.09 | -0.180 | -0.165 | -0.178 | **off**: loses -0.17R/trade over 1357 trades |
| orb5 | 2301 | 4.55 | 44% | -0.188 | -0.188 | -8.31 | -0.176 | -0.199 | -0.218 | **off**: loses -0.19R/trade over 2301 trades |
| afternoon_hod | 810 | 1.6 | 43% | -0.193 | -0.193 | -5.51 | -0.222 | -0.164 | -0.148 | **off**: loses -0.19R/trade over 810 trades |
| bull_flag | 2248 | 4.44 | 43% | -0.258 | -0.258 | -10.95 | -0.255 | -0.261 | -0.304 | **off**: loses -0.26R/trade over 2248 trades |
| failed_breakdown | 2583 | 5.1 | 42% | -0.263 | -0.263 | -12.45 | -0.244 | -0.283 | -0.288 | **off**: loses -0.26R/trade over 2583 trades |
| ema_bounce | 5321 | 10.52 | 42% | -0.267 | -0.267 | -17.28 | -0.247 | -0.288 | -0.264 | **off**: loses -0.27R/trade over 5321 trades |
| eod_squeeze | 744 | 1.47 | 36% | -0.331 | -0.433 | -3.56 | -0.175 | -0.488 | -0.223 | **off**: loses -0.33R/trade over 744 trades |
| vwap_pullback | 4522 | 8.94 | 38% | -0.434 | -0.434 | -25.75 | -0.442 | -0.426 | -0.440 | **off**: loses -0.43R/trade over 4522 trades |

t above 2 means the edge is very unlikely to be luck; between 1 and 2 is promising; below 1 is noise.

## Trade filter (learned from conditions)

Tested on the most recent 30% of data it never saw: all signals -0.296R vs filtered -0.139R (2930 of 6368 kept). Filter is **OFF (did not beat taking everything)**.

Conditions that matter most (positive = helps, negative = hurts): log_price +0.21, vwap_pullback -0.13, risk_pct +0.13, orb5 -0.10, eod_squeeze -0.09, afternoon_hod +0.07, orb15 -0.07, minute -0.07, failed_breakdown -0.07, bull_flag +0.06

## Where the money goes: edge vs trading costs

Gross R = what the setup earned before slippage/spread. Cost R = round-trip slippage as a share of the risk. A strategy only works when gross beats cost.

| Strategy | Gross R | Cost R | Net R |
|---|---|---|---|
| afternoon_hod | +0.049 | 0.242 | -0.193 |
| bull_flag | +0.052 | 0.310 | -0.258 |
| ema_bounce | +0.079 | 0.347 | -0.267 |
| eod_squeeze | +0.006 | 0.338 | -0.331 |
| failed_breakdown | +0.023 | 0.287 | -0.263 |
| hod_break | +0.045 | 0.197 | -0.152 |
| orb15 | +0.029 | 0.202 | -0.173 |
| orb5 | +0.008 | 0.195 | -0.188 |
| pm_high_break | +0.048 | 0.198 | -0.150 |
| vwap_pullback | +0.043 | 0.477 | -0.434 |

**By stock price**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under $5 | 4426 | +0.016 | 0.558 | -0.542 |
| $5-10 | 3785 | +0.049 | 0.322 | -0.273 |
| $10-20 | 4541 | +0.043 | 0.231 | -0.188 |
| $20-50 | 5770 | +0.056 | 0.247 | -0.191 |
| $50+ | 2703 | +0.068 | 0.262 | -0.195 |

**By stop width**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under 1% | 3407 | +0.114 | 0.542 | -0.428 |
| 1-2% | 7197 | +0.060 | 0.302 | -0.242 |
| 2-3% | 4801 | +0.024 | 0.273 | -0.248 |
| 3%+ | 5820 | +0.003 | 0.265 | -0.262 |

## Fixes tested: entry and exit variants

Entry: mkt = market order next bar (current), lim = limit at the signal close, good 3 minutes (no chase). Plan: h2 = half at 1R, rest 2R (current); r3 = all at 3R; tr = half at 1R, trail the rest on the 9 EMA.
Net R below uses the typical measured spread; survivors must also stay positive with the bot's slippage and the worse (75th pct) spread.

Measured quoted spreads at entry (median / 75th pct): under $5 0.46% / 0.69%, $5-10 0.23% / 0.53%, $10-20 0.24% / 0.49%, $20-50 0.24% / 0.44%, $50+ 0.21% / 0.39%. A market order pays about half the spread on the way in and half on the way out.

| Strategy | Entry | Plan | Trades | Fill rate | Gross R | Net R | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|
| pm_high_break | lim | h2 | 618 | 93% | +0.018 | -0.025 | -0.58 | -0.052 | +0.001 |
| hod_break | lim | h2 | 605 | 90% | +0.005 | -0.037 | -0.86 | -0.085 | +0.012 |
| ema_bounce | lim | r3 | 4856 | 91% | +0.048 | -0.043 | -1.67 | -0.035 | -0.051 |
| hod_break | lim | tr | 605 | 90% | -0.000 | -0.048 | -1.2 | -0.083 | -0.014 |
| orb15 | lim | h2 | 1233 | 91% | -0.003 | -0.049 | -1.62 | -0.041 | -0.056 |
| afternoon_hod | lim | h2 | 725 | 90% | +0.003 | -0.057 | -1.49 | -0.095 | -0.018 |
| orb15 | lim | tr | 1233 | 91% | -0.005 | -0.058 | -1.99 | -0.074 | -0.041 |
| pm_high_break | lim | tr | 618 | 93% | -0.009 | -0.062 | -1.51 | -0.079 | -0.046 |
| afternoon_hod | lim | tr | 725 | 90% | +0.002 | -0.065 | -1.72 | -0.121 | -0.008 |
| afternoon_hod | lim | r3 | 725 | 90% | +0.009 | -0.069 | -1.37 | -0.117 | -0.020 |
| hod_break | lim | r3 | 605 | 90% | -0.014 | -0.069 | -1.14 | -0.156 | +0.017 |
| ema_bounce | lim | h2 | 4856 | 91% | +0.001 | -0.074 | -4.54 | -0.058 | -0.090 |
| bull_flag | lim | r3 | 2018 | 90% | -0.001 | -0.078 | -2.0 | -0.140 | -0.016 |
| orb15 | lim | r3 | 1233 | 91% | -0.023 | -0.081 | -1.91 | -0.073 | -0.089 |
| bull_flag | lim | h2 | 2018 | 90% | -0.019 | -0.081 | -3.29 | -0.082 | -0.081 |

**Survivors (net > +0.05R, t > 2, positive in both halves, 200+ trades): 0** (none yet)

## Path to $20/day

Current 6 accounts replayed over the backtest with every live rule (1 trade/day, price cap, on/off, filter):

| Account | $/day | Days traded | Worst day |
|---|---|---|---|
| $200 | $+0.00 | 0/506 | $0.00 |
| $250 | $+0.00 | 0/506 | $0.00 |
| $350 | $+0.00 | 0/506 | $0.00 |
| $400 | $+0.00 | 0/506 | $0.00 |
| $550 | $+0.00 | 0/506 | $0.00 |
| $1000 | $+0.00 | 0/506 | $0.00 |

**All accounts: $+0.00/day.**
The current setup does not show a positive edge after costs, so more money would only lose faster. Fix the strategy list first.
