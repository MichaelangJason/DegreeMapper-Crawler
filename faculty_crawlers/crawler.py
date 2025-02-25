from faculty_crawlers.enums import Faculty
from faculty_crawlers.base import FacultyCrawler
from faculty_crawlers.CS.crawler import CSCrawler

class CoursePlannerCrawler:
  """
  Crawls the course planner for a list of faculties.
  """
  def __init__(self) -> None:
    self.crawlers: dict[Faculty, FacultyCrawler] = {
      Faculty.CS: CSCrawler(),
    }

  def crawl_faculty(self, faculty: Faculty) -> None:
    self.crawlers[faculty].crawl()

  def crawl_all(self) -> None:
    # tasks = [self.crawl_faculty(faculty) for faculty in Faculty]
    # asyncio.run(asyncio.gather(*tasks))
    for faculty in Faculty:
      self.crawl_faculty(faculty)