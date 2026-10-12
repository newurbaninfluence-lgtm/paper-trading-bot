"""Strategy lab: test many professional setups fast, with the same honest rules every time.

Every strategy is judged the same way: real SIP prices, realistic costs, no look-ahead, t-stat on DAILY results
(same-day trades move together), positive in both halves of the period, and positive with bad-case costs.

Families
  ETF  (daily + SPY minute bars, 2018 -> now, auction/limit orders so costs are ~1 bp a side)
       overnight      buy the close, sell the next open (the "overnight drift")
       intraday       buy the open, sell the close (the mirror image, for comparison)
       rsi2_index     2-day RSI < 10 above the 200-day: buy close, exit close above 5-day avg (max 10 days)
       turn_of_month  hold from the 2nd-last trading day's close to the 3rd trading day's close
       gap_down_fill  open gaps down 0.3%+: buy the open, sell the close
       spy_mom        SPY up from prior close at 10:00 -> buy 15:30, sell at the close (Gao et al. intraday momentum)
       buy_hold       benchmark
  ORB  stocks in play, 5-minute opening range breakout (Zarattini & Aziz 2024): each day take the 20 stocks with the
       highest opening relative volume; green first 5 min -> buy a break of its high, red -> short a break of its low;
       stop = k x 14-day ATR; out at the close. Tested long and short, k = 0.10 / 0.25 / 0.50.

Usage: python lab.py etf | orb [days] | report
"""
import os, sys, json, math, datetime as dt
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import research as R
from core import ET

BASE = os.path.dirname(os.path.abspath(__file__)); OUT = f"{BASE}/research"
ETFS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLU", "SMH"]
ETF_COST = 0.0001  # per side: auction / limit orders on the most liquid ETFs
ACCT = 1000


def log(m): print(f"{dt.datetime.now(ET):%H:%M:%S} {m}", flush=True)


def tstat(x):
    x = pd.Series(x).dropna()
    return round(x.mean() / (x.std(ddof=1) / math.sqrt(len(x))), 2) if len(x) > 2 and x.std() > 0 else 0.0


# ---------- ETF family
def rsi2(c):
    ch = c.diff(); up = ch.clip(lower=0).ewm(alpha=0.5, adjust=False).mean(); dn = (-ch).clip(lower=0).ewm(alpha=0.5, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def etf_trades(g):
    """trades for one ETF: list of dicts(strategy, date, ret) with ret = net return of that trade"""
    g = g.sort_values("date").reset_index(drop=True); c, o = g.c, g.o; out = []
    pc = c.shift(1)
    for i in range(1, len(g)):
        out.append(dict(strategy="overnight", date=g.date[i], ret=o[i] / pc[i] - 1 - 2 * ETF_COST))
        out.append(dict(strategy="intraday", date=g.date[i], ret=c[i] / o[i] - 1 - 2 * ETF_COST))
        out.append(dict(strategy="buy_hold", date=g.date[i], ret=c[i] / pc[i] - 1))
        if o[i] / pc[i] - 1 <= -0.003: out.append(dict(strategy="gap_down_fill", date=g.date[i], ret=c[i] / o[i] - 1 - 2 * ETF_COST))
    r2, s200, s5 = rsi2(c), c.rolling(200).mean(), c.rolling(5).mean()
    i = 200
    while i < len(g) - 1:
        if r2[i] < 10 and c[i] > s200[i]:
            j = i + 1
            while j < len(g) - 1 and not (c[j] > s5[j]) and j - i < 10: j += 1
            out.append(dict(strategy="rsi2_index", date=g.date[i], ret=c[j] / c[i] - 1 - 2 * ETF_COST, held=j - i)); i = j
        i += 1
    m = pd.to_datetime(g.date).dt.to_period("M"); idx = g.groupby(m).apply(lambda x: list(x.index))
    months = list(idx.index)
    for a, b in zip(months[:-1], months[1:]):
        cur, nxt = idx[a], idx[b]
        if len(cur) >= 2 and len(nxt) >= 3:
            s, e = cur[-2], nxt[2]
            out.append(dict(strategy="turn_of_month", date=g.date[s], ret=c[e] / c[s] - 1 - 2 * ETF_COST, held=e - s))
    return out


def spy_momentum(start, end):
    """SPY intraday momentum: sign of (10:00 price vs prior close) -> position from 15:30 to the close"""
    rows = R.paged("/v2/stocks/bars", dict(symbols="SPY", timeframe="1Min", start=R.iso(start, "09:30"), end=R.iso(end, "16:00"),
                                          limit=10000, adjustment="split", feed="sip"), "bars").get("SPY", [])
    m = pd.DataFrame(rows); m.index = pd.to_datetime(m.t).dt.tz_convert(ET); m = m.between_time("09:30", "15:59")
    out, prev_close = [], None
    for day, b in m.groupby(m.index.date):
        if len(b) < 300: prev_close = float(b.c.iloc[-1]) if len(b) else prev_close; continue
        p10 = b.between_time("09:59", "09:59"); p1530 = b.between_time("15:29", "15:29")
        if prev_close and len(p10) and len(p1530):
            r1 = float(p10.c.iloc[0]) / prev_close - 1; entry = float(p1530.c.iloc[0]); close = float(b.c.iloc[-1])
            if r1 > 0: out.append(dict(etf="SPY", strategy="spy_mom_long", date=day, ret=close / entry - 1 - 2 * ETF_COST))
            else: out.append(dict(etf="SPY", strategy="spy_mom_short", date=day, ret=entry / close - 1 - 2 * ETF_COST))
        prev_close = float(b.c.iloc[-1])
    return out


def run_etf():
    start = dt.date(2018, 1, 1); end = dt.datetime.now(ET).date() - dt.timedelta(days=1)
    d = R.daily_bars(ETFS, start, end); log(f"etf daily rows {len(d)}")
    rows = []
    for s, g in d.groupby("sym"):
        rows += [dict(etf=s, **x) for x in etf_trades(g)]
    log("spy minute bars for intraday momentum...")
    rows += spy_momentum(start, end)
    t = pd.DataFrame(rows); t.to_csv(f"{OUT}/lab_etf.csv", index=False); log(f"etf trades {len(t)}")


def etf_table(t):
    t = t.copy(); t["date"] = pd.to_datetime(t.date); res = []
    for (s, e), g in t.groupby(["strategy", "etf"]):
        g = g.sort_values("date"); half = len(g) // 2; yrs = (g.date.max() - g.date.min()).days / 365.25 or 1
        eq = (1 + g.ret).cumprod(); dd = (eq / eq.cummax() - 1).min()
        res.append(dict(strategy=s, etf=e, trades=len(g), per_year=round(len(g) / yrs, 1), win=(g.ret > 0).mean(), avg=g.ret.mean(), t=tstat(g.ret),
                        h1=g.ret.iloc[:half].mean(), h2=g.ret.iloc[half:].mean(), cagr=eq.iloc[-1] ** (1 / yrs) - 1, maxdd=dd,
                        last12=g[g.date >= g.date.max() - pd.Timedelta(days=365)].ret.sum()))
    return pd.DataFrame(res)


# ---------- ORB stocks-in-play family
KS = (0.10, 0.25, 0.50)


def orb_day(day, cands, mb, cps_pct):
    """cands rows: sym, pc, adv20, atr14. Returns trades for the 20 highest-RVOL stocks."""
    first = []
    for r in cands.itertuples():
        b = mb.get(r.sym)
        if b is None or b.empty: continue
        rth = b.between_time("09:30", "15:59")
        if len(rth) < 60: continue
        f5 = rth.between_time("09:30", "09:34")
        if len(f5) < 3: continue
        rv = f5.Volume.sum() / (r.adv20 * 0.06)  # first 5 minutes are ~6% of a normal day's volume
        first.append((rv, r, rth, f5))
    first = sorted([x for x in first if x[0] > 1], key=lambda x: -x[0])[:20]
    out = []
    for rank, (rv, r, rth, f5) in enumerate(first):
        o5, c5, hi5, lo5 = float(f5.Open.iloc[0]), float(f5.Close.iloc[-1]), float(f5.High.max()), float(f5.Low.min())
        if c5 == o5: continue
        side = 1 if c5 > o5 else -1; level = hi5 if side == 1 else lo5
        rest = rth.between_time("09:35", "15:59"); o, h, l, c = (rest[k].values for k in ("Open", "High", "Low", "Close"))
        j0 = next((j for j in range(len(rest)) if (h[j] >= level if side == 1 else l[j] <= level)), None)
        if j0 is None: continue
        entry = max(level, o[j0]) if side == 1 else min(level, o[j0])
        for k in KS:
            risk = k * r.atr14; stop = entry - side * risk; why = "close"; x = c[-1]
            for j in range(j0, len(rest)):
                if (l[j] <= stop) if side == 1 else (h[j] >= stop):
                    x = min(stop, o[j]) if side == 1 else max(stop, o[j]); why = "stop"
                    if j == j0: x = stop  # same bar as entry: assume stop (conservative)
                    break
            gross = side * (x - entry) / risk
            cost_sides = 1 + (1 if why == "stop" else 0)  # stop-in and stop-out pay the spread; the close is an auction
            out.append(dict(date=day, sym=r.sym, side="long" if side == 1 else "short", k=k, rank=rank, rvol=round(rv, 2), entry=round(entry, 4),
                            risk=round(risk, 4), why=why, Rg=round(gross, 4), cost_R=round(cost_sides * cps_pct(entry) * entry / risk, 4)))
    return out


def run_orb(n_days=500):
    end = dt.datetime.now(ET).date() - dt.timedelta(days=1); start = end - dt.timedelta(days=int(n_days * 1.46) + 60)
    syms = R.universe(); d = R.daily_bars(syms, start, end); log(f"daily rows {len(d)}")
    d = d.sort_values(["sym", "date"]); g = d.groupby("sym")
    d["pc"] = g.c.shift(1); d["adv20"] = g.v.transform(lambda v: v.shift(1).rolling(20).mean())
    tr = np.maximum(d.h - d.l, np.maximum((d.h - d.pc).abs(), (d.l - d.pc).abs()))
    d["atr14"] = tr.groupby(d.sym).transform(lambda s: s.shift(1).rolling(14).mean()); d["gap"] = (d.o / d.pc - 1).abs()
    d = d[(d.pc >= 5) & (d.adv20 >= 1e6) & (d.atr14 >= 0.5)]
    days = sorted(d.date.unique())[-n_days:]
    try: costs = json.load(open(f"{OUT}/costs.json"))["bands"]
    except Exception: costs = None
    def cps_pct(px):  # half the typical measured spread
        if not costs: return 0.0015
        for (lo, hi), lab in zip(zip(R.PRICE_BANDS[:-1], R.PRICE_BANDS[1:]), R.PRICE_LABELS):
            if lo < px <= hi: return costs[lab]["median"] / 2
        return 0.0015
    path = f"{OUT}/lab_orb.csv"; done = set(pd.read_csv(path).date.astype(str)) if os.path.exists(path) else set(); t0 = time_ = dt.datetime.now()
    for k, day in enumerate(days):
        if str(day) in done: continue
        c = d[d.date == day].nlargest(60, "gap")
        if c.empty: continue
        mb = R.minute_bars(list(c.sym), day)
        rows = orb_day(day, c, mb, cps_pct)
        if rows: pd.DataFrame(rows).to_csv(path, mode="a", header=not os.path.exists(path), index=False)
        if k % 25 == 0: log(f"orb day {k + 1}/{len(days)} {day}: {len(rows)} rows")
        if os.environ.get("MAX_MINUTES") and (dt.datetime.now() - t0).total_seconds() > 60 * float(os.environ["MAX_MINUTES"]): log("time budget reached"); break


def orb_table(t):
    t = t.copy(); t["net"] = t.Rg - t.cost_R; t["net_bad"] = t.Rg - 2 * t.cost_R; res = []
    for (side, k), g in t.groupby(["side", "k"]):
        g = g.sort_values("date"); dm = g.groupby("date").net.mean(); half = len(dm) // 2
        res.append(dict(side=side, k=k, trades=len(g), per_day=round(len(g) / g.date.nunique(), 1), win=(g.net > 0).mean(), gross=g.Rg.mean(),
                        net=g.net.mean(), net_bad=g.net_bad.mean(), t=tstat(dm), h1=dm.iloc[:half].mean(), h2=dm.iloc[half:].mean(),
                        top5=g[g["rank"] < 5].net.mean()))
    return pd.DataFrame(res)


def orb_account(t, side="long", k=0.25, acct=ACCT):
    """cash account, 1% risk per trade, total position value capped at the account (no margin, no shorting for 'long')"""
    t = t[(t.side == side) & (t.k == k)].copy(); t["net"] = t.Rg - t.cost_R; pnl_days = []
    for day, g in t.sort_values("rank").groupby("date"):
        room, pnl = acct, 0.0
        for r in g.itertuples():
            sh = min(acct * 0.01 / r.risk, room / r.entry)
            if sh * r.entry < 5: break
            room -= sh * r.entry; pnl += sh * r.risk * r.net
        pnl_days.append(pnl)
    s = pd.Series(pnl_days); return s.mean(), (s > 0).mean(), s.min()


# ---------- report
def report():
    L = [f"# Strategy lab ({dt.date.today()})", "", "Survivor test for every strategy: positive after costs, t > 2 on daily results, positive in both halves, "
         "and still positive with worse costs. Anything that fails is not traded with real money.", ""]
    if os.path.exists(f"{OUT}/lab_etf.csv"):
        e = etf_table(pd.read_csv(f"{OUT}/lab_etf.csv")); e.to_csv(f"{OUT}/lab_etf_summary.csv", index=False)
        L += ["## ETF and index strategies (2018 to now, $1,000 fully in each trade, 1 bp cost a side)", "",
              "| Strategy | ETF | Trades/yr | Win % | Avg/trade | t | 1st half | 2nd half | Yearly growth | Worst drop | Last 12 mo |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in e.sort_values(["strategy", "t"], ascending=[True, False]).itertuples():
            L.append(f"| {r.strategy} | {r.etf} | {r.per_year} | {r.win:.0%} | {r.avg:+.3%} | {r.t} | {r.h1:+.3%} | {r.h2:+.3%} | {r.cagr:+.1%} | {r.maxdd:.0%} | {r.last12:+.1%} |")
        ok = e[(e.strategy != "buy_hold") & (e.t > 2) & (e.h1 > 0) & (e.h2 > 0) & (e.trades >= 100)]
        L += ["", f"**ETF survivors: {len(ok)}**"] + [f"- {r.strategy} on {r.etf}: {r.avg:+.3%} per trade, {r.per_year} trades a year, t={r.t}, worst drop {r.maxdd:.0%}" for r in ok.sort_values("t", ascending=False).itertuples()] + [""]
    if os.path.exists(f"{OUT}/lab_orb.csv"):
        t = pd.read_csv(f"{OUT}/lab_orb.csv"); o = orb_table(t); o.to_csv(f"{OUT}/lab_orb_summary.csv", index=False)
        L += [f"## Stocks-in-play opening range breakout ({t.date.nunique()} days, {t.date.min()} to {t.date.max()})", "",
              "| Side | Stop (x ATR) | Trades/day | Win % | Gross R | Net R | Net R (worse costs) | t (daily) | 1st half | 2nd half | Top-5 RVOL only |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in o.itertuples():
            L.append(f"| {r.side} | {r.k} | {r.per_day} | {r.win:.0%} | {r.gross:+.3f} | {r.net:+.3f} | {r.net_bad:+.3f} | {r.t} | {r.h1:+.3f} | {r.h2:+.3f} | {r.top5:+.3f} |")
        ok = o[(o.net > 0) & (o.net_bad > 0) & (o.t > 2) & (o.h1 > 0) & (o.h2 > 0)]
        L += ["", f"**ORB survivors: {len(ok)}**"] + [f"- {r.side}, stop {r.k} ATR: {r.net:+.3f}R per trade, t={r.t}" for r in ok.itertuples()]
        L += ["", "Cash-account replay, long side only (1% risk per trade, no margin):", "", "| Stop | Account | $/day | Green days | Worst day |", "|---|---|---|---|---|"]
        for k in KS:
            for a in (200, 550, 1000):
                m, w, worst = orb_account(t, "long", k, a); L.append(f"| {k} ATR | ${a} | ${m:+.2f} | {w:.0%} | ${worst:.2f} |")
    open(f"{OUT}/lab.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "report"
    if mode == "etf": run_etf()
    elif mode == "orb": run_orb(int(sys.argv[2]) if len(sys.argv) > 2 else 500)
    report()
