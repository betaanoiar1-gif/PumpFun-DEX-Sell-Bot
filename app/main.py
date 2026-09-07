import asyncio
import json
import logging
import websockets
from .config import Config, PUMP_PROGRAM
from .rpc import RpcClient
from .parser_fixed import parse_migration
from .monitor import WSMonitor, resolve_pool
from .state import Run, State

logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
log=logging.getLogger("pumpfun-dex-sell")

async def migration_stream(cfg:Config,rpc:RpcClient):
    while True:
        try:
            async with websockets.connect(cfg.ws_url,ping_interval=20,ping_timeout=20,close_timeout=5) as ws:
                await ws.send(json.dumps({"jsonrpc":"2.0","id":1,"method":"logsSubscribe","params":[{"mentions":[PUMP_PROGRAM]},{"commitment":cfg.commitment}]}))
                log.info("Pump.fun logsSubscribe connected: %s",await ws.recv())
                while True:
                    msg=json.loads(await ws.recv())
                    value=msg.get("params",{}).get("result",{}).get("value") or {}
                    sig=value.get("signature")
                    if not sig or value.get("err"): continue
                    tx=await rpc.get_transaction(sig)
                    if not tx: continue
                    parsed=parse_migration(tx,sig)
                    if not parsed: continue
                    mint,candidates=parsed
                    run=Run(state=State.GRADUATION_DETECTED,mint=mint,migration_signature=sig,migration_slot=int(tx.get("slot") or 0))
                    pool=await resolve_pool(rpc,candidates)
                    if not pool:
                        run.state=State.NO_POOL_FOUND
                        log.info("NO_POOL_FOUND mint=%s migration=%s",mint,sig); continue
                    run.pool=pool; run.state=State.POOL_FOUND
                    log.info("POOL_FOUND mint=%s pool=%s migration=%s",mint,pool,sig)
                    run=await WSMonitor(rpc,cfg.ws_url,cfg.timeout).watch_pool(run)
                    if run.state==State.EXECUTABLE_ACTIVITY_DETECTED:
                        run.state=State.PAPER_SELL_READY
                        run.state=State.PAPER_SELL_RESULT
                        log.info("PAPER_SELL_RESULT mint=%s pool=%s activity=%s type=%s amount_base_units=%s",run.mint,run.pool,run.activity_signature,run.activity_type,cfg.sell_amount)
                    else:
                        log.info("%s mint=%s pool=%s",run.state.value,run.mint,run.pool)
        except (OSError,websockets.WebSocketException,asyncio.TimeoutError) as e:
            log.warning("Pump.fun websocket disconnected: %s; reconnecting",e); await asyncio.sleep(1)
        except Exception:
            log.exception("Unexpected stream error; reconnecting"); await asyncio.sleep(2)

async def main():
    cfg=Config(); cfg.validate()
    log.info("PAPER_MODE=true; strategy monitor starting")
    await migration_stream(cfg,RpcClient(cfg.rpc_url))

if __name__=="__main__": asyncio.run(main())
