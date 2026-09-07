import hashlib
from dataclasses import dataclass
from typing import Any
from .config import PUMP_PROGRAM, PUMP_AMM_PROGRAM

MIGRATE_DISC = hashlib.sha256(b"global:migrate").digest()[:8]
AMM_BUY_DISC = bytes.fromhex("66063d1201daebea")
AMM_SELL_DISC = bytes.fromhex("3e2f370aa503dc2a")

@dataclass(frozen=True)
class Activity:
    signature: str
    slot: int
    pool: str
    mint: str
    kind: str

def _b58decode(value: str) -> bytes:
    alphabet="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n=0
    for c in value: n=n*58+alphabet.index(c)
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(value)-len(value.lstrip("1")))+raw

def _keys(tx: dict[str, Any]) -> list[str]:
    msg=((tx.get("transaction") or {}).get("message") or {})
    out=[k.get("pubkey") if isinstance(k,dict) else k for k in msg.get("accountKeys",[])]
    loaded=(tx.get("meta") or {}).get("loadedAddresses") or {}
    out.extend(loaded.get("writable") or [])
    out.extend(loaded.get("readonly") or [])
    return out

def _program_id(ix: dict, keys: list[str]) -> str | None:
    if isinstance(ix.get("programId"),str): return ix["programId"]
    i=ix.get("programIdIndex")
    return keys[i] if isinstance(i,int) and i<len(keys) else None

def _data(ix: dict) -> bytes:
    d=ix.get("data","")
    try: return _b58decode(d) if isinstance(d,str) else b""
    except Exception: return b""

def _all_instructions(tx: dict):
    msg=((tx.get("transaction") or {}).get("message") or {})
    keys=_keys(tx)
    for ix in msg.get("instructions",[]): yield ix,keys
    for group in (tx.get("meta") or {}).get("innerInstructions") or []:
        for ix in group.get("instructions") or []: yield ix,keys

def _accounts(ix: dict, keys: list[str]) -> list[str]:
    return [keys[a] if isinstance(a,int) and a<len(keys) else a for a in ix.get("accounts",[]) or []]

def _candidate_pool_accounts(tx: dict) -> list[str]:
    out=[]
    for ix,keys in _all_instructions(tx):
        if _program_id(ix,keys)==PUMP_AMM_PROGRAM: out.extend(_accounts(ix,keys))
    return list(dict.fromkeys(out))

def parse_migration(tx: dict, signature: str) -> tuple[str,list[str]] | None:
    for ix,keys in _all_instructions(tx):
        if _program_id(ix,keys)==PUMP_PROGRAM and _data(ix).startswith(MIGRATE_DISC):
            a=_accounts(ix,keys)
            # Current Pump migrate layout: global, withdraw_authority, mint, ...
            # V2 variants may expose base_mint; find it by Token-2022/SPL mint
            # validation later if needed. For the canonical migrate path account[2] is mint.
            if len(a) >= 3:
                return a[2],_candidate_pool_accounts(tx)
    return None

def parse_activity(tx: dict, signature: str, target_pool: str, target_mint: str) -> Activity | None:
    keys=_keys(tx)
    for ix,keys in _all_instructions(tx):
        if _program_id(ix,keys)!=PUMP_AMM_PROGRAM: continue
        data=_data(ix)
        kind="BUY" if data.startswith(AMM_BUY_DISC) else "SELL" if data.startswith(AMM_SELL_DISC) else None
        if not kind: continue
        if target_pool not in _accounts(ix,keys): continue
        if target_mint not in keys: continue
        return Activity(signature,int(tx.get("slot") or 0),target_pool,target_mint,kind)
    return None
