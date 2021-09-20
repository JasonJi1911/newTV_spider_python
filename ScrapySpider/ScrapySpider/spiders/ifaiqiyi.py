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

class IfaiqiyiSpider(scrapy.Spider):
    name = 'ifaiqiyi'
    # allowed_domains = ['www.jxsp.tv']
    base_jiexi_url = 'http://rysp.tv/jx/?url='
    custom_settings = {
        'ITEM_PIPELINES': {
            'ScrapySpider.pipelines.ifIqiyiPipeline': 300,
        },
    }
    caiji_list_url = 'http://jhzy.jhdyw.vip:8091/api.php/provide/vod/from/qiyi/at/json/?ac=list&t=&pg=1&h=24&ids=&wd='
    base_caiji_url = 'http://jhzy.jhdyw.vip:8091/api.php/provide/vod/from/qiyi/at/json/?ac=videolist&t=&h=24&ids=&wd=&pg='
    start_urls = list()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(IfaiqiyiSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.conn = pymysql.Connect(**config)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        spider.conn.close()
        print('爬虫结束了')

    def start_requests(self):
        list_res = requests.get(self.caiji_list_ul, timeout=10)
        list_dict = json.loads(list_res.text)
        page_count = list_dict['pagecount']
        for page in range(1, page_count+1, 1):
            caiji_url = self.base_caiji_url + str(page)
            caiji_str = requests.get(caiji_url, timeout=10)
            caiji_dict = json.loads(caiji_str)
            video_list = caiji_dict['list']
            for video in video_list:
                item = IfVodItem()
                item['type_name'] = video['type_name']
                item['vod_name'] = video['vod_name']
                item['vod_class'] = video['vod_class']
                item['vod_actor'] = video['vod_actor']
                item['vod_director'] = video['vod_director']
                item['vod_class'] = video['vod_class']
                item['vod_pic'] = video['vod_pic']
                item['vod_score'] = video['vod_score']
                item['vod_content'] = video['vod_content']
                item['vod_year'] = video['vod_year']
                if video['vod_area'] == '中国' or '内地' in video['vod_area'] or '大陆' in video['vod_area'] or '华语' in video['vod_area']:
                    item['vod_area'] = '大陆'
                elif '港' in video['vod_area']:
                    item['vod_area'] = '香港'
                elif '台' in video['vod_area']:
                    item['vod_area'] = '台湾'
                elif '美' in video['vod_area'] or '欧' in video['vod_area'] or '法' in video['vod_area']:
                    item['vod_area'] = '欧美'
                elif '韩国' in video['vod_area']:
                    item['vod_area'] = '韩国'
                elif '日' in video['video_area']:
                    item['vod_area'] = '韩国'
                elif '英' in video['video_area']:
                    item['vod_area'] = '英国'
                elif '泰' in video['video_area']:
                    item['vod_area'] = '泰国'
                else:
                    item['vod_area'] = '其他'
                play_url_str = video['vod_play_url']
                play_url_arr = play_url_str.split('#')
                for j in range(0, 1, 1):
                # for j in range(0, len(play_url_arr), 1):
                    chapter_str = play_url_arr[j]
                    chapter_arr = chapter_str.split('$')
                    chapter_name = chapter_arr[0]
                    if item['type_name'] == '连续剧' or item['type_name'] == '动漫' or item['type_name'] == '纪录片':
                        if '第' in chapter_name:
                            chapter_name = chapter_name.replace('第', '')
                        if '集' in chapter_name:
                            chapter_name = chapter_name.replace('集', '')

                    item['chapter_name'] = chapter_name
                    chapter_url = chapter_arr[1]
                    if chapter_url != '':
                        yield scrapy.Request(chapter_url, callback=self.parseDetail
                                             , meta={'item': item})

    def parseDetail(self, response):
        item = response.meta['item']
        j = json.loads(response.text)
        if not ('code' in j.keys()) or j['code'] != '200':
            print("解析失败")
            return
        m3u8_url = j['url']
        item['vod_url'] = m3u8_url
        item['path'] = response.url

        print(item)

    def start_requests2(self):
        with self.conn.cursor(cursor=DictCursor) as c:
            # 查询语句
            query_table_sql = """
                SELECT a.video_id, b.title as vod_name, a.title, a.resource_url 
                from sf_video_chapter AS a 
                inner join sf_video as b on a.video_id = b.id
                WHERE a.resource_url like '%.iqiyi.%' limit 5
            """
            c.execute(query_table_sql)
            results = c.fetchall()
            print('视频数量: ' + str(len(results)))
            # for i in range(0, 1, 1):
            for i in range(0, len(results), 1):
                chapter = results[i]
                resource_str = chapter['resource_url']
                resource_arr = json.loads(resource_str)
                source = ""
                response_url = ''
                for key in resource_arr:
                    source = key
                    value = resource_arr[key]
                    if ".iqiyi." in value:
                        response_url = self.base_jiexi_url + value

                print(response_url)
                video_id = chapter['video_id']
                title = chapter['title']
                vod_name = chapter['vod_name']
                if response_url != '':
                    yield scrapy.Request(response_url, callback=self.parseDetail
                                         , meta={'source': source, 'title': title, 'vod_name': vod_name})

    def parseDetail2(self, response):
        source = response.meta['source']
        title = response.meta['title']
        vod_name = response.meta['vod_name']

        j = json.loads(response.text)
        if not ('code' in j.keys()) or j['code'] != '200':
            print("解析失败")
            return

        m3u8_url = j['url']
        item = IfVodItem()
        item['vod_name'] = vod_name
        item['chapter_name'] = title
        item['vod_url'] = m3u8_url
        item['source'] = source
        item['type_name'] = 'iqiyi'

        yield item


