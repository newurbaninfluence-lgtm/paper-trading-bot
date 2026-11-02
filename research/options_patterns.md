# Options pattern finder (2026-11-02)

Underlyings: SPY, QQQ, AAPL, NVDA, TSLA, AMZN, META, MSFT, AMD. Period 2024-03-01 to 2026-11-01. **Hunt** before 2025-07-01, **exam** from 2025-07-01 (never seen while hunting).
Every signal buys the nearest at-the-money call (up) or put (down), at real Alpaca historical option prices, entry the next minute.
Costs: assumed half-spread + fees each side (ETFs 1% of premium, min $0.01; stocks 2.5%, min $0.025). Day trades only: out by 3:50 PM.
Return = % gained or lost on the premium paid, after costs.

## Result: 0 of the hunt's top 15 passed the exam

Pass = strong on the hunt (t 2+), still positive after costs on the exam (t 2+), at least 30 exam trades.
Engine check: on fake random-walk prices (fairly priced options) the average trade loses about the trading costs, as it should. Exits on the same signal are not independent, so one lucky signal can show up several times: treat a PASS as worth paper trading, nothing more.

| # | ETF/stock | Pattern | Expiry | Exit | Hunt trades | Hunt avg | Hunt t | Exam trades | Exam avg | Exam win % | Exam t | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | etf | orb15 | 0dte | stop50_tgt100 | 657 | +1.6% | +0.6 | 668 | -4.6% | 32% | -1.8 | lost on exam |
| 2 | stock | orb30 | 0dte | stop50_tgt100 | 388 | +1.6% | +0.5 | 785 | -4.6% | 32% | -1.9 | lost on exam |
| 3 | etf | orb15 | 0dte | stop30_tgt60 | 657 | +0.5% | +0.3 | 668 | -4.3% | 30% | -2.7 | lost on exam |
| 4 | etf | gap_fade | 0dte | stop50_tgt100 | 85 | +1.2% | +0.2 | 129 | -11.6% | 27% | -2.0 | lost on exam |
| 5 | etf | orb30 | 0dte | stop50_tgt100 | 639 | +0.2% | +0.1 | 638 | -3.5% | 32% | -1.3 | lost on exam |
| 6 | etf | orb30 | 0dte | stop50_hold_to_close | 639 | +0.2% | +0.1 | 638 | +3.6% | 24% | +0.6 | weak on hunt |
| 7 | etf | gap_fade | weekly | stop25_tgt50 | 79 | -0.0% | -0.0 | 115 | -3.2% | 43% | -1.4 | lost on exam |
| 8 | etf | orb15 | 0dte | stop50_hold_to_close | 657 | -0.1% | -0.0 | 668 | -4.2% | 23% | -1.0 | lost on exam |
| 9 | stock | orb30 | 0dte | stop50_hold_to_close | 388 | -0.3% | -0.1 | 785 | -5.1% | 21% | -1.3 | lost on exam |
| 10 | etf | gap_fade | weekly | stop50_tgt100 | 79 | -0.3% | -0.1 | 115 | -5.2% | 42% | -2.1 | lost on exam |
| 11 | etf | gap_fade | 0dte | stop50_hold_to_close | 85 | -1.4% | -0.1 | 129 | -18.6% | 16% | -2.4 | lost on exam |
| 12 | etf | gap_fade | weekly | stop50_hold_to_close | 79 | -0.5% | -0.1 | 115 | -3.9% | 42% | -1.2 | lost on exam |
| 13 | etf | gap_fade | weekly | stop30_tgt60 | 79 | -0.8% | -0.3 | 115 | -3.9% | 43% | -1.6 | lost on exam |
| 14 | etf | orb30 | weekly | stop50_hold_to_close | 604 | -0.6% | -0.4 | 601 | -0.7% | 46% | -0.5 | lost on exam |
| 15 | etf | trend_at_2pm | 0dte | stop50_hold_to_close | 544 | -2.7% | -0.5 | 542 | -10.5% | 26% | -2.6 | lost on exam |

## 0DTE vs weekly (all patterns, exam period)

| Expiry | Trades | Avg return | Win % |
|---|---|---|---|
| 0dte | 28196 | -7.1% | 28% |
| weekly | 43864 | -4.3% | 34% |

## Earnings-size gaps (like Oct 30: Intel, Amazon)

| Pattern | Expiry | Trades | Avg return | Win % |
|---|---|---|---|---|
| big_gap_bounce | 0dte | 39 | -10.3% | 18% |
| big_gap_bounce | weekly | 66 | +5.6% | 44% |
| big_gap_follow | 0dte | 27 | +2.2% | 22% |
| big_gap_follow | weekly | 55 | -12.2% | 35% |

Best exam result of ANY combo (hindsight only, not a pick): +90.6%.