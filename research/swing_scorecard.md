# Swing strategies backtest (2026-10-24)

497 signal days from 2024-10-25 to 2026-10-22, 99908 simulated trades. Entry next open at market, stops fill at the worse of stop or open (gaps count against us). Measured quoted spread for these stocks: median 0.069%, 75th pct 0.140% (389 samples). Win % and t use typical-spread market orders. The bot-slippage column (2c or 0.15% a side) is a stress test.

## Every signal, by strategy and exit plan

| Strategy | Plan | Trades | Win % | Avg days | Gross R | Market orders, typical spread | Market orders, bad spread | Open/close auction orders | Bot slippage (stress test) | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| earn_gap | t20 | 290 | 39% | 13.2 | -0.029 | -0.041 | -0.054 | -0.036 | -0.082 | -0.77 | +0.062 | -0.144 |
| earn_gap | tr10 | 290 | 30% | 17.1 | -0.092 | -0.105 | -0.117 | -0.099 | -0.146 | -1.48 | -0.098 | -0.111 |
| trend_pb | sma5 | 49616 | 63% | 3.2 | +0.029 | +0.013 | -0.003 | +0.026 | -0.040 | -0.19 | +0.005 | +0.021 |
| trend_pb | t10 | 49254 | 48% | 8.5 | +0.052 | +0.036 | +0.020 | +0.046 | -0.017 | 0.66 | +0.050 | +0.023 |

**Pass the survivor test (net > +0.05R, t > 2, positive in both halves, 200+ trades, positive with market orders at typical and bad spreads and with auction orders): 0**

## Accounts replayed (live rules: 1% risk, cash only, no margin, fractional shares, earnings gaps first)

| Account | Trades | Win % | P&L | $/trading day | Worst trade |
|---|---|---|---|---|---|
| $200 | 414 | 48% | $5.67 | $+0.01 | $-6.72 |
| $250 | 444 | 46% | $-2.54 | $-0.01 | $-8.05 |
| $350 | 442 | 45% | $-21.53 | $-0.04 | $-10.86 |
| $400 | 445 | 46% | $-24.04 | $-0.05 | $-12.41 |
| $550 | 457 | 46% | $-21.46 | $-0.04 | $-17.43 |
| $1000 | 485 | 47% | $-0.76 | $-0.00 | $-32.39 |

**All 6 accounts together: $-0.13 per trading day.**
