# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

#import json
#import codecs
import pyorient

#from pymongo import MongoClient

class VNEGiaoDucPipeline(object):
    def __init__(self, client):
        self.client = client

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            client = pyorient.OrientDB("localhost", 2480)
        )

    def process_item(self, item, spider):
        
        """client = MongoClient()
        db = client.allvnexpress
        collAll = db.all
        oneRow = {
            "subject": item["subject"],
            "link": item["link"],
            "title": item["title"],
            "content": item["content"]
        }
        collAll.insert_one(oneRow)
        collAll.insert(dict(item))"""
        #self.client.command("INSERT INTO docs ( 'subject', 'link', 'title', 'content' ) values ( '" + item["subject"] + "', '" + item["link"] + "', '" + item["title"] + "', '" + item["content"] + "' )")
        self.client.command("INSERT INTO docs ( subject, link, title, content ) VALUES ( '%s', '%s', '%s', '%s' )" % (item["subject"], item["link"], item["title"], item["content"]))

        return item
        
    def open_spider(self, spider):
        session_id = self.client.connect("root", "123456")
        self.client.db_open("vne_giaoduc", "duytri", "123456")

    def close_spider(self, spider):
        self.client.db_close()
