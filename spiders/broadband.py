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


    # post_user_property_url = "https://bj.cbss.10010.com/custserv?service=swallow/common.UtilityPage/getInterfaceElement_first/1"
    driver_path="D:/tools/IEDriverServer.exe"
    # driver_path = "Z:/tools/IEDriverServer.exe"
    # driver_path = "C:/IEDriverServer.exe"
    userName = "bjsc-wangj1"
    passWd = "BySh@2019"
    province_code = "bj"
    depart_id = "11b2pk1"
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
        # WebDriverWait(driver, 600).until(EC.presence_of_element_located((By.ID, 'CSM1001')))
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
                'referer': 'https://bj.cbss.10010.com/essframe?service=page/component.Navigation&listener=init&needNotify=true&staffId=' + self.userName + '&departId=' + self.depart_id + '&subSysCode=CBS&eparchyCode=0010',
                'Host': 'bj.cbss.10010.com'
            }
        yield scrapy.Request(request_url, headers=headers, cookies=cookie_out, callback=self.parse_broadbandNo,
                                 meta={'reqeust_url': request_url})
    # 实时/月结账单查询 号段遍历
    def parse_broadbandNo(self,response):

        reqeust_url=response.meta['reqeust_url']
        html=etree.HTML(response.body.decode("gbk"))
        time.sleep(10)
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
        # #bulid post method
        post_url=self.post_url+BSS_ACCTMANM_JSESSIONID
        headNo = self.broadbandNo
        for subNo in range(int(self.startNo), int(self.endNo)):
            phoneNo=headNo+str(subNo).zfill(4)
            cond_NET_TYPE_CODE=''
            cond_PARENT_TYPE_CODE=''
            cond_ROUTE_EPARCHY_CODE='0010'
            data=self.prepare_data(cond_ROUTE_EPARCHY_CODE,query_month,phoneNo,cond_NET_TYPE_CODE,cond_PARENT_TYPE_CODE,cond_ROUTE_EPARCHY_CODE,Form0,service)
            logging.warning("============post params============")
            logging.warning(data)
            BSS_ACCTMANM_JSESSIONID_array=BSS_ACCTMANM_JSESSIONID.split("=")
            BSS_ACCTMANM_JSESSIONID_key=BSS_ACCTMANM_JSESSIONID_array[0]
            BSS_ACCTMANM_JSESSIONID_value = BSS_ACCTMANM_JSESSIONID_array[1]
            BSS_ACCTMANM_JSESSIONID_dict={BSS_ACCTMANM_JSESSIONID_key:BSS_ACCTMANM_JSESSIONID_value}
            with open('cookies.txt', 'r') as f:
                cookie_billPage = json.load(f)
            cookie_billPage.update(BSS_ACCTMANM_JSESSIONID_dict)
            post_headers = {
                'referer':reqeust_url,
                'Host':'bj.cbss.10010.com',
            }
            # 查询月账单信息
            yield scrapy.FormRequest(url=post_url, formdata=data, method="POST",
                                     cookies=cookie_billPage, callback=self.parse_monthly_bill,
                                     meta={'phoneNo':phoneNo,"headNo":headNo,"query_month":query_month})
    # 实时/月结账单查询 数据解析
    def parse_monthly_bill(self, response):
        response_str=response.body.decode("gbk")
        html = etree.HTML(response_str)
        broadbandNo=response.meta['phoneNo']
        headNo =response.meta['headNo']
        query_month=response.meta['query_month']
        error_msg =""
        openmenu_1 = self.driver.find_element_by_id("CSMB043").get_attribute("onclick")
        r_1 = re.findall(r"'([\S\s]+?)'", openmenu_1)
        userinfo_request_url = "https://" + self.province_code + ".cbss.10010.com" + r_1[
            0] + "&staffId=" + self.userName + "&departId=" + self.depart_id + "&subSysCode=CBS&eparchyCode=0010"
        try:
            error_msg=html.xpath("//div[@class='tip']/ul/li/text()")[0].split("：")[0]
        except:
            pass
        if (error_msg!="" and "错误提示"==error_msg):
            logging.warning(broadbandNo+"宽带号未查询到或已被注销！")
        else:
            logging.warning(broadbandNo+"宽带号有效！")
            userid=html.xpath('//input[@name="back_USER_ID"]/@value')[0]
            # user_property_dataForm = self.user_property_dataForm("7","csInterquery", broadbandNo, userid)
            acctflag=html.xpath("//table/tr/td[2]//text()")[12].strip()
            paytype=html.xpath("//table/tr/td[2]//text()")[13].strip()
            debtfee=html.xpath("//table/tr/td[2]//text()")[14].strip()
            try:
                fixtype=html.xpath("//table/tr/td[2]//text()")[15].strip()
            except:
                fixtype=""
            payname=html.xpath("//table/tr/td[4]//text()")[-3].strip()
            prodname=html.xpath("//table/tr/td[4]//text()")[-2].strip()
            fee=html.xpath("//table/tr/td[4]//text()")[-1].strip()
            openflag=html.xpath("//table/tr/td[6]//text()")[-3].strip()
            custbrand=html.xpath("//table/tr/td[6]//text()")[-2].strip()
            actualbal=html.xpath("//table/tr/td[6]//text()")[-1].strip()
            custlocation=html.xpath("//table/tr/td[8]//text()")[0].strip()
            creditbal= html.xpath("//table/tr/td[8]//text()")[1].strip()
            totalfee = html.xpath("//table[@id='UserBillTable']//tr/td[10]//text()")[-1].strip()
            actualfee = html.xpath("//table[@id='UserBillTable']//tr/td[14]//text()")[-1].strip()

            # 数据加载到Item
            # mobileItemLoader = ItemLoader(item=MobileItem(),response=response)
            # mobileItemLoader.add_value("crawldate", self.crawldate)
            # mobileItemLoader.add_value("userid", userid)
            # mobileItemLoader.add_value("rangeno", headNo)
            # mobileItemLoader.add_value("phoneno", phoneNo)
            # mobileItemLoader.add_value("querymonth", query_month)
            # mobileItemLoader.add_value("acctflag",acctflag)
            # mobileItemLoader.add_value("paytype",paytype)
            # mobileItemLoader.add_value("debtfee",debtfee)
            # mobileItemLoader.add_value("fixtype",fixtype)
            # mobileItemLoader.add_value("payname",payname)
            # mobileItemLoader.add_value("prodname",prodname)
            # mobileItemLoader.add_value("fee",fee)
            # mobileItemLoader.add_value("openflag",openflag)
            # mobileItemLoader.add_value("custbrand",custbrand)
            # mobileItemLoader.add_value("actualbal",actualbal)
            # mobileItemLoader.add_value("custlocation",custlocation)
            # mobileItemLoader.add_value("creditbal",creditbal)
            # mobileItemLoader.add_value("totalfee",totalfee)
            # mobileItemLoader.add_value("actualfee",actualfee)
            # userInfo = mobileItemLoader.load_item()
            # 账单信息
            # yield userInfo
            # 用户属性信息
            #查询用户综合信息
            yield scrapy.Request(url=userinfo_request_url,headers=self.get_headers(), cookies=self.get_cookie(),
                                      callback=self.query_user_info,meta={'broadbandNo': broadbandNo},dont_filter=True)
    def query_user_info(self,response):
        html = etree.HTML(response.body.decode("gbk"))
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
        dataForm=self.custserv_dataForm(DateField,_BoInfo,ACCPROVICE_ID,allInfo,broadbandNo,ACCPROVICE_ID,currentRightCode,Form0,PROVICE_ID,queryTradehide,service,tabSetList)
        post_intetrated_url="https://bj.cbss.10010.com/custserv"
        yield scrapy.FormRequest(url=post_intetrated_url, formdata=dataForm, method="POST", headers=self.get_headers(),cookies=self.get_cookie(),
                                 callback=self.get_user_property__info,meta={'phoneNo': broadbandNo},dont_filter=True)
    # 获取用户属性信息
    def get_user_property__info(self,response):
        logging.warning("============get_user_property_info============")
        broadbandNo = response.meta['broadbandNo']
        response_str = response.body.decode()
        logging.warning(broadbandNo)
        html = bytes(bytearray(response_str, encoding='utf-8'))
        html = etree.HTML(html)
        jsn = json.loads(html.xpath("//input[@id='userAttrInfo']/@value")[0])
        moffice_name = jsn['MOFFICE_NAME']
        detail_installed_address = jsn['DETAIL_INSTALL_ADDRESS']
        installed_address = jsn['INSTALL_ADDRESS']
        address_id = jsn['ADDRESS_ID']
        speed = jsn['SPEED']
        link_name = jsn['LINK_NAME']
        link_phone = jsn['LINK_PHONE']
        use_type_code = jsn['USE_TYPE_CODE']
        terminal_start_date = jsn['TERMINAL_START_DATE']
        logging.warning("link_name")
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
            "chklistframe17_hidden": "",
            "cond_ALIASE_ACCOUNT_IN": "",
            "cond_CUST_ID": "",
            "cond_CUST_NAME": "",
            "cond_NET_TYPE_CODE": "50",
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
            "DATAFLOWTAG": "0",
            "Form0": Form0,
            "importTag": "1",
            "N2_QKWB": "",
            "N6_15906_TAGCODE": "0",
            "N6_17426_USE_TAG": "0",
            "PAY_MODE_CODE": "",
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
