#!/usr/bin/env python3
"""Check FlowMonkey's sealed pre-open levels yourself.

Every trading morning at 9:12 ET, before the open, FlowMonkey writes one JSON
file with the day's levels (spot, Apex, call wall, put wall, gamma flip,
expected move) for SPX, SPY, QQQ, IWM, NVDA, TSLA, AAPL, MSFT and AMZN. It
hashes the file with SHA-256 and chains it: each file carries the previous
day's hash, so changing any past day breaks every hash after it. The hash is
also timestamped with OpenTimestamps, which anchors it in a Bitcoin block.

This script uses only the Python standard library.

    python verify_seal.py                 # check the latest sealed day
    python verify_seal.py 2026-10-26      # check one day
    python verify_seal.py --chain 20      # walk the last 20 days of the chain

For the Bitcoin timestamp, install the OpenTimestamps client
(pip install opentimestamps-client) and run the `ots verify` command this
script prints.
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.request

API = "https://api.flowmonkey.net/api/public/ledger"
UA = {"User-Agent": "flowmonkey-seal-verifier/1.0"}


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()


def index() -> list[dict]:
    return json.loads(get(API))["seals"]


def check_day(seal: dict, show_ots_cmd: bool = True) -> bool:
    day = seal["session"]
    raw = get(f"{API}/{day}")              # the exact sealed bytes
    actual = hashlib.sha256(raw).hexdigest()
    ok = actual == seal["sha256"]
    body = json.loads(raw)
    print(f"{day}  sealed {seal.get('sealed_at', '?')[:19]} UTC  "
          f"{'MATCH' if ok else 'MISMATCH'}  sha256 {actual[:16]}...")
    if not ok:
        print(f"    index says {seal['sha256']}")
    if body.get("prev_sha256") != seal.get("prev_sha256"):
        print("    previous-day hash inside the file does not match the index")
        ok = False
    ots = seal.get("ots") or {}
    if ots:
        stamped = str(ots.get("stamped_at") or "")[:19]
        sealed = str(seal.get("sealed_at") or "")[:19]
        print(f"    timestamp: {ots.get('status', 'pending')}, stamped {stamped} UTC")
        if stamped[:10] and sealed[:10] and stamped[:10] != sealed[:10]:
            # Proofs began 2026-10-25; earlier days were stamped in a catch-up run.
            print(f"    note: stamped after the seal day, so this proof shows the file existed "
                  f"by {stamped[:10]}, not that it existed before that day's open")
        if show_ots_cmd:
            print(f"    verify it yourself: curl -sO {seal.get('ots_url')} && "
                  f"curl -s {API}/{day} -o {day} && ots verify {day}.ots -f {day}")
    else:
        print("    timestamp: none for this day")
    return ok


def main(argv: list[str]) -> int:
    seals = index()                         # newest first
    if not seals:
        print("no seals published")
        return 1
    if argv and argv[0] == "--chain":
        n = int(argv[1]) if len(argv) > 1 else 10
        ok = True
        window = seals[: n + 1]
        for newer, older in zip(window, window[1:]):
            ok &= check_day(newer, show_ots_cmd=False)
            if newer.get("prev_sha256") and newer["prev_sha256"] != older["sha256"]:
                # gaps are normal around holidays and backfills; a mismatch is not
                print(f"    chain: {newer['session']} points at {newer['prev_sha256'][:16]}..., "
                      f"the next day listed is {older['session']} ({older['sha256'][:16]}...)")
        print("\nall files match their published hashes" if ok else "\nproblem found, see above")
        return 0 if ok else 2
    if argv:
        match = [s for s in seals if s["session"] == argv[0]]
        if not match:
            print(f"no seal for {argv[0]}")
            return 1
        return 0 if check_day(match[0]) else 2
    return 0 if check_day(seals[0]) else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
