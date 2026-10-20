# DebitMyData-Electrum

DebitMyData (DMD) fork of [Electrum](https://github.com/spesmilo/electrum) 4.8.2.
Chain parameters follow DebitMyData Core v1.3.3 (`src/kernel/chainparams.cpp`, `src/pow.cpp`).

## What differs from upstream Electrum

| Area | DebitMyData value |
|---|---|
| Addresses | P2PKH version 30, P2SH 31, bech32 HRP `dm`, WIF 0x9e (158) |
| Extended keys | standard xpub/xprv headers `0x04dab21e` / `0x04daade4` (DMD Core `EXT_PUBLIC_KEY` / `EXT_SECRET_KEY`) |
| BIP44 coin type | 4134 (SLIP-0044 "DebitMyData"): suggested paths `m/44'/4134'/0'`, `m/49'/4134'/0'`, `m/84'/4134'/0'` and `m/48'/4134'/…` when restoring a BIP39 seed (desktop and Android). "Detect Existing Accounts" also scans the coin type 0 paths of the earlier DebitMyData-Electrum (4.7 fork). Wallets created with an Electrum seed use Electrum's fixed path (`m/0'` for segwit), which has no coin type, as in upstream Electrum |
| Genesis | `00000992d19e3ed58ddf4117b597955752ff029e7256487a47557a24aeb4cadd` |
| Difficulty | legacy retarget every 8 blocks below height 120, LWMA (N=60, T=150 s) from 120 — exact port of DMD Core, incl. 256-bit wrap-around |
| Chain anchor | block 70159 must be `00000000000004b1c66c5c86b9af015e2c8c972a3e6c22b6fb3b0c799388db2a` (DMD Core `mandatory_block_hash`) |
| Payment links | `debitmydata:` |
| Signed messages | prefix `DebitMyData Signed Message:\n` (DMD Core `MESSAGE_MAGIC`) |
| Android app ID | `io.debitmydata.electrum` |
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
| `electrum/gui/icons/android_electrum_icon_foreground.png` + `_background.png` | home-screen icon (adaptive icon, 432×432 = 108 dp; keep the artwork inside the central 264 px circle, the launcher crops the rest) | wallet artwork on a #161616 background |
| `electrum/gui/icons/android_electrum_icon_legacy.png` | icon on launchers without adaptive icons | wallet artwork, transparent corners |
| `electrum/gui/icons/electrum_presplash.png` | launch screen while the app starts (black background); 1 px = 1 dp | splash artwork, ~230 dp wide |
| `electrum/gui/qml/android_res/drawable-xxhdpi/presplash.png`, `drawable-xxxhdpi/presplash.png` | the same launch screen at 3× and 4× resolution, so it stays sharp | same artwork, 3× and 4× the size |
| `electrum/gui/icons/electrum_banner_dark.png` | banner on the About and Terms of Use screens | header artwork for dark backgrounds |
| `fastlane/metadata/android/en-US/images/icon.png` | store listing icon (512×512, full square) | same as the home-screen icon |

The three presplash files must show the artwork at the same size in dp (pixel width ×1, ×3, ×4).

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
    git clone https://github.com/DebitMyData-PoW/electrum.git
    cd electrum
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

## Releasing a new version

- Tag each release, e.g. `git tag 4.8.2-dmd1`. The newest tag becomes the version in the file names
  of every build (Windows, Linux, macOS).
- For every new DebitMyData release on the same Electrum version, increase `DMD_RELEASE` in
  `electrum/version.py` (1 → 2 → 3 …) and tag it `4.8.2-dmd2`, `4.8.2-dmd3` …
  Android uses it in the app's version code, and phones and Google Play refuse an update whose
  version code is not higher than the installed one. When moving to a new Electrum version, set it back to 1.

## Building the Linux wallet (AppImage, on Ubuntu 24.04)

Same machine and Docker setup as the Windows build, from the same git clone:

```
./contrib/build-linux/appimage/build.sh
```

The result is `dist/debitmydata-electrum-<version>-x86_64.AppImage` (in the project's top-level
`dist/` folder). Users make it executable (`chmod +x`) and run it; it works on most 64-bit Linux
distributions from 2020 on (glibc 2.31+). The first build takes a while; later builds reuse
`contrib/build-linux/appimage/.cache/`.

## Building the Android app (on Ubuntu 24.04)

Same machine and Docker setup. The first Android build is the slowest of all: the Docker image
downloads the Android SDK and NDK and compiles Python and Qt for Android (expect one to several
hours and roughly 30-40 GB of disk). Later builds reuse `.buildozer_qml/` and `contrib/android/.cache/`.

App ID: `io.debitmydata.electrum`. Architectures: `arm64-v8a` (almost all phones today),
`armeabi-v7a` (older 32-bit phones), `x86_64` (emulators, a few tablets), or `all`.

1. **Test build** (signed with a throwaway debug key, can be installed directly on a phone):

    ```
    ./contrib/android/build.sh qml arm64-v8a debug
    ```

2. **Create your release signing key, once.** Every update of the app must be signed with the same
   key; if it is lost, existing installs can never be updated. Keep several offline backups of
   `~/.keystore` and its password.

    ```
    sudo apt-get install -y openjdk-17-jre-headless      # provides keytool
    keytool -genkeypair -v -keystore ~/.keystore -alias debitmydata \
        -keyalg RSA -keysize 4096 -validity 10000
    ```

    Use the same password for the keystore and the key (keytool's default); the build uses one password for both.

3. **Release build (APKs, e.g. for GitHub releases / direct download):**

    ```
    read -s -p "Keystore password: " KSPW; echo
    ./contrib/android/build.sh qml all release "$KSPW"
    ```

    (`read -s` keeps the password out of your shell history.) Results:
    `dist/debitmydata-electrum-<version>-<arch>-release.apk`, one per architecture.

4. **Google Play:** new apps must be uploaded as an Android App Bundle (.aab):

    ```
    ELEC_ANDROID_AAB=1 ./contrib/android/build.sh qml arm64-v8a release "$KSPW"
    ```

    This gives `dist/debitmydata-electrum-<version>-arm64-v8a-release.aab`. With Google Play App Signing,
    the key in `~/.keystore` acts as your *upload key*. The AAB option is new in this fork and has not
    been tried yet: do a normal APK release build first, then try this.

## Building the macOS wallet (on a Mac)

macOS builds must run on macOS itself; they cannot be made on Linux. Upstream builds on an
Intel (x86_64) Mac with macOS 11 and the result targets x86_64 (it also runs on Apple Silicon
Macs through Rosetta). Building on an Apple Silicon Mac is not tested upstream.

1. Install the Xcode command line tools (`xcode-select --install`) and Homebrew (https://brew.sh).
2. Clone the repository and check out your release:

    ```
    git clone https://github.com/DebitMyData-PoW/electrum.git
    cd electrum
    git checkout 4.8.2-dmd1
    ```

3. Build:

    ```
    ./contrib/osx/make_osx.sh
    ```

    The script asks for your password once (it installs the pinned Python version with `sudo installer`).
    Results: `dist/DebitMyData-Electrum.app` and `dist/debitmydata-electrum-<version>-unsigned.dmg`.

4. Without an Apple Developer account (99 USD/year) the app is not signed or notarized, and users
   must right-click the app and choose **Open** the first time. With an account, sign and notarize
   with `contrib/osx/sign_osx.sh` (see `contrib/osx/README.md`).

The app is `DebitMyData-Electrum.app` with bundle ID `io.debitmydata.electrum`, so it installs next to
Bitcoin Electrum instead of replacing it; it stores its data in `~/.debitmydata-electrum`.

There is no iOS version: Electrum only supports Android on mobile.

## Upstream tests

Most of Electrum's own tests use Bitcoin mainnet vectors (`bc1…`/`1…` addresses, `xpub` keys,
`bitcoin:` URIs, `lnbc` invoices) or disabled features (Lightning, 2FA, Trezor), so about 160 of them
fail on this fork by design. Run `pytest tests/test_dmd_blockchain.py tests/test_dmd_params.py tests/test_dmd_derivation.py tests/test_blockchain.py`
for the DebitMyData-specific checks.
