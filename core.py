"""Shared trading logic used by BOTH the live bot and the backtester, so they can never drift apart.
Strategies, their time windows, signal features, slippage and the trade-management simulator."""
import re, math, datetime as dt
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
RISKPCT = 0.01
T = dt.time


def slip(px):
    """Per-side cost: at least 2 cents, 0.15% on pricier stocks (spread + slippage)."""
    return round(max(0.02, 0.0015 * float(px)), 2)


def add_ind(rth):
    rth = rth.copy()
    tp = (rth.High + rth.Low + rth.Close) / 3
    rth["vwap"] = (tp * rth.Volume).cumsum() / rth.Volume.cumsum().replace(0, math.nan)
    rth["e9"] = rth.Close.ewm(span=9).mean()
    rth["e21"] = rth.Close.ewm(span=21).mean()
    return rth


# ---------- strategies: f(d, pm, chg, now_time) -> (stop, reason) | None.  d = completed regular-session bars
def vwap_pullback(d, pm, chg, now):
    if not (T(10, 0) <= now <= T(15, 30)) or len(d) < 30 or chg < 0.04: return None
    b = d.iloc[-1]
    if b.Low <= b.vwap * 1.003 and b.Close > b.vwap and b.Close > b.Open and d.Close.iloc[-30:].mean() > d.vwap.iloc[-30:].mean():
        return float(d.Low.iloc[-5:].min()) - 0.01, f"VWAP pullback: +{chg:.1%}, dipped to VWAP {b.vwap:.2f}, reclaimed with green bar"

def orb5(d, pm, chg, now):
    if not (T(9, 36) <= now <= T(11, 0)) or len(d) < 6: return None
    r = d.iloc[:5]; hi, lo = float(r.High.max()), float(r.Low.min())
    if r.Close.iloc[-1] <= r.Open.iloc[0]: return None
    b, prior = d.iloc[-1], d.iloc[5:-1]
    if b.Close > hi and (prior.empty or prior.Close.max() <= hi):
        return max(lo, b.Close * 0.97), f"5-min ORB: green first 5 min, closed above range high {hi:.2f}"

def orb15(d, pm, chg, now):
    if not (T(9, 46) <= now <= T(11, 30)) or len(d) < 16: return None
    r = d.iloc[:15]; hi, lo = float(r.High.max()), float(r.Low.min()); b, prior = d.iloc[-1], d.iloc[15:-1]
    if b.Close > hi and b.Close > b.vwap and (prior.empty or prior.Close.max() <= hi):
        return (hi + lo) / 2, f"15-min ORB: closed above 15-min high {hi:.2f}, above VWAP"

def hod_break(d, pm, chg, now):
    if not (T(9, 45) <= now <= T(11, 30)) or len(d) < 20 or chg < 0.10: return None
    b, prev = d.iloc[-1], d.iloc[:-1]; hod = float(prev.High.max()); since = prev.index[-1] - prev.High.idxmax()
    if b.Close > hod and since >= pd.Timedelta(minutes=10) and b.Volume > prev.Volume.iloc[-20:].mean() * 1.5:
        return float(d.Low.iloc[-10:].min()) - 0.01, f"Gap-and-go: +{chg:.1%}, based {int(since.total_seconds()//60)} min, broke HOD {hod:.2f} on 1.5x vol"

def bull_flag(d, pm, chg, now):
    if not (T(9, 45) <= now <= T(14, 0)) or len(d) < 25 or chg < 0.04: return None
    pole, flag, b = d.iloc[-23:-8], d.iloc[-8:-1], d.iloc[-1]
    rise, fr = pole.High.max() / pole.Low.min() - 1, flag.High.max() / flag.Low.min() - 1
    if rise >= 0.03 and fr <= 0.015 and flag.Volume.mean() < pole.Volume.mean() and b.Close > flag.High.max() and b.Close > b.vwap:
        return float(flag.Low.min()) - 0.01, f"Bull flag: {rise:.1%} pole, {fr:.1%} flag on light vol, broke {flag.High.max():.2f}"

def afternoon_hod(d, pm, chg, now):
    if not (T(13, 0) <= now <= T(15, 0)) or len(d) < 60 or chg < 0.05: return None
    b, prev = d.iloc[-1], d.iloc[:-1]; hod = float(prev.High.max())
    if b.Close > hod and b.Close > b.vwap and b.Volume > prev.Volume.iloc[-30:].mean() * 1.5:
        return float(d.Low.iloc[-15:].min()) - 0.01, f"Afternoon HOD: +{chg:.1%}, new high {hod:.2f} after 1pm on 1.5x vol"

def pm_high_break(d, pm, chg, now):  # playbook setup A
    if not (T(9, 35) <= now <= T(10, 30)) or len(d) < 5 or pm is None or len(pm) < 10 or chg < 0.03: return None
    pmh = float(pm.High.max()); b, prior = d.iloc[-1], d.iloc[:-1]
    if b.Close > pmh and b.Close > b.vwap and prior.Close.max() <= pmh:
        return float(d.Low.iloc[-5:].min()) - 0.01, f"Premarket-high break: closed above PM high {pmh:.2f}, above VWAP"

def ema_bounce(d, pm, chg, now):  # playbook setup E
    if not (T(10, 0) <= now <= T(15, 0)) or len(d) < 40 or chg < 0.03: return None
    b = d.iloc[-1]
    if b.e9 > b.e21 > d.e21.iloc[-10] and b.Low <= b.e21 * 1.002 and b.Close > b.e9 and b.Close > b.Open and b.Close > b.vwap:
        return min(float(d.Low.iloc[-3:].min()), b.e21 * 0.995) - 0.01, f"9/21 EMA bounce: tagged 21 EMA {b.e21:.2f}, closed back over 9 EMA"

def eod_squeeze(d, pm, chg, now):  # playbook setup C: hold overnight, sell next open
    if not (T(15, 30) <= now <= T(15, 50)) or len(d) < 300 or chg < 0.04: return None
    b = d.iloc[-1]; hod = float(d.High.max())
    if b.Close >= hod * 0.99 and b.Close > b.vwap and d.Close.iloc[-30:].mean() > d.vwap.iloc[-30:].mean():
        return float(d.Low.iloc[-30:].min()) - 0.01, f"EOD squeeze: +{chg:.1%}, within 1% of HOD {hod:.2f}, hold to next open"

def failed_breakdown(d, pm, chg, now):  # fake-out trade: flush below opening-range low traps sellers, reclaim = long
    if not (T(9, 50) <= now <= T(14, 30)) or len(d) < 25 or chg < 0.02: return None
    orl = float(d.Low.iloc[:15].min()); recent, b = d.iloc[-10:-1], d.iloc[-1]
    flush = float(recent.Low.min())
    if flush < orl * 0.998 and b.Close > orl and b.Close > b.Open and b.Close > d.High.iloc[-2] and b.Volume > d.Volume.iloc[-20:-1].mean():
        return flush - 0.01, f"Failed breakdown: flushed to {flush:.2f} under opening-range low {orl:.2f}, reclaimed it"

STRATS = {f.__name__: f for f in [vwap_pullback, orb5, orb15, hod_break, bull_flag, afternoon_hod, pm_high_break, ema_bounce, eod_squeeze, failed_breakdown]}
WINDOWS = {"vwap_pullback": (T(10, 0), T(15, 30)), "orb5": (T(9, 36), T(11, 0)), "orb15": (T(9, 46), T(11, 30)),
           "hod_break": (T(9, 45), T(11, 30)), "bull_flag": (T(9, 45), T(14, 0)), "afternoon_hod": (T(13, 0), T(15, 0)),
           "pm_high_break": (T(9, 35), T(10, 30)), "ema_bounce": (T(10, 0), T(15, 0)), "eod_squeeze": (T(15, 30), T(15, 50)),
           "failed_breakdown": (T(9, 50), T(14, 30))}
MINCHG = {"vwap_pullback": 0.04, "orb5": -9, "orb15": -9, "hod_break": 0.10, "bull_flag": 0.04, "afternoon_hod": 0.05,
          "pm_high_break": 0.03, "ema_bounce": 0.03, "eod_squeeze": 0.04, "failed_breakdown": 0.02}


def valid_risk(price, stop):
    r = price - stop
    return 0.02 <= r <= 0.04 * price


# ---------- features (identical live and in backtest)
CAT_KW = {"earnings": r"earnings|results|revenue|eps|quarter|guidance",
          "fda": r"fda|approv|clearance|phase \d|trial|pdufa",
          "deal": r"contract|partnership|agreement|award|order|collaborat|launch",
          "analyst": r"upgrade|price target|initiat|outperform|overweight|buy rating",
          "mna": r"acqui|merger|buyout|takeover"}
NUM = ["minute", "chg", "gap", "log_rvol", "vwap_dist", "risk_pct", "hod_dist", "log_pm_rvol", "log_price", "spy_chg", "cat",
       "cat_earnings", "cat_fda", "cat_deal", "cat_analyst", "cat_mna"]

def features(strat, d, pm, chg, now, prev_close, adv, spy_chg, cat, stop):
    b = d.iloc[-1]; price = float(b.Close)
    mins = now.hour * 60 + now.minute - 570
    frac = max(mins / 390, 0.01)
    rvol = float(d.Volume.sum()) / (adv * frac) if adv else 1.0
    pmv = float(pm.Volume.sum()) / adv if (adv and pm is not None and len(pm)) else 0.0
    c = cat or ""
    f = dict(strategy=strat, minute=mins, chg=chg, gap=float(d.Open.iloc[0]) / prev_close - 1,
             log_rvol=math.log1p(max(rvol, 0)), vwap_dist=(price / float(b.vwap) - 1) if b.vwap == b.vwap else 0.0,
             risk_pct=(price - stop) / price, hod_dist=price / float(d.High.max()) - 1, log_pm_rvol=math.log1p(max(pmv, 0)),
             log_price=math.log(max(price, 0.01)), spy_chg=float(spy_chg or 0.0), cat=1 if c and not c.startswith("NEG") else 0)
    for k, rx in CAT_KW.items():
        f["cat_" + k] = 1 if c and re.search(rx, c, re.I) else 0
    return f


# ---------- trade simulator (mirrors the live Engine exactly)
def simulate(rth, i, stop, strat, next_open=None, exit_time=T(15, 55)):
    """Signal on completed bar i; enter at bar i+1 open + slip. Half off at +1R, stop to breakeven, rest at +2R,
    time exit at 15:55 (eod_squeeze: next open). Returns dict with R (in units of initial risk)."""
    if i + 1 >= len(rth): return None
    o, h, l, c = (rth[k].values for k in ("Open", "High", "Low", "Close")); idx = rth.index
    entry = o[i + 1] + slip(o[i + 1]); risk = entry - stop
    if risk < max(0.01, 0.002 * entry): return None  # fill gapped through the stop: no trade
    t1, tgt = entry + risk, entry + 2 * risk
    stop_now, half, realized, rem = stop, False, 0.0, 1.0
    for j in range(i + 1, len(rth)):
        if strat != "eod_squeeze" and idx[j].time() >= exit_time:
            px = c[j - 1] - slip(c[j - 1]); realized += rem * (px - entry)
            return dict(entry=entry, risk=risk, exit=px, why="time", R=realized / risk, held=j - i)
        if l[j] <= stop_now:
            px = min(stop_now, o[j]) - slip(stop_now); realized += rem * (px - entry)
            return dict(entry=entry, risk=risk, exit=px, why="breakeven" if half else "stop", R=realized / risk, held=j - i)
        if not half and h[j] >= t1:
            realized += 0.5 * (t1 - entry); rem = 0.5; half = True; stop_now = entry
        if h[j] >= tgt:
            realized += rem * (tgt - entry)
            return dict(entry=entry, risk=risk, exit=tgt, why="target", R=realized / risk, held=j - i)
    if strat == "eod_squeeze" and next_open:
        px = next_open - slip(next_open); realized += rem * (px - entry)
        return dict(entry=entry, risk=risk, exit=px, why="next open", R=realized / risk, held=len(rth) - i)
    px = c[-1] - slip(c[-1]); realized += rem * (px - entry)
    return dict(entry=entry, risk=risk, exit=px, why="close", R=realized / risk, held=len(rth) - i)


# ---------- trade filter (meta-model) application
def model_score(model, f):
    if not model or not model.get("enabled"): return None
    x = [(f.get(k, 0.0) - m) / s for k, m, s in zip(model["num"], model["mean"], model["std"])]
    x += [1.0 if f["strategy"] == s else 0.0 for s in model["strats"]]
    z = model["intercept"] + sum(a * b for a, b in zip(model["coef"], x))
    return 1 / (1 + math.exp(-z))


# ---------- variant engine: same signal, different entry/exit plans. Returns GROSS R (no costs) plus
# cost_units = how many market-order "sides" the trade used (fractions for partial exits), so any cost
# model can be applied later: net R = gross R - cost_units * cost_per_side($) / risk($).
ENTRIES = ("mkt", "lim")            # mkt: buy next bar open at market; lim: limit at signal close, good for 3 bars
PLANS = ("h2", "r3", "tr")          # h2: half at 1R + rest at 2R (current); r3: all at 3R; tr: half at 1R, trail rest on 9 EMA close


def sim_variant(rth, i, stop, strat, entry_mode, plan, next_open=None, exit_time=T(15, 55)):
    n = len(rth)
    if i + 1 >= n: return None
    o, h, l, c = (rth[k].values for k in ("Open", "High", "Low", "Close")); e9 = rth["e9"].values; idx = rth.index
    if entry_mode == "mkt":
        j0, px, cu = i + 1, float(o[i + 1]), 1.0
    else:
        lim, j0 = float(c[i]), None
        for j in range(i + 1, min(i + 4, n)):
            if l[j] <= lim: j0, px = j, min(float(o[j]), lim); break
        if j0 is None: return dict(filled=0)
        cu = 0.0
    risk = px - stop
    if risk < max(0.01, 0.002 * px): return None
    t1, t2, t3 = px + risk, px + 2 * risk, px + 3 * risk
    stop_now, half, rem, gross = stop, False, 1.0, 0.0
    for j in range(j0, n):
        if strat != "eod_squeeze" and idx[j].time() >= exit_time:
            gross += rem * (c[j - 1] - px); cu += rem; return dict(filled=1, Rg=gross / risk, cu=cu, why="time", entry=px, risk=risk)
        if l[j] <= stop_now:
            gross += rem * (min(stop_now, o[j]) - px); cu += rem
            return dict(filled=1, Rg=gross / risk, cu=cu, why="breakeven" if half else "stop", entry=px, risk=risk)
        if plan == "r3":
            if h[j] >= t3: gross += rem * (t3 - px); return dict(filled=1, Rg=gross / risk, cu=cu, why="target", entry=px, risk=risk)
            continue
        if not half and h[j] >= t1:
            gross += 0.5 * (t1 - px); rem = 0.5; half = True; stop_now = px
        if plan == "h2" and h[j] >= t2:
            gross += rem * (t2 - px); return dict(filled=1, Rg=gross / risk, cu=cu, why="target", entry=px, risk=risk)
        if plan == "tr" and half and j > j0 and c[j] < e9[j]:
            gross += rem * (c[j] - px); cu += rem; return dict(filled=1, Rg=gross / risk, cu=cu, why="trail", entry=px, risk=risk)
    last = next_open if (strat == "eod_squeeze" and next_open) else c[-1]
    gross += rem * (last - px); cu += rem
    return dict(filled=1, Rg=gross / risk, cu=cu, why="next open" if strat == "eod_squeeze" and next_open else "close", entry=px, risk=risk)


def variant_cols(rth, i, stop, strat, next_open=None, exit_time=T(15, 55)):
    """flat dict of every entry x plan variant for one signal (gross R, cost units, entry, risk)"""
    out = {}
    for e in ENTRIES:
        for p in PLANS:
            v = sim_variant(rth, i, stop, strat, e, p, next_open, exit_time); k = f"{e}_{p}"
            if not v: out.update({f"Rg_{k}": None, f"cu_{k}": None, f"px_{k}": None, f"rk_{k}": None}); continue
            if not v["filled"]: out.update({f"Rg_{k}": None, f"cu_{k}": None, f"px_{k}": None, f"rk_{k}": None, f"nofill_{e}": 1}); continue
            out.update({f"Rg_{k}": round(v["Rg"], 4), f"cu_{k}": round(v["cu"], 3), f"px_{k}": round(v["entry"], 4), f"rk_{k}": round(v["risk"], 4)})
    return out
