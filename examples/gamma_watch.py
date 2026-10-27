#!/usr/bin/env python3
"""Read FlowMonkey's free public gamma-watch feed: dealer gamma levels for
SPY, QQQ and IWM, 15 minutes delayed, no key and no sign-up.

Please poll no faster than every 30 seconds (the feed is cached for 60).
Levels are where dealer hedging is concentrated, not targets. Not advice.

    python examples/gamma_watch.py
"""
import json
import urllib.request

URL = "https://api.flowmonkey.net/api/public/gamma-watch"

req = urllib.request.Request(URL, headers={"User-Agent": "flowmonkey-seal-example/1.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    feed = json.loads(r.read())

print(f"session: {feed['session']}  (data {feed['delay_minutes']} min behind)")
print(feed["regime"])
sealed = feed.get("sealed") or {}
if sealed:
    print(f"this morning's all-tickers seal: {sealed['day']}  sha256 {sealed['sha256']}")
print()
for sym in feed.get("symbols", []):
    if not isinstance(sym, dict):
        continue
    print(f"{sym.get('symbol', '?'):4}  last {sym.get('last')}  "
          f"call wall {sym.get('call_wall')}  put wall {sym.get('put_wall')}  "
          f"Apex {sym.get('apex')}  flip {sym.get('flip')}")
