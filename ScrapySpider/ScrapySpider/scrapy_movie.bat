@echo off

echo "这里的D:和D:\Python 是Python文件所在的盘及路径"
cd C:\Users\Administrator\Desktop\newTV_720\ScrapySpider\ScrapySpider
echo "开始抓取电影"
scrapy crawl ifmovie2
echo "运行完毕"
exit