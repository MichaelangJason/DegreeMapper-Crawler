from faculty_crawlers.base import FacultyCrawler
from faculty_crawlers.enums import Faculty
import httpx
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
from typing import Set, Dict, List, Mapping
from tqdm import tqdm
from pipelines.text_processing import clean_text
# from langid import classify
from pipelines.embedding_encoder import split_text
import json
from database.chroma import client
from database.enums import ChromaCollection

class CSCrawler(FacultyCrawler):
    """
    Crawls the course planner for the Computer Science faculty.
    """
    def __init__(self) -> None:
        self.crawled_urls: Set[str] = set()
        self.visited_urls: Set[str] = set()
        self.all_urls: Set[str] = set()
        self.is_header_crawled = False

    @property
    def faculty_name(self) -> str:
        return Faculty.CS.value

    @property
    def base_url(self) -> str:
        return 'www.cs.mcgill.ca'

    async def crawl(self) -> None:
        # get all urls from the base url
        tqdm.write('Getting all urls from the base url...')
        urls = await self.get_all_urls()
        tqdm.write('Done getting all urls from the base url!')

        client.delete_collection(ChromaCollection.Faculty)
        with tqdm(total=len(urls), desc='Fetching content for each url...') as pbar:
            # fetch page content for last page and display it
            for url in urls:
                pbar.set_description(f"Fetching content for {url}")
                content = await self.fetch_content(url)

                titles = ",".join(list(content.keys())) # a metadata for the content
                faculty = self.faculty_name # a metadata for the content
                chunks = split_text(content)

                metadata: List[Mapping[str, str | int | float | bool]] = [
                    {
                        "faculty": faculty,
                        "titles": titles,
                        "url": urljoin(f'https://{self.base_url}', url)
                    }
                    for _ in chunks
                ]

                ids = [
                    f"{faculty}-{url}-{i}"
                    for i, _ in enumerate(chunks)
                ]
                try:
                    client.add_documents(
                        collection_name=ChromaCollection.Faculty,
                        ids=ids,
                        metadata=metadata,
                        documents=chunks
                    )
                except Exception as e:
                    print(e)
                    print("metadata: ", metadata)
                    print("url: ", url)
                    print("chunks: ", chunks)
                    print("contents", json.dumps(content))
                    continue
                pbar.update(1)
                
    async def fetch_content(self, endpoint: str) -> Dict[str, str]:
        async with httpx.AsyncClient() as client:
            response = await client.get(urljoin(f'https://{self.base_url}', endpoint))
            soup = BeautifulSoup(response.text, 'html.parser')

            main_content = soup.find_all('div', class_='panel')

            if not main_content:
                print(f"No main content found for {endpoint}")
                return {}
            
            content_dict: Dict[str, str] = {}
            # print(main_content)

            for panel in main_content:
                # dictionary to store title-content pairs
                if isinstance(panel, Tag):
                    # find all headers (h1-h6)
                    headers = panel.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    
                    for _, header in enumerate(headers):
                        title = clean_text(header.get_text().strip())
                        content = []
                        
                        # get all elements between this header and the next one
                        current = header.next_sibling
                        while current and (not isinstance(current, Tag) or current.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                            if current is None:
                                break
                            if isinstance(current, (Tag, str)) and str(current).strip():
                                content.append(clean_text(current.get_text().strip() if isinstance(current, Tag) else str(current).strip()))
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
            # print(f"content_dict: {content_dict}")
        return content_dict

    def flatten_content(self, content_dict: Dict[str, str]) -> str:
        flattened_content = []
        for title, content in content_dict.items():
            flattened_content.append(f'{title}\n{content}')
        return '\n'.join(flattened_content)

    async def get_all_urls_from_url(self, target_url: str) -> Set[str]:
        if not target_url.endswith('/'):
            target_url += '/'

        urls = []
        # get all urls from the base url
        async with httpx.AsyncClient() as client:
            response = await client.get(target_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # skip header container if already visited
            header_container = soup.find('div', id='headercontainer')
            if header_container and self.is_header_crawled:
                header_container.decompose()
            elif header_container:
                self.is_header_crawled = True

            # find all links in the page
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

    async def get_all_urls(self) -> Set[str]:
        base_url = f'https://{self.base_url}'
        # add trailing slash if not present
        if not base_url.endswith('/'):
            base_url += '/'

        # get all urls from the base url
        urls = set(await self.get_all_urls_from_url(base_url))
        self.all_urls.update(urls)
        visited_endpoints: Set[str] = set()

        while urls:
            endpoint = urls.pop()
            if endpoint in visited_endpoints:
                continue
            visited_endpoints.add(endpoint)
            target_url = urljoin(base_url, endpoint)
            # print(target_url)
            res = await self.get_all_urls_from_url(target_url)

            urls.update(res)
            self.all_urls.update(res)

        return self.all_urls

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
            '/visitors/create'
        ]
        # meaning its a relative url with same base url
        return not parsed.scheme \
            and not parsed.netloc \
            and bool(parsed.path) \
            and not any(path in parsed.path for path in exclude_paths) \
            and parsed.path != '/'