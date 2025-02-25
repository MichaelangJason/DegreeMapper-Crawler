from faculty_crawlers.crawler import CoursePlannerCrawler
import asyncio

def main() -> None:
    crawler = CoursePlannerCrawler()
    try:
        asyncio.run(crawler.crawl_all())

    except KeyboardInterrupt:
        print("\nCrawling interrupted by user. Shutting down...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        raise

if __name__ == "__main__":
    main()