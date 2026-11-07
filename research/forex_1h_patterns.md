# Forex pattern finder, 1h bars (2026-11-07)

Data: 1h bars, 2023-03-20 to 2026-10-30, 5 markets (AUDUSD, EURUSD, GBPUSD, USDCAD, USDJPY).
**Hunt** period: before 2025-11-01. **Exam** period: 2025-11-01 on (never seen while hunting).
Costs: typical retail spread + slippage per pair (EURUSD 1.2 pips), long and short.
Rules tested: 756. R = profit in units of the risk per trade (1R = the stop distance). Net = after costs.

## Result: 0 of the hunt's top 15 passed the exam

Pass = strong on the hunt (t 2+), still positive after costs on the exam (t 2+), at least 30 exam trades, and making money in at least half the markets.
Luck check: on fake random-walk data this finder still lets roughly 1 rule in 20 through by chance, so a PASS earns paper trading, never real money straight away.

| # | Rule | Filter | Side | Exit | Hunt trades | Hunt net R | Hunt t | Exam trades | Exam gross R | Exam net R | Exam win % | Exam t | Markets up | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | hour_22utc | with_trend | long | stop2_hold12bars | 1810 | +0.051 | +2.2 | 699 | +0.118 | +0.050 | 50% | +1.3 | 3/5 | too weak |
| 2 | day_mon | any | long | stop2_hold24bars | 611 | +0.089 | +1.7 | 255 | +0.137 | +0.075 | 47% | +1.0 | 4/5 | weak on hunt |
| 3 | day_mon | any | long | stop2_hold12bars | 611 | +0.067 | +1.6 | 255 | +0.140 | +0.078 | 53% | +1.3 | 4/5 | weak on hunt |
| 4 | big_move_4bars_3.0atr_fade | with_trend | short | stop2_hold24bars | 265 | +0.160 | +1.6 | 98 | +0.040 | -0.024 | 44% | -0.2 | 2/5 | lost on exam |
| 5 | big_move_4bars_3.0atr_fade | with_trend | short | stop2_hold12bars | 272 | +0.113 | +1.5 | 100 | +0.209 | +0.145 | 55% | +1.1 | 4/5 | weak on hunt |
| 6 | big_move_12bars_3.0atr_follow | with_trend | long | stop2_hold12bars | 271 | +0.109 | +1.5 | 77 | -0.054 | -0.119 | 45% | -1.1 | 1/5 | lost on exam |
| 7 | hour_22utc | with_trend | long | stop2_hold4bars | 1812 | +0.019 | +1.4 | 703 | +0.084 | +0.016 | 53% | +0.7 | 4/5 | weak on hunt |
| 8 | day_mon | with_trend | long | stop2_hold24bars | 360 | +0.092 | +1.3 | 141 | +0.204 | +0.141 | 50% | +1.3 | 5/5 | weak on hunt |
| 9 | big_move_4bars_3.0atr_fade | with_trend | short | stop2_hold4bars | 273 | +0.056 | +1.3 | 101 | +0.103 | +0.040 | 58% | +0.5 | 2/5 | weak on hunt |
| 10 | day_mon | with_trend | long | stop2_hold12bars | 360 | +0.062 | +1.2 | 141 | +0.138 | +0.074 | 53% | +0.9 | 4/5 | weak on hunt |
| 11 | big_move_24bars_3.0atr_fade | any | short | stop2_hold24bars | 272 | +0.106 | +1.2 | 66 | +0.001 | -0.060 | 42% | -0.4 | 1/5 | lost on exam |
| 12 | london_breakout | with_trend | long | stop2_hold24bars | 816 | +0.063 | +1.2 | 276 | +0.129 | +0.061 | 41% | +0.7 | 4/5 | weak on hunt |
| 13 | day_wed | with_trend | long | stop2_hold24bars | 365 | +0.085 | +1.0 | 144 | +0.130 | +0.060 | 38% | +0.5 | 4/5 | weak on hunt |
| 14 | hour_22utc | any | long | stop2_hold12bars | 3132 | +0.018 | +1.0 | 1284 | +0.104 | +0.037 | 49% | +1.3 | 4/5 | weak on hunt |
| 15 | big_move_24bars_3.0atr_fade | with_trend | long | stop3_trail_exit_below_ema50 | 119 | +0.035 | +1.0 | 22 | +0.097 | +0.050 | 64% | +0.5 | 4/5 | weak on hunt |

## Reality check

- Rules positive on the hunt (after costs): 74 of 741.
- Of those, still positive on the exam: 31.
- Best exam result of ANY rule (pure hindsight, for comparison only): +0.386R (big_move_12bars_3.0atr_fade). Picking from the exam itself is the curve-fitting trap.
- Average rule before costs on the exam: +0.008R; after costs: -0.058R.
- Buy and hold over the exam period: AUDUSD +8%, EURUSD -3%, GBPUSD +2%, USDCAD -0%, USDJPY +2%.
