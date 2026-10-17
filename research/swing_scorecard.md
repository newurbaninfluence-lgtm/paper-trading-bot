# Swing strategies backtest (2026-10-17)

497 signal days from 2024-10-18 to 2026-10-15, 101308 simulated trades. Entry next open at market, stops fill at the worse of stop or open (gaps count against us). Measured quoted spread for these stocks: median 0.052%, 75th pct 0.132% (392 samples). Win % and t use typical-spread market orders. The bot-slippage column (2c or 0.15% a side) is a stress test.

## Every signal, by strategy and exit plan

| Strategy | Plan | Trades | Win % | Avg days | Gross R | Market orders, typical spread | Market orders, bad spread | Open/close auction orders | Bot slippage (stress test) | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| earn_gap | t20 | 296 | 40% | 13.3 | -0.009 | -0.018 | -0.032 | -0.015 | -0.062 | -0.49 | +0.082 | -0.117 |
| earn_gap | tr10 | 296 | 31% | 17.3 | -0.067 | -0.076 | -0.091 | -0.073 | -0.121 | -1.18 | -0.046 | -0.107 |
| trend_pb | sma5 | 50085 | 64% | 3.2 | +0.027 | +0.015 | -0.004 | +0.023 | -0.042 | -0.44 | +0.005 | +0.024 |
| trend_pb | t10 | 49885 | 48% | 8.5 | +0.058 | +0.046 | +0.028 | +0.053 | -0.011 | 0.68 | +0.053 | +0.039 |

**Pass the survivor test (net > +0.05R, t > 2, positive in both halves, 200+ trades, positive with market orders at typical and bad spreads and with auction orders): 0**

## Accounts replayed (live rules: 1% risk, cash only, no margin, fractional shares, earnings gaps first)

| Account | Trades | Win % | P&L | $/trading day | Worst trade |
|---|---|---|---|---|---|
| $200 | 401 | 47% | $-22.60 | $-0.05 | $-6.39 |
| $250 | 427 | 47% | $-34.19 | $-0.07 | $-7.98 |
| $350 | 434 | 46% | $-34.98 | $-0.07 | $-11.18 |
| $400 | 438 | 46% | $-43.09 | $-0.09 | $-12.77 |
| $550 | 447 | 47% | $-55.03 | $-0.11 | $-17.56 |
| $1000 | 478 | 47% | $-55.62 | $-0.11 | $-31.93 |

**All 6 accounts together: $-0.49 per trading day.**
