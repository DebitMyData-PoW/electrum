ELECTRUM_VERSION = '4.8.2'       # version of the client package
# DebitMyData release number on top of ELECTRUM_VERSION (4.8.2-dmd1 -> 1). Increase it for every
# new DebitMyData release on the same ELECTRUM_VERSION; reset to 1 when ELECTRUM_VERSION changes.
# It is part of the Android version code, which must increase with every app update.
DMD_RELEASE = 2

PROTOCOL_VERSION_MIN = '1.4'     # electrum protocol
PROTOCOL_VERSION_MAX = '1.6'

# The hash of the mnemonic seed must begin with this
SEED_PREFIX        = '01'      # Standard wallet
SEED_PREFIX_SW     = '100'     # Segwit wallet
SEED_PREFIX_2FA    = '101'     # Two-factor authentication
SEED_PREFIX_2FA_SW = '102'     # Two-factor auth, using segwit


def seed_prefix(seed_type):
    if seed_type == 'standard':
        return SEED_PREFIX
    elif seed_type == 'segwit':
        return SEED_PREFIX_SW
    elif seed_type == '2fa':
        return SEED_PREFIX_2FA
    elif seed_type == '2fa_segwit':
        return SEED_PREFIX_2FA_SW
    raise Exception(f"unknown seed_type: {seed_type!r}")
