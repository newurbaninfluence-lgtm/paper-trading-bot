# Forex pattern finder, 4h bars (2026-11-03)

Data: 4h bars, 2023-03-09 to 2026-10-30, 5 markets (AUDUSD, EURUSD, GBPUSD, USDCAD, USDJPY).
**Hunt** period: before 2025-11-01. **Exam** period: 2025-11-01 on (never seen while hunting).
Costs: typical retail spread + slippage per pair (EURUSD 1.2 pips), long and short.
Rules tested: 588. R = profit in units of the risk per trade (1R = the stop distance). Net = after costs.

## Result: 0 of the hunt's top 15 passed the exam

Pass = strong on the hunt (t 2+), still positive after costs on the exam (t 2+), at least 30 exam trades, and making money in at least half the markets.
Luck check: on fake random-walk data this finder still lets roughly 1 rule in 20 through by chance, so a PASS earns paper trading, never real money straight away.

| # | Rule | Filter | Side | Exit | Hunt trades | Hunt net R | Hunt t | Exam trades | Exam gross R | Exam net R | Exam win % | Exam t | Markets up | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | big_move_4bars_3.0atr_fade | any | long | stop2_hold12bars | 192 | +0.114 | +1.5 | 65 | -0.072 | -0.103 | 38% | -0.7 | 1/5 | lost on exam |
| 2 | big_move_12bars_1.5atr_fade | any | long | stop2_hold24bars | 561 | +0.088 | +1.5 | 189 | -0.128 | -0.159 | 34% | -1.9 | 2/5 | lost on exam |
| 3 | big_move_4bars_3.0atr_fade | any | long | stop2_hold24bars | 189 | +0.143 | +1.4 | 65 | -0.109 | -0.140 | 35% | -0.9 | 1/5 | lost on exam |
| 4 | big_move_4bars_1.5atr_fade | with_trend | short | stop2_hold4bars | 390 | +0.047 | +1.4 | 162 | +0.012 | -0.020 | 47% | -0.4 | 3/5 | lost on exam |
| 5 | band_fade_2.0sd | with_trend | short | stop2_hold4bars | 167 | +0.087 | +1.4 | 80 | +0.022 | -0.009 | 51% | -0.1 | 2/5 | lost on exam |
| 6 | big_move_12bars_1.5atr_fade | any | long | stop2_hold4bars | 872 | +0.032 | +1.4 | 294 | -0.012 | -0.043 | 48% | -1.1 | 2/5 | lost on exam |
| 7 | big_move_12bars_1.5atr_fade | any | long | stop2_hold12bars | 591 | +0.059 | +1.3 | 200 | -0.022 | -0.053 | 40% | -0.7 | 2/5 | lost on exam |
| 8 | big_move_4bars_3.0atr_fade | any | short | stop2_hold24bars | 195 | +0.136 | +1.2 | 51 | -0.115 | -0.145 | 33% | -0.9 | 2/5 | lost on exam |
| 9 | big_move_4bars_1.5atr_follow | any | long | stop2_tgt2 | 914 | +0.038 | +1.2 | 308 | -0.031 | -0.062 | 49% | -1.1 | 1/5 | lost on exam |
| 10 | big_move_4bars_1.5atr_follow | with_trend | long | stop2_tgt2 | 626 | +0.045 | +1.1 | 196 | -0.037 | -0.069 | 48% | -1.0 | 1/5 | lost on exam |
| 11 | band_fade_2.0sd | with_trend | short | stop3_trail_exit_below_ema50 | 178 | +0.056 | +1.1 | 85 | -0.030 | -0.051 | 51% | -1.2 | 2/5 | lost on exam |
| 12 | band_fade_2.0sd | with_trend | short | stop2_hold12bars | 147 | +0.101 | +1.0 | 70 | -0.054 | -0.084 | 40% | -0.7 | 2/5 | lost on exam |
| 13 | big_move_4bars_1.5atr_fade | with_trend | short | stop3_trail_exit_below_ema50 | 361 | +0.034 | +1.0 | 158 | -0.028 | -0.049 | 44% | -1.2 | 1/5 | lost on exam |
| 14 | big_move_24bars_1.5atr_fade | any | long | stop2_hold24bars | 391 | +0.072 | +1.0 | 144 | -0.172 | -0.204 | 35% | -2.2 | 2/5 | lost on exam |
| 15 | big_move_4bars_3.0atr_fade | any | short | stop2_hold12bars | 200 | +0.087 | +1.0 | 52 | -0.074 | -0.105 | 46% | -0.9 | 1/5 | lost on exam |

## Reality check

- Rules positive on the hunt (after costs): 113 of 474.
- Of those, still positive on the exam: 26.
- Best exam result of ANY rule (pure hindsight, for comparison only): +0.457R (big_move_4bars_3.0atr_follow). Picking from the exam itself is the curve-fitting trap.
- Average rule before costs on the exam: +0.004R; after costs: -0.028R.
- Buy and hold over the exam period: AUDUSD +7%, EURUSD -3%, GBPUSD +2%, USDCAD -0%, USDJPY +2%.
