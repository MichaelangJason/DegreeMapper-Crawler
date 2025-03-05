from collections.abc import Iterable
from scrapy import Spider, Selector
from scrapy.http import Request
from scrapy.http import Response
from typing import Any, Dict, List
from dotenv import load_dotenv
from pymongo import MongoClient
from bs4 import BeautifulSoup
import json
import os
load_dotenv()

class ProgramsMetaSpider(Spider):
    name = "programs_meta"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.domain = "https://www.mcgill.ca"
        self.year = os.getenv("YEAR")
        self.start_urls = [ self.domain + "/study/" + self.year + "/programs/search?page=0" ]

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            yield Request(url, callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # self.log(response.url)
        for program_card in response.css("div.views-row"):
            url = program_card.css("a::attr(href)").get()
            # program_id = url.split("/")[-1]
            name = program_card.css("a::text").get()
            faculty = program_card.css("span.views-field-field-faculty-code span.field-content::text").get()
            department = program_card.css("span.views-field-field-dept-code span.field-content::text").get()
            level = program_card.css("span.views-field-field-level-code span.field-content::text").get()
            degree = program_card.css("span.views-field-field-degree-code span.field-content::text").get()

            # self.log(f"Found program: {title} - URL: {url}, Faculty: {faculty}, Department: {department}, Level: {level}, Degree: {degree}")

            yield {
                "url": self.domain + url,
                # "id": program_id,
                "name": name,
                "faculty": faculty,
                "department": department,
                "level": level,
                "degree": degree
            }
            
        next_page = response.css("li.pager-next a::attr(href)").get()
        # self.log(f"Next page: {next_page}")
        if next_page:
            yield Request(self.domain + next_page, callback=self.parse)


class ProgramsSpider(Spider):
    name = "programs"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.year = os.getenv("YEAR")

    def start_requests(self) -> Iterable[Request]:
        client = MongoClient(os.getenv("MONGODB_URI"))
        db = client[os.getenv("MONGODB_DATABASE_NAME")]
        collection = db["programs" + "_" + self.year.replace("-", "_")]

        urls = [program["url"] for program in collection.find()]
        # self.log(f"Found {len(urls)} programs")
        
        for url in ["https://www.mcgill.ca/study/2024-2025/faculties/law/undergraduate/programs/bachelor-civil-law-bcl-and-juris-doctor-jd-law"]:
            yield Request(url, callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Use BeautifulSoup to get direct children more reliably
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.select_one("div.node-program div.content")
        
        # Get direct children only
        direct_children = content_div.find_all(recursive=False) if content_div else []
        # print(f"Number of direct children with BeautifulSoup: {len(direct_children)}")
        
        # we now parse the children one by one
        results: Dict[str, Dict[str, str | List[str]] | str] = {}
        curr_key = ""
        curr_value: str | List[str] = ""

        def clean_text(text: str | List[str]) -> str | List[str]:
            if isinstance(text, str):
                return text.strip().strip("\n")
            else:
                return [item.strip().strip("\n") for item in text]

        for child in direct_children:
            try:
                # print(child.name)
                if child.name == 'h3':
                    # print(child.text)
                    # we have a new section
                    curr_key = "overview"
                    # print(child.text.strip())
                    
                elif child.name == 'h4':
                    if clean_text(child.text) == "":
                        continue

                    if curr_key != "":
                        results[curr_key] = clean_text(curr_value)
                        curr_key = ""
                        curr_value = ""
                    # we have a new subsection
                    curr_key = clean_text(child.text)

                elif child.name == 'p':
                    # we have a new paragraph
                    if curr_key == "":
                        raise Exception("Paragraph found before section")
                    if len(clean_text(child.text)) == 0:
                        continue
                    
                    if len(curr_value) == 0: # first paragraph
                        curr_value = clean_text(child.text)
                    elif isinstance(curr_value, str):
                        curr_value = curr_value + "\n" + clean_text(child.text)
                    elif isinstance(curr_value, list) and len(curr_value) > 0:
                        curr_value = curr_value + [clean_text(child.text)]
                    

                elif child.name == 'ul':
                    # Handle the case where some li elements might not have an 'a' tag
                    entries = []

                    for li in child.find_all('li', recursive=False):
                        a_tag = li.find("a")

                        if not a_tag or a_tag.attrs["href"] == "" or len(a_tag.text) == 0:
                            continue

                        if a_tag.attrs["href"] != "":
                            text = a_tag.attrs["href"] \
                                .split("/")[-1] \
                                .upper() \
                                .replace("-", " ")
                            entries.append(clean_text(text))
                        else:
                            text = a_tag.text
                            entries.append(clean_text(text))
                    
                    # print("Found list with", len(entries), "items")
                    # print("\n")
                    # print(entries, len(entries))
                    if len(curr_value) == 0:
                        curr_value = entries
                    elif isinstance(curr_value, str):
                        curr_value = [curr_value] + entries
                    elif isinstance(curr_value, list):
                        curr_value = curr_value + entries

                else:
                    if curr_key != "":
                        results[curr_key] = clean_text(curr_value)
            except Exception as e:
                print(f"Error processing child {child.name}: {e}, {child.text}")
                continue

        if curr_key != "":
            results[curr_key] = clean_text(curr_value)

        if "overview" not in results:
            # print (response.url)
            print(json.dumps(results, indent=4))
            raise Exception("Overview not found")
        
        # print(json.dumps(results, indent=4))
        
        response = {
            "url": response.url,
            "overview": results.pop("overview"),
            "sections": results
        }

        # print(json.dumps(response, indent=4))

        # self.log(response["url"])

        yield response


        
