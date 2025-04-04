from chromadb import EmbeddingFunction, Embeddings, HttpClient, Collection
from chromadb.api.types import Embeddable, QueryResult, IncludeEnum, OneOrMany, ID
from pipelines.embedding_encoder import encode_text
from typing import List, Mapping
from database.enums import ChromaCollection
from tqdm import tqdm
import os
import dotenv

dotenv.load_dotenv()

class BGEEmbeddingFunction(EmbeddingFunction[Embeddable]):
    def __call__(self, text: List[str]) -> Embeddings: # type: ignore
        return encode_text(text).tolist()

class ChromaClient:
    def __init__(self) -> None:
        self.client = HttpClient(host='localhost', port=8000)
        self.client.heartbeat()

    def heartbeat(self) -> int:
        return self.client.heartbeat()

    def get_collection(self, name: ChromaCollection) -> Collection:
        self.client.heartbeat()
        
        collection = self.client.get_or_create_collection(
            name=name.value,
            embedding_function=BGEEmbeddingFunction(),
            metadata={
                    "hnsw:space": "cosine",
                    "hnsw:search_ef": 100,
                    "hnsw:construction_ef": 100,
                }
        )
        return collection

    
    def delete_collection(self, name: ChromaCollection) -> None:
        self.client.heartbeat()
        self.client.delete_collection(name.value)

    def add_documents(self, 
                      collection_name: ChromaCollection, 
                      documents: List[str],
                      metadata: List[Mapping[str, str | int | float | bool]],
                      ids: OneOrMany[ID],
                      batch_size: int = 1 # 1 is optimal for now
                    ) -> None:
        
        collection = self.get_collection(collection_name)
        self.client.heartbeat()
        
        # process in batches if the input is large
        if isinstance(ids, list) and len(ids) > batch_size:
            for i in tqdm(range(0, len(ids), batch_size), 
                            desc='Adding documents to Chroma...', 
                            unit='batch', 
                            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]', 
                            leave=False):

                batch_ids = ids[i:i+batch_size]
                batch_documents = documents[i:i+batch_size]
                batch_metadata = metadata[i:i+batch_size]
                
                collection.add(
                    ids=batch_ids,
                    documents=batch_documents,
                    metadatas=batch_metadata
                )
        else:
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadata
            )

    def query(self, 
              collection_name: ChromaCollection, 
              query: str, 
              n_results: int = 10) -> QueryResult:
        # check connection
        self.client.heartbeat()

        collection = self.client.get_collection(collection_name.value, 
                                                embedding_function=BGEEmbeddingFunction())
        if collection is None:
            raise ValueError(f"Collection {collection_name} not found")
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=[IncludeEnum.documents, IncludeEnum.metadatas]
        )
        return results
    
    def delete_documents(self, 
                         collection_name: ChromaCollection, 
                         ids: List[str]) -> None:
        self.client.heartbeat()
        collection = self.client.get_collection(collection_name.value)
        if collection is None:
            raise ValueError(f"Collection {collection_name} not found")
        collection.delete(ids=ids)

if os.getenv("QUERY_ONLY_LOCAL") == "1":
    client = None
    print("embedding only")
else:
    client = ChromaClient()
    print("Using local ChromaDB")