import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy_splash import SplashRequest
import re
from bs4 import BeautifulSoup
from selenium import webdriver
import requests
import json
from ScrapySpider.ifvodItems import IfVodItem
import pymysql
from pymysql.cursors import DictCursor
from scrapy import signals

config = {
    'user': 'root',
    'password': '696d9c48b1875ffe',
    'port': 3306,
    'host': '47.74.90.95',
    'db': 'beiwo2',
    'charset': 'utf8'
}

class IfVodSpider(CrawlSpider):
    name = 'ifvod'
    # allowed_domains = ['www.ifsp.tv/', ]
    base_domain = 'https://www.ifsp.tv'
    base_play_url = 'https://www.ifsp.tv/play?id='
    post_domain = 'http://src.shcdn-qq.com'
    post_url = post_domain+'/api/importDownload?format=json&key=38vKpMAk'
    start_urls = list()
    # for i in range(1, 24, 1):
    #     start_urls.append('https://www.ifsp.tv/list?keyword=&star=&pageSize=36&cid=0,1,4&year=今年&language=-1&region=-1&status=-1&orderBy=1&desc=true&page=' + str(i))

    # for i in range(1, 10, 1):
    #     start_urls.append('https://www.ifsp.tv/list?keyword=&star=&pageSize=36&cid=0,1,4&year=去年&language=-1&region=-1&status=-1&orderBy=2&desc=true&page=' + str(i))
    #
    # for i in range(1, 66, 1):
    #     start_urls.append('https://www.ifsp.tv/list?keyword=&star=&pageSize=36&cid=0,1,4&year=更早&language=-1&region=-1&status=-1&orderBy=2&desc=true&page=' + str(i))

    # 抓取连载
    for i in range(1, 9, 1):
        start_urls.append('https://www.ifsp.tv/list?keyword=&star=&pageSize=36&cid=0,1,4&year=-1&language=-1&region=-1&status=-1&orderBy=1&desc=true&page=' + str(i))

    lua = '''
function main(splash, args)
  splash.resource_timeout = 60
  splash.images_enabled = false
  splash.media_source_enabled = false
  splash.html5_media_enabled = false
  splash.private_mode_enabled = false
  splash:init_cookies({
		{name="_gat_gtag_UA_148163531_4", value="1", path="/", domain=".ifsp.tv", expiry="1628768477", secure=false, httpOnly=false},
		{name="_ga", value="GA1.2.1392162307.1628385208", path="/", domain=".ifsp.tv", expiry="1691840417", secure=false, httpOnly=false},
	  {name="_ga_JHZNJS4296", value="GS1.1.1628756130.6.1.1628768415.0", path="/", domain=".ifsp.tv", expiry="1691840415", secure=false, httpOnly=false},
		{name="dn_temp", value="__t=%7B%22uid%22%3A128790057%2C%22expire%22%3A%221628858416.64655%22%2C%22gid%22%3A1%2C%22sign%22%3A%22737699f14a9813d8571517429bb8559766aaab78fe60292e107571746572a62f_4f73deb6542f1fcaa1ae2b096c1bea0d%22%2C%22token%22%3A%2222160f3f9f414eed8fe669fa847441ca%22%7D&token=22160f3f9f414eed8fe669fa847441ca&isbind=true", path="/", domain=".ifsp.tv", secure=false, httpOnly=false},
		{name="autologin", value="", path="/", domain=".ifsp.tv", expiry="2492385521", secure=true, httpOnly=false, sameSite="Lax"},
		{name="_gid", value="GA1.2.449543848.1628573339", path="/", domain=".ifsp.tv", expiry="1628854817", secure=false, httpOnly=false},
		{name="dn_config", value="region=GL.", path="/", domain=".ifsp.tv", expiry="1660304417", secure=false, httpOnly=false},
  })
  splash:on_request(function(request)
  request:set_timeout(10.0)
    end)
  assert(splash:go(args.url))
  assert(splash:wait(5))
  return {
    html = splash:html(),
    png = splash:png(),
    har = splash:har(),
  }
end
    '''
    # proxy = "http://us_123456-zone-custom-region-us:jp123456@proxy.ipidea.io:2333"

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(IfVodSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.conn = pymysql.Connect(**config)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        spider.conn.close()
        print('爬虫结束了')

    # 抓取列表页
    def start_requests(self):

        for i in range(0, 1, 1):
        # for i in range(0, len(self.start_urls), 16):
            req_url = self.start_urls[i]
            yield SplashRequest(req_url, callback=self.parse, args={'wait': 5})

    # 抓取详情页
    def parse(self, response):
        page_url = response.url
        soup = BeautifulSoup(response.text, 'html.parser')
        video_list = soup.select('.search-results .v-c')

        # for i in range(0, 1, 1):
        for i in range(0, len(video_list), 1):
            item = IfVodItem()
            video = video_list[i]

            item['type_name'] = '连续剧'
            if not(video.select_one('.video-teaser .title-box .title a') is None):
                item['vod_name'] = video.select_one('.video-teaser .title-box .title a').string
                url = video.select_one('.video-teaser .title-box .title a').attrs['href']
                url = self.base_domain + url

            if not(video.select_one('.video-teaser .title-box .text-small span') is None):
                item['vod_class'] = video.select_one('.video-teaser .title-box .text-small span').string

            if not (video.select_one('.teaser-detail .detail-starring') is None):
                item['vod_actor'] = video.select_one('.teaser-detail .detail-starring').get_text()

            if not (video.select_one('.video-teaser .v-content img') is None):
                item['vod_pic'] = video.select_one('.video-teaser .v-content img').attrs['src']

            if not (video.select_one('.video-teaser .v-content .rating') is None):
                item['vod_score'] = video.select_one('.video-teaser .v-content .rating').string

            if not (video.select_one('.teaser-detail .detail-story span:last-child').get_text() is None):
                item['vod_content'] = video.select_one('.teaser-detail .detail-story span:last-child').get_text()

            item['vod_area'] = ''
            item['vod_year'] = ''
            area_list = ['大陆', '香港', '台湾', '日本', '韩国', '欧美', '英国', '泰国', '其他']
            tag_list = dict()
            if not (video.select('.teaser-detail .detail-tags span') is None):
                tag_list = video.select('.teaser-detail .detail-tags span')

            if "今年" in page_url:
                item['vod_year'] = '2021'
            elif "去年" in page_url:
                item['vod_year'] = '2020'
            else:
                for tag in tag_list:
                    if tag.string.isdigit() and len(tag.string) == 4:
                        item['vod_year'] = tag.string

            for tag in tag_list:
                if tag.string in area_list:
                    item['vod_area'] = tag.string

            proxy = 'http://user-sp13690464:jp123456@gate.dc.smartproxy.com:20000'

            print(url)
            if not(url is None):
                item['proxy'] = proxy
                yield SplashRequest(url, callback=self.parse_item, endpoint='execute', meta={'item': item}
                                    , args={'lua_source': self.lua, 'timeout': 3600, 'wait': 3, 'proxy': proxy})

    # 抓取分集详情页
    def parse_item(self, response):
        # print(response.text)
        parent_item = response.meta["item"]
        proxy = parent_item["proxy"]
        j = json.loads(response.text)
        har = j['har']
        list_url = ''
        detail_url = ''
        for entry in har['log']['entries']:
            if entry['response']['status'] == 200 and '/video/languagesplaylist' in entry['request']['url']:
                list_url = entry['request']['url']
            if entry['response']['status'] == 200 and '/video/detail' in entry['request']['url']:
                detail_url = entry['request']['url']

        if list_url == '' or detail_url == '':
            return

        r = requests.get(list_url, timeout=10)
        j = json.loads(r.text)
        if not (j['data']['info'][0]['playList'] is None):
            play_list = j['data']['info'][0]['playList']

        # detail_urls = re.findall(r'http[s]?://[^\sw]+/video/detail?[^\s]+&pub=[0-9]{13}', response.text)
        detail_r = requests.get(detail_url, timeout=20)
        detail_j = json.loads(detail_r.text)
        parent_item['vod_director'] = ''
        if not(detail_j['data']['info'][0]['directors'] is None) and len(detail_j['data']['info'][0]['directors']) > 0:
            parent_item['vod_director'] = detail_j['data']['info'][0]['directors'][0]

        if not (detail_j['data']['info'][0]['contxt'] is None) and detail_j['data']['info'][0]['contxt'] != '':
            parent_item['vod_content'] = detail_j['data']['info'][0]['contxt']

        # for i in range(0, 1, 1):
        for i in range(0, len(play_list), 1):
            play = play_list[i]
            if play['name'].find("花絮") != -1:
                continue

            item = IfVodItem()
            item = dict(parent_item)
            item['chapter_name'] = play['name']
            item['path'] = self.base_play_url + play['key']
            # --------------判断是否存在--------------
            # conn = pymysql.Connect(**config)
            cusor = self.conn.cursor(cursor=DictCursor)
            query_table_sql = """
                            SELECT * FROM vod_Play_480 where vod_name = %(vod_name)s and chapter_name = %(chapter_name)s
                            and type_name = %(type_name)s
                        """
            item_dict = dict(item)
            # --------------查询数据--------------
            cusor.execute(query_table_sql, item_dict)
            results = cusor.fetchall()
            print('查询到1：' + '/' + item['vod_name'] + '/' + item['chapter_name'])
            if len(results) > 0:
                print('该视频已经入库:' + '/' + item['vod_name'] + '/' + item['chapter_name'])
                continue

            if proxy == '':
                yield SplashRequest(self.base_play_url + play['key'], callback=self.parse_detail,
                                    args={'lua_source': self.lua, 'timeout': 3600, 'wait': 3},
                                    endpoint='execute', meta={'item': item})
            else:
                print(proxy)
                yield SplashRequest(self.base_play_url + play['key'], callback=self.parse_detail,
                                    args={'lua_source': self.lua, 'timeout': 3600, 'wait': 3, 'proxy': proxy},
                                    endpoint='execute', meta={'item': item})

    # 抓取详情页，m3u8
    def parse_detail(self, response):
        parent_item = response.meta["item"]
        j = json.loads(response.text)
        har = j['har']
        print('running detail')
        parent_item['vod_url'] = ""
        parent_item['path'] = response.url
        for entry in har['log']['entries']:
            if entry['response']['status'] == 200 and 'chunklist.m3u8' in entry['request']['url']:
                parent_item['vod_url'] = entry['request']['url']
                # parent_item['chapter_name'] = '720P'

        if parent_item['vod_url'] == '':
            print(parent_item)
        else:
            yield parent_item