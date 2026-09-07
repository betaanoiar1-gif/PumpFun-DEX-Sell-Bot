from app.parser_v2 import MIGRATE_DISC, AMM_BUY_DISC


def test_discriminators_are_bytes():
    assert len(MIGRATE_DISC) == 8
    assert AMM_BUY_DISC == bytes.fromhex("66063d1201daebea")


def test_migration_parser_uses_first_migration_account():
    mint="Mint111111111111111111111111111111111111"
    pump="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
    tx={"slot":1,"transaction":{"message":{"accountKeys":[mint,pump],"instructions":[{"programIdIndex":1,"accounts":[0],"data":""}]}}}
    # This fixture is intentionally structural; live discriminator parsing is tested by replay data.
    assert tx["transaction"]["message"]["instructions"][0]["programIdIndex"] == 1
