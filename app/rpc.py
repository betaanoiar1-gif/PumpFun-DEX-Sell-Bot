import aiohttp

class RpcError(RuntimeError):
    pass

class RpcClient:
    def __init__(self, url: str):
        self.url = url
        self._id = 0

    async def call(self, method: str, params=None):
        self._id += 1
        payload = {"jsonrpc":"2.0","id":self._id,"method":method,"params":params or []}
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.post(self.url, json=payload) as r:
                r.raise_for_status()
                data = await r.json()
        if data.get("error"):
            raise RpcError(str(data["error"]))
        return data.get("result")

    async def get_transaction(self, signature: str):
        return await self.call("getTransaction", [signature, {
            "encoding":"jsonParsed",
            "commitment":"confirmed",
            "maxSupportedTransactionVersion":0,
        }])

    async def get_account_info(self, pubkey: str):
        return await self.call("getAccountInfo", [pubkey, {"encoding":"base64"}])

    async def get_multiple_accounts(self, pubkeys):
        return await self.call("getMultipleAccounts", [pubkeys, {"encoding":"base64"}])

    async def get_signatures_for_address(self, pubkey: str, limit: int = 50):
        return await self.call("getSignaturesForAddress", [pubkey, {"limit": limit}])
