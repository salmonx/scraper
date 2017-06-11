from scrapy import Spider
from scrapy.http import Request

from firmware.items import FirmwareImage
from firmware.loader import FirmwareLoader

import re
import json
import urlparse

class TPLinkENSpider(Spider):
    name = "tp-link_en"
    vendor = "tp-link"
    allowed_domains = ["tp-link.com"]

    start_urls = ["http://www.tp-link.com/phppage/down-load-model-list.html?showEndLife=false&catid=350&appPath=us"]
    base_path = "http://www.tp-link.com/en/"

    def parse(self, response):
        total = json.loads(response.text)
        for product_list in total:
            for product in product_list['row']:
                productname = product['model']
                href = product['href']

                yield Request(
                    url=urlparse.urljoin(
                        self.base_path, href),
                    meta={"product": productname},
                    headers={"Referer": response.url},
                    callback=self.parse_products)

    def parse_products(self, response):
        # <div class="hardware-version"> more than one hardversion for the product
        for href in response.xpath('//div[@class="hardware-version"]//li/a/@href').extract():
            version = re.search("V(\d+)\.html", href).group(1)
            yield Request(
                url = response.url[:response.url.rfind('/') + 1] + href,
                meta = {"product": response.meta['product'],
                        "version": "V{}".format(version),
                        },
                callback = self.parse_product)

    def parse_product(self, response):
            if response.text.count('<h2>Firmware</h2>'):
                description = response.xpath("//div[@class=\"product-name\"]//strong/text()").extract()[0]
                url = response.xpath("//*[@id=\"content_Firmware\"]/table/tbody/tr[1]/th/a/@href").extract()[0]
                date = response.xpath("//*[@id=\"content_Firmware\"]/table/tbody/tr[2]/td[1]/span[2]/text()").extract()[0]

                item = FirmwareLoader(
                    item=FirmwareImage(), response=response, date_fmt=["%d/%m/%y"])

                item.add_value("url", url)
                item.add_value("date", item.find_date(date))
                item.add_value("description", description)
                item.add_value("product", response.meta["product"])
                item.add_value("version", response.meta["version"])
                item.add_value("vendor", self.vendor)
                yield item.load_item()
