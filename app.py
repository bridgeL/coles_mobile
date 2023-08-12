import pathlib
import asyncio
import datetime
import httpx
import sqlite3
import json


class Main:
    def load(self) -> None:
        '''load config and initialize modules'''
        # load config
        path = pathlib.Path(__file__).with_name("config.json")

        if not path.exists():
            raise FileNotFoundError("配置文件不存在")

        text = path.read_text("utf8")
        config = json.loads(text)

        # init spider
        self.url = f"https://colesmobile.com.au/api/v1/rest/network/balance/{config['SERVERID']}"
        self.headers = {
            "cookie": f"SITEACTIVEID={config['SITEACTIVEID']};"
        }

        # init sqlite database
        self.db = sqlite3.connect("data.db")
        self.db.execute(
            "create table if not exists data(timestamp integer, remain integer)")

    def insert(self, timestamp, remain):
        '''insert data into database'''
        self.db.execute(
            "insert into data (timestamp, remain) values (?, ?)", (timestamp, remain))
        self.db.commit()

    def get_dt(self):
        '''get current datetime'''
        return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=10)))

    async def get_data(self):
        '''get data'''
        async with httpx.AsyncClient() as c:
            res = await c.get(url=self.url, headers=self.headers)
        data = res.json()
        if "error" in data:
            raise ConnectionRefusedError("site active id is expired")
        return data["productAllowances"][0]

    async def main(self):
        '''main loop'''
        while True:
            dt = self.get_dt()
            dt_str = dt.strftime("%Y/%m/%d %H:%M:%S")
            dt_int = int(dt.timestamp())

            data = await self.get_data()

            remainingBalance = data["remainingBalance"]
            remainingBalance_int = int(remainingBalance)
            daysLeft = int(data["daysLeft"])
            remainingBalanceAvg = remainingBalance/daysLeft

            text = f"[{dt_str}]"
            text += f" 剩余流量 {round(remainingBalance / 1024, 2)}GB"
            text += f" 剩余时间 {daysLeft}天"
            text += f" 剩余日均流量 {round(remainingBalanceAvg, 2)}MB"
            print(text)

            self.insert(dt_int, remainingBalance_int)

            await asyncio.sleep(3600)

    def run(self):
        '''start'''
        self.load()
        asyncio.run(self.main())


Main().run()
