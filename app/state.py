from enum import Enum
from dataclasses import dataclass
from typing import Optional

class State(str, Enum):
    WAITING_FOR_GRADUATION="WAITING_FOR_GRADUATION"
    GRADUATION_DETECTED="GRADUATION_DETECTED"
    POOL_FOUND="POOL_FOUND"
    MONITORING_POOL="MONITORING_POOL"
    EXECUTABLE_ACTIVITY_DETECTED="EXECUTABLE_ACTIVITY_DETECTED"
    PAPER_SELL_READY="PAPER_SELL_READY"
    PAPER_SELL_RESULT="PAPER_SELL_RESULT"
    NO_POOL_FOUND="NO_POOL_FOUND"
    NO_EXECUTABLE_ACTIVITY_TIMEOUT="NO_EXECUTABLE_ACTIVITY_TIMEOUT"
    PARSE_ERROR="PARSE_ERROR"
    RPC_ERROR="RPC_ERROR"

@dataclass
class Run:
    state: State = State.WAITING_FOR_GRADUATION
    mint: Optional[str] = None
    migration_signature: Optional[str] = None
    migration_slot: Optional[int] = None
    pool: Optional[str] = None
    activity_signature: Optional[str] = None
    activity_type: Optional[str] = None
    error: Optional[str] = None
