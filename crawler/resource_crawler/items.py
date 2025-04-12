# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ResourceItem(scrapy.Item):
    # Fields used by the resource crawler
    url = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    content = scrapy.Field()
    code_snippets = scrapy.Field()
    tags = scrapy.Field()
    type = scrapy.Field()
    domain = scrapy.Field()
    languages = scrapy.Field()
    timestamp = scrapy.Field()
    quality_score = scrapy.Field()
