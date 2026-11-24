# DebitMyData-Electrum

DebitMyData (DMD) fork of [Electrum](https://github.com/spesmilo/electrum) 4.8.2.
Chain parameters follow DebitMyData Core v1.3.3 (`src/kernel/chainparams.cpp`, `src/pow.cpp`).

## What differs from upstream Electrum

| Area | DebitMyData value |
|---|---|
| Addresses | P2PKH version 30, P2SH 31, bech32 HRP `dm`, WIF 0x9e (158) |
| Extended keys | standard xpub/xprv headers `0x04dab21e` / `0x04daade4` (DebitMyData Core `EXT_PUBLIC_KEY` / `EXT_SECRET_KEY`) |
| BIP44 coin type | 4134 (SLIP-0044 "DebitMyData"): suggested paths `m/44'/4134'/0'`, `m/49'/4134'/0'`, `m/84'/4134'/0'` and `m/48'/4134'/…` when restoring a BIP39 seed (desktop and Android). "Detect Existing Accounts" also scans the coin type 0 paths of the earlier DebitMyData-Electrum (4.7 fork). Wallets created with an Electrum seed use Electrum's fixed path (`m/0'` for segwit), which has no coin type, as in upstream Electrum |
| Genesis | `00000992d19e3ed58ddf4117b597955752ff029e7256487a47557a24aeb4cadd` |
| Difficulty | legacy retarget every 8 blocks below height 120, LWMA (N=60, T=150 s) from 120 — exact port of DebitMyData Core, incl. 256-bit wrap-around |
| Chain anchor | block 70159 must be `00000000000004b1c66c5c86b9af015e2c8c972a3e6c22b6fb3b0c799388db2a` (DebitMyData Core `mandatory_block_hash`) |
| Payment links | `debitmydata:` |
| Signed messages | prefix `DebitMyData Signed Message:\n` (DebitMyData Core `MESSAGE_MAGIC`) |
| Android app ID | `io.debitmydata.electrum` |
| Android app name | DMD Electrum Wallet (`title` in `contrib/android/buildozer_qml.spec`; the app ID must never change, or phones treat it as a different app) |
| Units | DMD, mDMD, debits (µDMD), data (smallest unit); fee rates in data/vB |
| Data folder | `%APPDATA%\DebitMyData-Electrum`, `~/.debitmydata-electrum` |
| Servers | `electrum01`–`electrum06.debitmydata.network` (`electrum/chains/mainnet/servers.json`) |
| Explorer | https://mempool.debitmydata.io/ |

Disabled because they only work for Bitcoin, or need Lightning, which DebitMyData does not have:
Lightning (`LIGHTNING_SUPPORTED = False`, which also disables submarine swaps, NWC and the watchtower),
fiat exchange rates (`FX_SUPPORTED = False`), the update checker (`UPDATE_CHECK_SUPPORTED = False`),
automatic crash reports, TrustedCoin 2FA, the labels sync plugin, the timelock recovery plugin
(its printed guides point to Bitcoin block explorers), and hardware wallet plugins.

User-facing text says DebitMyData / DMD / debits / data instead of Bitcoin / BTC / bits / sat.
Strings that changed have no translations yet, so they show in English in other languages
until the DebitMyData translations are added.

## Android images

| File | Shown as | Made from |
|---|---|---|
| `electrum/gui/qml/android_res/mipmap-*/icon.png` (48, 72, 96, 144, 192 px) | home-screen icon | wallet artwork on a transparent background, filling the image |
| `electrum/gui/qml/android_res/mipmap-*/icon_round.png` (same sizes) | home-screen icon on launchers that use round icons | round version of the wallet artwork |
| `electrum/gui/icons/android_electrum_icon_legacy.png` | fallback copy of the 192 px icon (`icon.filename`) | same as `icon.png` |
| `electrum/gui/icons/android_electrum_icon_foreground.png` + `_background.png` | not used: adaptive icon, switched off in `buildozer_qml.spec` because launchers crop it | |
| `electrum/gui/icons/electrum_presplash.png` | launch screen while the app starts (black background); 1 px = 1 dp | splash artwork, ~230 dp wide |
| `electrum/gui/qml/android_res/drawable-xxhdpi/presplash.png`, `drawable-xxxhdpi/presplash.png` | the same launch screen at 3× and 4× resolution, so it stays sharp | same artwork, 3× and 4× the size |
| `electrum/gui/icons/electrum_banner_dark.png` | banner on the About and Terms of Use screens | header artwork for dark backgrounds |
| `fastlane/metadata/android/en-US/images/icon.png` | store listing icon (512×512, full square) | wallet artwork on a #161616 background |

The three presplash files must show the artwork at the same size in dp (pixel width ×1, ×3, ×4).

## Header verification and checkpoints

Every header is verified with DebitMyData's own difficulty rules (`electrum/blockchain.py`,
`dmd_get_next_work_required`). The port was cross-checked against DebitMyData Core's compiled `pow.cpp`
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

## Running and building it

Running it from source, the tests, and building the Windows, Linux, macOS and Android release
files: [INSTALL.md](INSTALL.md).
