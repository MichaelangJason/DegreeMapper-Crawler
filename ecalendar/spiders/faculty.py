from collections.abc import Iterable
from scrapy import Spider
from scrapy.http import Response, Request
import httpx
from typing import Any, Dict, Set, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
import tqdm
load_dotenv()

class CSFacultySpider(Spider):
    name = "cs_faculty"
    
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.base_url = "www.cs.mcgill.ca"
        self.crawled_urls: Set[str] = set()
        self.visited_urls: Set[str] = set()
        self.all_urls: Set[str] = set()
        self.is_header_crawled = False

    def start_requests(self) -> Iterable[Request]:
        # Start with the base URL
        self.get_all_urls()
        for endpoint in self.all_urls:
            yield Request(urljoin(f"https://{self.base_url}", endpoint), callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Process the current page content
        content_dict = self.fetch_content(response.text, response.url)

        yield {
            "url": urlparse(response.url).path,
            "content": content_dict
        }


    def get_all_urls(self) -> Set[str]:
        base_url = f'https://{self.base_url}'
        # add trailing slash if not present
        if not base_url.endswith('/'):
            base_url += '/'

        # get all urls from the base url
        urls = set(self.get_all_urls_from_url(base_url))
        self.all_urls.update(urls)
        visited_endpoints: Set[str] = set()

        while urls:
            endpoint = urls.pop()
            if endpoint in visited_endpoints:
                continue
            visited_endpoints.add(endpoint)
            target_url = urljoin(base_url, endpoint)
            # print(target_url)
            res = self.get_all_urls_from_url(target_url)

            urls.update(res)
            self.all_urls.update(res)

        return self.all_urls

    def get_all_urls_from_url(self, target_url: str) -> Set[str]:
        if not target_url.endswith('/'):
            target_url += '/'

        urls = []
        # get all urls from the base url
        with httpx.Client() as client:
            response = client.get(target_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # skip header container if already visited
            header_container = soup.find('div', id='headercontainer')
            if header_container and self.is_header_crawled:
                header_container.decompose()
            elif header_container:
                self.is_header_crawled = True

            # find all endpoints in the page
            for a_tag in soup.find_all('a', href=True):
                if isinstance(a_tag, Tag):
                    href = a_tag.get('href')
                    if href and self.is_valid_url(str(href)) \
                        and href not in self.all_urls:
                        # add trailing slash if not present and no file extension
                        normalized_href = str(href)
                        if '.' not in normalized_href.split('/')[-1]:
                            normalized_href = normalized_href.rstrip('/') + '/'
                        
                        if normalized_href not in self.all_urls:
                            urls.append(normalized_href)
        return set(urls)

    def fetch_content(self, text: str, url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(text, 'html.parser')

        main_content = soup.find_all('div', class_='panel')

        if not main_content:
            print(f"No main content found for {url}")
            return {}
        
        content_dict: Dict[str, str] = {}
        # print(main_content)

        for panel in main_content:
            # dictionary to store title-content pairs
            if isinstance(panel, Tag):
                # find all headers (h1-h6)
                headers = panel.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                
                for _, header in enumerate(headers):
                    title = self.clean_text(header.get_text().strip())
                    content = []
                    
                    # get all elements between this header and the next one
                    current = header.next_sibling
                    while current and (
                        not isinstance(current, Tag) 
                        or current.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):

                        if current is None:
                            break
                        if isinstance(current, (Tag, str)) and str(current).strip():
                            content.append(current.get_text().strip() if isinstance(current, Tag) else str(current).strip())
                        current = current.next_sibling

                    # print(f"title: {title}")
                    # print(f"content: {content}")
                    
                    if title:  # only add if title is not empty
                        # if classify(title)[0] != 'en':
                        #     print(f"title: {title} is not in english, its in {classify(title)}")
                            # continue
                        if content_dict.get(title):
                            content_dict[title] += '\n' + '\n'.join(filter(None, content))
                        else:
                            content_dict[title] = '\n'.join(filter(None, content))

        return content_dict

    def is_valid_url(self, url: str) -> bool:
        parsed = urlparse(url)
        exclude_paths = [
            '/forms', 
            '/admin', 
            '/events', 
            'news',
            '/employment', 
            '/media', 
            '/~username',
            'page-detail',
            '/people',
            '/courses',
            'tech_reports',
            '/visitors/create',
            '/docs/remote/vpn/'
        ]
        return not parsed.scheme \
            and not parsed.netloc \
            and bool(parsed.path) \
            and not any(path in parsed.path for path in exclude_paths) \
            and parsed.path != '/'

    def chunk_content(self, content: str, size: int=500, overlap: int=100) -> List[str]:
        words = content.split(" ")
        chunks = []
        for i in range(0, len(words), size - overlap):
            chunks.append(" ".join(words[i:i+size]))
        return chunks

    @staticmethod
    def clean_text(text: str) -> str:
        return text.strip().strip('\n')
