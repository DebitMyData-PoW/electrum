# DebitMyData-Electrum

DebitMyData (DMD) fork of [Electrum](https://github.com/spesmilo/electrum) 4.8.2.
Chain parameters follow DebitMyData Core v1.3.3 (`src/kernel/chainparams.cpp`, `src/pow.cpp`).

## What differs from upstream Electrum

| Area | DebitMyData value |
|---|---|
| Addresses | P2PKH version 30, P2SH 31, bech32 HRP `dm`, WIF 0x9e (158) |
| Extended keys | standard xpub/xprv headers `0x04dab21e` / `0x04daade4` (DMD Core `EXT_PUBLIC_KEY` / `EXT_SECRET_KEY`) |
| BIP44 coin type | 4134 (SLIP-0044 "DebitMyData") |
| Genesis | `00000992d19e3ed58ddf4117b597955752ff029e7256487a47557a24aeb4cadd` |
| Difficulty | legacy retarget every 8 blocks below height 120, LWMA (N=60, T=150 s) from 120 — exact port of DMD Core, incl. 256-bit wrap-around |
| Chain anchor | block 70159 must be `00000000000004b1c66c5c86b9af015e2c8c972a3e6c22b6fb3b0c799388db2a` (DMD Core `mandatory_block_hash`) |
| Payment links | `debitmydata:` |
| Units | DMD, mDMD, debits (µDMD), data (smallest unit); fee rates in data/vB |
| Data folder | `%APPDATA%\DebitMyData-Electrum`, `~/.debitmydata-electrum` |
| Servers | `electrum01`–`electrum06.debitmydata.network` (`electrum/chains/mainnet/servers.json`) |
| Explorer | https://chain.debitmydata.io/ |

Disabled because they only work for Bitcoin, or need Lightning, which DebitMyData does not have:
Lightning (`LIGHTNING_SUPPORTED = False`, which also disables submarine swaps, NWC and the watchtower),
fiat exchange rates (`FX_SUPPORTED = False`), the update checker (`UPDATE_CHECK_SUPPORTED = False`),
automatic crash reports, TrustedCoin 2FA, the labels sync plugin, and hardware wallet plugins.

## Header verification and checkpoints

Every header is verified with DebitMyData's own difficulty rules (`electrum/blockchain.py`,
`dmd_get_next_work_required`). The port was cross-checked against DMD Core's compiled `pow.cpp`
on 343,680 randomized heights (including timestamp edge cases and 256-bit overflow) with zero
mismatches. `tests/test_dmd_blockchain.py` covers sync, rejection of wrong difficulty / proof of work,
the chain anchor, chain work, forks and checkpoints.

`electrum/chains/mainnet/checkpoints.json` is currently empty, so a new wallet downloads and verifies
all headers from genesis (about 0.1 s of CPU per 2016 headers). To add checkpoints later:

1. Let a wallet built from this tree sync fully, then copy its `blockchain_headers` file
   (in the data folder above) somewhere else.
2. Run `python3 contrib/dmd_make_checkpoints.py path/to/blockchain_headers`.
   It re-verifies every header, then writes `checkpoints.json` and `checkpoints_tail.json`
   (LWMA needs the 60+ headers just below the last checkpoint; the wallet installs them from
   the tail file).
3. Commit both files.

## Upstream tests

Most of Electrum's own tests use Bitcoin mainnet vectors (`bc1…`/`1…` addresses, `xpub` keys,
`bitcoin:` URIs, `lnbc` invoices) or disabled features (Lightning, 2FA, Trezor), so about 160 of them
fail on this fork by design. Run `pytest tests/test_dmd_blockchain.py tests/test_blockchain.py`
for the DebitMyData-specific checks.
