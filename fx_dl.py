"""Download Dukascopy 1-minute FX candles (free, bank-grade feed) and save hourly bars.
Usage: python fx_dl.py OUT PAIRS START END
Resumable: each finished month is saved to OUT/raw/PAIR_YYYY-MM.csv and skipped next time (the workflow caches OUT/raw),
so a run that hits the rate limit or FX_MINUTES deadline keeps its progress. OUT/PAIR.csv is rebuilt from all saved months."""
import lzma, struct, time, os, sys, glob, datetime as dt, urllib.request, urllib.error, pandas as pd

OUT = sys.argv[1]; PAIRS = sys.argv[2].split(","); START = dt.date.fromisoformat(sys.argv[3]); END = dt.date.fromisoformat(sys.argv[4])
PACE = float(os.environ.get("FX_PACE", "1.0"))
DEADLINE = time.time() + 60 * float(os.environ.get("FX_MINUTES", "0") or 1e9)
PT = lambda p: 1e3 if "JPY" in p else 1e5
RAW = f"{OUT}/raw"; os.makedirs(RAW, exist_ok=True)


def day_rows(p, d):
    u = f"https://datafeed.dukascopy.com/datafeed/{p}/{d.year}/{d.month - 1:02d}/{d.day:02d}/BID_candles_min_1.bi5"
    for k in range(15):
        try:
            b = urllib.request.urlopen(u, timeout=30).read(); break
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(min(60, 5 * (k + 1))); continue
            return None
        except Exception: time.sleep(3)
    else: return None
    if not b: return []
    raw = lzma.decompress(b); base = dt.datetime(d.year, d.month, d.day); out = []
    for i in range(0, len(raw), 24):
        s, o, c, l, h, v = struct.unpack(">5if", raw[i:i + 24])
        if v > 0: out.append((base + dt.timedelta(seconds=s), o / PT(p), h / PT(p), l / PT(p), c / PT(p)))
    return out


def months():
    m = dt.date(START.year, START.month, 1)
    while m <= END:
        yield m
        m = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 1)


stopped = False
for m in months():                      # month by month across all pairs, so a deadline still leaves every pair the same length
    for p in PAIRS:
        f = f"{RAW}/{p}_{m:%Y-%m}.csv"
        nxt = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 1)
        complete = nxt <= END            # only finished months are saved for reuse
        if os.path.exists(f): continue
        if time.time() > DEADLINE: stopped = True; break
        rows, miss, d = [], 0, max(m, START)
        while d < nxt and d <= END:
            if d.weekday() != 5:
                r = day_rows(p, d)
                if r is None and d.weekday() < 5: miss += 1
                rows += r or []
                time.sleep(PACE)
            d += dt.timedelta(days=1)
        if not rows: continue
        df = pd.DataFrame(rows, columns=["t", "o", "h", "l", "c"]).set_index("t")
        df = df.resample("1h").agg(dict(o="first", h="max", l="min", c="last")).dropna()
        if complete and miss <= 2: df.to_csv(f)
        else: df.to_csv(f"{RAW}/{p}_{m:%Y-%m}.partial")
        print(f"{p} {m:%Y-%m}: {len(df)} hours, {miss} weekdays missing{'' if complete and miss <= 2 else ' (not cached)'}", flush=True)
    if stopped: print("deadline reached: stopping, progress is saved", flush=True); break

for p in PAIRS:
    parts = sorted(glob.glob(f"{RAW}/{p}_*.csv")) + sorted(glob.glob(f"{RAW}/{p}_*.partial"))
    if not parts: continue
    df = pd.concat(pd.read_csv(x, index_col=0) for x in parts).sort_index(); df = df[~df.index.duplicated()]
    df.to_csv(f"{OUT}/{p}.csv"); print(f"{p}: {len(df)} hourly bars, {df.index[0]} to {df.index[-1]}", flush=True)
for x in glob.glob(f"{RAW}/*.partial"): os.remove(x)
