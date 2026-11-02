# Crypto pattern finder, 4h bars (2026-11-02)

Data: 4h bars, 2022-02-19 to 2026-11-02, 8 markets (AVAXUSD, BTCUSD, DOGEUSD, ETHUSD, LINKUSD, LTCUSD, SOLUSD, XRPUSD).
**Hunt** period: before 2025-01-01. **Exam** period: 2025-01-01 on (never seen while hunting).
Costs: 0.30% per side (Alpaca crypto fee + slippage), long only (Alpaca can't short crypto).
Rules tested: 306. R = profit in units of the risk per trade (1R = the stop distance). Net = after costs.

## Result: 0 of the hunt's top 15 passed the exam

Pass = strong on the hunt (t 2+), still positive after costs on the exam (t 2+), at least 30 exam trades, and making money in at least half the markets.
Luck check: on fake random-walk data this finder still lets roughly 1 rule in 20 through by chance, so a PASS earns paper trading, never real money straight away.

| # | Rule | Filter | Side | Exit | Hunt trades | Hunt net R | Hunt t | Exam trades | Exam gross R | Exam net R | Exam win % | Exam t | Markets up | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | breakout_12bars | with_trend | long | stop3_trail_exit_below_ema50 | 477 | +0.355 | +1.9 | 360 | +0.171 | +0.036 | 24% | +0.3 | 5/8 | weak on hunt |
| 2 | big_move_4bars_3.0atr_follow | with_trend | long | stop3_trail_exit_below_ema50 | 184 | +0.997 | +1.8 | 144 | +0.325 | +0.201 | 33% | +1.1 | 5/8 | weak on hunt |
| 3 | big_move_4bars_3.0atr_follow | any | long | stop3_trail_exit_below_ema50 | 249 | +0.767 | +1.8 | 208 | +0.158 | +0.036 | 27% | +0.3 | 4/8 | weak on hunt |
| 4 | big_move_4bars_1.5atr_follow | with_trend | long | stop3_trail_exit_below_ema50 | 551 | +0.334 | +1.8 | 426 | +0.136 | +0.007 | 24% | +0.1 | 5/8 | weak on hunt |
| 5 | breakout_96bars | with_trend | long | stop3_trail_exit_below_ema50 | 213 | +0.675 | +1.7 | 137 | +0.200 | +0.082 | 33% | +0.5 | 6/8 | weak on hunt |
| 6 | breakout_24bars | with_trend | long | stop3_trail_exit_below_ema50 | 366 | +0.403 | +1.7 | 260 | +0.224 | +0.096 | 28% | +0.7 | 6/8 | weak on hunt |
| 7 | big_move_12bars_1.5atr_follow | with_trend | long | stop3_trail_exit_below_ema50 | 396 | +0.375 | +1.7 | 276 | +0.186 | +0.054 | 27% | +0.5 | 6/8 | weak on hunt |
| 8 | breakout_96bars | any | long | stop3_trail_exit_below_ema50 | 227 | +0.660 | +1.7 | 147 | +0.181 | +0.062 | 32% | +0.4 | 6/8 | weak on hunt |
| 9 | big_move_24bars_1.5atr_follow | with_trend | long | stop3_trail_exit_below_ema50 | 317 | +0.415 | +1.6 | 198 | +0.197 | +0.068 | 30% | +0.5 | 7/8 | weak on hunt |
| 10 | breakout_48bars | with_trend | long | stop3_trail_exit_below_ema50 | 269 | +0.496 | +1.6 | 190 | +0.183 | +0.063 | 31% | +0.5 | 4/8 | weak on hunt |
| 11 | big_move_12bars_1.5atr_follow | any | long | stop3_trail_exit_below_ema50 | 635 | +0.261 | +1.5 | 501 | +0.034 | -0.088 | 22% | -1.3 | 2/8 | lost on exam |
| 12 | big_move_24bars_1.5atr_follow | any | long | stop3_trail_exit_below_ema50 | 465 | +0.259 | +1.5 | 317 | +0.043 | -0.081 | 23% | -0.9 | 2/8 | lost on exam |
| 13 | breakout_24bars | any | long | stop3_trail_exit_below_ema50 | 548 | +0.298 | +1.4 | 437 | +0.031 | -0.091 | 22% | -1.1 | 2/8 | lost on exam |
| 14 | breakout_48bars | any | long | stop3_trail_exit_below_ema50 | 345 | +0.448 | +1.4 | 243 | +0.099 | -0.020 | 28% | -0.2 | 4/8 | lost on exam |
| 15 | breakout_96bars | with_trend | long | stop2_hold24bars | 299 | +0.579 | +1.4 | 175 | +0.384 | +0.208 | 34% | +1.2 | 6/8 | weak on hunt |

## Reality check

- Rules positive on the hunt (after costs): 61 of 261.
- Of those, still positive on the exam: 26.
- Best exam result of ANY rule (pure hindsight, for comparison only): +0.993R (big_move_12bars_3.0atr_follow). Picking from the exam itself is the curve-fitting trap.
- Average rule before costs on the exam: +0.044R; after costs: -0.128R.
- Buy and hold over the exam period: AVAXUSD -76%, BTCUSD -17%, DOGEUSD -76%, ETHUSD -32%, LINKUSD -44%, LTCUSD -47%, SOLUSD -51%, XRPUSD -41%.
