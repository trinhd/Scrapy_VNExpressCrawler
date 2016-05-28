# -*- coding: utf-8 -*-
import scrapy
import pymongo
import re

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
from vnexpress.items import VnexpressItem

from pymongo import MongoClient


class AllvnexpressSpider(scrapy.Spider):
	name = "allvnexpress"
	allowed_domains = ["vnexpress.net"]
	start_urls = (
		'http://vnexpress.net/',
		#'http://suckhoe.vnexpress.net/tin-tuc/dinh-duong/thuc-don/3-mon-an-giau-canxi-giup-tre-tang-chieu-cao-3350896.html',
		#'http://suckhoe.vnexpress.net/tin-tuc/suc-khoe/truy-nghi-van-nuoc-giai-khat-nhiem-chi-va-hoi-lo-can-bo-kiem-nghiem-3402482.html',
		#'http://giaitri.vnexpress.net/tin-tuc/gioi-sao/trong-nuoc/bo-trong-nhan-gia-dinh-khong-muon-con-duoc-tung-ho-qua-som-3403502.html',
	)

	rules = (
		Rule(LinkExtractor(deny=('/cong-dong/hoi-dap/')), callback='parse'),
		Rule(LinkExtractor(deny=('/tin-tuc/cong-dong/')), callback='parse'),
		Rule(LinkExtractor(deny=('video.vnexpress.net')), callback='parse')
	)

	count = 0

	def parse(self, response):
		links = response.xpath("//a/@href").extract()
		#links = ()

		crawledLinks = []
		client = MongoClient()
		db = client.allvnexpress
		collCrawledLinks = db.crawledLinks
		for cl in collCrawledLinks.find():
			crawledLinks.append(str(cl["crawled"])) #doc lai tu csdl nhung link da crawl

		linkPattern = re.compile("^(?:ftp|http|https):\/\/(?:[\w\.\-\+]+:{0,1}[\w\.\-\+]*@)?(?:[a-z0-9\-\.]+)(?::[0-9]+)?(?:\/|\/(?:[\w#!:\.\?\+=&amp;%@!\-\/\(\)]+)|\?(?:[\w#!:\.\?\+=&amp;%@!\-\/\(\)]+))?$")

		for link in links:
			if linkPattern.match(link) and not link in crawledLinks:
				collCrawledLinks.insert_one({"crawled": link})
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
		
		content = self.removeHTMLSpecialEntities(document)

		collAll = db.all
		oneRow = {
			"subject": subject,
			"link": response.url,
			"title": title,
			"content": content
		}
		collAll.insert_one(oneRow)

		item = VnexpressItem()
		item['link'] = response.url
		item['subject'] = subject
		item['title'] = title
		item['content'] = content
		self.count = self.count + 1
		print self.count
		yield item;

	def detectTag(self, sInput, iBegin):
	#Tim dau < dau tien de bat dau xac dinh the tag
		iBeginAngleBracketOpen = sInput.find('<', iBegin)
		if iBeginAngleBracketOpen == -1:
			return ['-1', '-1', len(sInput)] #Da het dau mo tag

		if iBeginAngleBracketOpen < len(sInput): #Neu dau mo the tag khong nam cuoi cung cua doan
			#Xac dinh vi tri khoang trang de xac dinh ten the tag la gi
			iFirstSpaceAfterAngle = sInput.find(' ', iBeginAngleBracketOpen)

			#Xac dinh vi tri dau dong ngoac cua the tag
			iBeginAngleBracketClose = sInput.find('>', iBeginAngleBracketOpen)
			if iBeginAngleBracketClose == -1:
				return ['-1', '-1', iBeginAngleBracketOpen + 1] #Neu khong co dau dong the tag thi do khong phai la tag html, tra ve vi tri tim kiem tiep theo la tu sau dau mo the tag vua tim duoc.

			
			if iBeginAngleBracketClose > iFirstSpaceAfterAngle and iFirstSpaceAfterAngle != -1: #Neu co khoang trang truoc khi co dau dong ngoac the tag, tuc la the tag co attrib
				sTag = sInput[iBeginAngleBracketOpen + 1:iFirstSpaceAfterAngle]
			else: #Nguoc lai, la mot the tag binh thuong
				sTag = sInput[iBeginAngleBracketOpen + 1:iBeginAngleBracketClose]

			iEndAngleBracketOpen = sInput.find('</'+sTag+'>', iBeginAngleBracketClose)
			if iEndAngleBracketOpen == -1:
				return ['-1','-1', iBeginAngleBracketClose + 1]

			return [sInput[iBeginAngleBracketOpen: iBeginAngleBracketClose + 1], sInput[iEndAngleBracketOpen: iEndAngleBracketOpen + len(sTag) + 3], iBeginAngleBracketOpen]; #Cong 3 do: 1 dau /, 1 dau > va 1 index cach ra
		else:
			return ['-1', '-1', len(sInput)] #Da het cach tim kiem

	def removeHTMLSpecialEntities(self, sInput):
		sOutput = sInput.replace("<br>\n", "\n") #Thay the tag break line
		sOutput = sOutput.replace("<br>", "\n") #Thay the tag break line
		sOutput = re.sub(r'<img\s[\w=\"\-\s\.]{1,}src="http:\/\/[\w\.\d\/\-]{1,}">', "",sOutput) #Thay the tag img
		sOutput = re.sub(r'&(aacute|Aacute|Acirc|acirc|acute|aelig|AElig|Agrave|agrave|alpha|Alpha|amp|and|ang|Aring|aring|asymp|Atilde|atilde|Auml|auml|bdquo|beta|Beta|brvbar|bull|cap|Ccedil|ccedil|cedil|cent|circ|clubs|cong|copy|crarr|cup|curren|Chi|chi|Dagger|dagger|darr|deg|delta|Delta|diams|divide|Eacute|eacute|Ecirc|ecirc|Egrave|egrave|empty|emsp|ensp|epsilon|Epsilon|equiv|eta|Eta|eth|ETH|euml|Euml|euro|exist|fnof|forall|frac12|frac14|frac34|gamma|Gamma|ge|gt|harr|hearts|hellip|Iacute|iacute|Icirc|icirc|iexcl|igrave|Igrave|infin|int|iota|Iota|iquest|isin|iuml|Iuml|kappa|Kappa|lambda|Lambda|laquo|larr|lceil|ldquo|le|lfloor|lowast|loz|lrm|lsaquo|lsquo|lt|macr|mdash|micro|minus|Mu|mu|nabla|nbsp|ndash|ne|ni|not|notin|nsub|ntilde|Ntilde|nu|Nu|oacute|Oacute|ocirc|Ocirc|oelig|OElig|ograve|Ograve|oline|Omega|omega|Omicron|omicron|oplus|or|ordf|ordm|oslash|Oslash|otilde|Otilde|otimes|Ouml|ouml|para|part|permil|perp|Pi|pi|piv|plusmn|pound|Prime|prime|prod|prop|Psi|psi|phi|Phi|radic|raquo|rarr|rceil|rdquo|reg|rfloor|rho|Rho|rlm|rsaquo|rsquo|sbquo|scaron|Scaron|sdot|sect|shy|Sigma|sigma|sigmaf|sim|spades|sub|sube|sum|sup|sup1|sup2|sup3|supe|szlig|tau|Tau|tilde|times|there4|Theta|theta|thetasym|thinsp|thorn|THORN|trade|uacute|Uacute|uarr|Ucirc|ucirc|Ugrave|ugrave|uml|upsih|upsilon|Upsilon|Uuml|uuml|Xi|xi|yacute|Yacute|yen|yuml|Yuml|Zeta|zeta|zwj|zwnj|;)+', "", sOutput)
		return sOutput;