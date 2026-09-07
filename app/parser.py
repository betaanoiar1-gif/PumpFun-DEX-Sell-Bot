import hashlib
from dataclasses import dataclass
from typing import Any
from .config import PUMP_PROGRAM, PUMP_AMM_PROGRAM

MIGRATE_DISC = hashlib.sha256(b"global:migrate").digest()[:8]
AMM_BUY_DISC = bytes.fromhex("66063d1201daebea")
AMM_SELL_DISC = bytes.fromhex("3e2f370aa503dc2a")

@dataclass(frozen=True)
class Migration:
    signature: str
    slot: int
    mint: str
    pool: str | None

@dataclass(frozen=True)
class Activity:
    signature: str
    slot: int
    pool: str
    mint: str
    kind: str


def _keys(tx: dict[str, Any]) -> list[str]:
    msg = ((tx.get("transaction") or {}).get("message") or {})
    out=[]
    for k in msg.get("accountKeys", []):
        out.append(k.get("pubkey") if isinstance(k, dict) else k)
    loaded = msg.get("loadedAddresses") or {}
    out.extend(loaded.get("writable") or [])
    out.extend(loaded.get("readonly") or [])
    return out


def _program_id(ix: dict, keys: list[str]) -> str | None:
    if isinstance(ix.get("programId"), str):
        return ix["programId"]
    i = ix.get("programIdIndex")
    return keys[i] if isinstance(i, int) and i < len(keys) else None


def _data(ix: dict) -> bytes:
    d = ix.get("data", "")
    try:
        import base64
        return base64.b64decode(d)
    except Exception:
        return b""


def _all_instructions(tx: dict):
    msg = ((tx.get("transaction") or {}).get("message") or {})
    keys = _keys(tx)
    for ix in msg.get("instructions", []):
        yield ix, keys
    meta = tx.get("meta") or {}
    for group in meta.get("innerInstructions") or []:
        for ix in group.get("instructions") or []:
            yield ix, keys


def _candidate_pool_accounts(tx: dict) -> list[str]:
    keys = _keys(tx)
    pools=[]
    for ix, _ in _all_instructions(tx):
        if _program_id(ix, keys) == PUMP_AMM_PROGRAM:
            # Do not assume a fixed account index. Keep every referenced account;
            # the resolver later verifies ownership by querying the chain.
            for i in ix.get("accounts", []):
                if isinstance(i, int) and i < len(keys):
                    pools.append(keys[i])
                elif isinstance(i, str):
                    pools.append(i)
    return list(dict.fromkeys(pools))


def parse_migration(tx: dict, signature: str) -> tuple[str, list[str]] | None:
    keys = _keys(tx)
    mint = None
    found = False
    for ix, _ in _all_instructions(tx):
        if _program_id(ix, keys) != PUMP_PROGRAM:
            continue
        if _data(ix).startswith(MIGRATE_DISC):
            found = True
            accounts = ix.get("accounts") or []
            if accounts:
                a = accounts[0]
                mint = keys[a] if isinstance(a, int) and a < len(keys) else (a if isinstance(a, str) else None)
            break
    if found and mint:
        return mint, _candidate_pool_accounts(tx)
    return None


def parse_activity(tx: dict, signature: str, target_pool: str, target_mint: str) -> Activity | None:
    keys = _keys(tx)
    for ix, _ in _all_instructions(tx):
        if _program_id(ix, keys) != PUMP_AMM_PROGRAM:
            continue
        data = _data(ix)
        if data.startswith(AMM_BUY_DISC):
            kind = "BUY"
        elif data.startswith(AMM_SELL_DISC):
            kind = "SELL"
        else:
            continue
        accounts = ix.get("accounts") or []
        resolved = [keys[a] if isinstance(a,int) and a < len(keys) else a for a in accounts]
        if target_pool not in resolved:
            continue
        # Strict mint validation: accept only if the target mint is actually
        # referenced by the same transaction. Never trust pool reuse alone.
        if target_mint not in keys:
            continue
        return Activity(signature, int(tx.get("slot") or 0), target_pool, target_mint, kind)
    return None
