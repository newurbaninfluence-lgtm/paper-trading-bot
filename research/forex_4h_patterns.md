# Forex pattern finder, 4h bars (2026-11-14)

Data: 4h bars, 2023-03-09 to 2026-11-06, 5 markets (AUDUSD, EURUSD, GBPUSD, USDCAD, USDJPY).
**Hunt** period: before 2025-11-01. **Exam** period: 2025-11-01 on (never seen while hunting).
Costs: typical retail spread + slippage per pair (EURUSD 1.2 pips), long and short.
Rules tested: 588. R = profit in units of the risk per trade (1R = the stop distance). Net = after costs.

## Result: 0 of the hunt's top 15 passed the exam

Pass = strong on the hunt (t 2+), still positive after costs on the exam (t 2+), at least 30 exam trades, and making money in at least half the markets.
Luck check: on fake random-walk data this finder still lets roughly 1 rule in 20 through by chance, so a PASS earns paper trading, never real money straight away.

| # | Rule | Filter | Side | Exit | Hunt trades | Hunt net R | Hunt t | Exam trades | Exam gross R | Exam net R | Exam win % | Exam t | Markets up | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | big_move_4bars_3.0atr_fade | any | long | stop2_hold12bars | 192 | +0.114 | +1.5 | 66 | -0.086 | -0.116 | 39% | -0.8 | 1/5 | lost on exam |
| 2 | big_move_12bars_1.5atr_fade | any | long | stop2_hold24bars | 561 | +0.088 | +1.5 | 193 | -0.124 | -0.155 | 34% | -1.8 | 2/5 | lost on exam |
| 3 | big_move_4bars_3.0atr_fade | any | long | stop2_hold24bars | 189 | +0.143 | +1.4 | 66 | -0.107 | -0.138 | 36% | -0.9 | 1/5 | lost on exam |
| 4 | big_move_4bars_1.5atr_fade | with_trend | short | stop2_hold4bars | 390 | +0.047 | +1.4 | 165 | +0.015 | -0.017 | 47% | -0.3 | 3/5 | lost on exam |
| 5 | band_fade_2.0sd | with_trend | short | stop2_hold4bars | 167 | +0.087 | +1.4 | 82 | +0.026 | -0.005 | 52% | -0.1 | 2/5 | lost on exam |
| 6 | big_move_12bars_1.5atr_fade | any | long | stop2_hold4bars | 872 | +0.032 | +1.4 | 298 | -0.018 | -0.049 | 48% | -1.3 | 2/5 | lost on exam |
| 7 | big_move_12bars_1.5atr_fade | any | long | stop2_hold12bars | 591 | +0.059 | +1.3 | 204 | -0.012 | -0.043 | 41% | -0.6 | 2/5 | lost on exam |
| 8 | big_move_4bars_3.0atr_fade | any | short | stop2_hold24bars | 195 | +0.136 | +1.2 | 52 | -0.121 | -0.151 | 33% | -0.9 | 2/5 | lost on exam |
| 9 | big_move_4bars_1.5atr_follow | any | long | stop2_tgt2 | 914 | +0.038 | +1.2 | 317 | -0.028 | -0.060 | 49% | -1.1 | 1/5 | lost on exam |
| 10 | big_move_4bars_1.5atr_follow | with_trend | long | stop2_tgt2 | 626 | +0.045 | +1.1 | 203 | -0.034 | -0.066 | 49% | -0.9 | 1/5 | lost on exam |
| 11 | band_fade_2.0sd | with_trend | short | stop3_trail_exit_below_ema50 | 178 | +0.056 | +1.1 | 87 | -0.036 | -0.057 | 51% | -1.4 | 2/5 | lost on exam |
| 12 | band_fade_2.0sd | with_trend | short | stop2_hold12bars | 147 | +0.101 | +1.0 | 72 | -0.067 | -0.097 | 39% | -0.8 | 2/5 | lost on exam |
| 13 | big_move_4bars_1.5atr_fade | with_trend | short | stop3_trail_exit_below_ema50 | 361 | +0.034 | +1.0 | 163 | -0.031 | -0.053 | 44% | -1.4 | 1/5 | lost on exam |
| 14 | big_move_24bars_1.5atr_fade | any | long | stop2_hold24bars | 391 | +0.072 | +1.0 | 146 | -0.178 | -0.209 | 34% | -2.2 | 1/5 | lost on exam |
| 15 | big_move_4bars_3.0atr_fade | any | short | stop2_hold12bars | 200 | +0.087 | +1.0 | 53 | -0.081 | -0.111 | 45% | -1.0 | 1/5 | lost on exam |

## Reality check

- Rules positive on the hunt (after costs): 113 of 474.
- Of those, still positive on the exam: 31.
- Best exam result of ANY rule (pure hindsight, for comparison only): +0.459R (big_move_4bars_3.0atr_follow). Picking from the exam itself is the curve-fitting trap.
- Average rule before costs on the exam: +0.008R; after costs: -0.024R.
- Buy and hold over the exam period: AUDUSD +5%, EURUSD -3%, GBPUSD +2%, USDCAD +1%, USDJPY +3%.
