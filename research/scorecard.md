# Research scorecard (2026-10-09)

Backtest: 500 trading days (2024-10-10 to 2026-10-08), 21019 signals across 2142 stocks. Same rules, fills and slippage as the live bot; candidates picked only from what was known at the open.

All signals together: -0.276R per trade, win rate 42%, t=-33.69.

## Strategies, best to worst

| Strategy | Trades | Per day | Win % | Avg R | Avg R (top 1% removed) | t | 1st half | 2nd half | With news | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| pm_high_break | 667 | 1.33 | 46% | -0.150 | -0.150 | -3.61 | -0.180 | -0.119 | -0.159 | **off**: loses -0.15R/trade over 667 trades |
| hod_break | 666 | 1.33 | 46% | -0.161 | -0.161 | -3.95 | -0.222 | -0.100 | -0.159 | **off**: loses -0.16R/trade over 666 trades |
| orb15 | 1342 | 2.68 | 45% | -0.168 | -0.168 | -5.91 | -0.178 | -0.158 | -0.173 | **off**: loses -0.17R/trade over 1342 trades |
| orb5 | 2268 | 4.54 | 44% | -0.186 | -0.186 | -8.16 | -0.175 | -0.196 | -0.213 | **off**: loses -0.19R/trade over 2268 trades |
| afternoon_hod | 803 | 1.61 | 43% | -0.192 | -0.192 | -5.47 | -0.218 | -0.166 | -0.148 | **off**: loses -0.19R/trade over 803 trades |
| bull_flag | 2232 | 4.46 | 43% | -0.258 | -0.258 | -10.9 | -0.251 | -0.264 | -0.301 | **off**: loses -0.26R/trade over 2232 trades |
| failed_breakdown | 2548 | 5.1 | 42% | -0.259 | -0.259 | -12.17 | -0.239 | -0.280 | -0.287 | **off**: loses -0.26R/trade over 2548 trades |
| ema_bounce | 5277 | 10.55 | 42% | -0.263 | -0.263 | -16.92 | -0.243 | -0.282 | -0.260 | **off**: loses -0.26R/trade over 5277 trades |
| eod_squeeze | 739 | 1.48 | 37% | -0.326 | -0.429 | -3.48 | -0.174 | -0.478 | -0.223 | **off**: loses -0.33R/trade over 739 trades |
| vwap_pullback | 4477 | 8.95 | 38% | -0.430 | -0.430 | -25.34 | -0.439 | -0.420 | -0.437 | **off**: loses -0.43R/trade over 4477 trades |

t above 2 means the edge is very unlikely to be luck; between 1 and 2 is promising; below 1 is noise.

## Trade filter (learned from conditions)

Tested on the most recent 30% of data it never saw: all signals -0.284R vs filtered -0.112R (2147 of 6306 kept). Filter is **OFF (did not beat taking everything)**.

Conditions that matter most (positive = helps, negative = hurts): log_price +0.21, vwap_pullback -0.13, risk_pct +0.13, orb5 -0.11, eod_squeeze -0.08, afternoon_hod +0.08, minute -0.07, orb15 -0.07, failed_breakdown -0.06, bull_flag +0.06

## Where the money goes: edge vs trading costs

Gross R = what the setup earned before slippage/spread. Cost R = round-trip slippage as a share of the risk. A strategy only works when gross beats cost.

| Strategy | Gross R | Cost R | Net R |
|---|---|---|---|
| afternoon_hod | +0.050 | 0.242 | -0.192 |
| bull_flag | +0.052 | 0.310 | -0.258 |
| ema_bounce | +0.083 | 0.346 | -0.263 |
| eod_squeeze | +0.011 | 0.337 | -0.326 |
| failed_breakdown | +0.026 | 0.286 | -0.259 |
| hod_break | +0.037 | 0.198 | -0.161 |
| orb15 | +0.033 | 0.202 | -0.168 |
| orb5 | +0.009 | 0.195 | -0.186 |
| pm_high_break | +0.048 | 0.198 | -0.150 |
| vwap_pullback | +0.047 | 0.476 | -0.430 |

**By stock price**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under $5 | 4347 | +0.020 | 0.558 | -0.538 |
| $5-10 | 3753 | +0.053 | 0.321 | -0.268 |
| $10-20 | 4516 | +0.046 | 0.231 | -0.185 |
| $20-50 | 5705 | +0.056 | 0.247 | -0.191 |
| $50+ | 2698 | +0.069 | 0.262 | -0.194 |

**By stop width**

| Group | Trades | Gross R | Cost R | Net R |
|---|---|---|---|---|
| under 1% | 3378 | +0.119 | 0.542 | -0.424 |
| 1-2% | 7137 | +0.063 | 0.301 | -0.238 |
| 2-3% | 4748 | +0.024 | 0.272 | -0.247 |
| 3%+ | 5756 | +0.005 | 0.265 | -0.259 |

## Fixes tested: entry and exit variants

Entry: mkt = market order next bar (current), lim = limit at the signal close, good 3 minutes (no chase). Plan: h2 = half at 1R, rest 2R (current); r3 = all at 3R; tr = half at 1R, trail the rest on the 9 EMA.
Net R below uses the typical measured spread; survivors must also stay positive with the bot's slippage and the worse (75th pct) spread.

Measured quoted spreads at entry (median / 75th pct): under $5 0.46% / 0.69%, $5-10 0.23% / 0.53%, $10-20 0.24% / 0.49%, $20-50 0.24% / 0.44%, $50+ 0.21% / 0.39%. A market order pays about half the spread on the way in and half on the way out.

| Strategy | Entry | Plan | Trades | Fill rate | Gross R | Net R | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|
| pm_high_break | lim | h2 | 618 | 93% | +0.018 | -0.025 | -0.58 | -0.052 | +0.001 |
| ema_bounce | lim | r3 | 4817 | 91% | +0.052 | -0.038 | -1.48 | -0.031 | -0.045 |
| hod_break | lim | h2 | 600 | 90% | -0.002 | -0.044 | -1.02 | -0.079 | -0.008 |
| orb15 | lim | h2 | 1220 | 91% | +0.000 | -0.045 | -1.5 | -0.045 | -0.046 |
| orb15 | lim | tr | 1220 | 91% | -0.001 | -0.054 | -1.85 | -0.077 | -0.030 |
| hod_break | lim | tr | 600 | 90% | -0.006 | -0.054 | -1.34 | -0.076 | -0.032 |
| afternoon_hod | lim | h2 | 719 | 90% | +0.005 | -0.055 | -1.43 | -0.097 | -0.012 |
| pm_high_break | lim | tr | 618 | 93% | -0.009 | -0.062 | -1.51 | -0.079 | -0.046 |
| afternoon_hod | lim | tr | 719 | 90% | +0.004 | -0.063 | -1.67 | -0.127 | +0.001 |
| afternoon_hod | lim | r3 | 719 | 90% | +0.011 | -0.067 | -1.33 | -0.124 | -0.010 |
| ema_bounce | lim | h2 | 4817 | 91% | +0.003 | -0.071 | -4.33 | -0.055 | -0.087 |
| orb15 | lim | r3 | 1220 | 91% | -0.019 | -0.076 | -1.79 | -0.077 | -0.076 |
| bull_flag | lim | r3 | 2007 | 90% | -0.001 | -0.077 | -1.99 | -0.138 | -0.017 |
| orb5 | lim | r3 | 2133 | 94% | -0.033 | -0.079 | -2.26 | -0.091 | -0.067 |
| bull_flag | lim | h2 | 2007 | 90% | -0.020 | -0.082 | -3.28 | -0.082 | -0.081 |

**Survivors (net > +0.05R, t > 2, positive in both halves, 200+ trades): 0** (none yet)

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
