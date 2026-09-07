from app.parser_fixed import AMM_BUY_DISC, MIGRATE_DISC, parse_activity, parse_migration

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
PUMP = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
AMM = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
MINT = "Mint111111111111111111111111111111111111"
POOL = "Pool111111111111111111111111111111111111"
OTHER_MINT = "OtherMint11111111111111111111111111111111"


def b58encode(data: bytes) -> str:
    n = int.from_bytes(data, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = ALPHABET[r] + out
    return "1" * (len(data) - len(data.lstrip(b"\0"))) + (out or "1")


def test_migration_extracts_mint_and_amm_candidates():
    tx = {
        "slot": 100,
        "transaction": {"message": {
            "accountKeys": [MINT, PUMP, POOL, AMM],
            "instructions": [
                {"programIdIndex": 1, "accounts": [0], "data": b58encode(MIGRATE_DISC)},
                {"programIdIndex": 3, "accounts": [2], "data": "1"},
            ],
        }},
        "meta": {"innerInstructions": []},
    }
    mint, candidates = parse_migration(tx, "migration-sig")
    assert mint == MINT
    assert POOL in candidates


def test_activity_requires_target_mint_and_pool():
    tx = {
        "slot": 101,
        "transaction": {"message": {
            "accountKeys": [POOL, AMM, MINT],
            "instructions": [{
                "programIdIndex": 1,
                "accounts": [0, 2],
                "data": b58encode(AMM_BUY_DISC),
            }],
        }},
        "meta": {"innerInstructions": []},
    }
    event = parse_activity(tx, "activity-sig", POOL, MINT)
    assert event is not None
    assert event.kind == "BUY"


def test_activity_rejects_reused_pool_without_target_mint():
    tx = {
        "slot": 102,
        "transaction": {"message": {
            "accountKeys": [POOL, AMM, OTHER_MINT],
            "instructions": [{
                "programIdIndex": 1,
                "accounts": [0, 2],
                "data": b58encode(AMM_BUY_DISC),
            }],
        }},
        "meta": {"innerInstructions": []},
    }
    assert parse_activity(tx, "wrong-mint", POOL, MINT) is None
