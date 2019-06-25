# _*_coding:utf-8_*_
__author__ = 'wmx'
__date__ = '2019/4/4 9:44'

import  pymysql,uuid,logging,copy
from twisted.enterprise import adbapi
from scrapy.utils.project import get_project_settings #导入setting文件


class DBHelper():

    def __init__(self):
        settings = get_project_settings()

        dbparam = dict (
            host = settings['MYSQL_HOST'],
            db = settings['MYSQL_DBNAME'],
            user = settings['MYSQL_USER'],
            passwd = settings['MYSQL_PASSWD'],
            charset = 'utf8',#编码要加上，否则可能出现中文乱码问题
            cursorclass = pymysql.cursors.DictCursor,
            use_unicode = False,
        )
        # **表示将字典扩展为关键字参数,相当于host=xxx,db=yyy....
        dbpool = adbapi.ConnectionPool('pymysql',**dbparam)
        self.dbpool = dbpool

    def connect(self):
        return self.dbpool

    #插入数据
    def insert_custInfo(self,item):
        insert_sql = """
        insert into bd_custInfo(object_id,crawldate,userid,rangeno,
                                  broadbandNo,querymonth,acctflag,paytype,
                                  debtfee,fixtype, payname,prodname,
                                  fee,openflag,custbrand,actualbal,
                                  custlocation,creditbal,totalfee,actualfee)
                       values (%s,%s,%s,%s,
                                %s,%s,%s,%s,
                                %s,%s,%s,%s,
                                %s,%s,%s,%s,
                                %s,%s,%s,%s)
            """
        # 对象拷贝   深拷贝
        asynItem = copy.deepcopy(item)
        # 调用插入的方法
        query = self.dbpool.runInteraction(self._custInfo_insert,insert_sql,asynItem)
        # 调用异常处理方法
        query.addErrback(self._handle_error)
        return item

    # 写入数据库中
    def _custInfo_insert(self,cursor,sql,item):
        # 取出要存入的数据，这里item就是爬虫代码爬下来要存入items内的数据
        params = (str(uuid.uuid1()),item["crawldate"],item["userid"], item["rangeno"], item["broadbandNo"], item["querymonth"]
                                    , item["acctflag"], item["paytype"], item["debtfee"], item["fixtype"]
                                    , item["payname"], item["prodname"], item["fee"], item["openflag"]
                                    , item["custbrand"], item["actualbal"], item["custlocation"], item["creditbal"]
                                    , item["totalfee"], item["actualfee"])
        cursor.execute(sql, params)

    def insert_bdInfo(self,item):
        insert_sql = """
        insert into bd_Info(object_id,crawldate,moffice_name,broadbandNo,
                              terminal_start_date,detail_installed_address,installed_address,address_id,
                              speed,link_name,link_phone,use_type_code)
                       values (%s,%s,%s,%s,
                                %s,%s,%s,%s,
                                %s,%s,%s,%s)
            """
        # 对象拷贝   深拷贝
        asynItem = copy.deepcopy(item)
        # 调用插入的方法
        query = self.dbpool.runInteraction(self._bdInfo_insert,insert_sql,asynItem)
        # 调用异常处理方法
        query.addErrback(self._handle_error)
        return item


    def _bdInfo_insert(self,cursor,sql,item):
        # 取出要存入的数据，这里item就是爬虫代码爬下来要存入items内的数据
        params = (str(uuid.uuid1()),item["crawldate"],item["moffice_name"],item["broadbandNo"],
                  item["terminal_start_date"],item["detail_installed_address"], item["installed_address"], item["address_id"],
                  item["speed"],item["link_name"],item["link_phone"],item["use_type_code"])
        cursor.execute(sql, params)

    def _handle_error(self,failure):
        logging.warning("--------------database operation exception!!----------------")
        logging.warning(failure)