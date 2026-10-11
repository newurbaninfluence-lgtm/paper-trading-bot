# Swing strategies backtest (2026-10-11)

497 signal days from 2024-10-11 to 2026-10-08, 102206 simulated trades. Entry next open at market, stops fill at the worse of stop or open (gaps count against us). Measured quoted spread for these stocks: median 0.064%, 75th pct 0.139% (394 samples). Win % and t use typical-spread market orders. The bot-slippage column (2c or 0.15% a side) is a stress test.

## Every signal, by strategy and exit plan

| Strategy | Plan | Trades | Win % | Avg days | Gross R | Market orders, typical spread | Market orders, bad spread | Open/close auction orders | Bot slippage (stress test) | t | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| earn_gap | t20 | 301 | 39% | 13.2 | -0.019 | -0.030 | -0.044 | -0.026 | -0.072 | -0.39 | +0.065 | -0.125 |
| earn_gap | tr10 | 300 | 31% | 17.1 | -0.079 | -0.091 | -0.104 | -0.086 | -0.133 | -1.1 | -0.064 | -0.118 |
| trend_pb | sma5 | 50629 | 64% | 3.2 | +0.032 | +0.017 | -0.000 | +0.028 | -0.037 | 5.92 | -0.003 | +0.036 |
| trend_pb | t10 | 49944 | 48% | 8.5 | +0.057 | +0.043 | +0.025 | +0.052 | -0.011 | 8.57 | +0.032 | +0.053 |

**Pass the survivor test (net > +0.05R, t > 2, positive in both halves, 200+ trades, positive with market orders at typical and bad spreads and with auction orders): 0**

## Accounts replayed (live rules: 1% risk, cash only, no margin, fractional shares, earnings gaps first)

| Account | Trades | Win % | P&L | $/trading day | Worst trade |
|---|---|---|---|---|---|
| $200 | 708 | 56% | $-31.13 | $-0.06 | $-3.88 |
| $250 | 731 | 57% | $-43.45 | $-0.09 | $-6.24 |
| $350 | 750 | 57% | $-56.88 | $-0.11 | $-8.97 |
| $400 | 758 | 57% | $-64.04 | $-0.13 | $-10.28 |
| $550 | 773 | 57% | $-89.45 | $-0.18 | $-14.12 |
| $1000 | 778 | 58% | $-137.61 | $-0.28 | $-26.51 |

**All 6 accounts together: $-0.85 per trading day.**
