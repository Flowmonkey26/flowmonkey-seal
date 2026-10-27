# flowmonkey-seal

Check FlowMonkey's levels yourself. Every trading morning, before the open, [FlowMonkey](https://flowmonkey.net) writes down the day's options gamma levels, hashes the file, and publishes the hash. After the close, anyone can download the same file, hash it again, and confirm nothing was changed once the market moved.

This repo holds a small script that does that check for you, plus an example for FlowMonkey's free public data feed. Both use only the Python standard library.

## Why a seal

Anyone can draw the right levels after the close. A seal proves the levels came first:

1. At 9:12 am Eastern, before the open, the day's levels go into one JSON file: price, the Apex (the biggest gamma strike), the call wall, the put wall, the gamma flip and the expected move.
2. The file is hashed with SHA-256, and the hash is published.
3. Each day's file also carries the previous day's hash. Changing any past day breaks every hash after it.
4. Since October 26, 2026, each morning's hash is also sent to [OpenTimestamps](https://opentimestamps.org), which anchors it in a Bitcoin block. That timestamp does not depend on FlowMonkey's servers.

Days before October 26, 2026 were timestamped later, in one catch-up run on October 26. For those days the Bitcoin proof shows the file existed by October 26, not that it existed before that day's open. The script says so when it checks one of those days.

## Check a day

```bash
git clone https://github.com/Flowmonkey26/flowmonkey-seal.git
cd flowmonkey-seal
python verify_seal.py                  # the latest sealed day
python verify_seal.py 2026-10-26       # one day
python verify_seal.py --chain 20       # the last 20 days
```

Example output:

```
2026-10-26  sealed 2026-10-26 13:12:01 UTC  MATCH  sha256 05d31898256c8053...
    timestamp: bitcoin block 973243, stamped 2026-10-26 13:12:04 UTC
```

13:12 UTC is 9:12 am Eastern, 18 minutes before the open.

### Without the script

```bash
curl -s https://api.flowmonkey.net/api/public/ledger | head -c 600     # the published hashes
curl -s https://api.flowmonkey.net/api/public/ledger/2026-10-26 | sha256sum
```

The two hashes must match.

### The Bitcoin timestamp

```bash
pip install opentimestamps-client
curl -sO https://api.flowmonkey.net/api/public/ledger/2026-10-26.ots
curl -s https://api.flowmonkey.net/api/public/ledger/2026-10-26 -o 2026-10-26
ots verify 2026-10-26.ots -f 2026-10-26
```

## Two seals

FlowMonkey publishes two morning files. Both are sealed at 9:12 am Eastern.

| File | What is in it | Where |
|---|---|---|
| The ledger | SPX, SPY, QQQ, IWM, NVDA, TSLA, AAPL, MSFT and AMZN, chained day to day, with Bitcoin timestamps | `/api/public/ledger/<day>` |
| All tickers | Every tracked ticker's price, Apex, ceiling, support and flip (in the file these are `cap` and `floor`) | `/api/public/sealed-levels/<day>` |

`verify_seal.py` checks the ledger. To check the all-tickers file, compare its hash with the `sealed.sha256` value in the free feed below:

```bash
curl -s https://api.flowmonkey.net/api/public/sealed-levels/2026-10-26 | sha256sum
```

## Free data feed

`examples/gamma_watch.py` reads the free public feed: dealer gamma levels for SPY, QQQ and IWM, 15 minutes delayed, no key and no sign-up. Please poll no faster than every 30 seconds.

```bash
python examples/gamma_watch.py
```

Full field list: [flowmonkey.net/developers](https://flowmonkey.net/developers). There's also an embeddable widget for sites and newsletters: [flowmonkey.net/embed](https://flowmonkey.net/embed).

## Grading

The sealed levels are graded against the next session, misses included, at [flowmonkey.net/ledger](https://flowmonkey.net/ledger) and [flowmonkey.net/receipts](https://flowmonkey.net/receipts).

Levels show where dealer hedging is concentrated. They are not targets, and nothing here is investment advice.

## License

MIT for the code in this repo. The data comes from FlowMonkey's public API and its terms at [flowmonkey.net/terms](https://flowmonkey.net/terms).
