# DebitMyData: BIP44/49/84/48 derivation paths must use coin type 4134 (SLIP-0044 "DebitMyData").

import os

from electrum import bitcoin, constants, keystore
from electrum.bip32 import BIP32Node
from electrum.bip39_recovery import account_discovery
from electrum.daemon import Daemon
from electrum.keystore import bip39_to_seed, bip44_derivation, purpose48_derivation
from electrum.plugin import Plugins
from electrum.simple_config import SimpleConfig
from electrum.wizard import NewWalletWizard

from . import ElectrumTestCase
from .test_wizard import DaemonMock

SEED_BIP39 = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'


def _address_at(path: str, script_type: str) -> str:
    root = BIP32Node.from_rootseed(bip39_to_seed(SEED_BIP39, passphrase=''), xtype='standard')
    pubkey = root.subkey_at_private_derivation(path).eckey.get_public_key_hex()
    return bitcoin.pubkey_to_address(script_type, pubkey)


class TestDmdDerivationPaths(ElectrumTestCase):

    def test_coin_type(self):
        self.assertEqual(4134, constants.net.BIP44_COIN_TYPE)

    def test_suggested_paths(self):
        # used by the desktop wizard; the mobile wizard builds the same paths from Network.bip44CoinType
        self.assertEqual("m/44h/4134h/0h", bip44_derivation(0, bip43_purpose=44))
        self.assertEqual("m/49h/4134h/0h", bip44_derivation(0, bip43_purpose=49))
        self.assertEqual("m/84h/4134h/0h", bip44_derivation(0, bip43_purpose=84))
        self.assertEqual("m/48h/4134h/0h/2h", purpose48_derivation(0, xtype='p2wsh'))
        self.assertEqual("m/48h/4134h/0h/1h", purpose48_derivation(0, xtype='p2wsh-p2sh'))

    def test_detect_accounts_list(self):
        formats = constants.BIP39_WALLET_FORMATS
        standard = {f['script_type']: f['derivation_path'] for f in formats if f['description'].startswith('Standard')}
        self.assertEqual({'p2pkh': "m/44'/4134'/0'", 'p2wpkh-p2sh': "m/49'/4134'/0'", 'p2wpkh': "m/84'/4134'/0'"}, standard)
        for f in formats:
            parts = f['derivation_path'].split('/')
            if len(parts) > 2 and parts[2] == "0'":
                # only the paths of the earlier DebitMyData-Electrum (4.7 fork) may use coin type 0
                self.assertTrue(f['description'].startswith('Earlier DebitMyData-Electrum'), f)

    async def test_account_discovery_finds_dmd_and_earlier_accounts(self):
        used = {
            _address_at("m/84'/4134'/0'/0/0", 'p2wpkh'),
            _address_at("m/44'/0'/0'/0/3", 'p2pkh'),  # funds left in a wallet from the 4.7 fork
        }
        used_scripthashes = {bitcoin.script_to_scripthash(bitcoin.address_to_script(a)) for a in used}

        class FakeNetwork:
            async def get_history_for_scripthash(self, sh):
                return [{'tx_hash': '00' * 32, 'height': 1}] if sh in used_scripthashes else []

        root = BIP32Node.from_rootseed(bip39_to_seed(SEED_BIP39, passphrase=''), xtype='standard')

        def get_account_xpub(account_path):
            return root.subkey_at_private_derivation(account_path).to_xpub()

        found = await account_discovery(FakeNetwork(), get_account_xpub)
        found = {(a['derivation_path'], a['script_type']) for a in found}
        self.assertIn(("m/84h/4134h/0h", 'p2wpkh'), found)
        self.assertIn(("m/44h/0h/0h", 'p2pkh'), found)

    def test_electrum_seed_path_unchanged(self):
        # Electrum's own seeds (the default for new wallets) have no coin type in their path, in upstream
        # Electrum and in every fork. Changing it would hide the funds of wallets created with this seed type.
        seed = 'wild father tree among universe such mobile favorite target dynamic credit identify'
        ks = keystore.from_seed(seed, passphrase=None)
        self.assertEqual("m/0h", ks.get_derivation_prefix())


class TestDmdWizardRestore(ElectrumTestCase):

    def setUp(self):
        super().setUp()
        self.config = SimpleConfig({'electrum_path': self.electrum_path})
        self.plugins = Plugins(self.config, gui_name='cmdline')

    def tearDown(self):
        self.plugins.stop()
        self.plugins.stopped_event.wait()
        super().tearDown()

    async def _restore_bip39(self, script_type: str, derivation_path: str):
        w = NewWalletWizard(DaemonMock(self.config), self.plugins)
        v = w.start()
        d = {'wallet_name': f'restored_{script_type}'}
        v = w.resolve_next(v.view, d)
        d.update({'wallet_type': 'standard'})
        v = w.resolve_next(v.view, d)
        d.update({'keystore_type': 'haveseed'})
        v = w.resolve_next(v.view, d)
        d.update({'seed': SEED_BIP39, 'seed_type': 'bip39', 'seed_extend': False, 'seed_variant': 'bip39'})
        v = w.resolve_next(v.view, d)
        self.assertEqual('script_and_derivation', v.view)
        d.update({'script_type': script_type, 'derivation_path': derivation_path})
        v = w.resolve_next(v.view, d)
        self.assertEqual('wallet_password', v.view)
        d.update({'password': None, 'encrypt': False})
        w.resolve_next(v.view, d)
        wallet_path = os.path.join(self.config.get_datadir_wallet_path(), d['wallet_name'])
        w.create_storage(wallet_path, d)
        return Daemon._load_wallet(wallet_path, password=None, config=self.config)

    async def test_restore_uses_4134_keys(self):
        for script_type, purpose in (('p2wpkh', 84), ('p2wpkh-p2sh', 49), ('p2pkh', 44)):
            with self.subTest(script_type=script_type):
                path = f"m/{purpose}'/4134'/0'"  # what the wizards now suggest
                wallet = await self._restore_bip39(script_type, path)
                self.assertEqual(f"m/{purpose}h/4134h/0h", wallet.get_keystore().get_derivation_prefix())
                self.assertEqual(_address_at(path + "/0/0", script_type), wallet.get_receiving_addresses()[0])
