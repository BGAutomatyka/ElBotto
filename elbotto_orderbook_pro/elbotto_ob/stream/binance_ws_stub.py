"""
Stub: pokazuje jak pobierać L2 top-of-book z Binance (wymaga: websockets/asyncio, klucze niepotrzebne dla public).
Uwaga: ten plik jest szkicem – dostosuj do swoich potrzeb i strumieni.
"""
import asyncio, json, gzip
import websockets

async def main(symbol="btcusdt"):
    url = f"wss://stream.binance.com:9443/ws/{symbol}@bookTicker"
    async with websockets.connect(url, max_size=2**24) as ws:
        while True:
            msg = await ws.recv()
            try:
                data = json.loads(msg)
                print(data)  # zapisz do CSV/parquet wg własnego formatu
            except Exception:
                pass

# asyncio.run(main())
