# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import scrapy
from scrapy.pipelines.files import FilesPipeline

class MyFilesPipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None):
        return request.meta.get('filename', '')

    def get_media_requests(self, item, info):
        file_url = item['file_url']
        if file_url:
            meta={'filename': item['file_name']}
            yield scrapy.Request(url=file_url, meta=meta)