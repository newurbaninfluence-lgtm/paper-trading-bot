# Research scorecard (2026-11-14)

Backtest: 526 trading days (2024-10-10 to 2026-11-13), 22174 signals across 2206 stocks. Same rules, fills and slippage as the live bot; candidates picked only from what was known at the open.

All signals together: -0.275R per trade, win rate 42%, t=-34.55.

## Strategies, best to worst

| Strategy | Trades | Per day | Win % | Avg R | Avg R (top 1% removed) | t | 1st half | 2nd half | With news | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| hod_break | 716 | 1.36 | 47% | -0.142 | -0.142 | -3.61 | -0.185 | -0.099 | -0.160 | **off**: loses -0.14R/trade over 716 trades |
| pm_high_break | 704 | 1.34 | 46% | -0.158 | -0.158 | -3.94 | -0.144 | -0.172 | -0.156 | **off**: loses -0.16R/trade over 704 trades |
| orb15 | 1420 | 2.7 | 46% | -0.163 | -0.163 | -5.88 | -0.170 | -0.156 | -0.165 | **off**: loses -0.16R/trade over 1420 trades |
| orb5 | 2400 | 4.56 | 44% | -0.187 | -0.187 | -8.45 | -0.169 | -0.204 | -0.218 | **off**: decay: last 50 live signals avg -0.32R |
| afternoon_hod | 852 | 1.62 | 42% | -0.209 | -0.209 | -6.13 | -0.220 | -0.197 | -0.176 | **off**: decay: last 49 live signals avg -0.51R |
| bull_flag | 2371 | 4.51 | 43% | -0.250 | -0.250 | -10.85 | -0.253 | -0.247 | -0.303 | **off**: decay: last 50 live signals avg -0.29R |
| ema_bounce | 5538 | 10.53 | 42% | -0.261 | -0.261 | -17.17 | -0.246 | -0.276 | -0.261 | **off**: decay: last 50 live signals avg -0.40R |
| failed_breakdown | 2682 | 5.1 | 42% | -0.265 | -0.265 | -12.76 | -0.240 | -0.289 | -0.290 | **off**: loses -0.27R/trade over 2682 trades |
| eod_squeeze | 779 | 1.48 | 37% | -0.319 | -0.416 | -3.56 | -0.137 | -0.500 | -0.217 | **off**: loses -0.32R/trade over 779 trades |
| vwap_pullback | 4712 | 8.96 | 38% | -0.430 | -0.430 | -25.96 | -0.434 | -0.425 | -0.435 | **off**: decay: last 50 live signals avg -0.21R |

t above 2 means the edge is very unlikely to be luck; between 1 and 2 is promising; below 1 is noise.

## Trade filter (learned from conditions)

Tested on the most recent 30% of data it never saw: all signals -0.272R vs filtered -0.112R (2920 of 6653 kept). Filter is **OFF (did not beat taking everything)**.

Conditions that matter most (positive = helps, negative = hurts): log_price +0.21, vwap_pullback -0.13, risk_pct +0.13, orb5 -0.11, minute -0.08, failed_breakdown -0.07, bull_flag +0.07, eod_squeeze -0.07, orb15 -0.06, log_pm_rvol +0.05

## Where the money goes: edge vs trading costs

Gross R = what the setup earned before slippage/spread. Cost R = round-trip slippage as a share of the risk. A strategy only works when gross beats cost.

| Strategy | Gross R | Cost R | Net R |
|---|---|---|---|
| afternoon_hod | +0.036 | 0.244 | -0.209 |
| bull_flag | +0.061 | 0.312 | -0.250 |
| ema_bounce | +0.088 | 0.349 | -0.261 |
| eod_squeeze | +0.019 | 0.337 | -0.319 |
| failed_breakdown | +0.023 | 0.288 | -0.265 |
| hod_break | +0.054 | 0.196 | -0.142 |
| orb15 | +0.038 | 0.201 | -0.163 |
| orb5 | +0.009 | 0.195 | -0.187 |
| pm_high_break | +0.041 | 0.199 | -0.158 |
| vwap_pullback | +0.050 | 0.480 | -0.430 |

**By stock price**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under $5 | 4651 | +0.022 | 0.561 | -0.539 |
| $5-10 | 3974 | +0.055 | 0.322 | -0.267 |
| $10-20 | 4804 | +0.049 | 0.233 | -0.184 |
| $20-50 | 5955 | +0.060 | 0.247 | -0.187 |
| $50+ | 2790 | +0.072 | 0.262 | -0.190 |

**By stop width**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under 1% | 3538 | +0.121 | 0.543 | -0.423 |
| 1-2% | 7542 | +0.064 | 0.303 | -0.238 |
| 2-3% | 5014 | +0.031 | 0.275 | -0.244 |
| 3%+ | 6080 | +0.008 | 0.267 | -0.259 |

## Fixes tested: entry and exit variants

Entry: mkt = market order next bar (current), lim = limit at the signal close, good 3 minutes (no chase). Plan: h2 = half at 1R, rest 2R (current); r3 = all at 3R; tr = half at 1R, trail the rest on the 9 EMA.
Net R below uses the typical measured spread; survivors must also stay positive with the bot's slippage and the worse (75th pct) spread.

Measured quoted spreads at entry (median / 75th pct): under $5 0.46% / 0.69%, $5-10 0.23% / 0.53%, $10-20 0.24% / 0.49%, $20-50 0.24% / 0.44%, $50+ 0.21% / 0.39%. A market order pays about half the spread on the way in and half on the way out.

| Strategy | Entry | Plan | Trades | Fill rate | Gross R | Net R | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|
| hod_break | lim | h2 | 644 | 90% | +0.010 | -0.031 | -0.74 | -0.066 | +0.005 |
| ema_bounce | lim | r3 | 5050 | 91% | +0.058 | -0.032 | -1.28 | -0.029 | -0.035 |
| orb15 | lim | h2 | 1293 | 91% | +0.009 | -0.036 | -1.22 | -0.034 | -0.037 |
| pm_high_break | lim | h2 | 652 | 93% | +0.007 | -0.038 | -0.89 | -0.037 | -0.038 |
| hod_break | lim | tr | 644 | 90% | +0.006 | -0.042 | -1.08 | -0.063 | -0.021 |
| orb15 | lim | tr | 1293 | 91% | +0.005 | -0.047 | -1.68 | -0.063 | -0.031 |
| hod_break | lim | r3 | 644 | 90% | -0.004 | -0.059 | -1.0 | -0.155 | +0.037 |
| ema_bounce | lim | h2 | 5050 | 91% | +0.006 | -0.068 | -4.25 | -0.057 | -0.079 |
| orb15 | lim | r3 | 1293 | 91% | -0.011 | -0.069 | -1.66 | -0.064 | -0.073 |
| bull_flag | lim | r3 | 2129 | 90% | +0.007 | -0.070 | -1.84 | -0.125 | -0.014 |
| afternoon_hod | lim | h2 | 762 | 89% | -0.010 | -0.070 | -1.89 | -0.095 | -0.045 |
| pm_high_break | lim | tr | 652 | 93% | -0.018 | -0.072 | -1.79 | -0.067 | -0.077 |
| bull_flag | lim | h2 | 2129 | 90% | -0.014 | -0.077 | -3.17 | -0.083 | -0.071 |
| afternoon_hod | lim | tr | 762 | 89% | -0.011 | -0.080 | -2.19 | -0.120 | -0.040 |
| orb5 | lim | h2 | 2261 | 94% | -0.044 | -0.081 | -3.58 | -0.058 | -0.105 |

**Survivors (net > +0.05R, t > 2, positive in both halves, 200+ trades): 0** (none yet)

## Path to $20/day

Current 6 accounts replayed over the backtest with every live rule (1 trade/day, price cap, on/off, filter):

| Account | $/day | Days traded | Worst day |
|---|---|---|---|
| $200 | $+0.00 | 0/526 | $0.00 |
| $250 | $+0.00 | 0/526 | $0.00 |
| $350 | $+0.00 | 0/526 | $0.00 |
| $400 | $+0.00 | 0/526 | $0.00 |
| $550 | $+0.00 | 0/526 | $0.00 |
| $1000 | $+0.00 | 0/526 | $0.00 |

**All accounts: $+0.00/day.**
The current setup does not show a positive edge after costs, so more money would only lose faster. Fix the strategy list first.
