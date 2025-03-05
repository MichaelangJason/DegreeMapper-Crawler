from fastapi import FastAPI
from database.chroma import client
from database.enums import ChromaCollection
from pydantic import BaseModel
from pipelines.embedding_encoder import encode_text

app = FastAPI(title="Course Planner Query API", description="Query the Course Planner database")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/api/query/")
async def query(query: str, n_results: int = 10):
    results = client.query(ChromaCollection.Faculty, query=query, n_results=n_results)
    return results

class EncodeRequest(BaseModel):
    texts: list[str]

@app.post("/api/encode/")
async def encode(request: EncodeRequest):
    results = encode_text(request.texts)
    return results.tolist()