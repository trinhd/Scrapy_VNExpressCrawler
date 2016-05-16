# -*- coding: utf-8 -*-
import scrapy

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
from vnexpress.items import VnexpressItem

import re

class AllvnexpressSpider(scrapy.Spider):
    name = "allvnexpress"
    allowed_domains = ["vnexpress.net"]
    start_urls = (
        'http://vnexpress.net/',
		#'http://sohoa.vnexpress.net/tin-tuc/san-pham/dien-thoai/smartphone-co-cam-bien-van-tay-gia-4-2-trieu-dong-tai-vn-3319796.html',
    )

    rules = (
	Rule(LinkExtractor(deny=('/cong-dong/hoi-dap/')), callback='parse')
    )

    count = 0

    def parse(self, response):
	links = response.xpath("//a/@href").extract()

	crawledLinks = []

	linkPattern = re.compile("^(?:ftp|http|https):\/\/(?:[\w\.\-\+]+:{0,1}[\w\.\-\+]*@)?(?:[a-z0-9\-\.]+)(?::[0-9]+)?(?:\/|\/(?:[\w#!:\.\?\+=&amp;%@!\-\/\(\)]+)|\?(?:[\w#!:\.\?\+=&amp;%@!\-\/\(\)]+))?$")

	for link in links:
	    if linkPattern.match(link) and not link in crawledLinks:
	        crawledLinks.append(link)
		yield Request(link, self.parse)
	
	subject = response.xpath('//li[contains(@class, "start")]/a/text()').extract_first()
	contents = response.xpath('//div[contains(@class, "fck_detail")]/p').extract()
	document = response.xpath('//div[contains(@class, "short_intro")]/text()').extract_first()
	title = response.xpath('//div[@class="title_news"]/h1/text()').extract_first()

	if title == None:
		return

	for para in contents:
	    """inPList = para.xpath('./span/text()').extract()
	    if inPList is None:
		inPList = para.xpath('./em/text()').extract()
		if inPList is None:
		    document = document + " " + para.xpath('./text()').extract_first()
		else:
		    for em in para:
	    if para.xpath('./span/text()').extract() is not None
		document = document + " " + para.xpath('./span/text()').extract_first()
	    elif para.xpath('./em/text()').extract() is not None:
		document = document + " " + para.xpath('./em/text()').extract_first()
	    else: document = document + " " + para.xpath('./text()').extract_first()

	para = contents[2]"""

	    deTag = self.detectTag(para, 0)
	    #print para
	    #print deTag
	    #print '-------------------'
	    while deTag[2] < len(para):
		if deTag[0] != '-1' and deTag[1] != '-1':
		    para = para.replace(deTag[0], '', 1).replace(deTag[1], '', 1)
		deTag = self.detectTag(para, deTag[2])
		#print para
		#print deTag
		#print '-------------------'
	    document = document + " " + para
    
	item = VnexpressItem()
	item['link'] = response.url
	item['subject'] = subject
	item['title'] = title
	item['content'] = document
	self.count = self.count + 1
	print self.count
	yield item

    def detectTag(self, sInput, iBegin):
	#Tim dau < dau tien de bat dau xac dinh the tag
	iBeginAngleBracketOpen = sInput.find('<', iBegin)
	if iBeginAngleBracketOpen == -1:
	    return ['-1', '-1', len(sInput)] #Da het dau mo tag
	
	#Xac dinh vi tri khoang trang de xac dinh ten the tag la gi
	iFirstSpaceAfterAngle = sInput.find(' ', iBeginAngleBracketOpen)

	#Xac dinh vi tri dau dong ngoac cua the tag
	iBeginAngleBracketClose = sInput.find('>', iBeginAngleBracketOpen)
	if iBeginAngleBracketClose == -1:
	    return ['-1', '-1', iBeginAngleBracketOpen + 1] #Neu khong co dau dong the tag thi do khong phai la tag html, tra ve vi tri tim kiem tiep theo la tu sau dau mo the tag vua tim duoc.

	if iBeginAngleBracketOpen < len(sInput): #Neu dau mo the tag khong nam cuoi cung cua doan
	    if iBeginAngleBracketClose > iFirstSpaceAfterAngle and iFirstSpaceAfterAngle != -1: #Neu co khoang trang truoc khi co dau dong ngoac the tag, tuc la the tag co attrib
		sTag = sInput[iBeginAngleBracketOpen + 1:iFirstSpaceAfterAngle]
	    else: #Nguoc lai, la mot the tag binh thuong
		sTag = sInput[iBeginAngleBracketOpen + 1:iBeginAngleBracketClose]
	else:
	    return ['-1', '-1', len(sInput)] #Da het cach tim kiem

	iEndAngleBracketOpen = sInput.find('</'+sTag+'>', iBeginAngleBracketClose)
	if iEndAngleBracketOpen == -1:
	    return ['-1','-1', iBeginAngleBracketClose + 1]

	return [sInput[iBeginAngleBracketOpen: iBeginAngleBracketClose + 1], sInput[iEndAngleBracketOpen: iEndAngleBracketOpen + len(sTag) + 3], 0] #Cong 3 do: 1 dau /, 1 dau > va 1 index cach ra