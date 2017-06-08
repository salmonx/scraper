#coding:utf-8
from scrapy import Spider
from scrapy.http import Request

from firmware.items import FirmwareImage
from firmware.loader import FirmwareLoader

import re


class HuaweiZHSpider(Spider):
    name = "huawei_zh"
    vendor = "huawei"
    region = "cn"
    product = ""
    description = ""
    #allowed_domains = ["emui.com", "dbankcloud.com"]
    start_urls = ["http://www.emui.com/plugin/hwdownload/download?dep2=6"]

    def parse(self, response):
        for a in response.xpath("//a"):
            if a.xpath("./@class").extract() and a.xpath("./@class").extract()[0].count(u'智能路由器'):
                href = a.xpath("./@href").extract()[0]
                if href.startswith('http://www.emui.com/cn/plugin/hwdownload/detail?modelId='):
                    yield Request(
                        url = href,
                        headers={"Referer": response.url},
                        callback=self.parse_page)



    def parse_page(self, response):
        self.product = response.xpath("//div[@class='emdet-l']/h2/text()").extract()[0]

        #emat-tab gf1 开发版
        #emat-tab gf2 稳定版
        dev = response.xpath("//div[@class='emat-tab gf1']")
        if dev:
            self.description = '开发版'
            yield self.parse_product(dev, response)

        stable = response.xpath("//div[@class='emat-tab gf2']")
        if stable:
            self.description = '稳定版'
            yield self.parse_product(stable, response)


    def parse_product(self, data, response):
       
        tmp = data.xpath("//div[@class='emat-cont']/p[1]/text()").extract()[0]
        date_group = re.search(u'([\d]{4})年([\d]{1,2})月([\d]{1,2})日', tmp)
        date = '{}-{}-{}'.format(date_group.group(1), date_group.group(2), date_group.group(3))
        version = re.search(u'版本: ([a-zA-Z0-9]+)', tmp).group(1)
        url = data.xpath("//div[@class='emat-cont']/a/@href").extract()[0]

        item = FirmwareLoader(
            item=FirmwareImage(), response=response)


        item.add_value("version", version)
        item.add_value("date", date)
        item.add_value("description", self.description)
        item.add_value("url", url)
        item.add_value("product", self.product)
        item.add_value("vendor", self.vendor)
        
        return item.load_item()