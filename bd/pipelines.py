# -*- coding: utf-8 -*-
import logging,uuid,pymysql
from bd.db.dbhelper import DBHelper
from .items import CustinfoItem,BdInfoItem

class BdPipeline(object):
    def __init__(self):
        self.db = DBHelper()
    def process_item(self, item, spider):
        if (len(item) > 2 and  item.__class__ == BdInfoItem):
            logging.warning("BdInfoItem")
            self.db.insert_bdInfo(item)
        elif (len(item) > 2 and item.__class__ == CustinfoItem):
            logging.warning("CustinfoItem")
            self.db.insert_custInfo(item)
        return item
