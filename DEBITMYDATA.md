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
| Signed messages | prefix `DebitMyData Signed Message:\n` (DMD Core `MESSAGE_MAGIC`) |
| Android app ID | `io.debitmydata.electrum` |
| Units | DMD, mDMD, debits (µDMD), data (smallest unit); fee rates in data/vB |
| Data folder | `%APPDATA%\DebitMyData-Electrum`, `~/.debitmydata-electrum` |
| Servers | `electrum01`–`electrum06.debitmydata.network` (`electrum/chains/mainnet/servers.json`) |
| Explorer | https://chain.debitmydata.io/ |

Disabled because they only work for Bitcoin, or need Lightning, which DebitMyData does not have:
Lightning (`LIGHTNING_SUPPORTED = False`, which also disables submarine swaps, NWC and the watchtower),
fiat exchange rates (`FX_SUPPORTED = False`), the update checker (`UPDATE_CHECK_SUPPORTED = False`),
automatic crash reports, TrustedCoin 2FA, the labels sync plugin, the timelock recovery plugin
(its printed guides point to Bitcoin block explorers), and hardware wallet plugins.

User-facing text says DebitMyData / DMD / debits / data instead of Bitcoin / BTC / bits / sat.
Strings that changed have no translations yet, so they show in English in other languages
until the DebitMyData translations are added.

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

## Building the Windows wallet (on Ubuntu 24.04)

The build runs inside Docker (Debian + Wine), exactly like upstream Electrum's
reproducible builds. It must run from a **git clone** (the scripts refuse to build from a
plain folder), on an x86_64 machine with about 20 GB of free disk space.

1. Install Docker (Docker's official repository):

    ```
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl git
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin
    sudo usermod -aG docker $USER
    ```

    Log out and back in (or reboot), then check with `docker run hello-world`.
    Run the build as this normal user, not as root.

2. Get the DebitMyData source as a git clone:

    ```
    git clone https://github.com/DebitMyData-PoW/electrum_new.git
    cd electrum_new
    git checkout <your DebitMyData branch>
    git tag 4.8.2-dmd1          # optional: the newest tag becomes the version in the file names
    ```

3. Build:

    ```
    ./contrib/build-wine/build.sh
    ```

    The first run takes a long time (often 30-60 minutes or more): it builds the Docker image
    with Wine and Python, compiles libsecp256k1, zbar and libusb, and downloads the Python
    dependencies and Electrum's translations. Later runs reuse the cache.

    - For a reproducible build from a clean checkout of a commit: `ELECBUILD_COMMIT=HEAD ./contrib/build-wine/build.sh`
    - To force a fresh Docker image: `ELECBUILD_NOCACHE=1 ./contrib/build-wine/build.sh`
    - The Docker image installs pinned packages from `snapshot.debian.org`, which is sometimes slow
      or times out. If that step keeps failing and you don't need bit-for-bit reproducibility,
      change the two lines of `contrib/build-wine/apt.sources.list` to
      `deb http://deb.debian.org/debian trixie main` and `deb-src http://deb.debian.org/debian trixie main`.

4. The results are in `contrib/build-wine/dist/`:

    | File | What it is |
    |---|---|
    | `debitmydata-electrum-<version>-setup.exe` | Windows installer (installs to `Program Files\DebitMyData-Electrum`, registers `debitmydata:` links) |
    | `debitmydata-electrum-<version>.exe` | standalone executable, no installation |
    | `debitmydata-electrum-<version>-portable.exe` | portable version, keeps its data next to the .exe |

    Wallets and settings of the installed/standalone versions live in `%APPDATA%\DebitMyData-Electrum`.

5. Optional: without an Authenticode code-signing certificate, Windows SmartScreen shows an
   "unknown publisher" warning on first launch. With a certificate, sign the files using
   `contrib/build-wine/sign.sh` (see `contrib/build-wine/README.md`).

## Upstream tests

Most of Electrum's own tests use Bitcoin mainnet vectors (`bc1…`/`1…` addresses, `xpub` keys,
`bitcoin:` URIs, `lnbc` invoices) or disabled features (Lightning, 2FA, Trezor), so about 160 of them
fail on this fork by design. Run `pytest tests/test_dmd_blockchain.py tests/test_dmd_params.py tests/test_blockchain.py`
for the DebitMyData-specific checks.
