# Crypto pattern finder, 1h bars (2026-11-02)

Data: 1h bars, 2022-02-19 to 2026-11-02, 8 markets (AVAXUSD, BTCUSD, DOGEUSD, ETHUSD, LINKUSD, LTCUSD, SOLUSD, XRPUSD).
**Hunt** period: before 2025-01-01. **Exam** period: 2025-01-01 on (never seen while hunting).
Costs: 0.30% per side (Alpaca crypto fee + slippage), long only (Alpaca can't short crypto).
Rules tested: 378. R = profit in units of the risk per trade (1R = the stop distance). Net = after costs.

## Result: 0 of the hunt's top 15 passed the exam

Pass = strong on the hunt (t 2+), still positive after costs on the exam (t 2+), at least 30 exam trades, and making money in at least half the markets.
Luck check: on fake random-walk data this finder still lets roughly 1 rule in 20 through by chance, so a PASS earns paper trading, never real money straight away.

| # | Rule | Filter | Side | Exit | Hunt trades | Hunt net R | Hunt t | Exam trades | Exam gross R | Exam net R | Exam win % | Exam t | Markets up | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | big_move_12bars_3.0atr_follow | with_trend | long | stop3_trail_exit_below_ema50 | 376 | +0.026 | +0.2 | 230 | +0.436 | +0.177 | 29% | +0.9 | 4/8 | weak on hunt |
| 2 | big_move_12bars_3.0atr_follow | any | long | stop3_trail_exit_below_ema50 | 549 | -0.054 | -0.5 | 378 | +0.259 | +0.008 | 25% | +0.1 | 3/8 | weak on hunt |
| 3 | big_move_4bars_3.0atr_follow | with_trend | long | stop3_trail_exit_below_ema50 | 664 | -0.053 | -0.5 | 466 | +0.154 | -0.116 | 24% | -1.1 | 2/8 | lost on exam |
| 4 | big_move_4bars_3.0atr_fade | with_trend | long | stop3_trail_exit_below_ema50 | 559 | -0.092 | -0.9 | 399 | -0.050 | -0.306 | 25% | -11.5 | 0/8 | lost on exam |
| 5 | day_fri | with_trend | long | stop2_hold24bars | 482 | -0.070 | -0.9 | 331 | +0.118 | -0.215 | 33% | -2.4 | 1/8 | lost on exam |
| 6 | breakout_96bars | with_trend | long | stop3_trail_exit_below_ema50 | 658 | -0.133 | -1.3 | 412 | +0.323 | +0.070 | 30% | +0.5 | 5/8 | weak on hunt |
| 7 | big_move_12bars_3.0atr_follow | with_trend | long | stop2_hold24bars | 426 | -0.144 | -1.6 | 266 | +0.227 | -0.154 | 32% | -1.1 | 2/8 | lost on exam |
| 8 | big_move_24bars_1.5atr_fade | any | long | stop2_hold24bars | 3109 | -0.184 | -1.8 | 2352 | -0.004 | -0.321 | 34% | -11.5 | 0/8 | lost on exam |
| 9 | big_move_24bars_3.0atr_fade | any | long | stop2_hold24bars | 217 | -0.193 | -1.8 | 206 | -0.036 | -0.331 | 30% | -3.1 | 1/8 | lost on exam |
| 10 | breakout_48bars | with_trend | long | stop3_trail_exit_below_ema50 | 872 | -0.149 | -1.9 | 586 | +0.170 | -0.103 | 26% | -1.0 | 3/8 | lost on exam |
| 11 | big_move_4bars_3.0atr_follow | any | long | stop3_trail_exit_below_ema50 | 1133 | -0.125 | -1.9 | 850 | +0.088 | -0.167 | 22% | -2.1 | 1/8 | lost on exam |
| 12 | big_move_24bars_3.0atr_follow | with_trend | long | stop3_trail_exit_below_ema50 | 235 | -0.248 | -2.1 | 136 | +0.607 | +0.365 | 33% | +1.7 | 7/8 | weak on hunt |
| 13 | breakout_96bars | any | long | stop3_trail_exit_below_ema50 | 922 | -0.174 | -2.2 | 624 | +0.198 | -0.049 | 25% | -0.5 | 3/8 | lost on exam |
| 14 | big_move_24bars_1.5atr_follow | with_trend | long | stop3_trail_exit_below_ema50 | 1006 | -0.159 | -2.5 | 650 | +0.192 | -0.085 | 26% | -1.0 | 3/8 | lost on exam |
| 15 | big_move_4bars_3.0atr_follow | any | long | stop2_hold12bars | 1374 | -0.205 | -2.5 | 1015 | +0.002 | -0.373 | 32% | -8.6 | 0/8 | lost on exam |

## Reality check

- Rules positive on the hunt (after costs): 1 of 372.
- Of those, still positive on the exam: 1.
- Best exam result of ANY rule (pure hindsight, for comparison only): +0.365R (big_move_24bars_3.0atr_follow). Picking from the exam itself is the curve-fitting trap.
- Average rule before costs on the exam: +0.005R; after costs: -0.353R.
- Buy and hold over the exam period: AVAXUSD -77%, BTCUSD -18%, DOGEUSD -77%, ETHUSD -33%, LINKUSD -45%, LTCUSD -48%, SOLUSD -52%, XRPUSD -41%.
