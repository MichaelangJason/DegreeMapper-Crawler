from abc import ABC, abstractmethod
from typing import Set

class FacultyCrawler(ABC):

    @property
    @abstractmethod
    def faculty_name(self) -> str:
        raise NotImplementedError("faculty_name must be implemented")

    @property
    @abstractmethod
    def base_url(self) -> str:
        raise NotImplementedError("base_url must be implemented")

    @abstractmethod
    async def crawl(self) -> None:
        raise NotImplementedError("crawl must be implemented")

    @abstractmethod
    def is_valid_url(self, url: str) -> bool:
        raise NotImplementedError("is_valid_url must be implemented")
    
    @abstractmethod
    async def get_all_urls(self) -> Set[str]:
        raise NotImplementedError("get_all_urls must be implemented")
    
    @abstractmethod
    async def get_all_urls_from_url(self, target_url: str) -> Set[str]:
        raise NotImplementedError("get_all_urls_from_url must be implemented")