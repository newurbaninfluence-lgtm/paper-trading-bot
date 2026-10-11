# Swing strategies backtest (2026-10-11)

497 signal days from 2024-10-11 to 2026-10-08, 100498 simulated trades. Entry next open at market, stops fill at the worse of stop or open (gaps count against us). Measured quoted spread for these stocks: median 0.058%, 75th pct 0.128% (391 samples). Win % and t use typical-spread market orders. The bot-slippage column (2c or 0.15% a side) is a stress test.

## Every signal, by strategy and exit plan

| Strategy | Plan | Trades | Win % | Avg days | Gross R | Market orders, typical spread | Market orders, bad spread | Open/close auction orders | Bot slippage (stress test) | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| earn_gap | t20 | 299 | 39% | 13.3 | -0.011 | -0.022 | -0.034 | -0.018 | -0.065 | -0.49 | +0.075 | -0.118 |
| earn_gap | tr10 | 298 | 31% | 17.2 | -0.072 | -0.083 | -0.095 | -0.078 | -0.126 | -1.24 | -0.055 | -0.111 |
| trend_pb | sma5 | 49779 | 64% | 3.2 | +0.031 | +0.018 | +0.002 | +0.028 | -0.038 | 0.3 | -0.002 | +0.037 |
| trend_pb | t10 | 49096 | 48% | 8.5 | +0.056 | +0.042 | +0.026 | +0.050 | -0.013 | 0.44 | +0.032 | +0.053 |

**Pass the survivor test (net > +0.05R, t > 2, positive in both halves, 200+ trades, positive with market orders at typical and bad spreads and with auction orders): 0**

## Accounts replayed (live rules: 1% risk, cash only, no margin, fractional shares, earnings gaps first)

| Account | Trades | Win % | P&L | $/trading day | Worst trade |
|---|---|---|---|---|---|
| $200 | 404 | 46% | $-19.83 | $-0.04 | $-5.28 |
| $250 | 429 | 46% | $-15.61 | $-0.03 | $-5.02 |
| $350 | 439 | 45% | $-30.42 | $-0.06 | $-10.65 |
| $400 | 439 | 45% | $-34.75 | $-0.07 | $-12.18 |
| $550 | 455 | 46% | $-39.32 | $-0.08 | $-16.99 |
| $1000 | 484 | 47% | $-32.43 | $-0.06 | $-31.82 |

**All 6 accounts together: $-0.34 per trading day.**
