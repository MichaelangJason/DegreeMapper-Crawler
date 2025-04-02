from collections.abc import Iterable
from scrapy import Spider, Selector
from scrapy.http import Request
from scrapy.http import Response
from typing import Any, Dict, List
from dotenv import load_dotenv
import os
import json

load_dotenv()

class CoursesMetaSpider(Spider):
    name = "courses_meta"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.domain = "https://www.mcgill.ca"
        self.year = os.getenv("YEAR")
        self.start_urls = [self.domain + "/study/" + self.year + "/courses/search?page=0"]

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            yield Request(url, callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for course_card in response.css("div.views-row"):
            url = course_card.css("a::attr(href)").get()
            course_id = url.split("/")[-1]
            name = course_card.css("a::text").get()
            faculty = course_card.css("span.views-field-field-faculty-code span.field-content::text").get()
            department = course_card.css("span.views-field-field-dept-code span.field-content::text").get()
            level = course_card.css("span.views-field-level span.field-content::text").get()
            
            yield {
                "url": self.domain + url,
                "id": course_id,
                "name": name,
                "faculty": faculty,
                "department": department,
                "level": level,
            }
            
        next_page = response.css("li.pager-next a::attr(href)").get()
        if next_page:
            yield Request(self.domain + next_page, callback=self.parse)