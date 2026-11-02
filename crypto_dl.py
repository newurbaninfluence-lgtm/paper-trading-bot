"""Download Alpaca crypto 1-hour bars (free, no key) from 2022. Usage: python crypto_dl.py OUT BTC/USD,ETH/USD,..."""
import json, sys, os, urllib.request, urllib.parse, pandas as pd
OUT = sys.argv[1]; SYMS = sys.argv[2].split(","); os.makedirs(OUT, exist_ok=True)
for s in SYMS:
    rows, tok = [], None
    while True:
        q = dict(symbols=s, timeframe="1Hour", start="2022-01-01T00:00:00Z", limit=10000)
        if tok: q["page_token"] = tok
        js = json.loads(urllib.request.urlopen("https://data.alpaca.markets/v1beta3/crypto/us/bars?" + urllib.parse.urlencode(q), timeout=60).read())
        rows += js["bars"].get(s, []); tok = js.get("next_page_token")
        if not tok: break
    df = pd.DataFrame(rows).rename(columns=dict(t="t")).set_index("t")[["o", "h", "l", "c", "v"]]
    df.to_csv(f"{OUT}/{s.replace('/', '')}.csv"); print(s, len(df), df.index[0], df.index[-1], flush=True)
