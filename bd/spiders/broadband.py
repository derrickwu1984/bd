# -*- coding: utf-8 -*-
import scrapy,logging,requests,time,json
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from scrapy.http import Request
from urllib import parse
from lxml import etree
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC #期望的条件
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from scrapy.loader import  ItemLoader
from bd.items import BdInfoItem,CustinfoItem
import time,re
import json
import datetime
import pickle
import sys
from io import BytesIO
from scrapy.http.cookies import CookieJar


class BroadbandSpider(scrapy.Spider):
    name = 'broadband'
    allowed_domains = ['cbss.10010.com']
    start_urls = ['https://cbss.10010.com/essframe']
    login_url = "https://cbss.10010.com/essframe"
    # 登陆后的链接
    initmy_url = "https://bj.cbss.10010.com/essframe"
    post_url = "https://bj.cbss.10010.com/acctmanm;"
    driver_path="D:/tools/IEDriverServer.exe"
    # driver_path = "Z:/tools/IEDriverServer.exe"
    # driver_path = "C:/IEDriverServer.exe"
    userName = "bjsc-zhaomx6"
    passWd = "wang1985@"
    province_code = "bj"
    depart_id = "11b2kv5"
    province_id = "11"
    driver = webdriver.Ie(driver_path)
    js_exec = "var but_click=document.getElementsByClassName('submit')[0].children[0].onclick"

    def __init__(self,broadbandNo,startNo,endNo):
        self.broadbandNo=broadbandNo
        self.startNo=startNo
        self.endNo=endNo
        self.cur_month = self.date_Formate(datetime.datetime.now().month)
        self.cur_day =self.date_Formate(datetime.datetime.now().day)
        self.crawldate = str(datetime.datetime.now().year) + str(self.cur_month) + str(self.cur_day)
        self.params =''
        pass

    # 将月份、日期小于10的前面补充0
    def date_Formate(self,object):
        if (object<10):
            object="0"+str(object)
        return object

    def start_requests(self):
        yield scrapy.Request(self.login_url, callback=self.login)

        #     登录逻辑
    def login(self, response):
        self.driver.get(self.login_url)
        time.sleep(3)
        self.driver.find_element_by_id("STAFF_ID").send_keys(self.userName)
        self.driver.find_element_by_id("LOGIN_PASSWORD").send_keys(self.passWd)
        Select(self.driver.find_element_by_name("LOGIN_PROVINCE_CODE")).select_by_value(self.province_id)
        WebDriverWait(self.driver, 1000).until(EC.url_to_be(self.initmy_url))
        logging.warning("恭喜您，您已登录成功了！")
        WebDriverWait(self.driver, 600).until(EC.presence_of_element_located((By.ID, 'navframe')))
        self.driver.switch_to.frame("navframe")
        # time.sleep(30)
        WebDriverWait(self.driver, 600).until(EC.presence_of_element_located((By.ID, 'SECOND_MENU_LINK_BIL6500')))
        # in order to find CSM1001
        js_query_acct = "var query_acct=document.getElementById('SECOND_MENU_LINK_BIL6500').onclick()"
        self.driver.execute_script(js_query_acct)
        time.sleep(3)
        WebDriverWait(self.driver, 600).until(EC.presence_of_element_located((By.ID, 'BIL6531')))
        openmenu = self.driver.find_element_by_id("BIL6531").get_attribute("onclick")
        r = re.findall(r"'([\S\s]+?)'", openmenu)
        request_url = "https://" + self.province_code + ".cbss.10010.com" + r[
            0] + "&staffId=" + self.userName + "&departId=" + self.depart_id + "&subSysCode=CBS&eparchyCode=0010"
        requests.adapters.DEFAULT_RETRIES = 5
        s = requests.session()
        cookies_dict = {}
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            cookies_dict[cookie['name']] = cookie['value']
        with open('cookies.txt', 'w+') as f:
            json.dump(cookies_dict, f)
        with open('cookies.txt', 'r') as f:
            cookie_out = json.load(f)
        headers = {
                'Referer': 'https://bj.cbss.10010.com/essframe?service=page/Sidebar',
                'Host': 'bj.cbss.10010.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'
            }
        yield scrapy.Request(request_url, headers=headers, cookies=cookie_out, callback=self.parse_broadbandNo,
                                 meta={'request_url': request_url})
    # 实时/月结账单查询 号段遍历
    def parse_broadbandNo(self,response):
        request_url=response.meta['request_url']
        html=etree.HTML(response.body.decode("gbk"))
        # time.sleep(10)
        BSS_ACCTMANM_JSESSIONID=html.xpath('//form/@action')[0].split(";")[1]
        service=html.xpath('//input[@name="service"]/@value')[0]
        Form0=html.xpath('//input[@name="Form0"]/@value')[0]
        yy=datetime.datetime.now().year
        mm=datetime.datetime.now().month
        if (mm<10 and mm>1):
            mm="0"+str(mm-1)
        if (mm==1):
            yy=yy-1
            mm=12
        query_month=str(yy)+str(mm)
        post_url=self.post_url+BSS_ACCTMANM_JSESSIONID
        headNo = self.broadbandNo
        for subNo in range(int(self.startNo), int(self.endNo)):
            phoneNo=headNo+str(subNo).zfill(5)
            cond_NET_TYPE_CODE=''
            cond_PARENT_TYPE_CODE=''
            cond_ROUTE_EPARCHY_CODE='0010'
            data=self.prepare_data(cond_ROUTE_EPARCHY_CODE,query_month,phoneNo,cond_NET_TYPE_CODE,cond_PARENT_TYPE_CODE,cond_ROUTE_EPARCHY_CODE,Form0,service)
            BSS_ACCTMANM_JSESSIONID_array=BSS_ACCTMANM_JSESSIONID.split("=")
            BSS_ACCTMANM_JSESSIONID_key=BSS_ACCTMANM_JSESSIONID_array[0]
            BSS_ACCTMANM_JSESSIONID_value = BSS_ACCTMANM_JSESSIONID_array[1]
            BSS_ACCTMANM_JSESSIONID_dict={BSS_ACCTMANM_JSESSIONID_key:BSS_ACCTMANM_JSESSIONID_value}
            with open('cookies.txt', 'r') as f:
                cookie_billPage = json.load(f)
            cookie_billPage.update(BSS_ACCTMANM_JSESSIONID_dict)
            post_headers = {
                'referer':request_url,
                'Host':'bj.cbss.10010.com',
            }
            # 查询月账单信息
            yield scrapy.FormRequest(url=post_url, formdata=data, method="POST",
                                     cookies=cookie_billPage, callback=self.parse_monthly_bill,
                                     meta={'broadbandNo':phoneNo,"headNo":headNo,"query_month":query_month,"request_url":request_url})
    # 实时/月结账单查询 数据解析
    def parse_monthly_bill(self, response):
        response_str=response.body.decode("gbk")
        html = etree.HTML(response_str)
        broadbandNo=response.meta['broadbandNo']
        headNo =response.meta['headNo']
        query_month=response.meta['query_month']
        request_url = response.meta['request_url']
        error_msg =""
        try:
            openmenu_1 = self.driver.find_element_by_id("CSMB043").get_attribute("onclick")
            r_1 = re.findall(r"'([\S\s]+?)'", openmenu_1)
            self.params =r_1
        except:
            self.params=self.params
        userinfo_request_url = "https://" + self.province_code + ".cbss.10010.com" + self.params[
            0] + "&staffId=" + self.userName + "&departId=" + self.depart_id + "&subSysCode=CBS&eparchyCode=0010"
        try:
            error_msg=html.xpath("//div[@class='tip']/ul/li/text()")[0].split("：")[0]
        except:
            pass
        if (error_msg!="" and "错误提示"==error_msg):
            logging.warning(broadbandNo+"宽带号未查询到或已被注销！")
        else:
            logging.warning(broadbandNo+"宽带号有效！")
            # 用户id
            userid=html.xpath('//input[@name="back_USER_ID"]/@value')[0]
            # user_property_dataForm = self.user_property_dataForm("7","csInterquery", broadbandNo, userid)
            # 账户标识
            try:
                acctflag=html.xpath("//table/tr[1]/td[2]/text()")[2].strip()
            except:
                acctflag =html.xpath("//table/tr[1]/td[2]/text()")[1].strip()
            # 付费类型
            try:
                paytype=html.xpath("//table/tr[2]/td[2]/text()")[2].strip()
            except:
                paytype = html.xpath("//table/tr[2]/td[2]/text()")[1].strip()
            # 欠费
            try:
                debtfee=html.xpath("//table/tr[3]/td[2]/text()")[2].strip()
            except:
                debtfee = html.xpath("//table/tr[3]/td[2]/text()")[1].strip()
            try:
                # 融合类型
                fixtype=html.xpath("//table/tr[4]/td[2]/text()")[1].strip()
            except:
                fixtype=html.xpath("//table/tr[4]/td[2]/text()")[0].strip()
            #     付费名称
            try:
                payname=html.xpath("//table/tr[1]/td[4]/text()")[2].strip()
            except:
                payname = html.xpath("//table/tr[1]/td[4]/text()")[1].strip()
            # 产品名称
            try:
                prodname=html.xpath("//table/tr[2]/td[4]/text()")[1].strip()
            except:
                prodname = html.xpath("//table/tr[2]/td[4]/text()")[0].strip()
            # 实时话费
            fee=html.xpath("//table/tr[3]/td[4]/text()")[2].strip()
            # 开通状态
            try:
                openflag=html.xpath("//table/tr[1]/td[6]/text()")[2].strip()
            except:
                openflag = html.xpath("//table/tr[1]/td[6]/text()")[1].strip()
            # 客户品牌
            try:
                custbrand=html.xpath("//table/tr[2]/td[6]/text()")[0].strip()
            except:
                custbrand = html.xpath("//table/tr[2]/td[6]/text()")[1].strip()
            # 实时结余
            actualbal=html.xpath("//table/tr[3]/td[6]/text()")[2].strip()
            # 客户市县
            custlocation=html.xpath("//table/tr[1]/td[8]/text()")[0].strip()
            # 信用额度
            creditbal= html.xpath("//table/tr[3]/td[8]/text()")[0].strip()
            # 总计计费应收
            totalfee = html.xpath("//table[@id='UserBillTable']//tr/td[10]//text()")[-1].strip()
            # 实际计费应收
            actualfee = html.xpath("//table[@id='UserBillTable']//tr/td[14]//text()")[-1].strip()
            # 数据加载到Item
            CustinfoItemLoader = ItemLoader(item=CustinfoItem(),response=response)
            CustinfoItemLoader.add_value("crawldate", self.crawldate)
            CustinfoItemLoader.add_value("userid", userid)
            CustinfoItemLoader.add_value("rangeno", headNo)
            CustinfoItemLoader.add_value("broadbandNo", broadbandNo)
            CustinfoItemLoader.add_value("querymonth", query_month)
            CustinfoItemLoader.add_value("acctflag",acctflag)
            CustinfoItemLoader.add_value("paytype",paytype)
            CustinfoItemLoader.add_value("debtfee",debtfee)
            CustinfoItemLoader.add_value("fixtype",fixtype)
            CustinfoItemLoader.add_value("payname",payname)
            CustinfoItemLoader.add_value("prodname",prodname)
            CustinfoItemLoader.add_value("fee",fee)
            CustinfoItemLoader.add_value("openflag",openflag)
            CustinfoItemLoader.add_value("custbrand",custbrand)
            CustinfoItemLoader.add_value("actualbal",actualbal)
            CustinfoItemLoader.add_value("custlocation",custlocation)
            CustinfoItemLoader.add_value("creditbal",creditbal)
            CustinfoItemLoader.add_value("totalfee",totalfee)
            CustinfoItemLoader.add_value("actualfee",actualfee)
            CustInfo = CustinfoItemLoader.load_item()
            # 宽带信息
            yield CustInfo
            #查询用户综合信息
            yield scrapy.Request(url=userinfo_request_url,headers=self.get_headers(), cookies=self.get_cookie(),
                                      callback=self.query_user_info,meta={'broadbandNo': broadbandNo,'userinfo_request_url':userinfo_request_url},dont_filter=True)
    def query_user_info(self,response):
        Cookie = response.request.headers.getlist('Cookie')
        response_str=response.body.decode("gbk")
        refer_url=response.meta['userinfo_request_url']
        # time.sleep(3)
        html = etree.HTML(response_str)
        DateField=""
        _BoInfo=html.xpath('//input[@name="_BoInfo"]/@value')[0]
        ACCPROVICE_ID=html.xpath('//input[@name="ACCPROVICE_ID"]/@value')[0]
        allInfo=html.xpath('//input[@name="allInfo"]/@value')[0]
        broadbandNo = response.meta['broadbandNo']
        currentRightCode=html.xpath('//input[@name="currentRightCode"]/@value')[0]
        Form0 = html.xpath('//input[@name="Form0"]/@value')[0]
        PROVICE_ID= html.xpath('//input[@name="PROVICE_ID"]/@value')[0]
        queryTradehide=html.xpath('//input[@name="queryTradehide"]/@value')[0]
        service=html.xpath('//input[@name="service"]/@value')[0]
        tabSetList=html.xpath('//input[@name="tabSetList"]/@value')[0]
        headers={
            # "Referer": "https://bj.cbss.10010.com/essframe?service=page/Sidebar,
            # "Referer": "https://bj.cbss.10010.com/custserv",
            "Referer":refer_url,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Host': 'bj.cbss.10010.com'
        }
        cookies = self.get_cookie()
        # del cookies["BSS_CUSTSERV_JSESSIONID"]
        # del cookies["BSS_ACCTMANM_JSESSIONID"]
        # json.dumps(cookies)
        dataForm=self.custserv_dataForm(DateField,_BoInfo,ACCPROVICE_ID,allInfo,broadbandNo,ACCPROVICE_ID,currentRightCode,Form0,PROVICE_ID,queryTradehide,service,tabSetList)
        post_intetrated_url="https://bj.cbss.10010.com/custserv"
        yield scrapy.FormRequest(url=post_intetrated_url, formdata=dataForm, method="POST", headers=headers,cookies=cookies,
                                 callback=self.get_user_property__info,meta={'broadbandNo': broadbandNo},dont_filter=True)
    # 获取用户属性信息
    def get_user_property__info(self,response):
        broadbandNo = response.meta['broadbandNo']
        # time.sleep(2)
        response_str = response.body.decode("gbk")
        html = etree.HTML(response_str)
        jsn = json.loads(html.xpath("//input[@id='userAttrInfo']/@value")[0])
        # 局向
        moffice_name = jsn['MOFFICE_NAME']
        # 详细地址
        detail_installed_address = jsn['DETAIL_INSTALL_ADDRESS']
        # 标准地址
        installed_address = jsn['INSTALL_ADDRESS']
        # 标准地址编码
        address_id = jsn['ADDRESS_ID']
        # 速率
        speed = jsn['SPEED']
        # 联系人
        link_name = jsn['LINK_NAME']
        # 联系电话
        link_phone = jsn['LINK_PHONE']
        # 使用人性质 1:个人
        use_type_code = jsn['USETYPE']
        # 使用人性质、终端启用时间
        try:
            terminal_start_date = jsn['TERMINAL_START_DATE']
        except:
            terminal_start_date=""
        # 数据加载到Item
        boardbandItemLoader = ItemLoader(item=BdInfoItem(), response=response)
        boardbandItemLoader.add_value("crawldate", self.crawldate)
        boardbandItemLoader.add_value("broadbandNo", broadbandNo)
        boardbandItemLoader.add_value("moffice_name", moffice_name)
        boardbandItemLoader.add_value("detail_installed_address", detail_installed_address)
        boardbandItemLoader.add_value("installed_address", installed_address)
        boardbandItemLoader.add_value("address_id", address_id)
        boardbandItemLoader.add_value("speed", speed)
        boardbandItemLoader.add_value("link_name", link_name)
        boardbandItemLoader.add_value("link_phone", link_phone)
        boardbandItemLoader.add_value("use_type_code", use_type_code)
        boardbandItemLoader.add_value("terminal_start_date", terminal_start_date)

        boardbandInfo = boardbandItemLoader.load_item()
        # 宽带信息
        yield boardbandInfo
    # 获取cookie
    def get_cookie(self):
        cookies_dict = {}
        # cookies = self.driver.get_cookies()
        # for cookie in cookies:
        #     cookies_dict[cookie['name']] = cookie['value']
        # with open('cookies.txt', 'w+') as f:
        #     json.dump(cookies_dict, f)
        with open('cookies.txt', 'r') as f:
            cookie_out = json.load(f)
        return cookie_out
    # 获取headers
    def get_headers(self):
        headers = {
            'referer': 'https://bj.cbss.10010.com/essframe?service=page/component.Navigation&listener=init&needNotify=true&staffId='+self.userName+'&departId='+self.depart_id+'&subSysCode=CBS&eparchyCode=0010',
            'Host':'bj.cbss.10010.com'
        }
        return headers

    def prepare_data(self,eparchy_code,query_month,phoneNo,cond_NET_TYPE_CODE,cond_PARENT_TYPE_CODE,cond_ROUTE_EPARCHY_CODE,Form0,service):
        data={
            "back_ACCT_ID":"",
            "back_USER_ID":"",
            "bquerytop":"+%B2%E9+%D1%AF+",
            "cond_ACCT_ID":"",
            "cond_BILLSEARCH_FLAG":"0",
            "cond_CBSSREQUEST_SOURCE":"",
            "cond_CONFIG_BILLCOUNT":"800",
            "cond_CYCLE_ID":query_month,
            "cond_CYCLE_SEGMENT":"6",
            "cond_END_CYCLE_ID":query_month,
            "cond_ID_TYPE":"1",
            "cond_NET_TYPE_CODE":"",
            "cond_NODISTURB":"",
            "cond_PARENT_TYPE_CODE":"",
            "cond_PRE_TAG":"0",
            "cond_REMOVE_TAG":"0",
            "cond_ROUTE_EPARCHY_CODE":"",
            "cond_SEND_SN":'',
            "cond_SENDBILLSMS_RIGHT":"0",
            "cond_SERIAL_NUMBER":phoneNo,
            "cond_SMS":"",
            "cond_USER_ID":"",
            "cond_USER_SERVICE_CODE":"",
            "cond_WRITEOFF_MODE":"1",
            "cond_X_USER_COUNT":"",
            "Form0":Form0,
            "MULTI_ACCT_DATA":"",
            "NOTE_ITEM_DISPLAY":"false",
            "service":service,
            "smsFlag":"false",
            "sp":"S0",
            "userinfoback_USER_ID":"",
            "X_CODING_STR":""
        }
        return data
    # 用户综合资料查询报文数据格式
    def custserv_dataForm(self,DateField,_BoInfo,ACCPROVICE_ID,allInfo,phoneNo,proviceCode,currentRightCode,Form0,PROVICE_ID,queryTradehide,service,tabSetList):
        data={
            "$DateField": DateField,
            "_BoInfo": _BoInfo,
            "AC_INFOS": "",
            "ACCPROVICE_ID": ACCPROVICE_ID,
            "allInfo": allInfo,
            "autoSearch": "no",
            "BILL_BUNDLE_MONTHS":"",
            "chklistframe17_hidden": "",
            "cond_ALIASE_ACCOUNT_IN": "",
            "cond_CUST_ID": "",
            "cond_CUST_NAME": "",
            "cond_NET_TYPE_CODE": "",
            "cond_PAGE_NUM": "",
            "cond_QUERY_METHOD": "0",
            "cond_SERIAL_NUMBER": phoneNo,
            "CS_CHR_QUERY_WO_SCORE": "0",
            "CS_CONTRAL_TAG": "0",
            "CS_SYNC_POPWINDOW": "1",
            "CUR_PROVINCE": proviceCode,
            "CURRENT_BRAND": "",
            "CURRENT_PRODUCT_NAME": "",
            "currentRightCode": currentRightCode,
            "custTreaty": "",
            "CYCLE_TYPE":"",
            "DATAFLOWTAG": "0",
            "Form0": Form0,
            "importTag": "1",
            "N2_QKWB": "",
            "N6_15906_TAGCODE": "0",
            "N6_17426_USE_TAG": "0",
            "PAY_MODE_CODE": "",
            "PAYMENT_CYCLE_MONTHS":"",
            "PROVICE_ID": PROVICE_ID,
            "QUERY_TYPE": "on",
            "queryTradehide": queryTradehide,
            "service": service,
            "sp": "S0",
            "SUPPORT_TAG": "",
            "tabSetList": tabSetList,
            "TAG_CHECKMODE_5": "",
            "TAN_CHUANG": "",
            "titleInfo": "",
            "TRADE_ID": "",
            "userAttrInfo": "",
            "VIP_CUST_LOYAL_529757_TAG": "0"
        }
        return data
    # 用户属性查询报文数据格式
    def user_info_dataForm(self,IDX,RIGHT_CODE,broadbandNo,userId):
        data={

            "custId": "",
            "custName": "",
            "globalPageName": "personalserv.integratequerytrade.IntegrateQueryTrade",
            "IDX": IDX,
            "netTypeCode": "50",
            "passWord": "",
            "queryMethod": "0",
            "removeTag": "0",
            "resNo": "",
            "RIGHT_CODE": RIGHT_CODE,
            "serialNumber": broadbandNo,
            "simCard": "null",
            "userId": userId
        }
        return data
    def parse(self, response):
        pass
