import asyncio
import datetime
import httpx
import sqlite3
import configparser

read_ini = configparser.RawConfigParser(strict=False)
read_ini.read("config.ini", "utf8")


class Main:
    def load(self) -> None:
        '''load config and initialize modules'''

        # load config
        SERVERID = read_ini['coles']['serverid']
        USERNAME = read_ini["coles"]["username"]
        PASSWORD = read_ini["coles"]["password"]

        self.balance_url = f"https://colesmobile.com.au/api/v1/rest/network/balance/{SERVERID}"
        self.login_form = f"------WebKitFormBoundaryUnIAFTHcy6L5kuKa\r\nContent-Disposition: form-data; name=\"username\"\r\n\r\n{USERNAME}\r\n------WebKitFormBoundaryUnIAFTHcy6L5kuKa\r\nContent-Disposition: form-data; name=\"password\"\r\n\r\n{PASSWORD}\r\n------WebKitFormBoundaryUnIAFTHcy6L5kuKa\r\nContent-Disposition: form-data; name=\"remember-me\"\r\n\r\nundefined\r\n------WebKitFormBoundaryUnIAFTHcy6L5kuKa--\r\n"

        # init sqlite database
        self.db = sqlite3.connect("data.db")
        self.db.execute(
            "create table if not exists data(timestamp integer, remain integer)")

        # init time zone
        self.tz = datetime.timezone(datetime.timedelta(hours=10))

    async def login(self):
        # get siteactiveid
        await self.client.get("https://colesmobile.com.au/pages/dashboard/")
        res = await self.client.post("https://colesmobile.com.au/login", headers={
            "content-type": "multipart/form-data; boundary=----WebKitFormBoundaryUnIAFTHcy6L5kuKa",
        },  content=self.login_form)
        print(res.json())
        print(self.client.cookies["SITEACTIVEID"])

    def insert(self, timestamp, remain):
        '''insert data into database'''
        self.db.execute(
            "insert into data (timestamp, remain) values (?, ?)", (timestamp, remain))
        self.db.commit()

    async def get_data(self):
        '''get data'''
        res = await self.client.get(url=self.balance_url)
        data = res.json()
        if "error" in data:
            return
        return data["productAllowances"][0]

    async def update(self):
        data = await self.get_data()

        # update login status
        if not data:
            await self.login()
            data = await self.get_data()

        if not data:
            raise Exception("cannot get data")

        # analyse
        remainingBalance = data["remainingBalance"]
        daysLeft = int(data["daysLeft"])
        remainingBalanceAvg = remainingBalance/daysLeft

        # show
        dt = datetime.datetime.now(self.tz)
        dt_str = dt.strftime("%Y/%m/%d %H:%M:%S")
        text = f"[{dt_str}]"
        text += f" 剩余流量 {round(remainingBalance / 1024, 2)}GB"
        text += f" 剩余时间 {daysLeft}天"
        text += f" 剩余日均流量 {round(remainingBalanceAvg, 2)}MB"
        print(text)

        # insert
        self.insert(int(dt.timestamp()), int(remainingBalance))

    async def main(self):
        '''main loop'''
        self.load()

        async with httpx.AsyncClient() as client:
            self.client = client

            while True:
                await self.update()
                await asyncio.sleep(3600)

    def run(self):
        '''start'''
        asyncio.run(self.main())


Main().run()
