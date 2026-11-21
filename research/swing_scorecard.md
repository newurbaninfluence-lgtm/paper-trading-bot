# Swing strategies backtest (2026-11-21)

497 signal days from 2024-11-22 to 2026-11-19, 98622 simulated trades. Entry next open at market, stops fill at the worse of stop or open (gaps count against us). Measured quoted spread for these stocks: median 0.063%, 75th pct 0.134% (390 samples). Win % and t use typical-spread market orders. The bot-slippage column (2c or 0.15% a side) is a stress test.

## Every signal, by strategy and exit plan

| Strategy | Plan | Trades | Win % | Avg days | Gross R | Market orders, typical spread | Market orders, bad spread | Open/close auction orders | Bot slippage (stress test) | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| earn_gap | t20 | 150 | 27% | 11.6 | -0.286 | -0.296 | -0.308 | -0.293 | -0.336 | -4.59 | -0.025 | -0.567 |
| earn_gap | tr10 | 155 | 24% | 14.1 | -0.302 | -0.312 | -0.324 | -0.309 | -0.351 | -3.95 | -0.138 | -0.483 |
| trend_pb | sma5 | 48462 | 63% | 3.2 | +0.015 | +0.001 | -0.016 | +0.012 | -0.053 | -0.98 | -0.006 | +0.007 |
| trend_pb | t10 | 48326 | 46% | 8.4 | +0.012 | -0.003 | -0.019 | +0.006 | -0.056 | -0.7 | +0.016 | -0.021 |

**Pass the survivor test (net > +0.05R, t > 2, positive in both halves, 200+ trades, positive with market orders at typical and bad spreads and with auction orders): 0**

## Accounts replayed (live rules: 1% risk, cash only, no margin, fractional shares, earnings gaps first)

| Account | Trades | Win % | P&L | $/trading day | Worst trade |
|---|---|---|---|---|---|
| $200 | 425 | 48% | $-5.46 | $-0.01 | $-3.61 |
| $250 | 443 | 48% | $2.52 | $+0.01 | $-4.73 |
| $350 | 453 | 47% | $-21.08 | $-0.04 | $-6.29 |
| $400 | 458 | 47% | $-38.32 | $-0.08 | $-6.07 |
| $550 | 458 | 47% | $0.02 | $+0.00 | $-10.25 |
| $1000 | 466 | 47% | $6.74 | $+0.01 | $-18.66 |

**All 6 accounts together: $-0.11 per trading day.**
