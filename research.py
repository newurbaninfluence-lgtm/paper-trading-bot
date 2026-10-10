"""Research job: backtest every strategy on years of real minute data, learn a trade filter, decide which
strategies stay on, and work out what it takes to reach $20/day.

No look-ahead: candidates are picked each morning only from what was knowable at the open (gap vs prior close,
prior 20-day volume, news in the 24h before the open). Same strategy code, fills, slippage and trade
management as the live bot (core.py).

Usage: python research.py run [days]      -> backtest last N trading days (default 500) + model + status + plan
       python research.py analyze         -> rebuild model/status/plan from existing research/signals_bt.csv
Needs ALPACA_KEY / ALPACA_SECRET (free paper account is enough)."""
import os, sys, json, time, math, datetime as dt, urllib.request, urllib.parse, urllib.error
from multiprocessing import Pool
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import ET, RISKPCT, add_ind, STRATS, WINDOWS, MINCHG, valid_risk, features, simulate, NUM, slip, variant_cols, ENTRIES, PLANS

BASE = os.path.dirname(os.path.abspath(__file__)); OUT = f"{BASE}/research"
DATA = "https://data.alpaca.markets"; TRADE = "https://paper-api.alpaca.markets"
H = {"APCA-API-KEY-ID": os.environ.get("ALPACA_KEY", ""), "APCA-API-SECRET-KEY": os.environ.get("ALPACA_SECRET", "")}
ACCOUNTS = None  # filled from bot.py at runtime
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "research")
BT = os.path.join(OUT_DIR, "signals_bt_v2.csv")      # v2 adds entry/exit variants; v1 kept for reference
NEG_WORDS = ("offering", "priced at", "dilut", "reverse split", "registered direct", "at-the-market", "delist", "bankrupt")
_last = [0.0]


def log(m):
    print(f"{dt.datetime.now(ET):%H:%M:%S} {m}", flush=True)


def get(base, path, params):
    """rate-limited GET (free plan: 200 req/min) with retries"""
    url = f"{base}{path}?{urllib.parse.urlencode(params)}"
    for attempt in range(6):
        wait = 0.32 - (time.time() - _last[0])
        if wait > 0: time.sleep(wait)
        _last[0] = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500: time.sleep(3 * (attempt + 1)); continue
            log(f"HTTP {e.code} {path} {e.read()[:150]!r}"); return None
        except Exception as e:
            log(f"net error {path} {e}"); time.sleep(3)
    return None


def paged(path, params, key):
    out, tok = ({} if key == "bars" else []), None
    while True:
        p = dict(params)
        if tok: p["page_token"] = tok
        js = get(DATA, path, p)
        if not js: break
        part = js.get(key) or ({} if key == "bars" else [])
        if key == "bars":
            for s, rows in part.items(): out.setdefault(s, []).extend(rows)
        else: out.extend(part)
        tok = js.get("next_page_token")
        if not tok: break
    return out


def iso(d, t="00:00"):
    return dt.datetime.combine(d, dt.time.fromisoformat(t), ET).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- step 1: universe + daily bars
def universe():
    js = get(TRADE, "/v2/assets", dict(status="active", asset_class="us_equity")) or []
    syms = [a["symbol"] for a in js if a.get("tradable") and a.get("exchange") in ("NYSE", "NASDAQ", "AMEX", "ARCA", "BATS")
            and a["symbol"].isalpha() and len(a["symbol"]) <= 5]
    return sorted(set(syms))


def daily_bars(syms, start, end):
    rows = []
    for i in range(0, len(syms), 200):
        chunk = syms[i:i + 200]
        bars = paged("/v2/stocks/bars", dict(symbols=",".join(chunk), timeframe="1Day", start=iso(start), end=iso(end, "23:59"),
                                            limit=10000, adjustment="split", feed="sip"), "bars")
        for s, bs in bars.items():
            for b in bs: rows.append((s, b["t"][:10], b["o"], b["h"], b["l"], b["c"], b["v"]))
        if i % 2000 == 0: log(f"daily bars {i}/{len(syms)}")
    df = pd.DataFrame(rows, columns=["sym", "date", "o", "h", "l", "c", "v"])
    df["date"] = pd.to_datetime(df.date).dt.date
    return df.sort_values(["sym", "date"])


def candidates(daily, per_day=15):
    d = daily.copy()
    g = d.groupby("sym")
    d["pc"] = g.c.shift(1); d["adv"] = g.v.transform(lambda v: v.shift(1).rolling(20, min_periods=10).mean())
    d["next_open"] = g.o.shift(-1)
    d["gap"] = d.o / d.pc - 1
    d = d[(d.gap >= 0.03) & (d.o >= 1) & (d.o <= 100) & (d.adv >= 300_000) & (d.adv * d.pc >= 2_000_000)]
    return d.sort_values(["date", "gap"], ascending=[True, False]).groupby("date").head(per_day)


# ---------- step 2: per-day minute bars + news, then simulate every strategy
def minute_bars(syms, day):
    bars = paged("/v2/stocks/bars", dict(symbols=",".join(syms), timeframe="1Min", start=iso(day, "04:00"), end=iso(day, "16:00"),
                                        limit=10000, adjustment="split", feed="sip"), "bars")
    out = {}
    for s, bs in bars.items():
        df = pd.DataFrame(bs)
        if df.empty: continue
        df.index = pd.to_datetime(df.t).dt.tz_convert(ET)
        out[s] = df.rename(columns=dict(o="Open", h="High", l="Low", c="Close", v="Volume"))[["Open", "High", "Low", "Close", "Volume"]]
    return out


def news_before_open(syms, day):
    """headlines in the 24h before the open (what the live scanner would have seen)"""
    items = paged("/v1beta1/news", dict(symbols=",".join(syms), start=iso(day - dt.timedelta(days=1), "09:30"), end=iso(day, "09:30"),
                                       limit=50, sort="desc"), "news")
    cat = {}
    for n in items:
        h = n.get("headline", "")
        for s in n.get("symbols", []):
            if s not in syms: continue
            if any(w in h.lower() for w in NEG_WORDS): cat[s] = "NEG:" + h
            elif s not in cat: cat[s] = h
    return cat


def sim_symbol_day(args):
    sym, day, mb, pc, adv, next_open, spy, cat, spy_pc = args
    if mb is None or mb.empty or not pc: return []
    rth = mb.between_time("09:30", "15:59")
    if len(rth) < 30: return []
    rth = add_ind(rth); pm = mb[mb.index.time < dt.time(9, 30)]
    spy_close = spy.Close if spy is not None and len(spy) else None
    closes = rth.Close.values; times = [ (ts + pd.Timedelta(minutes=1)).time() for ts in rth.index ]
    neg = bool(cat) and cat.startswith("NEG:")
    rows = []
    for strat, fn in STRATS.items():
        w0, w1 = WINDOWS[strat]
        for i in range(len(rth) - 1):
            now = times[i]
            if now < w0: continue
            if now > w1: break
            chg = closes[i] / pc - 1
            if chg < MINCHG[strat]: continue
            d = rth.iloc[:i + 1]
            sig = fn(d, pm, chg, now)
            if not sig: continue
            stop = round(sig[0], 2)
            if not valid_risk(closes[i], stop): continue
            sc = 0.0
            if spy_close is not None:
                sp = spy_close[spy_close.index <= rth.index[i]]
                if len(sp) and spy_pc: sc = float(sp.iloc[-1]) / spy_pc - 1
            f = features(strat, d, pm, chg, now, pc, adv, sc, cat, stop)
            out = simulate(rth, i, stop, strat, next_open)
            if out:
                rows.append(dict(date=str(day), time=f"{now:%H:%M}", ticker=sym, stop=stop, R=round(out["R"], 4), why=out["why"],
                                 entry=round(out["entry"], 4), has_news=int(bool(cat)), neg_news=int(neg), **f,
                                 **variant_cols(rth, i, stop, strat, next_open)))
            break  # first signal of the day per strategy per symbol (same as live logger)
    return rows


def backtest(n_days):
    os.makedirs(OUT, exist_ok=True)
    end = dt.datetime.now(ET).date() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=int(n_days * 1.46) + 40)
    syms = universe(); log(f"universe: {len(syms)} symbols")
    daily = daily_bars(syms + ["SPY"], start, end); log(f"daily rows: {len(daily)}")
    cands = candidates(daily[daily.sym != "SPY"])
    sd = daily[daily.sym == "SPY"].sort_values("date"); spy_prev = dict(zip(sd.date, sd.c.shift(1)))
    days = sorted(cands.date.unique())[-n_days:]
    log(f"{len(days)} trading days, {len(cands[cands.date.isin(days)])} candidate symbol-days")
    path = BT
    done = set(pd.read_csv(path).date.astype(str)) if os.path.exists(path) else set()
    pool = Pool(max(os.cpu_count() or 2, 2)); t0 = time.time()
    for k, day in enumerate(days):
        if str(day) in done: continue
        c = cands[cands.date == day]; syms_d = list(c.sym)
        mb = minute_bars(syms_d + ["SPY"], day)
        spy = mb.get("SPY"); spy_rth = spy.between_time("09:30", "15:59") if spy is not None else None
        cat = news_before_open(syms_d, day)
        spy_pc = spy_prev.get(day)
        tasks = [(r.sym, day, mb.get(r.sym), r.pc, r.adv, r.next_open if r.next_open == r.next_open else None, spy_rth, cat.get(r.sym), spy_pc) for r in c.itertuples()]
        rows = [x for part in pool.map(sim_symbol_day, tasks) for x in part]
        if rows:
            out = pd.DataFrame(rows)
            if os.path.exists(path): out = out.reindex(columns=list(pd.read_csv(path, nrows=0).columns))  # never misalign columns
            out.to_csv(path, mode="a", header=not os.path.exists(path), index=False)
        if k % 10 == 0: log(f"day {k + 1}/{len(days)} {day}: {len(rows)} signals ({time.time() - t0:.0f}s)")
        if os.environ.get("MAX_MINUTES") and time.time() - t0 > 60 * float(os.environ["MAX_MINUTES"]):
            log("time budget reached, saving partial results"); break
    pool.close()


# ---------- step 2b: measure real trading costs from SIP quotes at the moment of entry
def spread_at(sym, ts, secs=20):
    """median quoted spread (ask-bid)/mid in the first `secs` seconds from ts (ET minute) on the SIP feed"""
    js = get(DATA, "/v2/stocks/quotes", dict(symbols=sym, start=ts.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             end=(ts + dt.timedelta(seconds=secs)).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), feed="sip", limit=1000))
    q = ((js or {}).get("quotes") or {}).get(sym) or []
    sp = [(x["ap"] - x["bp"]) / ((x["ap"] + x["bp"]) / 2) for x in q if x.get("bp", 0) > 0 and x.get("ap", 0) > x.get("bp", 0)]
    return (float(np.median(sp)), len(sp)) if sp else (None, 0)


PRICE_BANDS = [0, 5, 10, 20, 50, 1e6]; PRICE_LABELS = ["under $5", "$5-10", "$10-20", "$20-50", "$50+"]


def measure_costs(n=1500):
    df = pd.read_csv(BT if os.path.exists(BT) else f"{OUT}/signals_bt.csv", low_memory=False)
    df = df.sample(min(n, len(df)), random_state=7)
    rows = []
    for k, r in enumerate(df.itertuples()):
        ts = dt.datetime.combine(dt.date.fromisoformat(str(r.date)), dt.time.fromisoformat(r.time), ET)
        sp, nq = spread_at(r.ticker, ts)
        rows.append(dict(date=r.date, time=r.time, ticker=r.ticker, strategy=r.strategy, entry=r.entry, spread_pct=sp, quotes=nq))
        if k % 200 == 0: log(f"spreads {k}/{len(df)}")
    sp = pd.DataFrame(rows); sp.to_csv(f"{OUT}/spreads.csv", index=False)
    sp = sp.dropna(subset=["spread_pct"]); sp["band"] = pd.cut(sp.entry, PRICE_BANDS, labels=PRICE_LABELS)
    summary = {str(k): dict(n=int(len(g)), median=round(float(g.spread_pct.median()), 5), p75=round(float(g.spread_pct.quantile(0.75)), 5))
               for k, g in sp.groupby("band", observed=True)}
    json.dump(dict(measured=str(dt.date.today()), bands=summary), open(f"{OUT}/costs.json", "w"), indent=1)
    log(f"costs: {summary}")


COST_MODELS = ("bot", "spread_med", "spread_p75")


def cost_per_side(px, model, costs):
    """$ cost of one market-order side. bot = the bot's slip() (2c or 0.15%); spread_med / spread_p75 = half of the
    measured SIP quoted spread at entry time (typical / worse-than-typical)"""
    if model == "bot" or not costs: return np.maximum(0.02, 0.0015 * px)
    b = pd.cut(px, PRICE_BANDS, labels=PRICE_LABELS).astype(str)
    pct = b.map({k: v["median" if model == "spread_med" else "p75"] for k, v in costs["bands"].items()}).astype(float).fillna(0.005)
    return np.maximum(0.005, pct / 2 * px)


def variant_table(df):
    """net R of every strategy x entry x plan under both cost models"""
    try: costs = json.load(open(f"{OUT}/costs.json"))
    except Exception: costs = None
    out = []
    for e in ENTRIES:
        for p in PLANS:
            k = f"{e}_{p}"
            if f"Rg_{k}" not in df: continue
            sub = df.dropna(subset=[f"Rg_{k}"])
            for model in (COST_MODELS if costs else ["bot"]):
                net = sub[f"Rg_{k}"] - sub[f"cu_{k}"] * cost_per_side(sub[f"px_{k}"], model, costs) / sub[f"rk_{k}"]
                for strat, g in net.groupby(sub.strategy):
                    st = stats(g); half = len(g) // 2
                    out.append(dict(strategy=strat, entry=e, plan=p, costs=model, n=st["n"], gross=round(sub.loc[g.index, f"Rg_{k}"].mean(), 3),
                                    net=st["avgR"], t=st["t"], first_half=round(g.iloc[:half].mean(), 3), second_half=round(g.iloc[half:].mean(), 3),
                                    fill_rate=round(len(sub[sub.strategy == strat]) / max(1, (df.strategy == strat).sum()), 2)))
    return pd.DataFrame(out), costs


# ---------- step 3: analysis
def stats(r):
    r = r.dropna()
    n = len(r)
    if n == 0: return dict(n=0)
    trim = r[r <= r.quantile(0.99)] if n >= 100 else r
    sd = r.std(ddof=1) if n > 1 else float("nan")
    return dict(n=n, win=round((r > 0).mean(), 3), avgR=round(r.mean(), 3), avgR_trim=round(trim.mean(), 3),
                t=round(r.mean() / (sd / math.sqrt(n)), 2) if sd and sd == sd and sd > 0 else 0.0,
                pf=round(r[r > 0].sum() / -r[r < 0].sum(), 2) if (r < 0).any() else float("inf"))


def scorecard(df):
    rows = []
    for s, g in df.groupby("strategy"):
        g = g.sort_values("date"); half = len(g) // 2
        st = stats(g.R); st.update(strategy=s, first_half=round(g.R.iloc[:half].mean(), 3), second_half=round(g.R.iloc[half:].mean(), 3),
                                   news_only=round(g[g.has_news == 1].R.mean(), 3), per_day=round(len(g) / max(df.date.nunique(), 1), 2))
        rows.append(st)
    return pd.DataFrame(rows).sort_values("avgR_trim", ascending=False)


def train_filter(df):
    """walk-forward logistic regression: learn P(trade wins) from conditions; enable only if it helps out of sample"""
    from sklearn.linear_model import LogisticRegression
    d = df.dropna(subset=["R"]).sort_values(["date", "time"]).copy()
    strats = sorted(d.strategy.unique())
    if len(d) < 400: return {"enabled": False, "reason": f"only {len(d)} signals"}
    X = d[NUM].astype(float).fillna(0).values
    mean, std = X.mean(0), X.std(0); std[std == 0] = 1
    Z = np.hstack([(X - mean) / std, np.array([[1.0 if s == k else 0.0 for k in strats] for s in d.strategy])])
    y = (d.R.values > 0).astype(int); cut = int(len(d) * 0.7)
    m = LogisticRegression(max_iter=2000, C=0.5).fit(Z[:cut], y[:cut])
    p_tr, p_te = m.predict_proba(Z[:cut])[:, 1], m.predict_proba(Z[cut:])[:, 1]
    R_tr, R_te = d.R.values[:cut], d.R.values[cut:]
    best = (None, -9)
    for q in np.arange(0.0, 0.71, 0.05):
        thr = np.quantile(p_tr, q); keep = p_tr >= thr
        if keep.sum() >= 0.3 * len(p_tr) and R_tr[keep].mean() > best[1]: best = (float(thr), float(R_tr[keep].mean()))
    thr = best[0]; keep_te = p_te >= thr
    base_te, filt_te = float(R_te.mean()), float(R_te[keep_te].mean()) if keep_te.sum() else float("nan")
    enabled = bool(keep_te.sum() >= 50 and filt_te > base_te + 0.03 and filt_te > 0)
    full = LogisticRegression(max_iter=2000, C=0.5).fit(Z, y)  # refit on all data for live use
    p_all = full.predict_proba(Z)[:, 1]
    return dict(enabled=enabled, threshold=thr, threshold_hi=float(np.quantile(p_all[p_all >= thr], 0.5)) if (p_all >= thr).any() else thr,
                num=NUM, mean=mean.tolist(), std=std.tolist(), strats=strats, coef=full.coef_[0].tolist(), intercept=float(full.intercept_[0]),
                test=dict(n=int(len(R_te)), avgR_all=round(base_te, 3), avgR_kept=round(filt_te, 3), kept=int(keep_te.sum())),
                top_features=sorted(zip(NUM + strats, full.coef_[0].round(3).tolist()), key=lambda x: -abs(x[1]))[:10])


def decide_status(sc, live_path):
    status, why = {}, {}
    live = pd.read_csv(live_path).dropna(subset=["R"]) if os.path.exists(live_path) else pd.DataFrame()
    for r in sc.itertuples():
        if r.n < 100: s, w = "probation", f"only {r.n} backtest trades"
        elif r.avgR_trim > 0 and r.t >= 1.0 and r.second_half > 0: s, w = "on", f"{r.avgR_trim:+.2f}R/trade, t={r.t}, holds up in recent half"
        elif r.avgR < 0 and r.t <= -1.0: s, w = "off", f"loses {r.avgR:+.2f}R/trade over {r.n} trades"
        else: s, w = "probation", f"unproven ({r.avgR_trim:+.2f}R, t={r.t}); half size"
        if len(live):
            lg = live[live.strategy == r.strategy].tail(50)
            if len(lg) >= 30 and lg.R.mean() < -0.15: s, w = "off", f"decay: last {len(lg)} live signals avg {lg.R.mean():+.2f}R"
        status[r.strategy], why[r.strategy] = s, w
    return dict(status=status, why=why, updated=str(dt.date.today()))


def plan(df, status, model):
    """simulate the 6 accounts (1 trade/day each, price cap, strategy on/off, filter) over the backtest -> $/day"""
    import bot; accts = bot.ACCOUNTS
    from core import model_score
    d = df.dropna(subset=["R"]).copy(); d["px"] = np.exp(d.log_price)
    res = []
    for acct, strats in accts.items():
        pnl = []
        for day, g in d.groupby("date"):
            g = g[g.strategy.isin(strats) & (g.px <= acct / 10)]
            g = g[g.strategy.map(lambda s: status.get(s, "on") != "off")]
            if model.get("enabled"):
                g = g[[model_score(model, r) >= model["threshold"] for r in g.to_dict("records")]]
            if not len(g): pnl.append(0.0); continue
            t = g.sort_values("time").iloc[0]
            size = 0.5 if status.get(t.strategy) == "probation" else 1.0
            pnl.append(t.R * acct * RISKPCT * size)
        pnl = np.array(pnl); res.append(dict(account=acct, per_day=round(pnl.mean(), 2), trade_days=int((pnl != 0).sum()), days=len(pnl),
                                             worst_day=round(pnl.min(), 2), total=round(pnl.sum(), 2)))
    r = pd.DataFrame(res); per_day = r.per_day.sum()
    scale = 20 / per_day if per_day > 0 else None
    return r, per_day, scale


def analyze():
    df = pd.read_csv(BT if os.path.exists(BT) else f"{OUT}/signals_bt.csv", low_memory=False); df["date"] = df.date.astype(str)
    df = df[(df.entry - df.stop) >= np.maximum(0.01, 0.002 * df.entry)]  # drop fills that gapped through the stop
    live_path = f"{BASE}/signals.csv"
    sc = scorecard(df); model = train_filter(df); st = decide_status(sc, live_path)
    json.dump(model, open(f"{BASE}/model.json", "w"), indent=1); json.dump(st, open(f"{BASE}/strategy_status.json", "w"), indent=1)
    acc, per_day, scale = plan(df, st["status"], model)
    allR = stats(df.R)
    L = [f"# Research scorecard ({dt.date.today()})", "",
         f"Backtest: {df.date.nunique()} trading days ({df.date.min()} to {df.date.max()}), {len(df)} signals across {df.ticker.nunique()} stocks. "
         "Same rules, fills and slippage as the live bot; candidates picked only from what was known at the open.", "",
         f"All signals together: {allR['avgR']:+.3f}R per trade, win rate {allR['win']:.0%}, t={allR['t']}.", "",
         "## Strategies, best to worst", "", "| Strategy | Trades | Per day | Win % | Avg R | Avg R (top 1% removed) | t | 1st half | 2nd half | With news | Status |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in sc.itertuples():
        L.append(f"| {r.strategy} | {r.n} | {r.per_day} | {r.win:.0%} | {r.avgR:+.3f} | {r.avgR_trim:+.3f} | {r.t} | {r.first_half:+.3f} | {r.second_half:+.3f} | {r.news_only:+.3f} | **{st['status'][r.strategy]}**: {st['why'][r.strategy]} |")
    L += ["", "t above 2 means the edge is very unlikely to be luck; between 1 and 2 is promising; below 1 is noise.", "",
          "## Trade filter (learned from conditions)", ""]
    if model.get("test"):
        t = model["test"]
        L += [f"Tested on the most recent 30% of data it never saw: all signals {t['avgR_all']:+.3f}R vs filtered {t['avgR_kept']:+.3f}R ({t['kept']} of {t['n']} kept). "
              f"Filter is **{'ON' if model['enabled'] else 'OFF (did not beat taking everything)'}**.", "",
              "Conditions that matter most (positive = helps, negative = hurts): " + ", ".join(f"{k} {v:+.2f}" for k, v in model["top_features"]), ""]
    else: L += [f"Not trained: {model.get('reason')}", ""]
    risk = df.entry - df.stop; df["costR"] = 2 * np.maximum(0.02, 0.0015 * df.entry) / risk; df["grossR"] = df.R + df.costR
    L += ["## Where the money goes: edge vs trading costs", "",
          "Gross R = what the setup earned before slippage/spread. Cost R = round-trip slippage as a share of the risk. A strategy only works when gross beats cost.", "",
          "| Strategy | Gross R | Cost R | Net R |", "|---|---|---|---|"]
    for k, g in df.groupby("strategy"):
        L.append(f"| {k} | {g.grossR.mean():+.3f} | {g.costR.mean():.3f} | {g.R.mean():+.3f} |")
    df["price_band"] = pd.cut(df.entry, [0, 5, 10, 20, 50, 1e6], labels=["under $5", "$5-10", "$10-20", "$20-50", "$50+"])
    df["stop_width"] = pd.cut(df.entry.sub(df.stop).div(df.entry), [0, 0.01, 0.02, 0.03, 1], labels=["under 1%", "1-2%", "2-3%", "3%+"])
    for col, title in [("price_band", "By stock price"), ("stop_width", "By stop width")]:
        L += ["", f"**{title}**", "", "| Group | Trades | Gross R | Cost R | Net R |", "|---|---|---|---|---|"]
        for k, g in df.groupby(col, observed=True):
            L.append(f"| {k} | {len(g)} | {g.grossR.mean():+.3f} | {g.costR.mean():.3f} | {g.R.mean():+.3f} |")
    L += [""]
    vt, costs = variant_table(df)
    if len(vt):
        vt.to_csv(f"{OUT}/variants.csv", index=False)
        L += ["## Fixes tested: entry and exit variants", "",
              "Entry: mkt = market order next bar (current), lim = limit at the signal close, good 3 minutes (no chase). "
              "Plan: h2 = half at 1R, rest 2R (current); r3 = all at 3R; tr = half at 1R, trail the rest on the 9 EMA.",
              ("Net R below uses the typical measured spread; survivors must also stay positive with the bot's slippage and the worse (75th pct) spread." if costs else
               "Costs: only the bot's slippage model so far (run research.py costs to measure real spreads)."), ""]
        main = "spread_med" if costs else "bot"
        best = vt[vt.costs == main].sort_values("net", ascending=False)
        if costs:
            L += ["Measured quoted spreads at entry (median / 75th pct): " + ", ".join(f"{k} {v['median']:.2%} / {v['p75']:.2%}" for k, v in costs["bands"].items()) +
                  ". A market order pays about half the spread on the way in and half on the way out.", ""]
        L += ["| Strategy | Entry | Plan | Trades | Fill rate | Gross R | Net R | t | 1st half | 2nd half |", "|---|---|---|---|---|---|---|---|---|---|"]
        L += [f"| {r.strategy} | {r.entry} | {r.plan} | {r.n} | {r.fill_rate:.0%} | {r.gross:+.3f} | {r.net:+.3f} | {r.t} | {r.first_half:+.3f} | {r.second_half:+.3f} |" for r in best.head(15).itertuples()]
        worst = vt.groupby(["strategy", "entry", "plan"]).net.min().rename("net_worst")
        best = best.join(worst, on=["strategy", "entry", "plan"])
        good = best[(best.net > 0.05) & (best.t > 2) & (best.first_half > 0) & (best.second_half > 0) & (best.n >= 200) & (best.net_worst > 0)]
        L += ["", f"**Survivors (net > +0.05R, t > 2, positive in both halves, 200+ trades): {len(good)}**" +
              ("".join(f"\n- {r.strategy} / {r.entry} / {r.plan}: {r.net:+.3f}R over {r.n} trades" for r in good.itertuples()) if len(good) else " (none yet)"), ""]
    L += ["## Path to $20/day", "", "Current 6 accounts replayed over the backtest with every live rule (1 trade/day, price cap, on/off, filter):", "",
          "| Account | $/day | Days traded | Worst day |", "|---|---|---|---|"]
    L += [f"| ${r.account} | ${r.per_day:+.2f} | {r.trade_days}/{r.days} | ${r.worst_day:.2f} |" for r in acc.itertuples()]
    L += ["", f"**All accounts: ${per_day:+.2f}/day.**"]
    if scale: L += [f"To average $20/day with the same edge, risk per trade needs to be about {scale:.1f}x today's, "
                    f"for example accounts totaling about ${2750 * scale:,.0f} at 1% risk."]
    else: L += ["The current setup does not show a positive edge after costs, so more money would only lose faster. Fix the strategy list first."]
    open(f"{OUT}/scorecard.md", "w").write("\n".join(L) + "\n")
    sc.to_csv(f"{OUT}/scorecard.csv", index=False); acc.to_csv(f"{OUT}/plan.csv", index=False)
    log("analysis written: research/scorecard.md, model.json, strategy_status.json")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if mode == "run":
        backtest(int(sys.argv[2]) if len(sys.argv) > 2 else 500)
    if mode in ("run", "costs") and not os.path.exists(f"{OUT}/costs.json") or mode == "costs":
        measure_costs(int(os.environ.get("COST_SAMPLES", "1500")))
    analyze()
