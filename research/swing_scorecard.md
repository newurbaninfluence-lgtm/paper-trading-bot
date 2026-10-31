# Swing strategies backtest (2026-10-31)

497 signal days from 2024-11-01 to 2026-10-29, 98744 simulated trades. Entry next open at market, stops fill at the worse of stop or open (gaps count against us). Measured quoted spread for these stocks: median 0.054%, 75th pct 0.119% (392 samples). Win % and t use typical-spread market orders. The bot-slippage column (2c or 0.15% a side) is a stress test.

## Every signal, by strategy and exit plan

| Strategy | Plan | Trades | Win % | Avg days | Gross R | Market orders, typical spread | Market orders, bad spread | Open/close auction orders | Bot slippage (stress test) | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| earn_gap | t20 | 283 | 39% | 13.1 | -0.063 | -0.073 | -0.084 | -0.069 | -0.116 | -1.05 | +0.008 | -0.153 |
| earn_gap | tr10 | 282 | 29% | 16.8 | -0.116 | -0.126 | -0.137 | -0.122 | -0.169 | -1.74 | -0.099 | -0.152 |
| trend_pb | sma5 | 48979 | 64% | 3.2 | +0.029 | +0.016 | +0.002 | +0.026 | -0.040 | 0.12 | +0.006 | +0.026 |
| trend_pb | t10 | 48798 | 48% | 8.5 | +0.042 | +0.030 | +0.015 | +0.038 | -0.026 | 0.14 | +0.037 | +0.023 |

**Pass the survivor test (net > +0.05R, t > 2, positive in both halves, 200+ trades, positive with market orders at typical and bad spreads and with auction orders): 0**

## Accounts replayed (live rules: 1% risk, cash only, no margin, fractional shares, earnings gaps first)

| Account | Trades | Win % | P&L | $/trading day | Worst trade |
|---|---|---|---|---|---|
| $200 | 405 | 48% | $-19.07 | $-0.04 | $-5.24 |
| $250 | 429 | 47% | $-17.31 | $-0.03 | $-5.78 |
| $350 | 445 | 46% | $-31.74 | $-0.06 | $-10.65 |
| $400 | 448 | 46% | $-35.13 | $-0.07 | $-12.22 |
| $550 | 462 | 47% | $-40.36 | $-0.08 | $-16.94 |
| $1000 | 481 | 47% | $-59.53 | $-0.12 | $-31.00 |

**All 6 accounts together: $-0.41 per trading day.**
