from database.chroma import client
from database.enums import ChromaCollection
import json
import sys

def query(query: str, n_results: int = 5) -> None:
    try:
        results = client.query(ChromaCollection.Faculty, query=query, n_results=n_results)
        print(json.dumps(results, indent=4))
    except KeyboardInterrupt:
        print("\nCrawling interrupted by user. Shutting down...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        raise

if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) != 2:
        print("Usage: python query.py <query> <n_results>")
        sys.exit(1)
    
    query(query=args[0], n_results=int(args[1]))