# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class BdItem(scrapy.Item):
    crawldate = scrapy.Field()
    userid = scrapy.Field()
    rangeno = scrapy.Field()
    broadbandNo = scrapy.Field()
    querymonth = scrapy.Field()
    acctflag = scrapy.Field()
    paytype = scrapy.Field()
    debtfee = scrapy.Field()
    fixtype = scrapy.Field()
    payname = scrapy.Field()
    prodname = scrapy.Field()
    fee = scrapy.Field()
    openflag = scrapy.Field()
    custbrand = scrapy.Field()
    actualbal = scrapy.Field()
    custlocation = scrapy.Field()
    creditbal = scrapy.Field()
    totalfee = scrapy.Field()
    actualfee = scrapy.Field()
    pass

class CustinfoItem(scrapy.Item):
    crawldate = scrapy.Field()
    userid = scrapy.Field()
    rangeno = scrapy.Field()
    phoneno = scrapy.Field()
    querymonth = scrapy.Field()
    acctflag = scrapy.Field()
    paytype = scrapy.Field()
    debtfee = scrapy.Field()
    fixtype = scrapy.Field()
    payname = scrapy.Field()
    prodname = scrapy.Field()
    fee = scrapy.Field()
    openflag = scrapy.Field()
    custbrand = scrapy.Field()
    actualbal = scrapy.Field()
    custlocation = scrapy.Field()
    creditbal = scrapy.Field()
    totalfee = scrapy.Field()
    actualfee = scrapy.Field()
    pass
