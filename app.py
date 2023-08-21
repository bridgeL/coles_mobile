import asyncio
import sys
import time
import httpx
import sqlite3
import configparser
import loguru

read_ini = configparser.RawConfigParser(strict=False)
read_ini.read("config.ini", "utf8")

loguru.logger.remove()
loguru.logger.add(
    sys.stdout, format="<g>{time:YYYY/MM/DD HH:mm:ss Z}</g> | <level>{level}</level> | <level>{message}</level>", diagnose=False, backtrace=False)
loguru.logger.add(
    open("data.log", "a+", encoding="utf8"),
    format="[{time:YYYY/MM/DD HH:mm:ss Z}] {message}", level="INFO")


class ColeMobileSupervisor:
    def __init__(self) -> None:
        # load config
        SERVERID = read_ini['coles']['serverid']
        USERNAME = read_ini["coles"]["username"]
        PASSWORD = read_ini["coles"]["password"]
        self.gap = int(read_ini["coles"]["gap"])

        self.balance_url = f"https://colesmobile.com.au/api/v1/rest/network/balance/{SERVERID}"
        self.login_form = f"------WebKitFormBoundaryUnIAFTHcy6L5kuKa\r\nContent-Disposition: form-data; name=\"username\"\r\n\r\n{USERNAME}\r\n------WebKitFormBoundaryUnIAFTHcy6L5kuKa\r\nContent-Disposition: form-data; name=\"password\"\r\n\r\n{PASSWORD}\r\n------WebKitFormBoundaryUnIAFTHcy6L5kuKa\r\nContent-Disposition: form-data; name=\"remember-me\"\r\n\r\nundefined\r\n------WebKitFormBoundaryUnIAFTHcy6L5kuKa--\r\n"

        # init sqlite database
        self.db = sqlite3.connect("data.db")
        self.db.execute(
            "create table if not exists data(timestamp integer, remain integer)")

        self.running = False
        self.end = False

    async def login(self):
        await self.client.get("https://colesmobile.com.au/pages/dashboard/")
        res = await self.client.post("https://colesmobile.com.au/login", headers={
            "content-type": "multipart/form-data; boundary=----WebKitFormBoundaryUnIAFTHcy6L5kuKa",
        },  content=self.login_form)
        data = res.json()
        loguru.logger.debug(str(data))
        return data

    def insert(self, timestamp: int, remain: int):
        '''insert data into database'''
        self.db.execute(
            "insert into data (timestamp, remain) values (?, ?)", (timestamp, remain))
        self.db.commit()

    async def get_data(self):
        '''get data'''
        res = await self.client.get(url=self.balance_url)
        data = res.json()
        loguru.logger.debug(str(data))
        return data["productAllowances"][0]

    async def update(self):
        await self.login()
        data = await self.get_data()

        # analyse
        remainingBalance = data["remainingBalance"]
        daysLeft = int(data["daysLeft"])
        remainingBalanceAvg = remainingBalance/daysLeft

        # show
        text = f"剩余流量 {round(remainingBalance / 1024, 2)}GB"
        text += f" 剩余时间 {daysLeft}天"
        text += f" 剩余日均流量 {round(remainingBalanceAvg, 2)}MB"
        loguru.logger.info(text)

        # insert
        self.insert(int(time.time()), int(remainingBalance))

    def start(self):
        self.running = True
        loguru.logger.info("已启动")

    def pause(self):
        self.running = False
        loguru.logger.info("已暂停")

    def stop(self):
        self.running = False
        self.end = True
        loguru.logger.info("已停止")

    async def sleep(self):
        for i in range(self.gap):
            await asyncio.sleep(1)
            if not self.running:
                break

    async def main(self):
        '''main loop'''
        async with httpx.AsyncClient() as client:
            self.client = client

            while True:
                await asyncio.sleep(1)
                if self.end:
                    break
                if self.running:
                    try:
                        await self.update()
                    except KeyboardInterrupt:
                        self.stop()
                        break
                    except:
                        loguru.logger.exception("Update Error")
                    await self.sleep()

    def create_task(self):
        asyncio.create_task(self.main())


async def main():
    cms = ColeMobileSupervisor()
    cms.create_task()
    print("- start\n- pause\n- stop")
    
    loop = asyncio.get_event_loop()

    while True:
        cmd = await loop.run_in_executor(None, input)
        if cmd == "start":
            cms.start()
        if cmd == "pause":
            cms.pause()
        if cmd == "stop":
            cms.stop()
            break
        if cmd == "help":
            print("- start\n- pause\n- stop")

asyncio.run(main())
