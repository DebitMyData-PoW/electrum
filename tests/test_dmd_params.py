# DebitMyData: checks of chain parameters that must match DebitMyData Core v1.3.3.

from electrum import constants, bitcoin, util
from electrum.bip21 import create_bip21_uri, parse_bip21_URI, InvalidBitcoinURI
from electrum.crypto import sha256d
from electrum_ecc import ECPrivkey

from . import ElectrumTestCase


class TestDmdParams(ElectrumTestCase):

    def test_mainnet_is_debitmydata(self):
        net = constants.net
        self.assertEqual(constants.BitcoinMainnet, net)
        self.assertEqual("00000992d19e3ed58ddf4117b597955752ff029e7256487a47557a24aeb4cadd", net.GENESIS)
        self.assertEqual((30, 31, 0x9e, "dm"), (net.ADDRTYPE_P2PKH, net.ADDRTYPE_P2SH, net.WIF_PREFIX, net.SEGWIT_HRP))
        self.assertEqual(4134, net.BIP44_COIN_TYPE)
        self.assertFalse(net.LIGHTNING_SUPPORTED)

    def test_addresses(self):
        h160 = bytes(20)
        self.assertTrue(bitcoin.hash160_to_p2pkh(h160).startswith('D'))
        self.assertTrue(bitcoin.hash160_to_p2sh(h160).startswith('D'))
        self.assertTrue(bitcoin.hash_to_segwit_addr(h160, witver=0).startswith('dm1q'))
        self.assertFalse(bitcoin.is_address('bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4'))
        self.assertFalse(bitcoin.is_address('1BoatSLRHtKNngkdXEeobR76b53LETtpyT'))

    def test_signed_message_magic_matches_core(self):
        # DebitMyData Core: MESSAGE_MAGIC = "DebitMyData Signed Message:\n", serialized with a compact-size length
        msg = b"DebitMyData test message"
        magic = b"DebitMyData Signed Message:\n"
        expected = bytes([len(magic)]) + magic + bytes([len(msg)]) + msg
        self.assertEqual(expected, bitcoin.usermessage_magic(msg))

    def test_sign_and_verify_message(self):
        privkey = ECPrivkey(bytes(31) + b'\x01')
        address = bitcoin.pubkey_to_address('p2pkh', privkey.get_public_key_hex(compressed=True))
        msg = b"hello DMD"
        sig = bitcoin.ecdsa_sign_usermessage(privkey, msg, is_compressed=True)
        self.assertTrue(bitcoin.verify_usermessage_with_address(address, sig, msg))
        # a signature made with Bitcoin's message prefix must not verify
        btc_hash = sha256d(b"\x18Bitcoin Signed Message:\n" + bytes([len(msg)]) + msg)
        btc_sig = privkey.ecdsa_sign_recoverable(btc_hash, is_compressed=True)
        self.assertFalse(bitcoin.verify_usermessage_with_address(address, btc_sig, msg))

    def test_uri_scheme(self):
        addr = bitcoin.hash160_to_p2pkh(bytes(20))
        uri = create_bip21_uri(addr, 150_000_000, "test")
        self.assertTrue(uri.startswith("debitmydata:" + addr))
        self.assertEqual(150_000_000, parse_bip21_URI(uri)['amount'])
        with self.assertRaises(InvalidBitcoinURI):
            parse_bip21_URI("bitcoin:" + addr)

    def test_units(self):
        self.assertEqual(['DMD', 'mDMD', 'debits', 'data'], util.base_units_list)
        self.assertEqual(8, util.DECIMAL_POINT_DEFAULT)
        self.assertEqual("data/vB", util.UI_UNIT_NAME_FEERATE_SAT_PER_VB)
