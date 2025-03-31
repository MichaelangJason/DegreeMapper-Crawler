from faculty_crawlers.crawler import CoursePlannerCrawler
from database.chroma import client
from ecalender_crawler.courses import update_course_embeddings, update_courses_atlas_index
from ecalender_crawler.programs import update_program_embeddings

def main() -> None:
    # crawler = CoursePlannerCrawler()
    try:
        # crawler.crawl_all()
        # print(client.heartbeat())
        # update_course_embeddings()
        # delete_document_fields("BSON-Float32-Embedding")
        # update_course_embeddings()
        update_course_embeddings()
        # update_courses_atlas_index()
        # update_program_embeddings()
    except KeyboardInterrupt:
        print("\nCrawling interrupted by user. Shutting down...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        raise

if __name__ == "__main__":
    main()