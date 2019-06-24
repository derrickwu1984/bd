from scrapy.cmdline import execute
import  logging,sys,re

execute(["scrapy", "crawl", "broadband", "-a", "broadbandNo=010151" , "-a", "startNo=00000", "-a", "endNo=100000"])
# broadbandNo= sys.argv[1]
# if (re.findall("1[345678][01256]\d{4}",phoneNo) and len(phoneNo)==7):
# broadband_len = len(broadbandNo)
# if (broadband_len==7):
#     execute(["scrapy", "crawl", "bd", "-a", "broadband="+broadbandNo, "-a", "startNo=0000", "-a", "endNo=10000"])
# else:
#     execute(["scrapy", "crawl", "bd", "-a", "broadband=" + broadbandNo, "-a", "startNo=000", "-a", "endNo=1000"])
