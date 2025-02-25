from chromadb import EmbeddingFunction, Embeddings, HttpClient, Collection
from chromadb.api.types import Embeddable, QueryResult, IncludeEnum, OneOrMany, ID
from pipelines.embedding_encoder import encode_text
from typing import List, Mapping
from database.enums import ChromaCollection


class BGEEmbeddingFunction(EmbeddingFunction[Embeddable]):
    def __call__(self, text: List[str]) -> Embeddings: # type: ignore
        return encode_text(text).tolist()

class ChromaClient:
    def __init__(self) -> None:
        self.client = HttpClient(host='localhost', port=8000)
        self.client.heartbeat()

    def get_collection(self, name: ChromaCollection) -> Collection:
        self.client.heartbeat()

        try:
            collection = self.client.get_collection(
                name=name.value,
                embedding_function=BGEEmbeddingFunction()
            )
        except Exception as _:
            collection = self.client.create_collection(
                name=name.value,
                embedding_function=BGEEmbeddingFunction(),
                # refer to https://docs.trychroma.com/docs/collections/configure
                metadata={
                    "hnsw:space": "ip",
                    "hnws:search_ef": 100,
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
                      ids: OneOrMany[ID]
                    ) -> None:
        
        collection = self.get_collection(collection_name)

        self.client.heartbeat()
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=BGEEmbeddingFunction()(documents),
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

client = ChromaClient()