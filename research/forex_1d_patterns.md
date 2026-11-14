# Forex pattern finder, 1d bars (2026-11-14)

Data: 1d bars, 2023-02-27 to 2026-11-06, 5 markets (AUDUSD, EURUSD, GBPUSD, USDCAD, USDJPY).
**Hunt** period: before 2025-11-01. **Exam** period: 2025-11-01 on (never seen while hunting).
Costs: typical retail spread + slippage per pair (EURUSD 1.2 pips), long and short.
Rules tested: 564. R = profit in units of the risk per trade (1R = the stop distance). Net = after costs.

## Result: 2 of the hunt's top 15 passed the exam

Pass = strong on the hunt (t 2+), still positive after costs on the exam (t 2+), at least 30 exam trades, and making money in at least half the markets.
Luck check: on fake random-walk data this finder still lets roughly 1 rule in 20 through by chance, so a PASS earns paper trading, never real money straight away.

| # | Rule | Filter | Side | Exit | Hunt trades | Hunt net R | Hunt t | Exam trades | Exam gross R | Exam net R | Exam win % | Exam t | Markets up | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | band_fade_2.5sd | any | short | stop2_hold4bars | 50 | +0.242 | +2.5 | 13 | -0.139 | -0.152 | 46% | -0.8 | 1/5 | lost on exam |
| 2 | day_fri | any | long | stop2_hold4bars | 695 | +0.048 | +2.1 | 265 | +0.115 | +0.101 | 59% | +2.7 | 5/5 | **PASS** |
| 3 | day_fri | with_trend | long | stop2_hold4bars | 385 | +0.062 | +2.0 | 143 | +0.161 | +0.147 | 62% | +3.0 | 5/5 | **PASS** |
| 4 | big_move_4bars_1.5atr_fade | any | long | stop2_tgt2 | 185 | +0.142 | +2.0 | 69 | -0.045 | -0.059 | 48% | -0.5 | 1/5 | lost on exam |
| 5 | band_fade_2.5sd | any | short | stop3_trail_exit_below_ema50 | 51 | +0.103 | +1.9 | 15 | -0.005 | -0.013 | 47% | -0.2 | 2/5 | lost on exam |
| 6 | big_move_4bars_1.5atr_fade | any | long | stop2_hold24bars | 145 | +0.215 | +1.8 | 60 | +0.072 | +0.058 | 45% | +0.4 | 4/5 | weak on hunt |
| 7 | ema50_cross | any | long | stop1.5_tgt3 | 97 | +0.274 | +1.8 | 37 | +0.255 | +0.238 | 43% | +1.0 | 4/5 | weak on hunt |
| 8 | ema50_cross | with_trend | long | stop2_hold12bars | 77 | +0.225 | +1.7 | 23 | +0.080 | +0.067 | 52% | +0.4 | 3/5 | weak on hunt |
| 9 | big_move_4bars_1.5atr_fade | any | long | stop3_trail_exit_below_ema50 | 225 | +0.062 | +1.7 | 94 | -0.097 | -0.107 | 44% | -3.0 | 0/5 | lost on exam |
| 10 | band_fade_2.0sd | any | long | stop1.5_tgt3 | 81 | +0.281 | +1.7 | 40 | -0.007 | -0.024 | 35% | -0.1 | 3/5 | lost on exam |
| 11 | ema50_cross | any | long | stop2_hold12bars | 106 | +0.185 | +1.7 | 37 | +0.085 | +0.072 | 51% | +0.4 | 3/5 | weak on hunt |
| 12 | ema50_cross | with_trend | long | stop2_hold24bars | 69 | +0.264 | +1.6 | 22 | +0.161 | +0.149 | 50% | +0.6 | 3/5 | weak on hunt |
| 13 | big_move_4bars_1.5atr_fade | any | long | stop2_hold12bars | 181 | +0.126 | +1.6 | 71 | -0.001 | -0.014 | 51% | -0.1 | 2/5 | lost on exam |
| 14 | ema50_cross | any | long | stop2_hold24bars | 93 | +0.206 | +1.5 | 35 | +0.206 | +0.193 | 49% | +0.9 | 3/5 | weak on hunt |
| 15 | ema50_cross | with_trend | long | stop1.5_tgt3 | 71 | +0.260 | +1.5 | 24 | +0.241 | +0.225 | 42% | +0.8 | 4/5 | weak on hunt |

## Reality check

- Rules positive on the hunt (after costs): 116 of 341.
- Of those, still positive on the exam: 50.
- Best exam result of ANY rule (pure hindsight, for comparison only): +0.470R (big_move_12bars_1.5atr_follow). Picking from the exam itself is the curve-fitting trap.
- Average rule before costs on the exam: +0.042R; after costs: +0.028R.
- Buy and hold over the exam period: AUDUSD +5%, EURUSD -3%, GBPUSD +2%, USDCAD +1%, USDJPY +3%.
