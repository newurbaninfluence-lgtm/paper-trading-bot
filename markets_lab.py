"""Pattern finder for crypto and forex (paper research only).
Hunts hundreds of simple, fixed rules on an older "hunt" period, then tests the best ones on a newer "exam" period
they never saw. Only rules that still make money after fees/spreads on the exam pass.
Usage: python markets_lab.py crypto DATA_DIR  |  python markets_lab.py forex DATA_DIR
Bars: 1-hour, UTC. Entry at the next bar's open after a signal; every trade risks 1R (stop = k x ATR)."""
import sys, os, math, itertools, datetime as dt
import numpy as np, pandas as pd

KIND, DATA = sys.argv[1], sys.argv[2]
TF = sys.argv[3] if len(sys.argv) > 3 else "1h"      # 1h, 4h or 1d
BPD = {"1h": 24, "4h": 6, "1d": 1}[TF]               # bars per day
OUT = os.environ.get("LAB_OUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "research")
MAXHOLD = 48

# ---------- costs (round trip, in price terms or as a fraction)
CRYPTO_SIDE = 0.0030          # Alpaca crypto taker fee 0.25% + ~0.05% slippage, per side
FX_SPREAD = {"EURUSD": 0.00012, "GBPUSD": 0.00018, "USDJPY": 0.015, "AUDUSD": 0.00014, "USDCAD": 0.00020}  # typical retail spread + slip
SPLIT = {"crypto": "2025-01-01", "forex": "2025-11-01"}[KIND]
SIDES = ("long",) if KIND == "crypto" else ("long", "short")   # Alpaca crypto can't short


def load():
    out = {}
    for f in sorted(os.listdir(DATA)):
        if not f.endswith(".csv"): continue
        d = pd.read_csv(f"{DATA}/{f}", index_col=0); d.index = pd.to_datetime(d.index, utc=True)
        d = d[["o", "h", "l", "c"]].astype(float).dropna()
        if TF != "1h": d = d.resample(TF.replace("h", "h").replace("1d", "1D")).agg(dict(o="first", h="max", l="min", c="last")).dropna()
        tr = pd.concat([d.h - d.l, (d.h - d.c.shift()).abs(), (d.l - d.c.shift()).abs()], axis=1).max(axis=1)
        d["atr"] = tr.rolling(max(14, BPD)).mean()
        d["e50"] = d.c.ewm(span=50).mean(); d["e200"] = d.c.ewm(span=200).mean()
        d["d50"] = d.c.rolling(BPD * 50).mean()                      # ~50-day average
        dl = d.c.diff(); up, dn = dl.clip(lower=0), -dl.clip(upper=0)
        d["rsi2"] = 100 - 100 / (1 + up.ewm(alpha=0.5).mean() / dn.ewm(alpha=0.5).mean().replace(0, 1e-12))
        d["sma20"], d["sd20"] = d.c.rolling(20).mean(), d.c.rolling(20).std()
        d["hour"], d["dow"] = d.index.hour, d.index.dayofweek
        out[f[:-4]] = d.dropna()
    return out


# ---------- rule families: f(d, side) -> boolean signal Series (at bar close)
def fam():
    R = {}
    for n in (12, 24, 48, 96) if TF != "1d" else (10, 20, 55):
        R[f"breakout_{n}bars"] = lambda d, s, n=n: (d.c > d.h.shift(1).rolling(n).max()) if s == "long" else (d.c < d.l.shift(1).rolling(n).min())
    for z in (2.0, 2.5):
        R[f"band_fade_{z}sd"] = lambda d, s, z=z: (d.c < d.sma20 - z * d.sd20) if s == "long" else (d.c > d.sma20 + z * d.sd20)
    for x in (5, 10):
        R[f"rsi2_{x}_in_trend"] = lambda d, s, x=x: ((d.rsi2 < x) & (d.c > d.e200)) if s == "long" else ((d.rsi2 > 100 - x) & (d.c < d.e200))
    for k, q in itertools.product((4, 12, 24), (1.5, 3.0)):
        R[f"big_move_{k}bars_{q}atr_follow"] = lambda d, s, k=k, q=q: ((d.c - d.c.shift(k)) > q * d.atr * math.sqrt(k) / 2) if s == "long" else ((d.c - d.c.shift(k)) < -q * d.atr * math.sqrt(k) / 2)
        R[f"big_move_{k}bars_{q}atr_fade"] = lambda d, s, k=k, q=q: ((d.c - d.c.shift(k)) < -q * d.atr * math.sqrt(k) / 2) if s == "long" else ((d.c - d.c.shift(k)) > q * d.atr * math.sqrt(k) / 2)
    R["ema50_cross"] = lambda d, s: ((d.c > d.e50) & (d.c.shift() <= d.e50.shift())) if s == "long" else ((d.c < d.e50) & (d.c.shift() >= d.e50.shift()))
    R["pullback_to_ema50_uptrend"] = lambda d, s: ((d.l <= d.e50) & (d.c > d.e50) & (d.e50 > d.e200)) if s == "long" else ((d.h >= d.e50) & (d.c < d.e50) & (d.e50 < d.e200))
    for h in (range(0, 24, 2) if TF == "1h" else []):
        R[f"hour_{h:02d}utc"] = lambda d, s, h=h: d.hour == h
    for w in range(7 if KIND == "crypto" else 5):
        R[f"day_{['mon','tue','wed','thu','fri','sat','sun'][w]}"] = lambda d, s, w=w: (d.dow == w) & (d.hour == 0)
    if KIND == "forex" and TF == "1h":   # London open breakout of the Asian range (00-07 UTC)
        def london(d, s):
            day = d.index.normalize(); asia = d[d.hour < 7]
            hi = asia.h.groupby(asia.index.normalize()).max().reindex(day).values; lo = asia.l.groupby(asia.index.normalize()).min().reindex(day).values
            win = (d.hour >= 7) & (d.hour <= 11)
            return win & ((d.c > hi) if s == "long" else (d.c < lo))
        R["london_breakout"] = london
    return R

FILTERS = {"any": lambda d, s: True,
           "with_trend": lambda d, s: (d.c > d.d50) if s == "long" else (d.c < d.d50)}
EXITS = {"stop1.5_tgt3": (1.5, 3.0, MAXHOLD), "stop2_tgt2": (2.0, 2.0, MAXHOLD), "stop2_hold4bars": (2.0, None, 4),
         "stop2_hold12bars": (2.0, None, 12), "stop2_hold24bars": (2.0, None, 24), "stop3_trail_exit_below_ema50": (3.0, "trail", 200)}


def run(d, sig, side, ex, sym):
    """non-overlapping trades: enter next bar open; stop/target intrabar (stop wins ties); time exit at close"""
    ks, kt, hold = EXITS[ex]
    o, h, l, c, atr, e50 = (d[k].values for k in ("o", "h", "l", "c", "atr", "e50")); idx = np.flatnonzero(sig.values); t = d.index
    res, nxt, sgn = [], 0, 1 if side == "long" else -1
    for i in idx:
        if i < nxt or i + 1 >= len(d): continue
        e = o[i + 1]; risk = ks * atr[i]
        if not risk > 0: continue
        trail = kt == "trail"; stop = e - sgn * risk; tgt = e + sgn * kt * atr[i] if kt and not trail else None
        end = min(i + 1 + hold, len(d)); px, j_exit = None, end - 1
        for j in range(i + 1, end):
            if (l[j] <= stop) if sgn > 0 else (h[j] >= stop): px, j_exit = (min(stop, o[j]) if sgn > 0 else max(stop, o[j])), j; break
            if tgt is not None and ((h[j] >= tgt) if sgn > 0 else (l[j] <= tgt)): px, j_exit = tgt, j; break
            if trail and j > i + 1 and ((c[j] < e50[j]) if sgn > 0 else (c[j] > e50[j])): px, j_exit = c[j], j; break
        if px is None: px = c[j_exit]
        cost = (e + px) * CRYPTO_SIDE if KIND == "crypto" else FX_SPREAD.get(sym, 0.00015)
        res.append((t[i + 1], sgn * (px - e) / risk, cost / risk))
        nxt = j_exit + 1
    return res


def stats(rows):
    if not rows: return dict(n=0, net=np.nan, gross=np.nan, win=np.nan, t=np.nan)
    g = np.array([r[1] for r in rows]); n_ = g - np.array([r[2] for r in rows])
    sd = n_.std(ddof=1) if len(n_) > 1 else np.nan
    return dict(n=len(n_), gross=g.mean(), net=n_.mean(), win=(n_ > 0).mean(), t=n_.mean() / (sd / math.sqrt(len(n_))) if sd and sd > 0 else np.nan)


def main():
    global SPLIT
    data = load(); rules = fam(); rows = []
    first, last = min(d.index[0] for d in data.values()), max(d.index[-1] for d in data.values())
    if pd.Timestamp(SPLIT, tz="UTC") > last - pd.Timedelta(days=120):   # not enough exam data yet: exam = newest third
        SPLIT = str((first + (last - first) * 2 / 3).date())
    split = pd.Timestamp(SPLIT, tz="UTC")
    for (rn, rf), (fn, ff), side, ex in itertools.product(rules.items(), FILTERS.items(), SIDES, EXITS):
        if rn.startswith(("hour_", "day_")) and not ex.startswith("stop2_hold"): continue  # calendar rules: time exits only
        tr, te, per = [], [], {}
        for sym, d in data.items():
            f = ff(d, side); sig = rf(d, side) & (f if isinstance(f, pd.Series) else True)
            r = run(d, sig.fillna(False), side, ex, sym)
            a = [x for x in r if x[0] < split]; b = [x for x in r if x[0] >= split]
            tr += a; te += b; per[sym] = stats(b)["net"]
        s1, s2 = stats(tr), stats(te)
        rows.append(dict(rule=rn, filter=fn, side=side, exit=ex, hunt_n=s1["n"], hunt_netR=s1["net"], hunt_t=s1["t"],
                         exam_n=s2["n"], exam_grossR=s2["gross"], exam_netR=s2["net"], exam_win=s2["win"], exam_t=s2["t"],
                         exam_symbols_up=sum(1 for v in per.values() if v == v and v > 0), symbols=len(per)))
    df = pd.DataFrame(rows); os.makedirs(OUT, exist_ok=True); df.to_csv(f"{OUT}/{KIND}_{TF}_patterns.csv", index=False)
    return data, df


def report(data, df):
    tested = len(df); ok = df[df.hunt_n >= (100 if TF != "1d" else 40)]
    top = ok.sort_values("hunt_t", ascending=False).head(15)
    passed = top[(top.hunt_t >= 2) & (top.exam_netR > 0) & (top.exam_t >= 2) & (top.exam_n >= 30) & (top.exam_symbols_up * 2 >= top.symbols)]
    first = min(d.index[0] for d in data.values()); last = max(d.index[-1] for d in data.values())
    bh = []
    for sym, d in data.items():
        a = d[d.index >= pd.Timestamp(SPLIT, tz="UTC")]
        if len(a): bh.append(f"{sym} {a.c.iloc[-1] / a.c.iloc[0] - 1:+.0%}")
    f = lambda x, p=3: "" if x != x else f"{x:+.{p}f}"
    L = [f"# {KIND.title()} pattern finder, {TF} bars ({dt.date.today()})", "",
         f"Data: {TF} bars, {first:%Y-%m-%d} to {last:%Y-%m-%d}, {len(data)} markets ({', '.join(data)}).",
         f"**Hunt** period: before {SPLIT}. **Exam** period: {SPLIT} on (never seen while hunting).",
         "Costs: " + ("0.30% per side (Alpaca crypto fee + slippage), long only (Alpaca can't short crypto)." if KIND == "crypto" else "typical retail spread + slippage per pair (EURUSD 1.2 pips), long and short."),
         f"Rules tested: {tested}. R = profit in units of the risk per trade (1R = the stop distance). Net = after costs.", "",
         f"## Result: {len(passed)} of the hunt's top 15 passed the exam", "",
         "Pass = strong on the hunt (t 2+), still positive after costs on the exam (t 2+), at least 30 exam trades, and making money in at least half the markets.",
         "Luck check: on fake random-walk data this finder still lets roughly 1 rule in 20 through by chance, so a PASS earns paper trading, never real money straight away.", "",
         "| # | Rule | Filter | Side | Exit | Hunt trades | Hunt net R | Hunt t | Exam trades | Exam gross R | Exam net R | Exam win % | Exam t | Markets up | Verdict |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, (_, r) in enumerate(top.iterrows(), 1):
        v = "**PASS**" if r.name in passed.index else ("lost on exam" if r.exam_netR <= 0 else "weak on hunt" if r.hunt_t < 2 else "too weak")
        L.append(f"| {k} | {r.rule} | {r['filter']} | {r.side} | {r.exit} | {r.hunt_n} | {f(r.hunt_netR)} | {f(r.hunt_t, 1)} | {r.exam_n} | {f(r.exam_grossR)} | {f(r.exam_netR)} | {r.exam_win:.0%} | {f(r.exam_t, 1)} | {r.exam_symbols_up}/{r.symbols} | {v} |")
    allx = df[df.exam_n >= 30]
    L += ["", "## Reality check", "",
          f"- Rules positive on the hunt (after costs): {(ok.hunt_netR > 0).sum()} of {len(ok)}.",
          f"- Of those, still positive on the exam: {((ok.hunt_netR > 0) & (ok.exam_netR > 0)).sum()}.",
          f"- Best exam result of ANY rule (pure hindsight, for comparison only): {f(allx.exam_netR.max())}R ({allx.loc[allx.exam_netR.idxmax(), 'rule'] if len(allx) else ''}). Picking from the exam itself is the curve-fitting trap.",
          f"- Average rule before costs on the exam: {f(allx.exam_grossR.mean())}R; after costs: {f(allx.exam_netR.mean())}R.",
          f"- Buy and hold over the exam period: {', '.join(bh)}.", ""]
    open(f"{OUT}/{KIND}_{TF}_patterns.md", "w").write("\n".join(L)); print("\n".join(L))


if __name__ == "__main__":
    report(*main())
