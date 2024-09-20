import scrapy
from dotenv import load_dotenv
import requests

import os
import json
from pathlib import Path
import time

load_dotenv()
PERSONAL_TOKEN = os.environ.get("PERSONAL_TOKEN")
post_proxies_url = "https://test-rg8.ddns.net/api/post_proxies"
get_token_url = "https://test-rg8.ddns.net/api/get_token"


class ProxySpider(scrapy.Spider):
    name = 'proxyspider'
    start_urls = [
        "https://www.freeproxy.world/?page=1",
        "https://www.freeproxy.world/?page=2",
        "https://www.freeproxy.world/?page=3",
        "https://www.freeproxy.world/?page=4",
        "https://www.freeproxy.world/?page=5",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = None

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ProxySpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=scrapy.signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=scrapy.signals.spider_closed)
        return spider
    
    def spider_opened(self):
        # Record the start time when the spider is opened
        self.start_time = time.perf_counter()

    def spider_closed(self):
        # Calculate the total time when the spider is closed
        total_seconds = time.perf_counter() - self.start_time
        total_time = time.strftime("%H:%M:%S", time.gmtime(total_seconds))

        Path("time.txt").write_text(f"Total time taken: {total_time}")

    def parse(self, response):
        table = response.css("table.layui-table")
        proxies = list()

        for data in table:
            ips = data.css("td.show-ip-div::text").getall()
            ports = response.css("td.show-ip-div + td a::text").getall()
            for ip, port in zip(ips, ports):
                print(ip.strip())
                print(port.strip())
                proxies.append(f"{ip.strip()}:{port.strip()}")
        
        proxies_string = ", ".join(proxies)
        payload = {
            "user_id": PERSONAL_TOKEN,
            "len": len(proxies),
            "proxies": proxies_string
        }

        s = requests.Session()
        s.get(get_token_url)
        r = s.post(url=post_proxies_url, json=payload)
        response_json = r.json()
        save_id = response_json.get("save_id")

        try:
            result = json.loads(Path("results.json").read_text())
        except json.JSONDecodeError:
            result = {}

        result[f"save_id_{save_id}"] = proxies
        Path("results.json").write_text(json.dumps(result, indent=4))
        time.sleep(20) # not to DDoS https://test-rg8.ddns.net
