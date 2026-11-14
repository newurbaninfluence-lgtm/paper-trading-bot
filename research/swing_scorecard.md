# Swing strategies backtest (2026-11-14)

497 signal days from 2024-11-15 to 2026-11-12, 98558 simulated trades. Entry next open at market, stops fill at the worse of stop or open (gaps count against us). Measured quoted spread for these stocks: median 0.064%, 75th pct 0.128% (394 samples). Win % and t use typical-spread market orders. The bot-slippage column (2c or 0.15% a side) is a stress test.

## Every signal, by strategy and exit plan

| Strategy | Plan | Trades | Win % | Avg days | Gross R | Market orders, typical spread | Market orders, bad spread | Open/close auction orders | Bot slippage (stress test) | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| earn_gap | t20 | 283 | 35% | 12.6 | -0.140 | -0.151 | -0.163 | -0.147 | -0.193 | -1.91 | -0.058 | -0.245 |
| earn_gap | tr10 | 282 | 28% | 16.1 | -0.151 | -0.163 | -0.174 | -0.158 | -0.205 | -2.05 | -0.082 | -0.243 |
| trend_pb | sma5 | 48923 | 63% | 3.2 | +0.025 | +0.010 | -0.004 | +0.022 | -0.043 | -0.11 | +0.002 | +0.019 |
| trend_pb | t10 | 48576 | 47% | 8.5 | +0.030 | +0.015 | +0.001 | +0.025 | -0.038 | 0.08 | +0.026 | +0.004 |

**Pass the survivor test (net > +0.05R, t > 2, positive in both halves, 200+ trades, positive with market orders at typical and bad spreads and with auction orders): 0**

## Accounts replayed (live rules: 1% risk, cash only, no margin, fractional shares, earnings gaps first)

| Account | Trades | Win % | P&L | $/trading day | Worst trade |
|---|---|---|---|---|---|
| $200 | 410 | 48% | $-17.17 | $-0.03 | $-6.01 |
| $250 | 425 | 48% | $-6.48 | $-0.01 | $-7.97 |
| $350 | 438 | 47% | $-1.38 | $-0.00 | $-11.05 |
| $400 | 438 | 47% | $-1.54 | $-0.00 | $-12.63 |
| $550 | 448 | 48% | $42.15 | $+0.08 | $-19.43 |
| $1000 | 461 | 47% | $58.80 | $+0.12 | $-34.79 |

**All 6 accounts together: $+0.15 per trading day.**
At the same edge, $20/day needs about 134.4x the money (about $369,723 total).
