import asyncio
import json
import time
import websockets
from .config import PUMP_AMM_PROGRAM
from .parser_fixed import parse_activity
from .rpc import RpcClient, RpcError
from .state import Run, State

class WSMonitor:
    def __init__(self, rpc: RpcClient, ws_url: str, timeout: int):
        self.rpc,self.ws_url,self.timeout=rpc,ws_url,timeout
        self._req=0
    async def _subscribe(self,ws,pubkey):
        self._req+=1
        await ws.send(json.dumps({"jsonrpc":"2.0","id":self._req,"method":"logsSubscribe","params":[{"mentions":[pubkey]},{"commitment":"confirmed"}]}))
        while True:
            msg=json.loads(await ws.recv())
            if msg.get("id")==self._req:
                if "error" in msg: raise RuntimeError(str(msg["error"]))
                return msg["result"]
    async def _next_signature(self,ws):
        while True:
            msg=json.loads(await ws.recv())
            value=msg.get("params",{}).get("result",{}).get("value") or {}
            sig=value.get("signature")
            if sig and not value.get("err"): return sig
    async def watch_pool(self,run:Run)->Run:
        if not run.pool or not run.mint:
            run.state=State.NO_POOL_FOUND; return run
        run.state=State.MONITORING_POOL
        deadline=time.monotonic()+self.timeout
        while time.monotonic()<deadline:
            try:
                async with websockets.connect(self.ws_url,ping_interval=20,ping_timeout=20,close_timeout=5) as ws:
                    await self._subscribe(ws,run.pool)
                    while time.monotonic()<deadline:
                        try: sig=await asyncio.wait_for(self._next_signature(ws),max(0,deadline-time.monotonic()))
                        except asyncio.TimeoutError: break
                        tx=await self.rpc.get_transaction(sig)
                        if not tx: continue
                        event=parse_activity(tx,sig,run.pool,run.mint)
                        if event:
                            run.activity_signature=event.signature
                            run.activity_type=event.kind
                            run.state=State.EXECUTABLE_ACTIVITY_DETECTED
                            return run
                break
            except (OSError,websockets.WebSocketException,RpcError) as e:
                if time.monotonic()>=deadline:
                    run.error=str(e); run.state=State.NO_EXECUTABLE_ACTIVITY_TIMEOUT; return run
                await asyncio.sleep(1)
        run.state=State.NO_EXECUTABLE_ACTIVITY_TIMEOUT
        return run

async def resolve_pool(rpc:RpcClient,candidates:list[str])->str|None:
    if not candidates: return None
    result=await rpc.get_multiple_accounts(candidates)
    for pubkey,account in zip(candidates,result.get("value") or []):
        if account and account.get("owner")==PUMP_AMM_PROGRAM: return pubkey
    return None
