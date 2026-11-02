"""Download free 1-minute FX bars from histdata.com and save hourly bars (UTC). Usage: python fx_dl.py OUT PAIRS START_YEAR
Finished years come as one file per year; the current year comes month by month. histdata times are fixed EST (UTC-5, no DST).
Each downloaded period is cached in OUT/raw so later runs only fetch what's new."""
import io, os, re, sys, time, zipfile, http.cookiejar, datetime as dt, urllib.request, urllib.parse, pandas as pd

OUT, PAIRS, Y0 = sys.argv[1], sys.argv[2].split(","), int(sys.argv[3])
RAW = f"{OUT}/raw"; os.makedirs(RAW, exist_ok=True)
TODAY = dt.date.today()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
op.addheaders = [("User-Agent", "Mozilla/5.0")]


def fetch(pair, year, month=None):
    page = f"https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{pair.lower()}/{year}" + (f"/{month}" if month else "")
    html = op.open(page, timeout=60).read().decode("utf-8", "ignore")
    tk = re.search(r'name="tk" id="tk" value="([^"]+)"', html)
    if not tk: return None
    form = dict(tk=tk.group(1), date=str(year), datemonth=f"{year}{month:02d}" if month else str(year), platform="ASCII", timeframe="M1", fxpair=pair)
    req = urllib.request.Request("https://www.histdata.com/get.php", data=urllib.parse.urlencode(form).encode(), headers={"Referer": page})
    b = op.open(req, timeout=180).read()
    if not b.startswith(b"PK"): return None
    z = zipfile.ZipFile(io.BytesIO(b)); name = [n for n in z.namelist() if n.endswith(".csv")][0]
    d = pd.read_csv(z.open(name), sep=";", header=None, names=["t", "o", "h", "l", "c", "v"])
    d.index = pd.to_datetime(d.t, format="%Y%m%d %H%M%S") + pd.Timedelta(hours=5)   # fixed EST -> UTC
    return d[["o", "h", "l", "c"]].resample("1h").agg(dict(o="first", h="max", l="min", c="last")).dropna()


for p in PAIRS:
    parts = []
    for y in range(Y0, TODAY.year + 1):
        periods = [(y, None)] if y < TODAY.year else [(y, m) for m in range(1, TODAY.month + 1)]
        for yy, mm in periods:
            f = f"{RAW}/{p}_{yy}" + (f"-{mm:02d}" if mm else "") + ".csv"
            done = mm is None or (yy, mm) < (TODAY.year, TODAY.month)     # current month is never cached (still filling in)
            if done and os.path.exists(f): parts.append(pd.read_csv(f, index_col=0, parse_dates=True)); continue
            try: d = fetch(p, yy, mm)
            except Exception as e: print(f"{p} {yy}-{mm}: error {e}", flush=True); d = None
            if d is None or d.empty:
                print(f"{p} {yy}" + (f"-{mm:02d}" if mm else "") + ": not available", flush=True); continue
            if done: d.to_csv(f)
            parts.append(d); print(f"{p} {yy}" + (f"-{mm:02d}" if mm else "") + f": {len(d)} hours", flush=True)
            time.sleep(2)
    if parts:
        df = pd.concat(parts).sort_index(); df = df[~df.index.duplicated()]
        df.to_csv(f"{OUT}/{p}.csv"); print(f"{p}: {len(df)} hourly bars, {df.index[0]} to {df.index[-1]}", flush=True)
