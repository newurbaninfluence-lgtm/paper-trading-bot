# Swing strategies backtest (2026-11-07)

497 signal days from 2024-11-08 to 2026-11-05, 98904 simulated trades. Entry next open at market, stops fill at the worse of stop or open (gaps count against us). Measured quoted spread for these stocks: median 0.063%, 75th pct 0.116% (387 samples). Win % and t use typical-spread market orders. The bot-slippage column (2c or 0.15% a side) is a stress test.

## Every signal, by strategy and exit plan

| Strategy | Plan | Trades | Win % | Avg days | Gross R | Market orders, typical spread | Market orders, bad spread | Open/close auction orders | Bot slippage (stress test) | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| earn_gap | t20 | 276 | 36% | 12.6 | -0.116 | -0.128 | -0.137 | -0.123 | -0.171 | -1.5 | -0.049 | -0.206 |
| earn_gap | tr10 | 275 | 28% | 16.2 | -0.149 | -0.161 | -0.170 | -0.155 | -0.203 | -2.05 | -0.103 | -0.218 |
| trend_pb | sma5 | 48964 | 63% | 3.2 | +0.024 | +0.010 | -0.002 | +0.021 | -0.044 | -0.47 | -0.001 | +0.021 |
| trend_pb | t10 | 48737 | 47% | 8.5 | +0.031 | +0.017 | +0.005 | +0.026 | -0.037 | -0.14 | +0.027 | +0.006 |

**Pass the survivor test (net > +0.05R, t > 2, positive in both halves, 200+ trades, positive with market orders at typical and bad spreads and with auction orders): 0**

## Accounts replayed (live rules: 1% risk, cash only, no margin, fractional shares, earnings gaps first)

| Account | Trades | Win % | P&L | $/trading day | Worst trade |
|---|---|---|---|---|---|
| $200 | 406 | 47% | $-14.39 | $-0.03 | $-6.08 |
| $250 | 426 | 48% | $-6.55 | $-0.01 | $-7.98 |
| $350 | 444 | 46% | $-16.28 | $-0.03 | $-11.01 |
| $400 | 445 | 46% | $-20.47 | $-0.04 | $-12.59 |
| $550 | 455 | 46% | $-18.37 | $-0.04 | $-17.64 |
| $1000 | 480 | 45% | $-137.89 | $-0.28 | $-28.78 |

**All 6 accounts together: $-0.43 per trading day.**
