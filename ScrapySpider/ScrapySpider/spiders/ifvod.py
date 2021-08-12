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
    'password': '874527a8bdd8ec2a',
    'port': 3306,
    'host': '47.88.17.122',
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
    # for i in range(1, 6, 1):
    #     start_urls.append('https://www.ifsp.tv/list?keyword=&star=&pageSize=36&cid=0,1,4&year=今年&language=-1&region=-1&status=-1&orderBy=2&desc=true&page=' + str(i))

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
          splash:on_request(function(request)
              request:set_timeout(10.0)
          end)
          assert(splash:go(args.url))
          assert(splash:wait(5))
          splash.resource_timeout = 60
          splash.images_enabled = false
          splash.media_source_enabled = false
          splash.html5_media_enabled = false
          splash.private_mode_enabled = false
          splash:on_request(function(request)
              request:set_timeout(10.0)
          end)
          return {
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
        # for i in range(0, len(self.start_urls), 1):
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

            print(url)
            if not(url is None):
                yield SplashRequest(url, callback=self.parse_item, endpoint='execute', meta={'item': item}
                                    , args={'lua_source': self.lua, 'timeout': 3600, 'wait': 3})

    # 抓取分集详情页
    def parse_item(self, response):
        # print(response.text)
        parent_item = response.meta["item"]
        urls = re.findall(r'http[s]?://[^\sw]+/video/languagesplaylist?[^\s]+&pub=[0-9]{13}', response.text)
        if len(urls) == 0:
            return

        r = requests.get(urls[0], timeout=10)
        j = json.loads(r.text)
        if not (j['data']['info'][0]['playList'] is None):
            play_list = j['data']['info'][0]['playList']

        detail_urls = re.findall(r'http[s]?://[^\sw]+/video/detail?[^\s]+&pub=[0-9]{13}', response.text)
        detail_r = requests.get(detail_urls[0], timeout=20)
        detail_j = json.loads(detail_r.text)
        parent_item['vod_director'] = ''
        if not(detail_j['data']['info'][0]['directors'] is None) and len(detail_j['data']['info'][0]['directors']) > 0:
            parent_item['vod_director'] = detail_j['data']['info'][0]['directors'][0]

        if not (detail_j['data']['info'][0]['contxt'] is None) and detail_j['data']['info'][0]['contxt'] != '':
            parent_item['vod_content'] = detail_j['data']['info'][0]['contxt']

        # proxy_url = 'http://tiqu.linksocket.com:81/abroad?type=2&lb=1&sb=0&flow=1&regions=us&port=1&n=0&num=1'
        # r = requests.get(proxy_url, timeout=20)
        # proxy_list = json.loads(r.text)
        # if len(proxy_list['data']) > 0 and not (proxy_list['data'][0] is None):
        #     proxy_host = proxy_list['data'][0]['ip']
        #     proxy_port = proxy_list['data'][0]['port']
        #     proxy = 'http://%(host)s:%(port)s' % {
        #         'host': proxy_host,
        #         'port': proxy_port,
        #     }
        #     print(proxy)
        # else:
        proxy = ''

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
                            SELECT * FROM vod_Play_720 where vod_name = %(vod_name)s and chapter_name = %(chapter_name)s
                            and source = 1
                        """
            # query_table_sql = """
            #                 SELECT * FROM vod_Play_1080 where vod_name = %(vod_name)s and chapter_name = %(chapter_name)s
            #             """
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
        item = response.meta["item"]
        urls = re.findall(r'http[s]?://[^\sw]+/video/play?[^\s]+&pub=[0-9]{13}', response.text)
        if len(urls) == 0:
            return

        req_url = urls[0] + "&uid=128790057&sign=25e60824a0a3aa1accd0a7e1836a972b0427925698ebf097bed35d7cd80d3040_4f73deb6542f1fcaa1ae2b096c1bea0d&token=14dcd831ce6e43dab60d1324b49e8ff6&gid=1"
        r = requests.get(req_url, timeout=10)
        j = json.loads(r.text)
        clarity_list = j['data']['info'][0]['clarity']
        for clarity in clarity_list:
            if not(clarity['path'] is None) and not(clarity['path']['result'] is None):
                if clarity['title'] == '720':
                    item['path'] = response.url
                    item['vod_url'] = clarity['path']['result']
                    # item['chapter_name'] = '720P'

                # elif clarity['title'] == '1080':
                #     item['path'] = response.url
                #     item['vod_url'] = clarity['path']['result']
                # item['chapter_name'] = '1080P'
                else:
                    continue
        yield item