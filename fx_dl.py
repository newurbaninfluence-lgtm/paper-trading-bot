"""Download Dukascopy 1-minute FX candles (free, bank-grade feed) and save hourly bars. Usage: python fx_dl.py OUT PAIRS START END"""
import lzma, struct, time, os, sys, datetime as dt, urllib.request, urllib.error, pandas as pd
OUT = sys.argv[1]; PAIRS = sys.argv[2].split(","); start = dt.date.fromisoformat(sys.argv[3]); end = dt.date.fromisoformat(sys.argv[4])
PT = lambda p: 1e3 if "JPY" in p else 1e5
os.makedirs(OUT, exist_ok=True)
for p in PAIRS:
    f = f"{OUT}/{p}.csv"
    if os.path.exists(f): continue
    rows = []; d = start; miss = got = 0
    while d <= end:
        if d.weekday() != 5:
            u = f"https://datafeed.dukascopy.com/datafeed/{p}/{d.year}/{d.month-1:02d}/{d.day:02d}/BID_candles_min_1.bi5"
            for k in range(15):
                try:
                    b = urllib.request.urlopen(u, timeout=30).read(); break
                except urllib.error.HTTPError as e:
                    if e.code == 429: time.sleep(min(60, 5 * (k + 1))); continue
                    b = b""; break
                except Exception: time.sleep(3)
            else: b = b""
            got += bool(b); miss += (not b and d.weekday() < 5)
            if (got + miss) % 100 == 0: print(f"{p} {d} days ok {got}, missing {miss}", flush=True)
            if b:
                raw = lzma.decompress(b); base = dt.datetime(d.year, d.month, d.day)
                for i in range(0, len(raw), 24):
                    s, o, c, l, h, v = struct.unpack(">5if", raw[i:i+24])
                    if v > 0: rows.append((base + dt.timedelta(seconds=s), o / PT(p), h / PT(p), l / PT(p), c / PT(p)))
            time.sleep(float(os.environ.get('FX_PACE', '1.0')))
        d += dt.timedelta(days=1)
    df = pd.DataFrame(rows, columns=["t", "o", "h", "l", "c"]).set_index("t")
    df.resample("1h").agg(dict(o="first", h="max", l="min", c="last")).dropna().to_csv(f)
    print(p, len(df), "minute rows,", got, "days ok,", miss, "weekdays missing", flush=True)
