"""Paper day-trading bot v3. 6 accounts x 3 strategies, 1 trade/account/day, 1% risk.
Adds playbook ideas: premarket-high break, 9/21 EMA bounce, end-of-day squeeze (sell next open),
half off at +1R then stop to breakeven, 4-minute signal age limit, monthly-opex skip.
Usage: python3 bot3.py live            -> runs every market day
       python3 bot3.py replay YYYY-MM-DD T1,T2,...  -> replays a past day on given tickers
No broker connection. Fills: next 1-min bar open + $0.02; stops $0.02 worse."""
import os, sys, re, json, time, math, email.utils, urllib.request, urllib.parse, datetime as dt, warnings
import pandas as pd, yfinance as yf
from zoneinfo import ZoneInfo
warnings.filterwarnings("ignore")
ET = ZoneInfo("America/New_York")
SLIP, RISKPCT = 0.02, 0.01
BASE = os.path.dirname(os.path.abspath(__file__))
LOG, JOURNAL = f"{BASE}/bot3.log", f"{BASE}/journal.csv"
ACCOUNTS = {200: ["pm_high_break", "vwap_pullback", "eod_squeeze"],
            250: ["orb15", "ema_bounce", "afternoon_hod"],
            350: ["hod_break", "bull_flag", "eod_squeeze"],
            400: ["orb5", "ema_bounce", "vwap_pullback"],
            550: ["pm_high_break", "bull_flag", "afternoon_hod"],
            1000: ["orb5", "orb15", "hod_break"]}
SKIP = {"FEDU", "VACI", "FEAM"}
NEG = re.compile(r"\b(offering|priced at|dilut\w*|reverse split|registered direct|at-the-market|delist\w*|bankrupt\w*)\b", re.I)
MODE = sys.argv[1] if len(sys.argv) > 1 else "live"

def log(m, now=None):
    s = f"{(now or dt.datetime.now(ET)):%m-%d %H:%M:%S} {m}"
    print(s, flush=True); open(LOG, "a").write(s + "\n")

def record(row):
    pd.DataFrame([row]).to_csv(JOURNAL, mode="a", header=not os.path.exists(JOURNAL), index=False)

def is_opex(d):  # 3rd Friday of month
    return d.weekday() == 4 and 15 <= d.day <= 21

# ---------- data
def fetch(t, day, pre=True):
    d = yf.download(t, start=str(day), end=str(day + dt.timedelta(days=1)), interval="1m", prepost=pre, progress=False, auto_adjust=False)
    if d.empty: return d, d
    if isinstance(d.columns, pd.MultiIndex): d.columns = [c[0] for c in d.columns]
    d.index = d.index.tz_convert(ET)
    rth = d.between_time("09:30", "15:59").copy()
    pm = d[d.index.time < dt.time(9, 30)]
    if not rth.empty:
        tp = (rth.High + rth.Low + rth.Close) / 3
        rth["vwap"] = (tp * rth.Volume).cumsum() / rth.Volume.cumsum().replace(0, math.nan)
        rth["e9"] = rth.Close.ewm(span=9).mean(); rth["e21"] = rth.Close.ewm(span=21).mean()
    return rth, pm

def prev_close(t, day):
    h = yf.Ticker(t).history(start=str(day - dt.timedelta(days=10)), end=str(day))
    return float(h.Close.iloc[-1]) if len(h) else None

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

# ---------- strategies: f(d, pm, chg, now) -> (stop, reason) | None ; d = completed RTH bars
def vwap_pullback(d, pm, chg, now):
    if not (dt.time(10, 0) <= now <= dt.time(15, 30)) or len(d) < 30 or chg < 0.04: return None
    b = d.iloc[-1]
    if b.Low <= b.vwap * 1.003 and b.Close > b.vwap and b.Close > b.Open and d.Close.iloc[-30:].mean() > d.vwap.iloc[-30:].mean():
        return float(d.Low.iloc[-5:].min()) - 0.01, f"VWAP pullback: +{chg:.1%}, dipped to VWAP {b.vwap:.2f}, reclaimed with green bar"
def orb5(d, pm, chg, now):
    if not (dt.time(9, 36) <= now <= dt.time(11, 0)) or len(d) < 6: return None
    r = d.iloc[:5]; hi, lo = float(r.High.max()), float(r.Low.min())
    if r.Close.iloc[-1] <= r.Open.iloc[0]: return None
    b, prior = d.iloc[-1], d.iloc[5:-1]
    if b.Close > hi and (prior.empty or prior.Close.max() <= hi):
        return max(lo, b.Close * 0.97), f"5-min ORB: green first 5 min, closed above range high {hi:.2f}"
def orb15(d, pm, chg, now):
    if not (dt.time(9, 46) <= now <= dt.time(11, 30)) or len(d) < 16: return None
    r = d.iloc[:15]; hi, lo = float(r.High.max()), float(r.Low.min()); b, prior = d.iloc[-1], d.iloc[15:-1]
    if b.Close > hi and b.Close > b.vwap and (prior.empty or prior.Close.max() <= hi):
        return (hi + lo) / 2, f"15-min ORB: closed above 15-min high {hi:.2f}, above VWAP"
def hod_break(d, pm, chg, now):
    if not (dt.time(9, 45) <= now <= dt.time(11, 30)) or len(d) < 20 or chg < 0.10: return None
    b, prev = d.iloc[-1], d.iloc[:-1]; hod = float(prev.High.max()); since = prev.index[-1] - prev.High.idxmax()
    if b.Close > hod and since >= pd.Timedelta(minutes=10) and b.Volume > prev.Volume.iloc[-20:].mean() * 1.5:
        return float(d.Low.iloc[-10:].min()) - 0.01, f"Gap-and-go: +{chg:.1%}, based {int(since.total_seconds()//60)} min, broke HOD {hod:.2f} on 1.5x vol"
def bull_flag(d, pm, chg, now):
    if not (dt.time(9, 45) <= now <= dt.time(14, 0)) or len(d) < 25 or chg < 0.04: return None
    pole, flag, b = d.iloc[-23:-8], d.iloc[-8:-1], d.iloc[-1]
    rise, fr = pole.High.max() / pole.Low.min() - 1, flag.High.max() / flag.Low.min() - 1
    if rise >= 0.03 and fr <= 0.015 and flag.Volume.mean() < pole.Volume.mean() and b.Close > flag.High.max() and b.Close > b.vwap:
        return float(flag.Low.min()) - 0.01, f"Bull flag: {rise:.1%} pole, {fr:.1%} flag on light vol, broke {flag.High.max():.2f}"
def afternoon_hod(d, pm, chg, now):
    if not (dt.time(13, 0) <= now <= dt.time(15, 0)) or len(d) < 60 or chg < 0.05: return None
    b, prev = d.iloc[-1], d.iloc[:-1]; hod = float(prev.High.max())
    if b.Close > hod and b.Close > b.vwap and b.Volume > prev.Volume.iloc[-30:].mean() * 1.5:
        return float(d.Low.iloc[-15:].min()) - 0.01, f"Afternoon HOD: +{chg:.1%}, new high {hod:.2f} after 1pm on 1.5x vol"
def pm_high_break(d, pm, chg, now):  # playbook setup A: break of premarket high after 5-min confirmation
    if not (dt.time(9, 35) <= now <= dt.time(10, 30)) or len(d) < 5 or pm is None or len(pm) < 10 or chg < 0.03: return None
    pmh = float(pm.High.max()); b, prior = d.iloc[-1], d.iloc[:-1]
    if b.Close > pmh and b.Close > b.vwap and prior.Close.max() <= pmh:
        return float(d.Low.iloc[-5:].min()) - 0.01, f"Premarket-high break: closed above PM high {pmh:.2f} after open, above VWAP"
def ema_bounce(d, pm, chg, now):  # playbook setup E: 9/21 EMA bounce in an uptrend
    if not (dt.time(10, 0) <= now <= dt.time(15, 0)) or len(d) < 40 or chg < 0.03: return None
    b = d.iloc[-1]
    if b.e9 > b.e21 > d.e21.iloc[-10] and b.Low <= b.e21 * 1.002 and b.Close > b.e9 and b.Close > b.Open and b.Close > b.vwap:
        return min(float(d.Low.iloc[-3:].min()), b.e21 * 0.995) - 0.01, f"9/21 EMA bounce: EMAs stacked up, tagged 21 EMA {b.e21:.2f}, closed back over 9 EMA"
def eod_squeeze(d, pm, chg, now):  # playbook setup C: strong close, hold overnight, sell next open
    if not (dt.time(15, 30) <= now <= dt.time(15, 50)) or len(d) < 300 or chg < 0.04: return None
    b = d.iloc[-1]; hod = float(d.High.max())
    if b.Close >= hod * 0.99 and b.Close > b.vwap and d.Close.iloc[-30:].mean() > d.vwap.iloc[-30:].mean():
        return float(d.Low.iloc[-30:].min()) - 0.01, f"EOD squeeze: +{chg:.1%}, closing within 1% of HOD {hod:.2f}, hold to next open"
STRATS = {f.__name__: f for f in [vwap_pullback, orb5, orb15, hod_break, bull_flag, afternoon_hod, pm_high_break, ema_bounce, eod_squeeze]}


# ---------- Alpaca paper mirror: real paper orders alongside the conservative simulator
import json, urllib.error
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

# ---------- engine (same code for live and replay)
class Engine:
    def __init__(self, day):
        self.day = day; self.S = {a: {"pos": None, "pending": None, "done": False} for a in ACCOUNTS}

    def step(self, now, data, prev):
        """now: ET datetime; data[t] = (rth bars completed before now, pm bars)"""
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
                    fill = round(float(nb.Open.iloc[0]) + SLIP, 2); risk = fill - o["stop"]
                    sh = min(int(acct * RISKPCT // risk), int(acct // fill)) if risk > 0 else 0
                    if sh < 2:
                        log(f"[{tag}] {o['t']} skip at fill (risk/share {risk:.2f})", now)
                        if ALP: ALP.flatten(acct, o)
                        continue
                    st["pos"] = dict(o, entry=fill, shares=sh, open_sh=sh, risk=risk, t1=round(fill + risk, 2),
                                     target=round(fill + 2 * risk, 2), stop_now=o["stop"], realized=0.0, entry_time=nb.index[0], half=False)
                    log(f"[{tag}] BUY {sh} {o['t']} @ {fill} stop {o['stop']:.2f} half@{st['pos']['t1']} tgt {st['pos']['target']} | {o['strat']} | {o['reason']}", now)
            elif st["pos"]:
                self.manage(acct, st, now, data)
            elif not st["done"]:
                for strat in ACCOUNTS[acct]:
                    for t, (d, pm) in data.items():
                        if d.empty or t not in prev or float(d.Close.iloc[-1]) > acct / 10: continue
                        chg = float(d.Close.iloc[-1]) / prev[t] - 1
                        sig = STRATS[strat](d, pm, chg, now.time())
                        if not sig: continue
                        stop, why = round(sig[0], 2), sig[1]; r = float(d.Close.iloc[-1]) - stop
                        if r < 0.02 or r > 0.04 * float(d.Close.iloc[-1]): continue
                        st["pending"] = dict(t=t, strat=strat, stop=stop, sig_time=d.index[-1], reason=f"{why} | news: {(CAT.get(t) or '')[:60]}")
                        log(f"[{tag}/{strat}] SIGNAL {t}: {why}; stop {stop}", now)
                        if ALP:
                            lc = float(d.Close.iloc[-1]); est = lc + 0.03
                            ALP.enter(acct, st["pending"], lc, min(int(acct * RISKPCT // max(est - stop, 0.01)), int(acct // est)))
                        break
                    if st["pending"]: break

    def manage(self, acct, st, now, data):
        p = st["pos"]; d = data[p["t"]][0]; nb = d[d.index > p.get("checked", p["entry_time"] - pd.Timedelta(minutes=1))]
        if ALP: ALP.tick(acct, p)
        for ts, b in nb.iterrows():
            p["checked"] = ts
            if b.Low <= p["stop_now"]:
                px = round(min(p["stop_now"], b.Open) - SLIP, 2); return self.close(acct, st, px, "stop" if not p["half"] else "breakeven", now)
            if not p["half"] and b.High >= p["t1"]:
                h = p["open_sh"] // 2; p["realized"] += (p["t1"] - p["entry"]) * h; p["open_sh"] -= h; p["half"] = True
                p["stop_now"] = p["entry"]; log(f"[${acct}] HALF OFF {h} {p['t']} @ {p['t1']} (+1R), stop to breakeven", now)
                if ALP: ALP.breakeven(acct, p)
            if b.High >= p["target"]: return self.close(acct, st, p["target"], "target", now)
        if p["strat"] != "eod_squeeze" and now.time() >= dt.time(15, 55) and len(d):
            self.close(acct, st, round(float(d.Close.iloc[-1]) - SLIP, 2), "time", now)

    def close(self, acct, st, px, why, now):
        p = st["pos"]; pnl = round(p["realized"] + (px - p["entry"]) * p["open_sh"], 2)
        log(f"[${acct}] EXIT {p['open_sh']} {p['t']} @ {px} ({why}) total P&L ${pnl}", now)
        record(dict(date=str(self.day), account=acct, strategy=p["strat"], ticker=p["t"], shares=p["shares"], entry=p["entry"],
                    stop=p["stop"], half_at=p["t1"], target=p["target"], exit=px, exit_reason=why, pnl=pnl,
                    R=round(pnl / (acct * RISKPCT), 2), reason=p["reason"]))
        if ALP:
            if why in ("time", "next open"): ALP.flatten(acct, p)
            ALP.reconcile(acct, p, pnl, self.day)
        st["pos"] = None; st["done"] = True

    def eod_overnight(self, next_open_px, now):
        """sell overnight eod_squeeze holds at next day's first price"""
        for acct, st in self.S.items():
            p = st["pos"]
            if p and p["strat"] == "eod_squeeze" and p["t"] in next_open_px:
                self.close(acct, st, round(next_open_px[p["t"]] - SLIP, 2), "next open", now)

# ---------- replay
def replay(day, tickers):
    log(f"=== REPLAY {day} on {tickers}")
    full = {t: fetch(t, day) for t in tickers}; prev = {t: prev_close(t, day) for t in tickers}
    for t in tickers: catalyst(t)
    E = Engine(day)
    for m in pd.date_range(f"{day} 09:31", f"{day} 15:59", freq="1min", tz=ET):
        data = {t: (r[r.index < m], pm) for t, (r, pm) in full.items()}
        E.step(m.to_pydatetime(), data, prev)
    nxt = day + dt.timedelta(days=1)
    while nxt.weekday() >= 5: nxt += dt.timedelta(days=1)
    held = [st["pos"]["t"] for st in E.S.values() if st["pos"]]
    if held:
        px = {}
        for t in set(held):
            r, _ = fetch(t, nxt, pre=False)
            if len(r): px[t] = float(r.Open.iloc[0])
        E.eod_overnight(px, dt.datetime.combine(nxt, dt.time(9, 31), ET))

# ---------- live (resumable: state saved to state.pkl so cloud jobs can hand off)
import pickle, subprocess
STATE = f"{BASE}/state.pkl"
def save_state(day, E, U, prev):
    pickle.dump(dict(day=day, S=E.S if E else None, U=U, prev=prev, CAT=CAT), open(STATE, "wb"))
def git_sync(msg):
    if os.environ.get("GITHUB_ACTIONS") != "true": return
    cmd = f'cd "{BASE}" && git add -A && (git diff --cached --quiet || git commit -qm "{msg}") && (git push -q || (git pull -q --rebase && git push -q))'
    subprocess.run(cmd, shell=True)

def live():
    global ALP
    ALP = Alpaca() if Alpaca().on else None
    log("alpaca paper mirror: " + ("ON" if ALP else "off"))
    hours = float(os.environ.get("MAX_HOURS", "0")) or None
    stop_at = time.time() + hours * 3600 if hours else None
    start_date = dt.date.fromisoformat(os.environ["START_DATE"]) if os.environ.get("START_DATE") else None
    day, E, U, prev = None, None, [], {}
    if os.path.exists(STATE):
        st = pickle.load(open(STATE, "rb")); CAT.update(st.get("CAT") or {})
        day, U, prev = st["day"], st["U"], st["prev"]
        if st["S"] is not None: E = Engine(day); E.S = st["S"]
        log(f"resumed state from {day}")
    log("bot3 live start" + (f" (max {hours}h)" if hours else ""))
    last_sync = time.time()
    while True:
        now = dt.datetime.now(ET)
        if stop_at and time.time() > stop_at: break
        if stop_at and ((start_date and now.date() < start_date) or now.weekday() >= 5): log("not a trading day for this run, exiting"); break
        if now.weekday() < 5 and now.time() >= dt.time(16, 2) and E and day == now.date() and stop_at: break  # cloud: done for the day
        if (start_date and now.date() < start_date) or now.weekday() >= 5 or not (dt.time(9, 31) <= now.time() < dt.time(16, 0)):
            if stop_at and now.time() >= dt.time(16, 0): break
            time.sleep(30); continue
        if day != now.date():
            carry = [(a, st) for a, st in E.S.items() if st["pos"] and st["pos"]["strat"] == "eod_squeeze"] if E else []
            day = now.date(); E = Engine(day)
            if carry:
                for a, st in carry: E.S[a] = st
                px = {}
                for a, st in carry:
                    r, _ = fetch(st["pos"]["t"], day, pre=False)
                    if len(r): px[st["pos"]["t"]] = float(r.Open.iloc[0])
                E.eod_overnight(px, now)
            if ALP and not carry: ALP.req("DELETE", "/orders")
            if is_opex(day): log("monthly opex day: no new trades (playbook rule)")
            try: market_brief(day)
            except Exception as e: log(f"brief error {e}")
            U = scan(); prev = {t: prev_close(t, day) for t in U}; log(f"new day universe={U}")
            save_state(day, E, U, prev)
        if not is_opex(day) and now.time() < dt.time(10, 30) and now.minute % 15 == 0:
            for t in scan():
                if t not in U: U.append(t); prev[t] = prev_close(t, day)
        try:
            data = {}
            for t in set(U) | {st["pos"]["t"] for st in E.S.values() if st["pos"]} | {st["pending"]["t"] for st in E.S.values() if st["pending"]}:
                r, pm = fetch(t, day); data[t] = (r[r.index < now.replace(second=0, microsecond=0)] if len(r) else r, pm)
            if is_opex(day):
                for st in E.S.values(): st["done"] = st["done"] or (not st["pos"] and not st["pending"])
            E.step(now, data, prev)
            save_state(day, E, U, prev)
        except Exception as e: log(f"error {e}")
        if now.minute % 10 == 0:
            log("status " + " ".join(f"{a}:{'pos '+v['pos']['t'] if v['pos'] else 'pending' if v['pending'] else 'done' if v['done'] else 'watching'}" for a, v in E.S.items()))
        if time.time() - last_sync > 1800: git_sync(f"bot update {now:%Y-%m-%d %H:%M}"); last_sync = time.time()
        time.sleep(max(5, 62 - dt.datetime.now(ET).second))
    if E: save_state(day, E, U, prev)
    log("bot3 session end"); git_sync(f"bot session end {dt.datetime.now(ET):%Y-%m-%d %H:%M}")

def configure():
    a = Alpaca()
    if not a.on: log("configure: alpaca not configured or not paper"); return
    before = a.req("GET", "/account/configurations")
    log(f"configure before: {before}")
    after = a.req("PATCH", "/account/configurations", dict(max_margin_multiplier="1", no_shorting=True, fractional_trading=False))
    log(f"configure after: {after}")
    acc = a.req("GET", "/account") or {}
    log(f"account: equity={acc.get('equity')} cash={acc.get('cash')} buying_power={acc.get('buying_power')} multiplier={acc.get('multiplier')} pattern_day_trader={acc.get('pattern_day_trader')} shorting_enabled={acc.get('shorting_enabled')}")
    git_sync("configure")

def selftest():
    a = Alpaca()
    if a.on:
        acc = a.req("GET", "/account") or {}; clk = a.req("GET", "/clock") or {}
        log(f"selftest alpaca: status={acc.get('status')} equity={acc.get('equity')} buying_power={acc.get('buying_power')} market_open={clk.get('is_open')}")
    else: log("selftest alpaca: not configured or not paper")
    log(f"selftest benzinga: {len(news_benzinga(None, 6, 5))} recent headlines")
    log(f"selftest sec SKYD filings 30d: {sec_filings('SKYD', 30)[:3]}")
    log(f"selftest wires SECZ: {[n['t'][:60] for n in news_wires('SECZ', 72)][:2]}")
    market_brief()
    log("selftest: scanning"); U = scan(); log(f"selftest universe={U}")
    if U:
        r, pm = fetch(U[0], dt.datetime.now(ET).date()); log(f"selftest {U[0]} bars={len(r)} premarket={len(pm)}")
    git_sync("selftest")

if __name__ == "__main__":
    if MODE == "replay": replay(dt.date.fromisoformat(sys.argv[2]), sys.argv[3].split(","))
    elif MODE == "selftest": selftest()
    elif MODE == "configure": configure()
    elif MODE == "brief": market_brief(); git_sync("market brief")
    else: live()
