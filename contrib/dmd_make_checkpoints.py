#!/usr/bin/env python3
#
# DebitMyData: generate electrum/chains/mainnet/checkpoints.json and checkpoints_tail.json
# from a fully synced headers file.
#
# Usage:
#   1. Run this wallet without checkpoints (or with the current ones) until it is fully synced.
#      The headers file is <electrum user dir>/blockchain_headers, e.g.
#        Windows: %APPDATA%\DebitMyData-Electrum\blockchain_headers
#        Linux:   ~/.debitmydata-electrum/blockchain_headers
#      Copy it somewhere first; do not run this against a file the wallet is writing to.
#   2. python3 contrib/dmd_make_checkpoints.py path/to/blockchain_headers
#
# Every header in the file is re-verified with DebitMyData's consensus rules (genesis,
# prev-hash links, difficulty, proof of work, chain anchors) before anything is written.
# Checkpoints stop at least --confirmations blocks below the tip, to stay clear of reorgs.

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from electrum import constants  # noqa: E402
from electrum.blockchain import (  # noqa: E402
    HEADER_SIZE, CHUNK_SIZE, Blockchain, deserialize_header, hash_raw_header,
    dmd_get_next_work_required, InvalidHeader,
)

TAIL_LENGTH = 2 * constants.net.LWMA_WINDOW  # LWMA needs WINDOW+1; keep some margin


class CheckpointError(Exception):
    pass


def make_checkpoints(data: bytes, *, confirmations: int, log=print):
    """Verify every header in `data` (a raw headers file) and return (checkpoints, tail)."""
    net = constants.net
    count = len(data) // HEADER_SIZE
    if count == 0:
        raise CheckpointError("headers file is empty")
    tip = count - 1
    log(f"headers file has {count} headers (tip height {tip}); verifying all of them...")

    headers = []
    prev_hash = '00' * 32
    for height in range(count):
        raw = data[height * HEADER_SIZE:(height + 1) * HEADER_SIZE]
        if raw == bytes(HEADER_SIZE):
            raise CheckpointError(
                f"header {height} is missing (zeros). The file must contain every header from "
                f"genesis; delete the headers file, run a build without checkpoints and resync.")
        header = deserialize_header(raw, height)
        header_hash = hash_raw_header(raw)
        if height == 0:
            if header_hash != net.GENESIS:
                raise CheckpointError(f"genesis mismatch: {header_hash}")
            expected_bits = None
        else:
            expected_bits = dmd_get_next_work_required(height, lambda h: headers[h])
        try:
            Blockchain.verify_header(header, prev_hash, expected_bits)
        except InvalidHeader as e:
            raise CheckpointError(f"header {height} is invalid: {e}")
        headers.append(header)
        prev_hash = header_hash
        if height % 20000 == 0 and height:
            log(f"  ...{height}")

    num_chunks = (tip - confirmations + 1) // CHUNK_SIZE
    if num_chunks <= 0:
        raise CheckpointError("chain is too short for a checkpoint at this confirmations depth")
    checkpoints = []
    for index in range(num_chunks):
        h = (index + 1) * CHUNK_SIZE - 1
        raw = data[h * HEADER_SIZE:(h + 1) * HEADER_SIZE]
        checkpoints.append([hash_raw_header(raw), Blockchain.bits_to_target(headers[h]['bits'])])
    max_cp = num_chunks * CHUNK_SIZE - 1
    tail_start = max_cp - TAIL_LENGTH + 1
    tail = [data[h * HEADER_SIZE:(h + 1) * HEADER_SIZE].hex() for h in range(tail_start, max_cp + 1)]
    return checkpoints, tail


def main():
    parser = argparse.ArgumentParser(description="Generate DebitMyData Electrum checkpoints from a synced headers file.")
    parser.add_argument('headers_file')
    parser.add_argument('--out-dir', default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                          '..', 'electrum', 'chains', 'mainnet'))
    parser.add_argument('--confirmations', type=int, default=1000,
                        help='minimum depth of the last checkpoint below the tip (default: 1000)')
    args = parser.parse_args()
    assert constants.net.NET_NAME == 'mainnet'
    with open(args.headers_file, 'rb') as f:
        data = f.read()
    try:
        checkpoints, tail = make_checkpoints(data, confirmations=args.confirmations)
    except CheckpointError as e:
        sys.exit(str(e))
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, 'checkpoints.json'), 'w', encoding='utf-8') as f:
        json.dump(checkpoints, f, indent=4)
        f.write('\n')
    with open(os.path.join(args.out_dir, 'checkpoints_tail.json'), 'w', encoding='utf-8') as f:
        json.dump(tail, f, indent=1)
        f.write('\n')
    max_cp = len(checkpoints) * CHUNK_SIZE - 1
    print(f"wrote {len(checkpoints)} checkpoints (up to height {max_cp}) and "
          f"{len(tail)} tail headers to {os.path.abspath(args.out_dir)}")


if __name__ == '__main__':
    main()
