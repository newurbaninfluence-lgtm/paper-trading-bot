# Crypto pattern finder, 1d bars (2026-11-02)

Data: 1d bars, 2022-02-19 to 2026-11-02, 8 markets (AVAXUSD, BTCUSD, DOGEUSD, ETHUSD, LINKUSD, LTCUSD, SOLUSD, XRPUSD).
**Hunt** period: before 2025-01-01. **Exam** period: 2025-01-01 on (never seen while hunting).
Costs: 0.30% per side (Alpaca crypto fee + slippage), long only (Alpaca can't short crypto).
Rules tested: 294. R = profit in units of the risk per trade (1R = the stop distance). Net = after costs.

## Result: 0 of the hunt's top 15 passed the exam

Pass = strong on the hunt (t 2+), still positive after costs on the exam (t 2+), at least 30 exam trades, and making money in at least half the markets.
Luck check: on fake random-walk data this finder still lets roughly 1 rule in 20 through by chance, so a PASS earns paper trading, never real money straight away.

| # | Rule | Filter | Side | Exit | Hunt trades | Hunt net R | Hunt t | Exam trades | Exam gross R | Exam net R | Exam win % | Exam t | Markets up | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | day_tue | any | long | stop2_hold12bars | 562 | +0.260 | +2.5 | 433 | -0.002 | -0.060 | 36% | -1.0 | 0/8 | lost on exam |
| 2 | big_move_4bars_3.0atr_follow | any | long | stop2_hold24bars | 48 | +1.806 | +2.5 | 40 | +0.025 | -0.052 | 38% | -0.2 | 3/8 | lost on exam |
| 3 | big_move_4bars_3.0atr_follow | with_trend | long | stop2_hold24bars | 48 | +1.806 | +2.5 | 40 | +0.025 | -0.052 | 38% | -0.2 | 3/8 | lost on exam |
| 4 | breakout_55bars | any | long | stop2_hold24bars | 66 | +1.230 | +2.3 | 44 | +0.111 | +0.033 | 39% | +0.1 | 4/8 | too weak |
| 5 | breakout_55bars | with_trend | long | stop2_hold24bars | 66 | +1.230 | +2.3 | 44 | +0.111 | +0.033 | 39% | +0.1 | 4/8 | too weak |
| 6 | day_fri | any | long | stop2_hold24bars | 324 | +0.413 | +2.2 | 241 | -0.071 | -0.127 | 31% | -1.4 | 0/8 | lost on exam |
| 7 | big_move_4bars_3.0atr_follow | any | long | stop2_hold12bars | 54 | +0.730 | +2.1 | 42 | +0.322 | +0.243 | 48% | +1.2 | 5/8 | too weak |
| 8 | big_move_4bars_3.0atr_follow | with_trend | long | stop2_hold12bars | 54 | +0.730 | +2.1 | 42 | +0.322 | +0.243 | 48% | +1.2 | 5/8 | too weak |
| 9 | breakout_55bars | with_trend | long | stop2_hold12bars | 79 | +0.493 | +2.1 | 51 | +0.190 | +0.112 | 39% | +0.5 | 6/8 | too weak |
| 10 | breakout_55bars | any | long | stop2_hold12bars | 79 | +0.493 | +2.1 | 51 | +0.190 | +0.112 | 39% | +0.5 | 6/8 | too weak |
| 11 | day_thu | any | long | stop2_hold24bars | 314 | +0.382 | +2.1 | 234 | +0.041 | -0.013 | 41% | -0.1 | 4/8 | lost on exam |
| 12 | day_thu | with_trend | long | stop2_hold24bars | 179 | +0.845 | +2.1 | 120 | +0.181 | +0.111 | 38% | +0.7 | 3/8 | too weak |
| 13 | big_move_12bars_1.5atr_follow | with_trend | long | stop2_hold24bars | 116 | +1.233 | +2.1 | 79 | -0.083 | -0.158 | 32% | -0.9 | 3/8 | lost on exam |
| 14 | day_sun | with_trend | long | stop2_hold24bars | 186 | +0.793 | +2.1 | 124 | -0.059 | -0.125 | 32% | -0.9 | 3/8 | lost on exam |
| 15 | day_tue | with_trend | long | stop2_hold12bars | 300 | +0.369 | +2.1 | 195 | +0.040 | -0.027 | 32% | -0.3 | 4/8 | lost on exam |

## Reality check

- Rules positive on the hunt (after costs): 145 of 204.
- Of those, still positive on the exam: 52.
- Best exam result of ANY rule (pure hindsight, for comparison only): +0.456R (big_move_4bars_3.0atr_follow). Picking from the exam itself is the curve-fitting trap.
- Average rule before costs on the exam: -0.002R; after costs: -0.067R.
- Buy and hold over the exam period: AVAXUSD -77%, BTCUSD -18%, DOGEUSD -77%, ETHUSD -32%, LINKUSD -48%, LTCUSD -48%, SOLUSD -51%, XRPUSD -46%.
