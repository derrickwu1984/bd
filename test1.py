# _*_coding:utf-8_*_
__author__ = 'wmx'
__date__ = '2019/4/29 17:12'
import  json

def get_cookie():
    cookies_dict = {}
    # cookies = self.driver.get_cookies()
    # for cookie in cookies:
    #     cookies_dict[cookie['name']] = cookie['value']
    # with open('cookies.txt', 'w+') as f:
    #     json.dump(cookies_dict, f)
    with open('cookies.txt', 'r') as f:
        cookie_out = json.load(f)
    return cookie_out

if __name__ == "__main__":
    fileToDict = get_cookie()
    # print (fileToDict)
    del fileToDict["BSS_CUSTSERV_JSESSIONID"]
    print (json.dumps(fileToDict))