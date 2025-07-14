import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from module.binance_p2p import P2PBinance

def thongke_job_sync():
    #df = binance_p2p().thongke_today()
    print("DONE")

def transactions_trading_sync():
    P2PBinance().transactions_trading()

async def main():
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, transactions_trading_sync)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: loop.run_in_executor(None, thongke_job_sync), 'cron', minute=21)
    scheduler.start()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
