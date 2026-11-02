"""Options pattern finder (paper research only). Runs on GitHub Actions with the Alpaca keys.
Signals come from the underlying's 1-minute chart; each signal buys the at-the-money call (up) or put (down)
using REAL historical option prices from Alpaca, for two expirations: same day (0DTE) and about a week out.
Hunt period finds the best patterns, exam period (never seen while hunting) decides PASS / FAIL.
Usage: python options_lab.py [START YYYY-MM-DD] [END]      OPT_MOCK=1 runs on fake data (pipeline test only)."""
import os, sys, json, math, time, datetime as dt, urllib.request, urllib.parse, urllib.error
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd

ET = ZoneInfo("America/New_York")
BASE = os.environ.get("LAB_OUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "research")
CACHE = os.environ.get("OPT_CACHE", "/tmp/optcache")
MOCK = os.environ.get("OPT_MOCK") == "1"
ETFS = ["SPY", "QQQ"]
STOCKS = ["AAPL", "NVDA", "TSLA", "AMZN", "META", "MSFT", "AMD"]
UNDER = (os.environ.get("OPT_SYMBOLS") or ",".join(ETFS + STOCKS)).split(",")
START = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date(2024, 3, 1)   # Alpaca option history starts Feb 2024
END = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else dt.date.today() - dt.timedelta(days=1)
SPLIT = dt.date.fromisoformat(os.environ.get("OPT_SPLIT", "2025-07-01"))
EXIT_T = dt.time(15, 50)
# exits on the option premium: (stop loss %, profit target %); None target = hold to 3:50 PM
EXITS = {"stop50_tgt100": (0.50, 1.00), "stop30_tgt60": (0.30, 0.60), "stop50_hold_to_close": (0.50, None), "stop25_tgt50": (0.25, 0.50)}
API_CALLS = [0]


def half_spread(sym, prem):
    """assumed cost per side (half the bid/ask spread + fees). Conservative; live paper fills will check it."""
    return max(0.01, 0.01 * prem) + 0.003 if sym in ETFS else max(0.025, 0.025 * prem) + 0.003


# ---------- data
def _get(url):
    h = {"APCA-API-KEY-ID": os.environ.get("ALPACA_KEY", ""), "APCA-API-SECRET-KEY": os.environ.get("ALPACA_SECRET", "")}
    for k in range(6):
        try:
            API_CALLS[0] += 1
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60).read())
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(10 * (k + 1)); continue
            print(f"http {e.code} {url[:140]} {e.read()[:200]!r}", flush=True); return None
        except Exception as e:
            print(f"err {e} {url[:120]}", flush=True); time.sleep(3)
    return None


def _bars(path, params, key):
    out, tok = {}, None
    while True:
        q = dict(params, limit=10000)
        if tok: q["page_token"] = tok
        js = _get(f"https://data.alpaca.markets{path}?" + urllib.parse.urlencode(q))
        if js is None and not out and tok is None: return None
        if not js: break
        for s, bs in (js.get("bars") or {}).items(): out.setdefault(s, []).extend(bs)
        tok = js.get("next_page_token")
        if not tok: break
    return {s: pd.DataFrame(b).assign(t=lambda x: pd.to_datetime(x.t, utc=True).dt.tz_convert(ET)).set_index("t")[["o", "h", "l", "c", "v"]] for s, b in out.items() if b}


def stock_minutes(sym):
    f = f"{CACHE}/stk_{sym}_{START}_{END}.pkl"
    if os.path.exists(f): return pd.read_pickle(f)
    if MOCK: d = mock_stock(sym)
    else:
        parts = []
        for a in pd.date_range(START, END, freq="90D"):
            b = min(a.date() + dt.timedelta(days=89), END)
            r = _bars("/v2/stocks/bars", dict(symbols=sym, timeframe="1Min", start=f"{a.date()}T00:00:00Z", end=f"{b}T23:59:00Z", feed="sip", adjustment="raw"), sym)
            if r and sym in r: parts.append(r[sym])
        d = pd.concat(parts) if parts else pd.DataFrame(columns=["o", "h", "l", "c", "v"])
    d = d[~d.index.duplicated()].sort_index(); d = d[(d.index.time >= dt.time(9, 30)) & (d.index.time < dt.time(16, 0))]
    os.makedirs(CACHE, exist_ok=True); d.to_pickle(f); return d


def occ(u, exp, cp, k): return f"{u}{exp:%y%m%d}{cp}{int(round(k * 1000)):08d}"


def strikes_near(u, px):
    steps = [1.0] if u in ETFS else [1.0, 2.5, 5.0]
    ks = set()
    for s in steps:
        base = round(px / s) * s
        ks |= {round(base + i * s, 2) for i in (-1, 0, 1)}
    return sorted(ks, key=lambda k: abs(k - px))


def expiries(u, day):
    """0DTE = today (if it lists); weekly = the Friday 5-11 days out (Thursday if Friday is a holiday is skipped: no bars)"""
    fri = day + dt.timedelta(days=(4 - day.weekday()) % 7)
    wk = fri if (fri - day).days >= 5 else fri + dt.timedelta(days=7)
    return {"0dte": day, "weekly": wk}


def option_minutes(syms, day):
    syms = sorted(set(syms))
    f = f"{CACHE}/opt_{day}_{abs(hash(tuple(syms))) % 10**10}.pkl"
    if os.path.exists(f): return pd.read_pickle(f)
    if MOCK: r = mock_options(syms, day)
    else:
        r = {}
        def grab(chunk, depth=0):   # a bad symbol in a batch can fail the whole request: split and retry
            got = _bars("/v1beta1/options/bars", dict(symbols=",".join(chunk), timeframe="1Min", start=f"{day}T13:00:00Z", end=f"{day}T21:00:00Z"), None)
            if got is None and len(chunk) > 1 and depth < 3:
                for j in range(0, len(chunk), max(1, len(chunk) // 4)): grab(chunk[j:j + max(1, len(chunk) // 4)], depth + 1)
            elif got: r.update(got)
        for i in range(0, len(syms), 80): grab(syms[i:i + 80])
    pd.to_pickle(r, f); return r


# ---------- signals on the underlying (first signal per pattern per day). Returns [(pattern, bar_index, +1 call / -1 put)]
def day_signals(d, prev_close, etf):
    out = []; o, h, l, c, v = (d[k].values for k in ("o", "h", "l", "c", "v")); tm = [x.time() for x in d.index]
    if len(d) < 60 or not prev_close: return out
    tp = (h + l + c) / 3; vw = np.cumsum(tp * v) / np.maximum(np.cumsum(v), 1)
    gap = o[0] / prev_close - 1; g_small, g_big = (0.004, 0.015) if etf else (0.015, 0.04)
    def first(name, cond_fn, t0, t1):
        for i in range(len(d)):
            if t0 <= tm[i] <= t1:
                s = cond_fn(i)
                if s: out.append((name, i, s)); return
    for n in (15, 30):
        hi, lo = h[:n].max(), l[:n].min()
        first(f"orb{n}", lambda i, hi=hi, lo=lo, n=n: (1 if c[i] > hi and c[:i].max() <= hi else -1 if c[i] < lo and c[:i].min() >= lo else 0) if i >= n else 0, (dt.datetime(2000, 1, 1, 9, 30) + dt.timedelta(minutes=n)).time(), dt.time(11, 30))
    first("vwap_cross_after_1030", lambda i: (1 if c[i] > vw[i] and c[i - 1] <= vw[i - 1] else -1 if c[i] < vw[i] and c[i - 1] >= vw[i - 1] else 0), dt.time(10, 30), dt.time(14, 30))
    if abs(gap) >= g_small:
        sg = 1 if gap > 0 else -1
        first("gap_and_go", lambda i: sg if ((c[i] > o[0] and c[i] >= h[:i + 1].max()) if sg > 0 else (c[i] < o[0] and c[i] <= l[:i + 1].min())) else 0, dt.time(9, 35), dt.time(10, 0))
        first("gap_fade", lambda i: -sg if sg * (c[i] - o[0]) < 0 and sg * (c[:i] - o[0]).min() >= 0 else 0, dt.time(9, 35), dt.time(10, 30))
    if abs(gap) >= g_big:   # earnings-size gap (the Oct 30 Intel/Amazon type day)
        sg = 1 if gap > 0 else -1
        first("big_gap_follow", lambda i: sg if sg * (c[i] - o[0]) > 0 else 0, dt.time(9, 35), dt.time(9, 45))
        first("big_gap_bounce", lambda i: -sg if sg * (c[i] - o[0]) < 0 and i >= 15 else 0, dt.time(9, 45), dt.time(10, 30))
    for name, t in (("trend_at_2pm", dt.time(14, 0)), ("power_hour_3pm", dt.time(15, 0))):
        first(name, lambda i: (1 if c[i] > o[0] and c[i] > vw[i] else -1 if c[i] < o[0] and c[i] < vw[i] else 0), t, t)
    return out


# ---------- trade one option contract from its minute bars
def trade(ob, sig_time, sym_u, exit_plan):
    stop, tgt = EXITS[exit_plan]
    after = ob[ob.index > sig_time]
    if after.empty or (after.index[0] - sig_time) > pd.Timedelta(minutes=3): return None   # no trade within 3 min: can't assume a fill
    e0 = float(after.o.iloc[0]);
    if e0 < 0.10: return None
    e = e0 + half_spread(sym_u, e0); s_px = e * (1 - stop); t_px = e * (1 + tgt) if tgt else None
    live = after[after.index.time < EXIT_T]
    if live.empty: return None
    lo, hi, op = live.l.values, live.h.values, live.o.values
    hs = np.flatnonzero(lo <= s_px); ht = np.flatnonzero(hi >= t_px) if t_px else np.array([], int)
    js, jt = (hs[0] if len(hs) else 10**9), (ht[0] if len(ht) else 10**9)
    if js == jt == 10**9: ex, why = float(live.c.iloc[-1]), "close"
    elif js <= jt: ex, why = min(s_px, float(op[js])), "stop"          # stop wins a same-bar tie
    else: ex, why = t_px, "target"
    ex = max(0.0, ex - half_spread(sym_u, ex))
    return dict(entry=e, exit_px=ex, ret=ex / e - 1, why=why)


def main():
    rows = []; t0 = time.time()
    for u in UNDER:
        d = stock_minutes(u)
        if d.empty: print(f"{u}: no stock data", flush=True); continue
        byday = {k: g for k, g in d.groupby(d.index.date)}; days = sorted(byday); closes = pd.Series({k: float(g.c.iloc[-1]) for k, g in byday.items()})
        n0 = len(rows)
        print(f"{u}: {len(days)} days of minute bars ({API_CALLS[0]} api calls, {time.time() - t0:.0f}s)", flush=True)
        for k, day in enumerate(days[1:], 1):
            dd = byday[day]; sigs = day_signals(dd, float(closes.iloc[k - 1]), u in ETFS)
            if not sigs: continue
            ex = expiries(u, day); want = {}
            for pat, i, s in sigs:
                px = float(dd.c.iloc[i]); cp = "C" if s > 0 else "P"
                for en, e in ex.items():
                    want[(pat, en)] = [occ(u, e, cp, kk) for kk in strikes_near(u, px)]
            ob = option_minutes([x for v in want.values() for x in v], day)
            for pat, i, s in sigs:
                st = dd.index[i]; px = float(dd.c.iloc[i])
                for en in ex:
                    cand = [x for x in want[(pat, en)] if x in ob and len(ob[x])]
                    if not cand: continue
                    sym = cand[0]   # nearest-to-the-money strike that actually traded
                    for xp in EXITS:
                        r = trade(ob[sym], st, u, xp)
                        if r: rows.append(dict(date=str(day), under=u, kind="etf" if u in ETFS else "stock", pattern=pat, side="call" if s > 0 else "put",
                                               expiry=en, exit=xp, contract=sym, sig_time=f"{st:%H:%M}", under_px=px, **r))
        print(f"{u}: {len(rows) - n0} simulated option trades", flush=True)
    os.makedirs(BASE, exist_ok=True)
    df = pd.DataFrame(rows); df.to_csv(f"{BASE}/options_trades.csv.gz", index=False)
    report(df); print(f"done: {len(df)} simulated trades, {API_CALLS[0]} api calls, {time.time() - t0:.0f}s")


def st_(x):
    if len(x) < 2: return dict(n=len(x), ret=x.mean() if len(x) else np.nan, win=np.nan, t=np.nan)
    return dict(n=len(x), ret=x.mean(), win=(x > 0).mean(), t=x.mean() / (x.std(ddof=1) / math.sqrt(len(x))) if x.std(ddof=1) > 0 else np.nan)


def report(df):
    L = [f"# Options pattern finder ({dt.date.today()})", "",
         f"Underlyings: {', '.join(UNDER)}. Period {START} to {END}. **Hunt** before {SPLIT}, **exam** from {SPLIT} (never seen while hunting).",
         "Every signal buys the nearest at-the-money call (up) or put (down), at real Alpaca historical option prices, entry the next minute.",
         "Costs: assumed half-spread + fees each side (ETFs 1% of premium, min $0.01; stocks 2.5%, min $0.025). Day trades only: out by 3:50 PM.",
         "Return = % gained or lost on the premium paid, after costs.", ""]
    if df.empty: open(f"{BASE}/options_patterns.md", "w").write("\n".join(L + ["No trades simulated (data problem: check the job log)."])); return
    df["exam"] = pd.to_datetime(df.date).dt.date >= SPLIT; res = []
    for keys, g in df.groupby(["kind", "pattern", "expiry", "exit"]):
        a, b = st_(g[~g.exam].ret), st_(g[g.exam].ret)
        res.append(dict(zip(["kind", "pattern", "expiry", "exit"], keys), hn=a["n"], hr=a["ret"], ht=a["t"], en=b["n"], er=b["ret"], ew=b["win"], et=b["t"]))
    r = pd.DataFrame(res); r.to_csv(f"{BASE}/options_patterns.csv", index=False)
    top = r[r.hn >= 40].sort_values("ht", ascending=False).head(15)
    ok = top[(top.ht >= 2) & (top.er > 0) & (top.et >= 2) & (top.en >= 30)]
    f = lambda x, p=1: "" if x != x else f"{x:+.{p}%}" if p == 1 else f"{x:+.1f}"
    L += [f"## Result: {len(ok)} of the hunt's top 15 passed the exam", "", "Pass = strong on the hunt (t 2+), still positive after costs on the exam (t 2+), at least 30 exam trades.",
          "Engine check: on fake random-walk prices (fairly priced options) the average trade loses about the trading costs, as it should. Exits on the same signal are not independent, so one lucky signal can show up several times: treat a PASS as worth paper trading, nothing more.", "",
          "| # | ETF/stock | Pattern | Expiry | Exit | Hunt trades | Hunt avg | Hunt t | Exam trades | Exam avg | Exam win % | Exam t | Verdict |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, (i, x) in enumerate(top.iterrows(), 1):
        v = "**PASS**" if i in ok.index else ("lost on exam" if not x.er > 0 else "weak on hunt" if x.ht < 2 else "too weak")
        L.append(f"| {k} | {x.kind} | {x.pattern} | {x.expiry} | {x.exit} | {x.hn} | {f(x.hr)} | {f(x.ht, 0)} | {x.en} | {f(x.er)} | {'' if x.ew != x.ew else f'{x.ew:.0%}'} | {f(x.et, 0)} | {v} |")
    L += ["", "## 0DTE vs weekly (all patterns, exam period)", "", "| Expiry | Trades | Avg return | Win % |", "|---|---|---|---|"]
    for en, g in df[df.exam].groupby("expiry"): L.append(f"| {en} | {len(g)} | {g.ret.mean():+.1%} | {(g.ret > 0).mean():.0%} |")
    big = df[df.pattern.str.startswith("big_gap") & df.exam]
    if len(big):
        L += ["", "## Earnings-size gaps (like Oct 30: Intel, Amazon)", "", "| Pattern | Expiry | Trades | Avg return | Win % |", "|---|---|---|---|---|"]
        for (p, en), g in big[big.exit == "stop50_hold_to_close"].groupby(["pattern", "expiry"]): L.append(f"| {p} | {en} | {len(g)} | {g.ret.mean():+.1%} | {(g.ret > 0).mean():.0%} |")
    L += ["", f"Best exam result of ANY combo (hindsight only, not a pick): {f(r[r.en >= 30].er.max())}."]
    open(f"{BASE}/options_patterns.md", "w").write("\n".join(L)); print("\n".join(L))


# ---------- fake data for a pipeline test (no API, no meaning)
def mock_stock(sym):
    rng = np.random.default_rng(abs(hash(sym)) % 2**32); out = []
    px = 500.0 if sym in ETFS else 150.0
    for day in pd.bdate_range(START, END):
        idx = pd.date_range(f"{day.date()} 09:30", periods=390, freq="1min", tz=ET)
        r = rng.normal(0, 0.0007, 390); r[0] += rng.normal(0, 0.006); c = px * np.exp(np.cumsum(r))
        o = np.r_[px * np.exp(r[0]), c[:-1]]; hi = np.maximum(o, c) * 1.0003; lo = np.minimum(o, c) * 0.9997
        out.append(pd.DataFrame(dict(o=o, h=hi, l=lo, c=c, v=rng.integers(1e4, 1e5, 390)), index=idx)); px = c[-1]
    return pd.concat(out)


def mock_options(syms, day):
    u = syms[0][:len(syms[0]) - 15]; d = mock_stock(u); d = d[d.index.date == day]; out = {}
    for s in syms:
        k = int(s[-8:]) / 1000; cp = s[-9]; exp = dt.datetime.strptime(s[-15:-9], "%y%m%d").date()
        if (k * 100) % 100 not in (0,) and u in ETFS: continue
        T = np.maximum(((exp - day).days * 390 + 390 - np.arange(len(d))) / (390 * 252), 1e-6); S = d.c.values; vol = 0.0007 * math.sqrt(390 * 252)
        from scipy.stats import norm
        d1 = (np.log(S / k) + 0.5 * vol ** 2 * T) / (vol * np.sqrt(T)); d2 = d1 - vol * np.sqrt(T)
        p = S * norm.cdf(d1) - k * norm.cdf(d2) if cp == "C" else k * norm.cdf(-d2) - S * norm.cdf(-d1)
        po = np.r_[p[0], p[:-1]]
        out[s] = pd.DataFrame(dict(o=po, h=np.maximum(po, p) * 1.003, l=np.minimum(po, p) * 0.997, c=p, v=10), index=d.index)
    return out


if __name__ == "__main__":
    main()
