from faculty_crawlers.crawler import CoursePlannerCrawler
import asyncio
from database.chroma import client
from database.enums import ChromaCollection
import json
def main() -> None:
    crawler = CoursePlannerCrawler()
    try:
        # asyncio.run(crawler.crawl_all())
        results = client.query(ChromaCollection.Faculty, query="Computer Science programs that can be taken as part of the B.Sc. degree", n_results=5)
        print(json.dumps(results, indent=4))
    except KeyboardInterrupt:
        print("\nCrawling interrupted by user. Shutting down...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        raise

if __name__ == "__main__":
    main()