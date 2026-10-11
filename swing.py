"""Swing strategies: hold for days, so trading costs are a small slice of the risk.
Same code runs the 2-year backtest and the live paper books (live = this engine replayed forward from START, rebuilt
from data every evening, so there is no hidden state that can drift from the backtest).

Strategies (signal at the close of day t, entry at the open of day t+1, market or auction orders, costs from measured spreads):
  earn_gap  post-earnings drift: gap up 4%+ on 2.5x volume, earnings headline before the open, closes green and in the
            top half of its range. Stop = gap-day low. Plans: t20 = exit at the close 20 days later; tr10 = exit on a close
            below the 10-day low (max 40 days).
  trend_pb  pullback in an uptrend: close > 200-day avg, 50-day avg > 200-day avg, 2-day RSI < 10. Stop = 2 x ATR.
            Plans: sma5 = exit on the first close above the 5-day avg (max 10 days); t10 = exit at the close 10 days later.
Universe: price >= $20 and 20-day average dollar volume >= $20M (tight spreads).

Usage: python swing.py backtest [days] | live
"""
import os, sys, re, json, math, datetime as dt
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import research as R
from core import ET, CAT_KW

BASE = os.path.dirname(os.path.abspath(__file__)); OUT = f"{BASE}/research"
START = dt.date.fromisoformat(os.environ.get("SWING_START", "2026-10-09"))  # first signal day for the live books (entries from Mon 10/12)
ACCTS = [200, 250, 350, 400, 550, 1000]
RISK = 0.01
PLANS = {"earn_gap": ("t20", "tr10"), "trend_pb": ("sma5", "t10")}
LIVE_PLAN = {"earn_gap": "t20", "trend_pb": "t10"}  # plan the live books trade (t10 tested best of the trend_pb exits)
EARN_RX = CAT_KW["earnings"]


def log(m): print(f"{dt.datetime.now(ET):%H:%M:%S} {m}", flush=True)


LEV_RX = re.compile(r"\b(2x|3x|-2x|-3x|leveraged|ultra|ultrapro|inverse|daily .*(bull|bear))\b", re.I)


def leveraged_set():
    """leveraged / inverse ETFs (they decay and just double up the same bet): excluded from the swing universe"""
    js = R.get(R.TRADE, "/v2/assets", dict(status="active", asset_class="us_equity")) or []
    return {a["symbol"] for a in js if LEV_RX.search(a.get("name") or "")}


# ---------- indicators
def indicators(d):
    # drop symbols that can never qualify (cheap or thin) before the heavy math
    keep = d.assign(dv=d.c * d.v).groupby("sym").agg(mx=("c", "max"), dv=("dv", "median"))
    d = d[d.sym.isin(keep[(keep.mx >= 18) & (keep.dv >= 5e6)].index)]
    d = d.sort_values(["sym", "date"]).copy(); g = d.groupby("sym", group_keys=False)
    d["pc"] = g.c.shift(1)
    d["sma5"] = g.c.transform(lambda s: s.rolling(5).mean())
    d["sma50"] = g.c.transform(lambda s: s.rolling(50).mean())
    d["sma200"] = g.c.transform(lambda s: s.rolling(200).mean())
    d["low10"] = g.l.transform(lambda s: s.rolling(10).min().shift(1))
    tr = np.maximum(d.h - d.l, np.maximum((d.h - d.pc).abs(), (d.l - d.pc).abs()))
    d["atr14"] = tr.groupby(d.sym).transform(lambda s: s.rolling(14).mean())
    ch = g.c.diff(); up = ch.clip(lower=0); dn = (-ch).clip(lower=0)
    au = up.groupby(d.sym).transform(lambda s: s.ewm(alpha=0.5, adjust=False).mean())
    ad = dn.groupby(d.sym).transform(lambda s: s.ewm(alpha=0.5, adjust=False).mean())
    d["rsi2"] = 100 - 100 / (1 + au / ad.replace(0, np.nan))
    d["adv20"] = g.v.transform(lambda s: s.shift(1).rolling(20).mean())
    d["dv20"] = (d.c * d.v).groupby(d.sym).transform(lambda s: s.shift(1).rolling(20).mean())
    d["gap"] = d.o / d.pc - 1
    d["liquid"] = (d.c >= 20) & (d.dv20 >= 20e6)
    return d


def earnings_flags(cands):
    """{(sym, date): headline} for earnings headlines in the 24h before that day's open"""
    out = {}
    for day, g in cands.groupby("date"):
        syms = list(g.sym)
        for i in range(0, len(syms), 50):
            cat = R.news_before_open(syms[i:i + 50], day)
            for s, h in cat.items():
                if not h.startswith("NEG:") and re.search(EARN_RX, h, re.I): out[(s, day)] = h
    return out


def signals(d, earn, exclude=()):
    """all signals (both strategies) with stop and features; signal day = t, entry next open"""
    base = d[d.liquid & d.sma200.notna() & ~d.sym.isin(set(exclude))]
    eg = base[(base.gap >= 0.04) & (base.v >= 2.5 * base.adv20) & (base.c >= base.o) & ((base.c - base.l) >= 0.5 * (base.h - base.l))].copy()
    eg["earn"] = [1 if (s, t) in earn else 0 for s, t in zip(eg.sym, eg.date)]
    eg = eg[eg.earn == 1]; eg["strategy"] = "earn_gap"; eg["stop"] = eg.l - 0.01; eg["rank"] = -eg.gap
    tp = base[(base.c > base.sma200) & (base.sma50 > base.sma200) & (base.rsi2 < 10)].copy()
    tp["strategy"] = "trend_pb"; tp["stop"] = tp.c - 2 * tp.atr14; tp["rank"] = tp.rsi2
    s = pd.concat([eg, tp])[["sym", "date", "strategy", "stop", "rank", "c", "gap", "rsi2", "atr14"]]
    return s.sort_values(["date", "strategy", "rank"])


# ---------- trade simulation on daily bars
def simulate(bars, i, stop, plan):
    """bars: one symbol's rows (numpy arrays dict), signal at row i, entry at row i+1 open.
    Returns gross R, exit date, why, entry, risk; stops fill at min(stop, open) (gaps go against you)."""
    n = len(bars["o"])
    if i + 1 >= n: return None
    e = i + 1; px = bars["o"][e]; risk = px - stop
    if not (risk > 0 and 0.01 <= risk / px <= 0.15): return None
    maxd = {"t20": 20, "tr10": 40, "sma5": 10, "t10": 10}[plan]
    for j in range(e, n):
        held = j - e + 1
        if bars["l"][j] <= stop:
            x = min(stop, bars["o"][j]); return dict(Rg=(x - px) / risk, exit=bars["date"][j], why="stop", entry=px, risk=risk, held=held)
        c = bars["c"][j]
        if plan == "sma5" and c > bars["sma5"][j]: return dict(Rg=(c - px) / risk, exit=bars["date"][j], why="sma5", entry=px, risk=risk, held=held)
        if plan == "tr10" and j > e and c < bars["low10"][j]: return dict(Rg=(c - px) / risk, exit=bars["date"][j], why="trail", entry=px, risk=risk, held=held)
        if held >= maxd: return dict(Rg=(c - px) / risk, exit=bars["date"][j], why="time", entry=px, risk=risk, held=held)
    return dict(Rg=(bars["c"][n - 1] - px) / risk, exit=None, why="open", entry=px, risk=risk, held=n - e)


def run_signals(d, sig):
    by = {s: {k: g[k].values for k in ("date", "o", "h", "l", "c", "sma5", "low10")} for s, g in d.groupby("sym")}
    pos = {s: {t: k for k, t in enumerate(v["date"])} for s, v in by.items()}
    rows = []
    for r in sig.itertuples():
        b = by.get(r.sym)
        if b is None: continue
        i = pos[r.sym][r.date]
        for plan in PLANS[r.strategy]:
            out = simulate(b, i, r.stop, plan)
            if out: rows.append(dict(date=r.date, sym=r.sym, strategy=r.strategy, plan=plan, stop=round(r.stop, 4), rank=r.rank,
                                     entry_date=b["date"][i + 1], **out))
    return pd.DataFrame(rows)


def swing_costs():
    """measured quoted spreads for this liquid universe (research/swing_costs.json); conservative default if not measured yet"""
    try: return json.load(open(f"{OUT}/swing_costs.json"))
    except Exception: return dict(median=0.002, p75=0.004, n=0, note="default, not measured")


def measure_spreads(sig, n=400):
    smp = sig.sample(min(n, len(sig)), random_state=11); sp = []
    for k, r in enumerate(smp.itertuples()):
        v, _ = R.spread_at(r.sym, dt.datetime.combine(r.date, dt.time(15, 30), ET))
        if v is not None: sp.append(v)
        if k % 100 == 0: log(f"swing spreads {k}/{len(smp)}")
    out = dict(median=round(float(np.median(sp)), 5), p75=round(float(np.percentile(sp, 75)), 5), n=len(sp), measured=str(dt.date.today()))
    json.dump(out, open(f"{OUT}/swing_costs.json", "w"), indent=1); log(f"swing spreads: {out}"); return out


COST_COLS = {"net_liquid": "Market orders, typical spread", "net_liquid_bad": "Market orders, bad spread",
             "net_auction": "Open/close auction orders", "net_bot": "Bot slippage (stress test)"}
REQUIRED = ("net_liquid", "net_liquid_bad", "net_auction")


def add_net(t, sc):
    """costs: market orders pay half the spread each side; auction orders (market-on-open in, market-on-close out) pay no
    spread except when a stop fires intraday"""
    exit_px = t.entry + t.Rg * t.risk
    t["net_liquid"] = t.Rg - 2 * (sc["median"] / 2 * t.entry) / t.risk
    t["net_liquid_bad"] = t.Rg - 2 * (sc["p75"] / 2 * t.entry) / t.risk
    t["net_auction"] = t.Rg - (t.why == "stop") * (sc["p75"] / 2 * exit_px) / t.risk
    t["net_bot"] = t.Rg - 2 * np.maximum(0.02, 0.0015 * t.entry) / t.risk
    return t


# ---------- account books (cash account, no margin, fractional shares, 1% risk per trade)
def books(t, start=None, plan_map=None, sc=None):
    """replay every account forward; returns (closed trades, open positions).
    Cash rule: a position's money is tied up from entry until the day after it exits (T+1 settlement)."""
    plan_map = plan_map or LIVE_PLAN
    t = t[t.plan == t.strategy.map(plan_map)].copy()
    if start: t = t[t.date >= start]
    t = t.sort_values(["entry_date", "strategy", "rank"])
    sc = sc or swing_costs()
    closed, still_open = [], []
    for acct in ACCTS:
        held = []
        for day, todays in t.groupby("entry_date", sort=True):
            realized = sum(p["pnl"] for p in held if p["exit"] is not None and p["exit"] < day)
            tied = sum(p["cost"] for p in held if p["exit"] is None or p["exit"] >= day)
            risk_d = (acct + realized) * RISK
            for r in todays.itertuples():
                ex = None if pd.isna(r.exit) else r.exit
                if any(p["sym"] == r.sym and (p["exit"] is None or p["exit"] >= day) for p in held): continue
                room = acct + realized - tied
                if room < 10: break
                sh = min(risk_d / r.risk, room / r.entry); cost = sh * r.entry
                cps = sc["median"] / 2 * r.entry
                pnl = round(sh * (r.Rg * r.risk - 2 * cps), 2) if ex is not None else None
                held.append(dict(account=acct, sym=r.sym, strategy=r.strategy, plan=r.plan, signal_date=r.date, entry_date=r.entry_date,
                                 entry=round(r.entry, 2), stop=round(r.stop, 2), shares=round(sh, 4), cost=round(cost, 2), exit=ex, why=r.why,
                                 held=r.held, exit_px=round(r.entry + r.Rg * r.risk, 2), pnl=pnl, R=None if pnl is None else round(pnl / risk_d, 2)))
                tied += cost
        closed += [p for p in held if p["exit"] is not None]; still_open += [p for p in held if p["exit"] is None]
    return pd.DataFrame(closed), pd.DataFrame(still_open)


# ---------- reports
def strategy_table(t):
    L = ["| Strategy | Plan | Trades | Win % | Avg days | Gross R | " + " | ".join(COST_COLS.values()) + " | t | 1st half | 2nd half |",
         "|---|---|---|---|---|---|" + "---|" * len(COST_COLS) + "---|---|---|"]
    res = []
    for (s_, p), g in t[t.exit.notna()].groupby(["strategy", "plan"]):
        g = g.sort_values("date"); half = len(g) // 2; main = g["net_liquid"]
        st = R.stats(main.groupby(g.date).mean())  # t on DAILY averages: same-day signals move together, so per-trade t overstates confidence
        row = dict(strategy=s_, plan=p, n=len(g), win=(main > 0).mean(), days=g.held.mean(), gross=g.Rg.mean(), net=main.mean(),
                   t=st["t"], h1=main.iloc[:half].mean(), h2=main.iloc[half:].mean(), worst=min(g[c].mean() for c in REQUIRED),
                   **{c: g[c].mean() for c in COST_COLS})
        res.append(row)
        L.append(f"| {s_} | {p} | {row['n']} | {row['win']:.0%} | {row['days']:.1f} | {row['gross']:+.3f} | " +
                 " | ".join(f"{row[c]:+.3f}" for c in COST_COLS) + f" | {row['t']} | {row['h1']:+.3f} | {row['h2']:+.3f} |")
    return L, pd.DataFrame(res)


def backtest(n_days=500):
    end = dt.datetime.now(ET).date() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=int(n_days * 1.46) + 330)
    syms = R.universe(); log(f"universe {len(syms)}")
    d = R.daily_bars(syms, start, end); log(f"daily rows {len(d)}")
    d = indicators(d)
    days = sorted(d.date.unique()); first = days[-n_days]
    d_sig = d[d.date >= first]
    eg_c = d_sig[d_sig.liquid & (d_sig.gap >= 0.04) & (d_sig.v >= 2.5 * d_sig.adv20)]
    log(f"earnings-gap candidates to check for news: {len(eg_c)}")
    earn = earnings_flags(eg_c[["sym", "date"]]); log(f"earnings gaps: {len(earn)}")
    lev = leveraged_set(); log(f"leveraged/inverse ETFs excluded: {len(lev)}")
    sig = signals(d_sig, earn, lev); log(f"signals: {sig.strategy.value_counts().to_dict()}")
    sc = measure_spreads(sig)
    t = add_net(run_signals(d, sig), sc)
    os.makedirs(OUT, exist_ok=True); t.to_csv(f"{OUT}/swing_bt.csv", index=False)
    report(t, d, first)


def report(t, d, first):
    sc = swing_costs()
    L = [f"# Swing strategies backtest ({dt.date.today()})", "",
         f"{t.date.nunique()} signal days from {first} to {t.date.max()}, {len(t)} simulated trades. Entry next open at market, stops fill at the worse of stop "
         f"or open (gaps count against us). Measured quoted spread for these stocks: median {sc['median']:.3%}, 75th pct {sc['p75']:.3%} "
         f"({sc.get('n')} samples). Win % and t use typical-spread market orders. The bot-slippage column (2c or 0.15% a side) is a stress test.", "", "## Every signal, by strategy and exit plan", ""]
    tab, res = strategy_table(t); L += tab
    good = res[(res.net > 0.05) & (res.t > 2) & (res.h1 > 0) & (res.h2 > 0) & (res.n >= 200) & (res.worst > 0)]
    L += ["", f"**Pass the survivor test (net > +0.05R, t > 2, positive in both halves, 200+ trades, positive with market orders at typical and bad spreads and with auction orders): {len(good)}**"]
    L += [f"- {r.strategy} / {r.plan}: {r.net:+.3f}R per trade over {r.n} trades, {r.days:.1f} days average hold" for r in good.itertuples()]
    j, _ = books(t, sc=sc)
    if len(j):
        nd = len([x for x in sorted(d.date.unique()) if x >= first])
        L += ["", "## Accounts replayed (live rules: 1% risk, cash only, no margin, fractional shares, earnings gaps first)", "",
              "| Account | Trades | Win % | P&L | $/trading day | Worst trade |", "|---|---|---|---|---|---|"]
        for a, g in j.groupby("account"):
            L.append(f"| ${a} | {len(g)} | {(g.pnl > 0).mean():.0%} | ${g.pnl.sum():,.2f} | ${g.pnl.sum() / nd:+.2f} | ${g.pnl.min():.2f} |")
        per_day = j.pnl.sum() / nd
        L += ["", f"**All 6 accounts together: ${per_day:+.2f} per trading day.**"]
        if per_day > 0: L += [f"At the same edge, $20/day needs about {20 / per_day:.1f}x the money (about ${2750 * 20 / per_day:,.0f} total)."]
    open(f"{OUT}/swing_scorecard.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))


# ---------- live: rebuild the books from START every evening
def live():
    end = dt.datetime.now(ET).date()
    start = START - dt.timedelta(days=330)
    syms = R.universe(); d = indicators(R.daily_bars(syms, start, end))
    last = d.date.max(); log(f"latest daily bar: {last}")
    d_sig = d[d.date >= START]
    eg_c = d_sig[d_sig.liquid & (d_sig.gap >= 0.04) & (d_sig.v >= 2.5 * d_sig.adv20)]
    earn = earnings_flags(eg_c[["sym", "date"]]) if len(eg_c) else {}
    sig = signals(d_sig, earn, leveraged_set())
    sc = swing_costs()
    t = run_signals(d, sig)
    os.makedirs(f"{BASE}/swing", exist_ok=True)
    tomorrow = sig[sig.date == last]
    tomorrow.to_csv(f"{BASE}/swing/next_open_buys.csv", index=False)
    L = [f"# Swing paper books ({last})", "", f"Signals at today's close (bought at the next open): "
         f"{', '.join(f'{r.sym} ({r.strategy})' for r in tomorrow.itertuples()) or 'none'}", ""]
    if len(t):
        t = add_net(t, sc); j, o = books(t, START, sc=sc)
        j.to_csv(f"{BASE}/swing/journal.csv", index=False); o.to_csv(f"{BASE}/swing/open.csv", index=False)
        if len(o):
            px = d[d.date == last].set_index("sym").c
            o["last"] = o.sym.map(px); o["unrealized"] = ((o["last"] - o.entry) * o.shares).round(2)
            L += ["## Open positions", "", "| Account | Ticker | Strategy | Entry date | Entry | Stop | Shares | Last | Unrealized |", "|---|---|---|---|---|---|---|---|---|"]
            L += [f"| ${r.account} | {r.sym} | {r.strategy} | {r.entry_date} | {r.entry} | {r.stop} | {r.shares} | {r.last} | ${r.unrealized} |" for r in o.itertuples()]
        if len(j):
            L += ["", "## Closed trades", "", "| Account | Ticker | Strategy | In | Out | Why | P&L | R |", "|---|---|---|---|---|---|---|---|"]
            L += [f"| ${r.account} | {r.sym} | {r.strategy} | {r.entry_date} | {r.exit} | {r.why} | ${r.pnl} | {r.R} |" for r in j.itertuples()]
            L += ["", f"**Closed P&L: ${j.pnl.sum():.2f}**"]
    else: L += ["No positions yet."]
    open(f"{BASE}/swing/report.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "live"
    if mode == "backtest": backtest(int(sys.argv[2]) if len(sys.argv) > 2 else 500)
    else: live()
