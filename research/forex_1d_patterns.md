# Forex pattern finder, 1d bars (2026-11-03)

Data: 1d bars, 2023-02-27 to 2026-10-30, 5 markets (AUDUSD, EURUSD, GBPUSD, USDCAD, USDJPY).
**Hunt** period: before 2025-11-01. **Exam** period: 2025-11-01 on (never seen while hunting).
Costs: typical retail spread + slippage per pair (EURUSD 1.2 pips), long and short.
Rules tested: 564. R = profit in units of the risk per trade (1R = the stop distance). Net = after costs.

## Result: 2 of the hunt's top 15 passed the exam

Pass = strong on the hunt (t 2+), still positive after costs on the exam (t 2+), at least 30 exam trades, and making money in at least half the markets.
Luck check: on fake random-walk data this finder still lets roughly 1 rule in 20 through by chance, so a PASS earns paper trading, never real money straight away.

| # | Rule | Filter | Side | Exit | Hunt trades | Hunt net R | Hunt t | Exam trades | Exam gross R | Exam net R | Exam win % | Exam t | Markets up | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | band_fade_2.5sd | any | short | stop2_hold4bars | 50 | +0.242 | +2.5 | 13 | -0.139 | -0.152 | 46% | -0.8 | 1/5 | lost on exam |
| 2 | day_fri | any | long | stop2_hold4bars | 695 | +0.048 | +2.1 | 260 | +0.108 | +0.094 | 58% | +2.5 | 5/5 | **PASS** |
| 3 | day_fri | with_trend | long | stop2_hold4bars | 385 | +0.062 | +2.0 | 142 | +0.154 | +0.140 | 62% | +2.8 | 5/5 | **PASS** |
| 4 | big_move_4bars_1.5atr_fade | any | long | stop2_tgt2 | 185 | +0.142 | +2.0 | 67 | -0.057 | -0.070 | 48% | -0.6 | 2/5 | lost on exam |
| 5 | band_fade_2.5sd | any | short | stop3_trail_exit_below_ema50 | 51 | +0.103 | +1.9 | 15 | -0.005 | -0.013 | 47% | -0.2 | 2/5 | lost on exam |
| 6 | big_move_4bars_1.5atr_fade | any | long | stop2_hold24bars | 145 | +0.215 | +1.8 | 58 | +0.059 | +0.045 | 45% | +0.3 | 4/5 | weak on hunt |
| 7 | ema50_cross | any | long | stop1.5_tgt3 | 97 | +0.274 | +1.8 | 37 | +0.270 | +0.253 | 43% | +1.1 | 4/5 | weak on hunt |
| 8 | ema50_cross | with_trend | long | stop2_hold12bars | 77 | +0.225 | +1.7 | 24 | +0.022 | +0.009 | 50% | +0.0 | 3/5 | weak on hunt |
| 9 | big_move_4bars_1.5atr_fade | any | long | stop3_trail_exit_below_ema50 | 225 | +0.062 | +1.7 | 91 | -0.103 | -0.112 | 42% | -3.1 | 0/5 | lost on exam |
| 10 | band_fade_2.0sd | any | long | stop1.5_tgt3 | 81 | +0.281 | +1.7 | 39 | +0.003 | -0.014 | 36% | -0.1 | 2/5 | lost on exam |
| 11 | ema50_cross | any | long | stop2_hold12bars | 106 | +0.185 | +1.7 | 38 | +0.058 | +0.045 | 47% | +0.3 | 3/5 | weak on hunt |
| 12 | ema50_cross | with_trend | long | stop2_hold24bars | 69 | +0.264 | +1.6 | 22 | +0.147 | +0.135 | 50% | +0.5 | 3/5 | weak on hunt |
| 13 | big_move_4bars_1.5atr_fade | any | long | stop2_hold12bars | 181 | +0.126 | +1.6 | 69 | -0.005 | -0.019 | 51% | -0.2 | 2/5 | lost on exam |
| 14 | ema50_cross | any | long | stop2_hold24bars | 93 | +0.206 | +1.5 | 35 | +0.225 | +0.212 | 49% | +1.0 | 4/5 | weak on hunt |
| 15 | ema50_cross | with_trend | long | stop1.5_tgt3 | 71 | +0.260 | +1.5 | 24 | +0.224 | +0.208 | 42% | +0.7 | 4/5 | weak on hunt |

## Reality check

- Rules positive on the hunt (after costs): 116 of 341.
- Of those, still positive on the exam: 48.
- Best exam result of ANY rule (pure hindsight, for comparison only): +0.406R (big_move_4bars_1.5atr_follow). Picking from the exam itself is the curve-fitting trap.
- Average rule before costs on the exam: +0.042R; after costs: +0.028R.
- Buy and hold over the exam period: AUDUSD +7%, EURUSD -3%, GBPUSD +2%, USDCAD -0%, USDJPY +2%.
