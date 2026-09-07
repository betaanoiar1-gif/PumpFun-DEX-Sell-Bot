from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
PUMP_AMM_PROGRAM = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
PAPER_MODE = os.getenv("PAPER_MODE", "true").lower() == "true"

@dataclass(frozen=True)
class Config:
    rpc_url: str = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    ws_url: str = os.getenv("SOLANA_WS_URL", "wss://api.mainnet-beta.solana.com/")
    timeout: int = int(os.getenv("POOL_ACTIVITY_TIMEOUT_SEC", "60"))
    sell_amount: int = int(os.getenv("PAPER_SELL_AMOUNT_BASE_UNITS", "0"))
    commitment: str = os.getenv("COMMITMENT", "confirmed")

    def validate(self) -> None:
        if not PAPER_MODE:
            raise RuntimeError("This project is permanently PAPER_MODE-only.")
        if self.timeout <= 0:
            raise ValueError("POOL_ACTIVITY_TIMEOUT_SEC must be > 0")
        if self.sell_amount < 0:
            raise ValueError("PAPER_SELL_AMOUNT_BASE_UNITS must be >= 0")
