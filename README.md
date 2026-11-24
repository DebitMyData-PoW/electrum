# DebitMyData Electrum

The lightweight wallet of the DebitMyData (DMD) chain, for **Windows, Linux, macOS and Android**.
It is a fork of [Electrum](https://github.com/spesmilo/electrum) 4.8.2, one of the oldest and most
trusted Bitcoin wallets, adapted to DebitMyData.

## What it offers

- **Your keys, on your device.** A seed phrase creates the wallet; nobody else holds its keys.
  Encrypted wallet files, watch-only wallets, multi-signature wallets and offline signing, as in
  Electrum.
- **Fast, without a full node.** It downloads only the block headers and asks DebitMyData's
  Electrum servers about its own addresses, so it is ready quickly on any computer or phone.
- **It checks the chain itself.** Every header is verified with DebitMyData's own difficulty rules,
  an exact port of DebitMyData Core's, and the chain must contain DebitMyData's anchor block: a
  server cannot feed it a false chain.
- **DebitMyData everywhere**: DMD addresses (`D…`, `dm1…`), `debitmydata:` payment links, amounts in
  DMD, mDMD, debits and data, and seed phrases from other wallets restored on DebitMyData's own
  derivation paths (coin type 4134).
- **Separate from Bitcoin's Electrum**: its own app, data folder and app ID, so both can be
  installed side by side.

Lightning, fiat exchange rates and the other Bitcoin-only features are switched off: the details,
and every value that differs from upstream Electrum, are in [DEBITMYDATA.md](DEBITMYDATA.md).

## Installation

Running it from its source, the tests, and building the Windows, Linux, macOS and Android release
files: see **[INSTALL.md](INSTALL.md)**.

## License

MIT, as Electrum ([LICENCE](LICENCE)). Electrum is © Thomas Voegtlin and the Electrum developers
([AUTHORS](AUTHORS)); the DebitMyData changes are © DebitMyData.
