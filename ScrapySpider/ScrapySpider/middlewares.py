# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import json
import pickle
import time

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from browsermobproxy import Server
from selenium.webdriver.common.action_chains import ActionChains


class ScrapyspiderSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ScrapyspiderDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class SelenuimDownloaderMiddleware:

    def process_request(self, request, spider):
        server = spider.server
        proxy = spider.proxy

        chrome_options = Options()
        chrome_options.add_argument('--proxy-server={0}'.format(proxy.proxy))
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--no-sandbox')
        capabilities = DesiredCapabilities.CHROME.copy()
        capabilities['acceptSslCerts'] = True
        capabilities['acceptInsecureCerts'] = True
        chrome: WebDriver = webdriver.Chrome(executable_path=r'C:\Users\Administrator\Desktop\newTV_spider_python\ScrapySpider\ScrapySpider\ChromeDriver\chromedriver.exe'
                                  , chrome_options=chrome_options, desired_capabilities=capabilities)
        url = request.url
        proxy.new_har(options={'captureHeaders': True, 'captureContent': True})
        chrome.get('https://www.ifsp.tv')
        with open('./cookies.txt', 'r') as cookief:
            # 使用json读取cookies 注意读取的是文件 所以用load而不是loads
            if cookief != None and cookief != '':
                cookieslist = json.load(cookief)
                for cookie in cookieslist:
                    chrome.add_cookie(cookie)

        chrome.get(url)
        # chrome.refresh()
        with open('cookies.txt', 'w') as cookief:
            # 将cookies保存为json格式
            cookief.write(json.dumps(chrome.get_cookies()))
        if 'id=' in url and 'a=' not in url:
            chrome.refresh()
            # chrome.find_element_by_tag_name('button').click()
            time.sleep(8)  # seconds
        else:
            buttons = chrome.find_elements_by_tag_name('button')
            for bt in buttons:
                if bt.text == '提交':
                    # bt.click()
                    # time.sleep(5)
                    # actions = ActionChains(chrome)
                    # # actions.move_by_offset(10, 70).context_click().perform()
                    # actions.move_by_offset(10, 70).double_click().perform()
                    # actions.move_by_offset(10, 70).double_click().perform()
                    chrome.execute_script('''var buttons = document.getElementsByTagName('button');buttons[0].click();''')

            time.sleep(5)  # seconds

        html = chrome.page_source
        har = proxy.har
        body = {'html': html, 'har': har}
        body = json.dumps(body)
        chrome.quit()
        # server.stop()
        return HtmlResponse(url=url, body=body, request=request, encoding='utf-8')
