# Options pattern finder (2026-11-14)

Underlyings: SPY, QQQ, AAPL, NVDA, TSLA, AMZN, META, MSFT, AMD. Period 2024-03-01 to 2026-11-13. **Hunt** before 2025-07-01, **exam** from 2025-07-01 (never seen while hunting).
Every signal buys the nearest at-the-money call (up) or put (down), at real Alpaca historical option prices, entry the next minute.
Costs: assumed half-spread + fees each side (ETFs 1% of premium, min $0.01; stocks 2.5%, min $0.025). Day trades only: out by 3:50 PM.
Return = % gained or lost on the premium paid, after costs.

## Result: 0 of the hunt's top 15 passed the exam

Pass = strong on the hunt (t 2+), still positive after costs on the exam (t 2+), at least 30 exam trades.
Engine check: on fake random-walk prices (fairly priced options) the average trade loses about the trading costs, as it should. Exits on the same signal are not independent, so one lucky signal can show up several times: treat a PASS as worth paper trading, nothing more.

| # | ETF/stock | Pattern | Expiry | Exit | Hunt trades | Hunt avg | Hunt t | Exam trades | Exam avg | Exam win % | Exam t | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | etf | orb15 | 0dte | stop50_tgt100 | 657 | +1.6% | +0.6 | 688 | -4.0% | 32% | -1.6 | lost on exam |
| 2 | stock | orb30 | 0dte | stop50_tgt100 | 388 | +1.6% | +0.5 | 819 | -5.5% | 32% | -2.3 | lost on exam |
| 3 | etf | orb15 | 0dte | stop30_tgt60 | 657 | +0.5% | +0.3 | 688 | -3.7% | 31% | -2.3 | lost on exam |
| 4 | etf | gap_fade | 0dte | stop50_tgt100 | 85 | +1.2% | +0.2 | 131 | -11.1% | 27% | -1.9 | lost on exam |
| 5 | etf | orb30 | 0dte | stop50_tgt100 | 639 | +0.2% | +0.1 | 656 | -2.3% | 33% | -0.8 | lost on exam |
| 6 | etf | orb30 | 0dte | stop50_hold_to_close | 639 | +0.2% | +0.1 | 656 | +4.4% | 24% | +0.8 | weak on hunt |
| 7 | etf | gap_fade | weekly | stop25_tgt50 | 79 | -0.0% | -0.0 | 117 | -3.3% | 42% | -1.5 | lost on exam |
| 8 | etf | orb15 | 0dte | stop50_hold_to_close | 657 | -0.1% | -0.0 | 688 | -3.1% | 23% | -0.7 | lost on exam |
| 9 | stock | orb30 | 0dte | stop50_hold_to_close | 388 | -0.3% | -0.1 | 819 | -5.1% | 20% | -1.3 | lost on exam |
| 10 | etf | gap_fade | weekly | stop50_tgt100 | 79 | -0.3% | -0.1 | 117 | -5.2% | 41% | -2.1 | lost on exam |
| 11 | etf | gap_fade | 0dte | stop50_hold_to_close | 85 | -1.4% | -0.1 | 131 | -19.1% | 16% | -2.5 | lost on exam |
| 12 | etf | gap_fade | weekly | stop50_hold_to_close | 79 | -0.5% | -0.1 | 117 | -3.9% | 41% | -1.2 | lost on exam |
| 13 | etf | gap_fade | weekly | stop30_tgt60 | 79 | -0.8% | -0.3 | 117 | -3.9% | 42% | -1.7 | lost on exam |
| 14 | etf | orb30 | weekly | stop50_hold_to_close | 604 | -0.6% | -0.4 | 619 | -0.5% | 46% | -0.4 | lost on exam |
| 15 | etf | trend_at_2pm | 0dte | stop50_hold_to_close | 544 | -2.7% | -0.5 | 556 | -10.7% | 26% | -2.7 | lost on exam |

## 0DTE vs weekly (all patterns, exam period)

| Expiry | Trades | Avg return | Win % |
|---|---|---|---|
| 0dte | 29288 | -6.7% | 28% |
| weekly | 45188 | -4.2% | 34% |

## Earnings-size gaps (like Oct 30: Intel, Amazon)

| Pattern | Expiry | Trades | Avg return | Win % |
|---|---|---|---|---|
| big_gap_bounce | 0dte | 46 | -13.7% | 17% |
| big_gap_bounce | weekly | 73 | +4.9% | 44% |
| big_gap_follow | 0dte | 35 | +8.5% | 23% |
| big_gap_follow | weekly | 64 | -9.3% | 36% |

Best exam result of ANY combo (hindsight only, not a pick): +83.5%.