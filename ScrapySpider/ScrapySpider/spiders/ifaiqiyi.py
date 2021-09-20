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
import time

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
    base_jiexi_url = 'http://66.165.227.210:8899/?url='
    custom_settings = {
        'ITEM_PIPELINES': {
            'ScrapySpider.pipelines.ifIqiyiPipeline': 300,
        },
    }
    caiji_list_url = 'http://jhzy.jhdyw.vip:8091/api.php/provide/vod/from/qiyi/at/json/?ac=list&t=&pg=1&h=24&ids=&wd='
    base_caiji_url = 'http://jhzy.jhdyw.vip:8091/api.php/provide/vod/from/qiyi/at/json/?ac=videolist&t=&h=24&ids=&wd=&pg='
    drama_bind = ['连续剧', '国产', '港台', '日韩', '欧美']
    movie_bind = ['电影', '动作', '喜剧', '爱情', '科幻', '恐怖', '剧情', '战争', '惊悚', '犯罪', '冒险', '悬疑', '武侠', '奇幻']
    enter_bind = ['综艺']
    anni_bind = ['动画', '动漫']
    docu_bind = ['记录']

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
        list_res = requests.get(self.caiji_list_url, timeout=10)
        list_dict = json.loads(list_res.text)
        page_count = list_dict['pagecount']
        # for page in range(1, 2, 1):
        for page in range(1, page_count+1, 1):
            caiji_url = self.base_caiji_url + str(page)
            caiji_res = requests.get(caiji_url, timeout=10)
            caiji_str = caiji_res.text
            caiji_dict = json.loads(caiji_str)
            video_list = caiji_dict['list']
            # for i in range(0, 2, 1):
            for i in range(0, len(video_list), 1):
                video = video_list[i]
                item = IfVodItem()
                if video['type_name'] in self.drama_bind:
                    item['type_name'] = '连续剧'
                elif video['type_name'] in self.movie_bind:
                    item['type_name'] = '电影'
                elif video['type_name'] in self.enter_bind:
                    item['type_name'] = '综艺'
                elif video['type_name'] in self.anni_bind:
                    item['type_name'] = '动漫'
                elif video['type_name'] in self.docu_bind:
                    item['type_name'] = '纪录片'

                item['vod_name'] = video['vod_name']
                item['vod_class'] = video['vod_class']
                item['vod_actor'] = video['vod_actor']
                item['vod_director'] = video['vod_director']
                item['vod_class'] = video['vod_class'] + ',' + video['type_name']
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
                # for j in range(0, 1, 1):
                for j in range(0, len(play_url_arr), 1):
                    ifitem = IfVodItem()
                    ifitem = dict(item)
                    chapter_str = play_url_arr[j]
                    chapter_arr = chapter_str.split('$')
                    chapter_name = chapter_arr[0]
                    if item['type_name'] == '连续剧' or item['type_name'] == '动漫' or item['type_name'] == '纪录片':
                        if '第' in chapter_name:
                            chapter_name = chapter_name.replace('第', '')
                        if '集' in chapter_name:
                            chapter_name = chapter_name.replace('集', '')
                        if len(chapter_name) == 1:
                            chapter_name = '0' + chapter_name

                    ifitem['chapter_name'] = chapter_name
                    chapter_url = chapter_arr[1]
                    chapter_url = self.base_jiexi_url + chapter_url
                    # --------------判断是否存在--------------
                    # conn = pymysql.Connect(**config)
                    cusor = self.conn.cursor(cursor=DictCursor)
                    query_table_sql = """
                       SELECT * FROM vod_Play_720 where vod_name = %(vod_name)s and chapter_name = %(chapter_name)s
                       and type_name = %(type_name)s
                   """
                    item_dict = dict(ifitem)
                    # --------------查询数据--------------
                    cusor.execute(query_table_sql, item_dict)
                    results = cusor.fetchall()
                    print('查询到1：' + '/' + ifitem['vod_name'] + '/' + ifitem['chapter_name'])
                    if len(results) > 0:
                        print('该视频已经入库:' + '/' + ifitem['vod_name'] + '/' + ifitem['chapter_name'])
                        continue
                    if chapter_url != '':
                        yield scrapy.Request(chapter_url, callback=self.parseDetail
                                             , meta={'item': ifitem})
                        time.sleep(2)

    def parseDetail(self, response):
        item = response.meta['item']
        j = json.loads(response.text)
        if not ('code' in j.keys()) or j['code'] != '200':
            print("解析失败")
            return
        m3u8_url = j['url']
        item['vod_url'] = m3u8_url
        item['path'] = response.url

        yield item

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


