"""Paper day-trading bot (live). 6 accounts x 3-4 strategies, 1 trade/account/day, 1% risk.
Shared rules live in core.py (identical to the backtester). Every signal is logged with features and
labeled with its outcome after the close, so the research job can learn which conditions actually work.
Usage: python bot.py live | selftest | configure | brief | replay YYYY-MM-DD T1,T2"""
import os, sys, re, json, time, math, email.utils, urllib.request, urllib.parse, urllib.error, pickle, subprocess, datetime as dt, warnings
import pandas as pd, yfinance as yf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import (ET, RISKPCT, slip, add_ind, STRATS, WINDOWS, MINCHG, valid_risk, features, simulate, model_score, variant_cols)
warnings.filterwarnings("ignore")
BASE = os.environ.get("BOT_BASE") or os.path.dirname(os.path.abspath(__file__))
# TRADE_ALL=1: paper accounts keep trading strategies the research marked "off", to collect live fill/timing data.
# The signal log still records the real status, and reports label these trades as test trades.
TRADE_ALL = os.environ.get("TRADE_ALL") == "1"
LOG, JOURNAL, SIGNALS = f"{BASE}/bot.log", f"{BASE}/journal.csv", f"{BASE}/signals.csv"
ACCOUNTS = {200: ["pm_high_break", "vwap_pullback", "eod_squeeze"],
            250: ["orb15", "ema_bounce", "failed_breakdown", "afternoon_hod"],
            350: ["hod_break", "bull_flag", "eod_squeeze"],
            400: ["orb5", "ema_bounce", "vwap_pullback"],
            550: ["pm_high_break", "bull_flag", "failed_breakdown", "afternoon_hod"],
            1000: ["orb5", "orb15", "hod_break"]}
SKIP = {"FEDU", "VACI", "FEAM", "SPY"}
NEG = re.compile(r"\b(offering|priced at|dilut\w*|reverse split|registered direct|at-the-market|delist\w*|bankrupt\w*)\b", re.I)
MODE = sys.argv[1] if len(sys.argv) > 1 else "live"

def log(m, now=None):
    s = f"{(now or dt.datetime.now(ET)):%m-%d %H:%M:%S} {m}"
    print(s, flush=True); open(LOG, "a").write(s + "\n")

def append_csv(path, row):
    """append one row, aligned to the file's existing columns (files gain columns over time, e.g. after labeling)"""
    if not os.path.exists(path):
        pd.DataFrame([row]).to_csv(path, index=False); return
    cols = list(pd.read_csv(path, nrows=0).columns)
    if set(row) <= set(cols):
        pd.DataFrame([row]).reindex(columns=cols).to_csv(path, mode="a", header=False, index=False)
    else:
        pd.concat([pd.read_csv(path, low_memory=False), pd.DataFrame([row])], ignore_index=True).to_csv(path, index=False)

def load_json(name, default):
    try: return json.load(open(f"{BASE}/{name}"))
    except Exception: return default

def is_opex(d): return d.weekday() == 4 and 15 <= d.day <= 21

# ---------- data
def fetch(t, day, pre=True):
    d = yf.download(t, start=str(day), end=str(day + dt.timedelta(days=1)), interval="1m", prepost=pre, progress=False, auto_adjust=False)
    if d.empty: return d, d
    if isinstance(d.columns, pd.MultiIndex): d.columns = [c[0] for c in d.columns]
    d.index = d.index.tz_convert(ET)
    rth = d.between_time("09:30", "15:59")
    pm = d[d.index.time < dt.time(9, 30)]
    return (add_ind(rth) if len(rth) else rth), pm

def prev_stats(t, day):
    """previous close and 20-day average daily volume (as of yesterday)"""
    h = yf.Ticker(t).history(start=str(day - dt.timedelta(days=40)), end=str(day))
    if not len(h): return None, None
    return float(h.Close.iloc[-1]), float(h.Volume.iloc[-20:].mean())


CAT = {}
# ---------- news: primary sources first (Benzinga via Alpaca, newswires, SEC filings), Google News as fallback
SEC_UA = os.environ.get("SEC_UA", "PaperTradingBot paper-bot@users.noreply.github.com")
OPINION = re.compile(r"\b(why i'?m|should you|is it time|buy or sell|top \d+|stock price, news, quote|what'?s next|time to buy|could|might)\b", re.I)
GENERIC = re.compile(r"stocks moving|reported earlier|mid-day|movers|shares are trading|why .* (shares|stock) (is|are)|short interest|unusual options|price over earnings|law firm|investigat|class action|shareholder alert|investor alert|lawsuit|rosen|pomerantz|levi & korsinsky", re.I)
DILUTION_FORMS = {"S-1", "S-1/A", "S-3", "S-3/A", "F-1", "F-1/A", "F-3", "424B1", "424B2", "424B3", "424B4", "424B5"}
_CIK = {}

def _get(url, headers=None, timeout=15):
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"}), timeout=timeout).read().decode("utf-8", "ignore")

def news_benzinga(sym=None, hours=24, limit=10):
    k, sec = os.environ.get("ALPACA_KEY"), os.environ.get("ALPACA_SECRET")
    if not (k and sec): return []
    start = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    q = f"https://data.alpaca.markets/v1beta1/news?start={start}&limit={limit}&sort=desc" + (f"&symbols={sym}" if sym else "")
    try: js = json.loads(_get(q, {"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": sec}))
    except Exception as e: log(f"benzinga news error {e}"); return []
    return [dict(t=n["headline"], src="Benzinga", when=n["created_at"], syms=n.get("symbols", [])) for n in js.get("news", [])]

def _rss(query, hours=24):
    try: x = _get(f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-US&gl=US&ceid=US:en")
    except Exception: return []
    cut = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours); out = []
    for t, d in re.findall(r"<item>.*?<title>(.*?)</title>.*?<pubDate>(.*?)</pubDate>", x, re.S):
        try:
            if email.utils.parsedate_to_datetime(d) >= cut: out.append(dict(t=t.replace("&amp;", "&"), when=d))
        except Exception: pass
    return out

def news_wires(sym, hours=24):
    q = f"{sym} (site:globenewswire.com OR site:prnewswire.com OR site:businesswire.com OR site:accessnewswire.com) when:2d"
    return [dict(n, src="Newswire") for n in _rss(q, hours)]

def sec_filings(sym, days=3):
    try:
        if not _CIK: _CIK.update({v["ticker"]: v["cik_str"] for v in json.loads(_get("https://www.sec.gov/files/company_tickers.json", {"User-Agent": SEC_UA})).values()})
        cik = _CIK.get(sym)
        if not cik: return []
        rf = json.loads(_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", {"User-Agent": SEC_UA}))["filings"]["recent"]
    except Exception as e:
        log(f"sec error {sym} {str(e)[:60]}"); return []
    cut = str(dt.date.today() - dt.timedelta(days=days))
    return [dict(form=f, date=d) for f, d in zip(rf["form"], rf["filingDate"]) if d >= cut]

def catalyst(sym, name=""):
    if sym in CAT: return CAT[sym]
    key = (name or sym).split()[0].lower()
    filings = sec_filings(sym)
    dil = [f for f in filings if f["form"] in DILUTION_FORMS]
    if dil: CAT[sym] = f"NEG:SEC {dil[0]['form']} filed {dil[0]['date']} (possible share offering)"; return CAT[sym]
    hits = [n for n in news_benzinga(sym) + news_wires(sym) if not GENERIC.search(n["t"]) and (n["src"] != "Benzinga" or sym in n["syms"])]
    if not hits:
        hits = [dict(n, src="Google News") for n in _rss(f"{sym} stock when:1d") if (sym.lower() in n["t"].lower() or key in n["t"].lower()) and not OPINION.search(n["t"]) and not GENERIC.search(n["t"])]
    eightk = [f for f in filings if f["form"].startswith("8-K")]
    neg = [h for h in hits if NEG.search(h["t"])]
    if neg: CAT[sym] = f"NEG:[{neg[0]['src']}] {neg[0]['t']}"
    elif hits: CAT[sym] = f"[{hits[0]['src']}] {hits[0]['t']}" + (" +8-K" if eightk else "")
    elif eightk: CAT[sym] = f"[SEC] 8-K filed {eightk[0]['date']}"
    else: CAT[sym] = None
    return CAT[sym]

# ---------- daily market brief from every side of the spectrum (AllSides-style lean labels)
OUTLETS = [("Left", "MSNBC", "msnbc.com"), ("Left", "HuffPost", "huffpost.com"),
           ("Lean Left", "AP", "apnews.com"), ("Lean Left", "Bloomberg", "bloomberg.com"), ("Lean Left", "New York Times", "nytimes.com"), ("Lean Left", "Axios", "axios.com"),
           ("Center", "Reuters", "reuters.com"), ("Center", "CNBC", "cnbc.com"), ("Center", "Wall Street Journal", "wsj.com"), ("Center", "The Hill", "thehill.com"), ("Center", "Forbes", "forbes.com"),
           ("Lean Right", "Fox Business", "foxbusiness.com"), ("Lean Right", "Washington Examiner", "washingtonexaminer.com"), ("Lean Right", "New York Post", "nypost.com"),
           ("Right", "Fox News", "foxnews.com"), ("Right", "Breitbart", "breitbart.com"), ("Right", "Newsmax", "newsmax.com"), ("Right", "Daily Wire", "dailywire.com")]
MKT = re.compile(r"stock|market|econom|fed\b|fed's|rate|tariff|inflation|price|jobs|earnings|dow|s&p|nasdaq|oil|dollar|bond|treasury|recession|gdp|bank|trade|ai\b", re.I)
TOPICS = "(stocks OR \"stock market\" OR economy OR Fed OR tariffs OR inflation OR jobs)"

def market_brief(day=None):
    day = day or dt.datetime.now(ET).date(); os.makedirs(f"{BASE}/briefs", exist_ok=True)
    lines = [f"# Market brief {day}", "", "Lean labels follow AllSides-style ratings. Read across the spectrum: where every side reports the same fact, it's likely solid; where only one side runs a story, check it before trading on it.", ""]
    bz = news_benzinga(None, hours=16, limit=25)
    lines += ["## Benzinga wire (no political lean, fastest)", ""] + [f"- {n['t']}" + (f" ({', '.join(n['syms'][:4])})" if n['syms'] else "") for n in bz[:15]] + [""]
    for lean in ["Left", "Lean Left", "Center", "Lean Right", "Right"]:
        lines += [f"## {lean}", ""]
        for l, name, dom in OUTLETS:
            if l != lean: continue
            hs = [h["t"].rsplit(" - ", 1)[0] for h in _rss(f"{TOPICS} site:{dom} when:1d", 20) if MKT.search(h["t"])][:3]
            lines += [f"**{name}**"] + ([f"- {h}" for h in hs] or ["- (no market headlines found)"]) + [""]
    open(f"{BASE}/briefs/{day}.md", "w").write("\n".join(lines))
    log(f"market brief written: briefs/{day}.md ({len(bz)} Benzinga items)")



def scan():
    now = dt.datetime.now(ET); frac = max(0.05, min(1.0, ((now.hour - 9) * 60 + now.minute - 30) / 390)); cand = {}
    for q in ["day_gainers", "small_cap_gainers", "most_actives"]:
        try:
            for x in yf.screen(q, count=50)["quotes"]:
                s, p, c = x["symbol"], x.get("regularMarketPrice", 0), x.get("regularMarketChangePercent", 0)
                v, av = x.get("regularMarketVolume") or 0, x.get("averageDailyVolume3Month") or 0
                if 1 <= p <= 100 and c >= 4 and "-" not in s and s not in SKIP and av and v / (av * frac) >= 2:
                    cand[s] = (c, v / (av * frac), x.get("shortName", ""))
        except Exception as e: log(f"scan error {q} {e}")
    out = []
    for s in sorted(cand, key=lambda k: cand[k][0], reverse=True)[:20]:
        c, rv, nm = cand[s]; cat = catalyst(s, nm)
        if not cat: log(f"scan drop {s} +{c:.1f}% rvol {rv:.1f}: no news 24h"); continue
        if cat.startswith("NEG:"): log(f"scan drop {s}: negative news ({cat[4:][:70]})"); continue
        log(f"scan keep {s} +{c:.1f}% rvol {rv:.1f} | {cat[:80]}"); out.append(s)
    return out[:12]


# ---------- Alpaca paper mirror
class Alpaca:
    def __init__(self):
        ep = (os.environ.get("ALPACA_ENDPOINT") or "").rstrip("/")
        self.base = ep[:-3] if ep.endswith("/v2") else ep
        self.key, self.sec = os.environ.get("ALPACA_KEY"), os.environ.get("ALPACA_SECRET")
        self.on = bool(self.base and self.key and self.sec) and "paper-api" in self.base  # paper only, never live
        if self.base and "paper-api" not in self.base: log("ALPACA DISABLED: endpoint is not the paper endpoint")
    def req(self, method, path, body=None):
        r = urllib.request.Request(self.base + "/v2" + path, method=method, data=json.dumps(body).encode() if body else None,
                                   headers={"APCA-API-KEY-ID": self.key, "APCA-API-SECRET-KEY": self.sec, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(r, timeout=15) as x: t = x.read(); return json.loads(t) if t else {}
        except urllib.error.HTTPError as e:
            log(f"alpaca {method} {path} -> {e.code} {e.read()[:200]!r}"); return None
        except Exception as e:
            log(f"alpaca {method} {path} error {e}"); return None
    def enter(self, acct, pend, last, sh):
        if not self.on or sh < 2: return
        lim = round(last + 0.03, 2); risk = lim - pend["stop"]
        if risk <= 0.01: return
        tag = f"{acct}-{pend['t']}-{dt.datetime.now(ET):%m%d%H%M%S}"; ids = []
        for i, (q, tp) in enumerate([(sh // 2, lim + risk), (sh - sh // 2, lim + 2 * risk)]):
            o = self.req("POST", "/orders", dict(symbol=pend["t"], qty=str(q), side="buy", type="limit", limit_price=f"{lim:.2f}",
                         time_in_force="day", order_class="bracket", client_order_id=f"{tag}-{i}",
                         take_profit=dict(limit_price=f"{tp:.2f}"), stop_loss=dict(stop_price=f"{pend['stop']:.2f}")))
            if o: ids.append(o["id"])
        pend["alp"] = dict(ids=ids, sent=time.time(), limit=lim)
        log(f"[${acct}] ALPACA paper bracket x2 sent: {sh} {pend['t']} limit {lim} (ids {len(ids)})")
    def orders(self, p):
        return [o for o in (self.req("GET", f"/orders/{i}?nested=true") for i in p.get("alp", {}).get("ids", [])) if o]
    def tick(self, acct, p):  # 4-minute rule on the real order
        a = p.get("alp")
        if not self.on or not a or a.get("checked_fill"): return
        os_ = self.orders(p)
        if os_ and all(o["status"] == "filled" for o in os_): a["checked_fill"] = True; return
        if time.time() - a["sent"] > 240:
            for o in os_:
                if o["status"] not in ("filled", "canceled"): self.req("DELETE", f"/orders/{o['id']}")
            a["checked_fill"] = True; log(f"[${acct}] ALPACA entry not filled within 4 min: canceled unfilled part")
    def breakeven(self, acct, p):
        if not self.on or "alp" not in p or len(p["alp"]["ids"]) < 2: return
        o = self.req("GET", f"/orders/{p['alp']['ids'][1]}?nested=true")
        for leg in (o or {}).get("legs") or []:
            if leg.get("type") in ("stop", "stop_limit") and leg["status"] in ("new", "accepted", "held"):
                self.req("PATCH", f"/orders/{leg['id']}", dict(stop_price=f"{p['alp']['limit']:.2f}"))
                log(f"[${acct}] ALPACA runner stop moved to {p['alp']['limit']}")
    def flatten(self, acct, p):
        if not self.on or "alp" not in p: return
        held = 0
        for o in self.orders(p):
            held += float(o.get("filled_qty") or 0)
            for leg in o.get("legs") or []:
                held -= float(leg.get("filled_qty") or 0)
                if leg["status"] not in ("filled", "canceled", "expired"): self.req("DELETE", f"/orders/{leg['id']}")
            if o["status"] not in ("filled", "canceled", "expired"): self.req("DELETE", f"/orders/{o['id']}")
        if held > 0:
            time.sleep(1); o = self.req("POST", "/orders", dict(symbol=p["t"], qty=str(int(held)), side="sell", type="market", time_in_force="day"))
            if o: p["alp"].setdefault("flat", []).append(o["id"]); log(f"[${acct}] ALPACA market sell {int(held)} {p['t']} to flatten")
    def reconcile(self, acct, p, sim_pnl, day):
        if not self.on or "alp" not in p: return
        time.sleep(2); cost = proceeds = qin = qout = 0.0
        for o in self.orders(p):
            q = float(o.get("filled_qty") or 0); qin += q; cost += q * float(o.get("filled_avg_price") or 0)
            for leg in o.get("legs") or []:
                lq = float(leg.get("filled_qty") or 0); qout += lq; proceeds += lq * float(leg.get("filled_avg_price") or 0)
        for fid in p["alp"].get("flat", []):
            o = self.req("GET", f"/orders/{fid}") or {}
            lq = float(o.get("filled_qty") or 0); qout += lq; proceeds += lq * float(o.get("filled_avg_price") or 0)
        row = dict(date=str(day), account=acct, strategy=p["strat"], ticker=p["t"], sim_pnl=sim_pnl, alp_shares_in=qin, alp_shares_out=qout,
                   alp_avg_entry=round(cost / qin, 4) if qin else None, alp_pnl=round(proceeds - cost, 2) if qin and qout >= qin else None,
                   status="closed" if qin and qout >= qin else ("no fill" if not qin else "partially open"))
        pd.DataFrame([row]).to_csv(f"{BASE}/alpaca_journal.csv", mode="a", header=not os.path.exists(f"{BASE}/alpaca_journal.csv"), index=False)
        log(f"[${acct}] ALPACA result {p['t']}: sim ${sim_pnl} vs alpaca ${row['alp_pnl']} ({row['status']})")


ALP = None

# ---------- engine (live; replay uses the same code)
class Engine:
    def __init__(self, day, exit_time=dt.time(15, 55)):
        self.day, self.exit_time = day, exit_time
        self.S = {a: {"pos": None, "pending": None, "done": False} for a in ACCOUNTS}
        self.logged = set()

    def step(self, now, data, stats, spy_chg, model, status):
        """data[t] = (completed RTH bars, premarket bars); stats[t] = (prev_close, adv)"""
        # 1) shadow logger: every strategy x every ticker, first signal of the day, taken or not
        for t, (d, pm) in data.items():
            if t in SKIP or d.empty or t not in stats or not stats[t][0]: continue
            pc, adv = stats[t]; chg = float(d.Close.iloc[-1]) / pc - 1
            for strat, fn in STRATS.items():
                key = (strat, t)
                if key in self.logged: continue
                w = WINDOWS[strat]
                if not (w[0] <= now.time() <= w[1]) or chg < MINCHG[strat]: continue
                sig = fn(d, pm, chg, now.time())
                if not sig: continue
                stop = round(sig[0], 2); px = float(d.Close.iloc[-1])
                if not valid_risk(px, stop): continue
                self.logged.add(key)
                f = features(strat, d, pm, chg, now.time(), pc, adv, spy_chg, CAT.get(t), stop)
                p = model_score(model, f)
                append_csv(SIGNALS, dict(date=str(self.day), time=f"{now:%H:%M}", ticker=t, stop=stop, sig_bar=str(d.index[-1]),
                                         p=None if p is None else round(p, 3), status=status.get(strat, "on"), R=None, why=None, **f))
        # 2) accounts
        for acct, st in self.S.items():
            tag = f"${acct}"
            if st["pending"]:
                o = st["pending"]; d = data[o["t"]][0]; nb = d[d.index > o["sig_time"]]
                if len(nb):
                    st["pending"] = None
                    if (nb.index[0] - o["sig_time"]) > pd.Timedelta(minutes=4):
                        log(f"[{tag}] {o['t']} skip: fill would be >4 min after signal", now)
                        if ALP: ALP.flatten(acct, o)
                        continue
                    op = float(nb.Open.iloc[0]); fill = round(op + slip(op), 2); risk = fill - o["stop"]
                    budget = acct * RISKPCT * o.get("size", 1.0)
                    sh = min(int(budget // risk), int(acct // fill)) if risk > 0 else 0
                    if sh < 2:
                        log(f"[{tag}] {o['t']} skip at fill (risk/share {risk:.2f})", now)
                        if ALP: ALP.flatten(acct, o)
                        continue
                    st["pos"] = dict(o, entry=fill, shares=sh, open_sh=sh, risk=risk, t1=round(fill + risk, 2), target=round(fill + 2 * risk, 2),
                                     stop_now=o["stop"], realized=0.0, entry_time=nb.index[0], half=False)
                    log(f"[{tag}] BUY {sh} {o['t']} @ {fill} stop {o['stop']:.2f} half@{st['pos']['t1']} tgt {st['pos']['target']} | {o['strat']} | {o['reason']}", now)
            elif st["pos"]:
                self.manage(acct, st, now, data)
            elif not st["done"]:
                for strat in ACCOUNTS[acct]:
                    if status.get(strat, "on") == "off" and not TRADE_ALL: continue
                    for t, (d, pm) in data.items():
                        if t in SKIP or d.empty or t not in stats or not stats[t][0] or float(d.Close.iloc[-1]) > acct / 10: continue
                        pc, adv = stats[t]; chg = float(d.Close.iloc[-1]) / pc - 1
                        w = WINDOWS[strat]
                        if not (w[0] <= now.time() <= w[1]) or chg < MINCHG[strat]: continue
                        sig = STRATS[strat](d, pm, chg, now.time())
                        if not sig: continue
                        stop, why = round(sig[0], 2), sig[1]; px = float(d.Close.iloc[-1])
                        if not valid_risk(px, stop): continue
                        f = features(strat, d, pm, chg, now.time(), pc, adv, spy_chg, CAT.get(t), stop)
                        p = model_score(model, f); size = 0.5 if status.get(strat) == "probation" else 1.0
                        if TRADE_ALL and status.get(strat) == "off": p = None  # test trade: no filter, full size
                        if p is not None:
                            if p < model["threshold"]: log(f"[{tag}/{strat}] {t} filtered out by model (p={p:.2f} < {model['threshold']:.2f})", now); continue
                            if p < model.get("threshold_hi", 1): size = min(size, 0.5)
                        st["pending"] = dict(t=t, strat=strat, stop=stop, size=size, sig_time=d.index[-1], p=p, test=status.get(strat) == "off",
                                             reason=f"{why} | news: {(CAT.get(t) or '')[:60]}" + (f" | p={p:.2f}" if p is not None else ""))
                        log(f"[{tag}/{strat}] SIGNAL {t}: {why}; stop {stop}; size {size:.0%}", now)
                        if ALP:
                            est = px + 0.03; shs = min(int(acct * RISKPCT * size // max(est - stop, 0.01)), int(acct // est))
                            ALP.enter(acct, st["pending"], px, shs)
                        break
                    if st["pending"]: break

    def manage(self, acct, st, now, data):
        p = st["pos"]; d = data[p["t"]][0]; nb = d[d.index > p.get("checked", p["entry_time"] - pd.Timedelta(minutes=1))]
        if ALP: ALP.tick(acct, p)
        for ts, b in nb.iterrows():
            p["checked"] = ts
            if p["strat"] != "eod_squeeze" and ts.time() >= self.exit_time: break
            if b.Low <= p["stop_now"]:
                px = round(min(p["stop_now"], b.Open) - slip(p["stop_now"]), 2); return self.close(acct, st, px, "breakeven" if p["half"] else "stop", now)
            if not p["half"] and b.High >= p["t1"]:
                h = p["open_sh"] // 2; p["realized"] += (p["t1"] - p["entry"]) * h; p["open_sh"] -= h; p["half"] = True
                p["stop_now"] = p["entry"]; log(f"[${acct}] HALF OFF {h} {p['t']} @ {p['t1']} (+1R), stop to breakeven", now)
                if ALP: ALP.breakeven(acct, p)
            if b.High >= p["target"]: return self.close(acct, st, p["target"], "target", now)
        if p["strat"] != "eod_squeeze" and now.time() >= self.exit_time and len(d):
            last = d[d.index.time < self.exit_time]
            if len(last): self.close(acct, st, round(float(last.Close.iloc[-1]) - slip(float(last.Close.iloc[-1])), 2), "time", now)

    def close(self, acct, st, px, why, now):
        p = st["pos"]; pnl = round(p["realized"] + (px - p["entry"]) * p["open_sh"], 2)
        log(f"[${acct}] EXIT {p['open_sh']} {p['t']} @ {px} ({why}) total P&L ${pnl}", now)
        append_csv(JOURNAL, dict(date=str(self.day), account=acct, strategy=p["strat"], ticker=p["t"], shares=p["shares"], entry=p["entry"],
                                 stop=p["stop"], half_at=p["t1"], target=p["target"], exit=px, exit_reason=why, pnl=pnl,
                                 R=round(pnl / (acct * RISKPCT), 2), size=p.get("size", 1.0), p=p.get("p"), test=int(bool(p.get("test"))), reason=p["reason"]))
        if ALP:
            if why in ("time", "next open"): ALP.flatten(acct, p)
            ALP.reconcile(acct, p, pnl, self.day)
        st["pos"] = None; st["done"] = True

    def eod_overnight(self, next_open_px, now):
        for acct, st in self.S.items():
            p = st["pos"]
            if p and p["strat"] == "eod_squeeze" and p["t"] in next_open_px:
                self.close(acct, st, round(next_open_px[p["t"]] - slip(next_open_px[p["t"]]), 2), "next open", now)

def spread_at(sym, ts, secs=20):
    """median SIP quoted spread (fraction of price) in the first seconds after ts; needs the 15-min SIP delay, so call after the close"""
    k, s_ = os.environ.get("ALPACA_KEY"), os.environ.get("ALPACA_SECRET")
    if not (k and s_): return None
    u = lambda x: x.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    q = urllib.parse.urlencode(dict(symbols=sym, start=u(ts), end=u(ts + dt.timedelta(seconds=secs)), feed="sip", limit=1000))
    try:
        js = json.loads(urllib.request.urlopen(urllib.request.Request(f"https://data.alpaca.markets/v2/stocks/quotes?{q}",
             headers={"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s_}), timeout=20).read())
    except Exception as e:
        log(f"spread {sym} error {e}"); return None
    sp = sorted((x["ap"] - x["bp"]) / ((x["ap"] + x["bp"]) / 2) for x in (js.get("quotes") or {}).get(sym, []) if x.get("bp", 0) > 0 and x.get("ap", 0) > x["bp"])
    return round(sp[len(sp) // 2], 5) if sp else None


# ---------- label today's logged signals with their real outcome (after the close)
def label_signals(day, full_bars, next_opens=None):
    if not os.path.exists(SIGNALS): return 0
    df = pd.read_csv(SIGNALS); n = 0
    df["why"] = df["why"].astype("object"); df["date"] = df["date"].astype(str)
    for i, r in df[(df.date == str(day)) & (df.R.isna())].iterrows():
        if r.strategy == "eod_squeeze" and not (next_opens and r.ticker in next_opens): continue
        rth = full_bars.get(r.ticker)
        if rth is None or rth.empty: continue
        pos = rth.index.get_indexer([pd.Timestamp(r.sig_bar)])[0]
        if pos < 0: continue
        out = simulate(rth, pos, r.stop, r.strategy, (next_opens or {}).get(r.ticker))
        if out: df.loc[i, "R"] = round(out["R"], 3); df.loc[i, "why"] = out["why"]; n += 1
        for k, v in variant_cols(rth, pos, r.stop, r.strategy, (next_opens or {}).get(r.ticker)).items():
            if k not in df: df[k] = None
            df.loc[i, k] = v
        if "spread_pct" not in df or pd.isna(df.loc[i, "spread_pct"]):
            sp = spread_at(r.ticker, pd.Timestamp(r.sig_bar).to_pydatetime() + dt.timedelta(minutes=1))
            if "spread_pct" not in df: df["spread_pct"] = None
            df.loc[i, "spread_pct"] = sp
    df.to_csv(SIGNALS, index=False); return n

def label_overnight(prev_day, today):
    """fill in eod_squeeze outcomes from yesterday using today's open"""
    if not os.path.exists(SIGNALS): return
    df = pd.read_csv(SIGNALS); df["date"] = df["date"].astype(str)
    rows = df[(df.date == str(prev_day)) & (df.strategy == "eod_squeeze") & (df.R.isna())]
    if rows.empty: return
    bars, opens = {}, {}
    for t in rows.ticker.unique():
        bars[t] = fetch(t, prev_day, pre=False)[0]
        r, _ = fetch(t, today, pre=False)
        if len(r): opens[t] = float(r.Open.iloc[0])
    label_signals(prev_day, bars, opens)


# ---------- live (resumable: state saved to state.pkl so cloud jobs can hand off)
STATE = f"{BASE}/state.pkl"
def save_state(day, E, U, stats):
    pickle.dump(dict(day=day, S=E.S if E else None, logged=E.logged if E else set(), exit_time=E.exit_time if E else None,
                     U=U, stats=stats, CAT=CAT), open(STATE, "wb"))

def git_sync(msg):
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("BOT_BASE"): return
    cmd = f'cd "{BASE}" && git add -A && (git diff --cached --quiet || git commit -qm "{msg}") && (git push -q || (git pull -q --rebase -X theirs && git push -q))'
    subprocess.run(cmd, shell=True)

def market_day(day):
    """(is_trading_day, close_time) from Alpaca's market calendar; weekday fallback"""
    a = Alpaca()
    if a.on:
        cal = a.req("GET", f"/calendar?start={day}&end={day}")
        if cal is not None:
            if not cal: return False, None
            hh, mm = map(int, cal[0]["close"].split(":")); return True, dt.time(hh, mm)
    return day.weekday() < 5, dt.time(16, 0)

def end_of_day(day, E, U):
    """label signals, write the daily report"""
    try:
        bars = {t: fetch(t, day, pre=False)[0] for t in set(pd.read_csv(SIGNALS).query("date == @day_s", local_dict={"day_s": str(day)}).ticker)} if os.path.exists(SIGNALS) else {}
        n = label_signals(day, bars); log(f"labeled {n} signals with outcomes")
    except Exception as e: log(f"label error {e}")
    try:
        import report; report.daily(BASE, day); log("daily report written")
    except Exception as e: log(f"report error {e}")

def live():
    global ALP
    ALP = Alpaca() if Alpaca().on else None
    log("alpaca paper mirror: " + ("ON" if ALP else "off"))
    hours = float(os.environ.get("MAX_HOURS", "0")) or None
    stop_at = time.time() + hours * 3600 if hours else None
    start_date = dt.date.fromisoformat(os.environ["START_DATE"]) if os.environ.get("START_DATE") else None
    model, status = load_json("model.json", {}), load_json("strategy_status.json", {}).get("status", {})
    log(f"model filter: {'ON' if model.get('enabled') else 'off'}; strategies off: {[k for k, v in status.items() if v == 'off']}")
    day, E, U, stats, eod_done = None, None, [], {}, False
    if os.path.exists(STATE):
        st = pickle.load(open(STATE, "rb")); CAT.update(st.get("CAT") or {})
        day, U, stats = st["day"], st["U"], st.get("stats", {})
        if st["S"] is not None:
            E = Engine(day, st.get("exit_time") or dt.time(15, 55)); E.S = st["S"]; E.logged = st.get("logged", set())
        log(f"resumed state from {day}")
    log("bot live start" + (f" (max {hours}h)" if hours else ""))
    last_sync, today_ok = time.time(), None
    while True:
        now = dt.datetime.now(ET)
        if stop_at and time.time() > stop_at: break
        if stop_at and start_date and now.date() < start_date: log("before start date, exiting"); break
        if today_ok is None or today_ok[0] != now.date():
            ok, close_t = market_day(now.date()); today_ok = (now.date(), ok, close_t)
            if not ok:
                log("market closed today (holiday/weekend)")
                if stop_at: break
        _, ok, close_t = today_ok
        close_dt = dt.datetime.combine(now.date(), close_t or dt.time(16, 0), ET)
        if ok and E and day == now.date() and now >= close_dt + dt.timedelta(minutes=2):
            if not eod_done: end_of_day(day, E, U); eod_done = True; save_state(day, E, U, stats)
            if stop_at: break
        if not ok or not (dt.time(9, 31) <= now.time()) or now >= close_dt:
            time.sleep(30); continue
        if day != now.date():
            prev_day = day
            carry = [(a, st) for a, st in E.S.items() if st["pos"] and st["pos"]["strat"] == "eod_squeeze"] if E else []
            exit_t = (close_dt - dt.timedelta(minutes=5)).time()
            day = now.date(); E = Engine(day, exit_t); eod_done = False
            if exit_t != dt.time(15, 55): log(f"early close today: exits at {exit_t}")
            if carry:
                for a, st in carry: E.S[a] = st
                px = {}
                for a, st in carry:
                    r, _ = fetch(st["pos"]["t"], day, pre=False)
                    if len(r): px[st["pos"]["t"]] = float(r.Open.iloc[0])
                E.eod_overnight(px, now)
            if prev_day:
                try: label_overnight(prev_day, day)
                except Exception as e: log(f"overnight label error {e}")
            if ALP and not carry: ALP.req("DELETE", "/orders")
            if is_opex(day): log("monthly opex day: no new trades (playbook rule)")
            try: market_brief(day)
            except Exception as e: log(f"brief error {e}")
            U = scan(); stats = {t: prev_stats(t, day) for t in U + ["SPY"]}; log(f"new day universe={U}")
            save_state(day, E, U, stats)
        if not is_opex(day) and now.time() < dt.time(10, 30) and now.minute % 15 == 0:
            for t in scan():
                if t not in U: U.append(t); stats[t] = prev_stats(t, day)
        try:
            data = {}
            want = set(U) | {"SPY"} | {st["pos"]["t"] for st in E.S.values() if st["pos"]} | {st["pending"]["t"] for st in E.S.values() if st["pending"]}
            for t in want:
                r, pm = fetch(t, day); data[t] = (r[r.index < now.replace(second=0, microsecond=0)] if len(r) else r, pm)
            spy = data.get("SPY", (pd.DataFrame(), None))[0]
            spy_chg = float(spy.Close.iloc[-1]) / stats["SPY"][0] - 1 if len(spy) and stats.get("SPY") and stats["SPY"][0] else 0.0
            if is_opex(day):
                for st in E.S.values(): st["done"] = st["done"] or (not st["pos"] and not st["pending"])
            E.step(now, data, stats, spy_chg, model, status)
            save_state(day, E, U, stats)
        except Exception as e: log(f"error {e}")
        if now.minute % 10 == 0:
            log("status " + " ".join(f"{a}:{'pos '+v['pos']['t'] if v['pos'] else 'pending' if v['pending'] else 'done' if v['done'] else 'watching'}" for a, v in E.S.items()))
        if time.time() - last_sync > 1800: git_sync(f"bot update {now:%Y-%m-%d %H:%M}"); last_sync = time.time()
        time.sleep(max(5, 62 - dt.datetime.now(ET).second))
    if E: save_state(day, E, U, stats)
    log("bot session end"); git_sync(f"bot session end {dt.datetime.now(ET):%Y-%m-%d %H:%M}")

# ---------- replay a past day with the live engine (sanity check)
def replay(day, tickers):
    log(f"=== REPLAY {day} on {tickers}")
    full = {t: fetch(t, day) for t in tickers + ["SPY"]}; stats = {t: prev_stats(t, day) for t in tickers + ["SPY"]}
    for t in tickers: catalyst(t)
    E = Engine(day); model, status = load_json("model.json", {}), load_json("strategy_status.json", {}).get("status", {})
    for m in pd.date_range(f"{day} 09:31", f"{day} 15:59", freq="1min", tz=ET):
        data = {t: (r[r.index < m], pm) for t, (r, pm) in full.items()}
        spy = data["SPY"][0]; spy_chg = float(spy.Close.iloc[-1]) / stats["SPY"][0] - 1 if len(spy) else 0
        E.step(m.to_pydatetime(), data, stats, spy_chg, model, status)

def dryrun(day, tickers):
    """full pipeline on a past day in a scratch folder: engine -> journal -> label signals (+variants, spreads) -> report"""
    os.makedirs(BASE, exist_ok=True)
    replay(day, tickers)
    end_of_day(day, None, tickers)
    for f in ("signals.csv", "journal.csv", f"reports/{day}.md"):
        p = f"{BASE}/{f}"; print(f"\n===== {f} =====")
        print(open(p).read()[:6000] if os.path.exists(p) else "(missing)")


def configure():
    a = Alpaca()
    if not a.on: log("configure: alpaca not configured or not paper"); return
    log(f"configure before: {a.req('GET', '/account/configurations')}")
    log(f"configure after: {a.req('PATCH', '/account/configurations', dict(max_margin_multiplier='1', no_shorting=True, fractional_trading=False))}")
    acc = a.req("GET", "/account") or {}
    log(f"account: equity={acc.get('equity')} buying_power={acc.get('buying_power')} multiplier={acc.get('multiplier')} shorting={acc.get('shorting_enabled')}")
    git_sync("configure")

def selftest():
    a = Alpaca()
    if a.on:
        acc = a.req("GET", "/account") or {}; clk = a.req("GET", "/clock") or {}
        log(f"selftest alpaca: status={acc.get('status')} equity={acc.get('equity')} market_open={clk.get('is_open')}")
        log(f"selftest calendar today: {market_day(dt.datetime.now(ET).date())}")
    else: log("selftest alpaca: not configured or not paper")
    log(f"selftest benzinga: {len(news_benzinga(None, 6, 5))} recent headlines")
    log(f"selftest sec SKYD filings 30d: {sec_filings('SKYD', 30)[:3]}")
    U = scan(); log(f"selftest universe={U}")
    if U:
        r, pm = fetch(U[0], dt.datetime.now(ET).date()); log(f"selftest {U[0]} bars={len(r)} premarket={len(pm)} stats={prev_stats(U[0], dt.datetime.now(ET).date())}")
    git_sync("selftest")

if __name__ == "__main__":
    if MODE == "replay": replay(dt.date.fromisoformat(sys.argv[2]), sys.argv[3].split(","))
    elif MODE == "dryrun": dryrun(dt.date.fromisoformat(sys.argv[2]), sys.argv[3].split(","))
    elif MODE == "selftest": selftest()
    elif MODE == "configure": configure()
    elif MODE == "brief": market_brief(); git_sync("market brief")
    else: live()
