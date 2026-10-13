# DebitMyData: tests for header verification with DebitMyData's difficulty rules
# (legacy 8-block retarget below LWMA_HEIGHT, LWMA after), chain anchors, chain work
# and checkpoints with checkpoints_tail.json.
#
# A synthetic chain is built with DebitMyData's real difficulty parameters. Real mining at
# that difficulty is far too slow for unit tests, so the proof-of-work hash is replaced by a
# stand-in: a header "meets its target" iff its nonce is 1. Everything else (bits required
# by legacy retarget / LWMA, links, anchors, checkpoints, chain work) is the real code.
# The difficulty function itself was cross-checked against DebitMyData Core's pow.cpp.

import hashlib
import importlib.util
import os
import random
from pathlib import Path
from unittest import mock

from electrum import constants
from electrum import blockchain as blockchain_module
from electrum.blockchain import (
    Blockchain, BlockchainManager, deserialize_header, serialize_header, hash_header,
    dmd_get_next_work_required, _work_from_bits, HEADER_SIZE, CHUNK_SIZE,
)

from . import ElectrumTestCase


POW_LIMIT = constants.BitcoinMainnet.POW_LIMIT


def _fake_pow_hash(header: dict) -> str:
    return '00' * 32 if header['nonce'] == 1 else 'ff' * 32


def _mine(header: dict) -> dict:
    header['nonce'] = 1
    return header


class _Chain:
    """Builds a valid chain under constants.net (must be a _DmdTestNet)."""

    def __init__(self, headers=None):
        self.headers = list(headers or [])

    def extend(self, count: int, rng: random.Random, solvetime=lambda rng: int(rng.expovariate(1 / 150)), tag=b''):
        for _ in range(count):
            height = len(self.headers)
            if height == 0:
                header = {'version': 1, 'prev_block_hash': '00' * 32, 'timestamp': 1771620622,
                          'bits': Blockchain.target_to_bits(constants.net.POW_LIMIT)}
            else:
                prev = self.headers[-1]
                header = {'version': 0x20000000, 'prev_block_hash': hash_header(prev),
                          'timestamp': max(1, prev['timestamp'] + solvetime(rng)),
                          'bits': dmd_get_next_work_required(height, lambda h: self.headers[h])}
            header['merkle_root'] = hashlib.sha256(tag + height.to_bytes(4, 'little')).hexdigest()
            header['block_height'] = height
            self.headers.append(_mine(header))
        return self

    def raw(self, start=0, end=None) -> bytes:
        end = len(self.headers) if end is None else end
        return b''.join(serialize_header(h) for h in self.headers[start:end])

    def chunk(self, index: int) -> bytes:
        return self.raw(index * CHUNK_SIZE, min(len(self.headers), (index + 1) * CHUNK_SIZE))


class _DmdTestNet(constants.BitcoinMainnet):
    CHAIN_ANCHORS = {}
    _cached_checkpoints = []
    _cached_checkpoint_tail = []


_CHAIN_CACHE = {}


def _main_chain() -> _Chain:
    # 3 full chunks + 500 headers; mined once per test run
    if 'main' not in _CHAIN_CACHE:
        _CHAIN_CACHE['main'] = _Chain().extend(3 * CHUNK_SIZE + 500, random.Random(42))
    return _CHAIN_CACHE['main']


class TestDmdBlockchain(ElectrumTestCase):

    def setUp(self):
        super().setUp()
        self._saved_net = constants.net
        _DmdTestNet._cached_checkpoints = []
        _DmdTestNet._cached_checkpoint_tail = []
        _DmdTestNet.CHAIN_ANCHORS = {}
        _DmdTestNet.set_as_network()
        patcher = mock.patch.object(blockchain_module, 'pow_hash_header', _fake_pow_hash)
        patcher.start()
        self.addCleanup(patcher.stop)
        # chain work is cached per block hash for the whole process; tests use different checkpoints
        saved_cache = dict(blockchain_module._CHAINWORK_CACHE)
        self.addCleanup(lambda: (blockchain_module._CHAINWORK_CACHE.clear(),
                                 blockchain_module._CHAINWORK_CACHE.update(saved_cache)))
        blockchain_module._CHAINWORK_CACHE.clear()
        blockchain_module._CHAINWORK_CACHE['00' * 32] = 0
        self.chain = _main_chain()
        _DmdTestNet.GENESIS = hash_header(self.chain.headers[0])
        self.headers_dir = Path(self.electrum_path) / 'headers'
        self.headers_dir.mkdir()

    def tearDown(self):
        self._saved_net.set_as_network()
        super().tearDown()

    def _new_mgr(self, subdir='a') -> BlockchainManager:
        d = self.headers_dir / subdir
        d.mkdir(exist_ok=True)
        return BlockchainManager(headers_dir=d)

    def _sync_chunks(self, bc: Blockchain, indices):
        for i in indices:
            self.assertTrue(bc.connect_chunk(i, self.chain.chunk(i)), f"chunk {i} rejected")

    def test_sync_whole_chain_from_genesis(self):
        bc = self._new_mgr().get_best_chain()
        self._sync_chunks(bc, range(4))
        self.assertEqual(len(self.chain.headers) - 1, bc.height())
        self.assertEqual(hash_header(self.chain.headers[-1]), bc.get_hash(bc.height()))

    def test_sync_header_by_header(self):
        bc = self._new_mgr().get_best_chain()
        self._sync_chunks(bc, range(1))
        for h in self.chain.headers[CHUNK_SIZE:CHUNK_SIZE + 300]:
            self.assertTrue(bc.can_connect(h))
            bc.save_header(h)
        self.assertEqual(CHUNK_SIZE + 299, bc.height())

    def _tampered_chunk(self, height: int, **changes) -> bytes:
        headers = [dict(h) for h in self.chain.headers]
        headers[height].update(changes)
        _mine(headers[height])
        for h in range(height + 1, min(len(headers), (height // CHUNK_SIZE + 1) * CHUNK_SIZE)):
            headers[h]['prev_block_hash'] = hash_header(headers[h - 1])
            _mine(headers[h])
        index = height // CHUNK_SIZE
        return b''.join(serialize_header(x) for x in headers[index * CHUNK_SIZE:(index + 1) * CHUNK_SIZE]), headers[height]

    def test_rejects_easier_bits_than_consensus(self):
        # a server tries to hand us a header claiming less difficulty than LWMA requires
        height = 2 * CHUNK_SIZE + 77
        real_bits = self.chain.headers[height]['bits']
        easier = Blockchain.target_to_bits(min(POW_LIMIT, Blockchain.bits_to_target(real_bits) * 2))
        self.assertNotEqual(real_bits, easier)
        data, bad_header = self._tampered_chunk(height, bits=easier)
        bc = self._new_mgr().get_best_chain()
        self._sync_chunks(bc, range(2))
        self.assertFalse(bc.connect_chunk(2, data))
        self.assertEqual(2 * CHUNK_SIZE - 1, bc.height())
        # and header-by-header
        for h in self.chain.headers[2 * CHUNK_SIZE:height]:
            bc.save_header(h)
        self.assertFalse(bc.can_connect(bad_header))
        self.assertTrue(bc.can_connect(self.chain.headers[height]))

    def test_rejects_wrong_bits_in_legacy_region(self):
        # below LWMA_HEIGHT difficulty retargets every 8 blocks
        height = 64  # a retarget height
        real_bits = self.chain.headers[height]['bits']
        data, _ = self._tampered_chunk(height, bits=Blockchain.target_to_bits(Blockchain.bits_to_target(real_bits) // 2))
        bc = self._new_mgr().get_best_chain()
        self.assertFalse(bc.connect_chunk(0, data))

    def test_rejects_insufficient_pow(self):
        height = CHUNK_SIZE + 5
        header = dict(self.chain.headers[height])
        header['nonce'] = 0  # does not meet its target
        bc = self._new_mgr().get_best_chain()
        self._sync_chunks(bc, range(1))
        for h in self.chain.headers[CHUNK_SIZE:height]:
            bc.save_header(h)
        self.assertFalse(bc.can_connect(header))

    def test_anchor(self):
        anchor_height = 1000
        _DmdTestNet.CHAIN_ANCHORS = {anchor_height: hash_header(self.chain.headers[anchor_height])}
        bc = self._new_mgr('ok').get_best_chain()
        self._sync_chunks(bc, range(4))
        _DmdTestNet.CHAIN_ANCHORS = {anchor_height: 'ab' * 32}
        bc = self._new_mgr('bad').get_best_chain()
        self.assertFalse(bc.connect_chunk(0, self.chain.chunk(0)))

    def test_chainwork_is_sum_of_header_work(self):
        bc = self._new_mgr().get_best_chain()
        self._sync_chunks(bc, range(4))
        cumulative = 0
        expected = {}
        for h, header in enumerate(self.chain.headers):
            cumulative += _work_from_bits(header['bits'])
            expected[h] = cumulative
        for h in (0, 1, 119, 120, CHUNK_SIZE - 1, CHUNK_SIZE, 2 * CHUNK_SIZE + 333, len(self.chain.headers) - 1):
            self.assertEqual(expected[h], bc.get_chainwork(h), h)

    def test_fork_with_more_work_becomes_best_chain(self):
        mgr = self._new_mgr()
        bc = mgr.get_best_chain()
        self._sync_chunks(bc, range(4))
        forkpoint = 3 * CHUNK_SIZE + 300
        # a competing branch mined faster: LWMA raises its difficulty, so it accumulates more work
        fork = _Chain(self.chain.headers[:forkpoint]).extend(
            len(self.chain.headers) - forkpoint, random.Random(7), solvetime=lambda rng: 40, tag=b'fork')
        main_work = sum(_work_from_bits(h['bits']) for h in self.chain.headers[forkpoint:])
        fork_work = sum(_work_from_bits(h['bits']) for h in fork.headers[forkpoint:])
        self.assertGreater(fork_work, main_work)
        first = fork.headers[forkpoint]
        self.assertIsNone(mgr.can_connect(first))  # not a tip extension
        fork_chain = bc.fork(first)
        for h in fork.headers[forkpoint + 1:]:
            self.assertTrue(fork_chain.can_connect(h))
            fork_chain.save_header(h)
        best = mgr.get_best_chain()
        self.assertEqual(hash_header(fork.headers[-1]), best.get_hash(len(fork.headers) - 1))

    def test_checkpoints_with_tail(self):
        spec = importlib.util.spec_from_file_location(
            'dmd_make_checkpoints',
            os.path.join(os.path.dirname(__file__), '..', 'contrib', 'dmd_make_checkpoints.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        checkpoints, tail = mod.make_checkpoints(self.chain.raw(), confirmations=300, log=lambda *a: None)
        self.assertEqual(3, len(checkpoints))
        max_cp = 3 * CHUNK_SIZE - 1
        self.assertEqual(hash_header(self.chain.headers[max_cp]), checkpoints[-1][0])

        # with checkpoints but without the tail, LWMA cannot verify the first headers after them
        _DmdTestNet._cached_checkpoints = checkpoints
        _DmdTestNet._cached_checkpoint_tail = []
        bc = self._new_mgr('notail').get_best_chain()
        self.assertFalse(bc.connect_chunk(3, self.chain.chunk(3)))

        # with the tail: syncs from the last checkpoint without downloading earlier chunks
        _DmdTestNet._cached_checkpoint_tail = tail
        mgr = self._new_mgr('tail')
        bc = mgr.get_best_chain()
        self.assertIsNone(bc.read_header(5))  # not downloaded
        self.assertTrue(bc.connect_chunk(3, self.chain.chunk(3)))
        self.assertEqual(len(self.chain.headers) - 1, bc.height())
        # a checkpointed chunk can still be fetched later (e.g. for SPV of an old tx)
        self.assertTrue(bc.connect_chunk(1, self.chain.chunk(1)))
        bad = bytearray(self.chain.chunk(1))
        bad[HEADER_SIZE * 10 + 70] ^= 1  # corrupt one header's timestamp
        self.assertFalse(bc.connect_chunk(1, bytes(bad)))
        # restart: consistency check must accept the stored chain
        mgr2 = self._new_mgr('tail')
        self.assertEqual(len(self.chain.headers) - 1, mgr2.get_best_chain().height())
        # chain work beyond the checkpoints is computed from real header bits
        cp_work = sum(CHUNK_SIZE * ((2 ** 256 - t - 1) // (t + 1) + 1) for _, t in checkpoints)
        exact = sum(_work_from_bits(h['bits']) for h in self.chain.headers[max_cp + 1:])
        self.assertEqual(cp_work + exact, mgr2.get_best_chain().get_chainwork())

    def test_tail_must_match_checkpoints(self):
        spec = importlib.util.spec_from_file_location(
            'dmd_make_checkpoints',
            os.path.join(os.path.dirname(__file__), '..', 'contrib', 'dmd_make_checkpoints.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        checkpoints, tail = mod.make_checkpoints(self.chain.raw(), confirmations=300, log=lambda *a: None)
        _DmdTestNet._cached_checkpoints = checkpoints[:2]  # tail ends at chunk 2, checkpoints at chunk 1
        _DmdTestNet._cached_checkpoint_tail = tail
        with self.assertRaises(Exception):
            self._new_mgr('mismatch')


class TestDmdGenesis(ElectrumTestCase):
    """Real DebitMyData data: the mainnet genesis block from src/kernel/chainparams.cpp
    (CreateGenesisBlock(1771620622, 3799038, 0x1e0ffff0, 1, 35 * COIN))."""

    def test_genesis_header_hash_and_pow(self):
        self.assertEqual("mainnet", constants.net.NET_NAME)
        header = {
            'version': 1,
            'prev_block_hash': '00' * 32,
            'merkle_root': '282e01bbdf334e601d0ba1bebe9ea1534168846956ab5106f49398e22d3aec8e',
            'timestamp': 1771620622,
            'bits': 0x1e0ffff0,
            'nonce': 3799038,
            'block_height': 0,
        }
        self.assertEqual(constants.net.GENESIS, hash_header(header))
        # genesis is pinned by hash; its own proof of work must still be valid
        Blockchain.verify_header(header, '00' * 32, None, expected_header_hash=constants.net.GENESIS)
        header['nonce'] += 1
        with self.assertRaises(Exception):
            Blockchain.verify_header(header, '00' * 32, None)
