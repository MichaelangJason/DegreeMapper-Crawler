from pymongo import MongoClient, UpdateOne
from pymongo.operations import SearchIndexModel
from database.embbedings import encode_text
from bson.binary import Binary, BinaryVectorDtype
from dotenv import load_dotenv
import os
from tqdm import tqdm

load_dotenv()

# Generate BSON vector using `BinaryVectorDtype`
def generate_bson_vector(vector, vector_dtype):
    return Binary.from_vector(vector, vector_dtype)

# https://www.mongodb.com/docs/atlas/atlas-vector-search/create-embeddings/
# only create vector index for overview field
def update_course_embeddings():
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("MONGODB_DATABASE_NAME")]
    collection = db[os.getenv("MONGODB_COLLECTION_NAME")]

    # json schema
    overview_filter = { '$and': [ { 'overview': { '$exists': True, '$ne': None } } ] }

    # get courses with overview
    courses = collection.find(overview_filter, {"_id": 1, "overview": 1, "name": 1})

    embedding_field = "embeddings"
    
    operations = []
    for course in tqdm(courses, total=collection.count_documents(overview_filter)):
        overview = course["overview"]
        name = course["name"]
        text = f"{name}\n{overview}"
        
        # generate embeddings for precision float32
        vector = encode_text([text]).tolist()[0]
        vector_bson_float32 = generate_bson_vector(vector, BinaryVectorDtype.FLOAT32)

        operations.append(UpdateOne({"_id": course["_id"]}, {"$set": {embedding_field: vector_bson_float32}}))

    if operations:
        result = collection.bulk_write(operations)
        print(f"Updated {result.modified_count} courses") # about ~10000 courses

    drop_index("vector_index")
    # create index
    search_index_model = SearchIndexModel(
        definition = {
            "fields": [
            {
                "type": "vector",
                "path": embedding_field, 
                "similarity": "dotProduct", # https://www.pinecone.io/learn/vector-similarity/
                "numDimensions": 1024 # dimension specified here: https://huggingface.co/BAAI/bge-m3
            }
            ]
        },
        name="vector_index",
        type="vectorSearch",
    )
    collection.create_search_index(model=search_index_model)

# the search index, not vector index
def update_courses_atlas_index():
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("MONGODB_DATABASE_NAME")]
    collection = db[os.getenv("MONGODB_COLLECTION_NAME")]

    drop_index("search_index")
    # this index can be improved further, with many different options
    index = {
        "name": "search_index",
        "definition": {
            "mappings": {
                "dynamic": False,
                "fields": {
                "id": {
                    "type": "string",
                    "analyzer": "custom1",
                    "indexOptions": "offsets",
                    "store": True,
                    "norms": "include"
                }
                }
            },
            "analyzers": [
                {
                    "name": "custom1",
                    "tokenizer": {
                        "type": "nGram",
                        "minGram": 4,
                        "maxGram": 9
                    },
                    "tokenFilters": [
                        {
                            "type": "lowercase"
                        },
                        {
                            "type": "trim"
                        },
                        {
                            "type": "regex",
                            "pattern": "s+",
                        "replacement": "",
                        "matches": "all"
                        },
                        {
                        "type": "stopword",
                        "tokens": [
                            ""
                        ],
                        "ignoreCase": False
                        }
                    ]
                }
            ]
            }
    }
    collection.create_search_index(index)


def drop_index(name: str):
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("MONGODB_DATABASE_NAME")]
    collection = db[os.getenv("MONGODB_COLLECTION_NAME")]

    try:
        collection.drop_search_index(name)
    except Exception as e:
        print(f"Error dropping index: {e}")

def delete_document_fields(field: str):
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("MONGODB_DATABASE_NAME")]
    collection = db[os.getenv("MONGODB_COLLECTION_NAME")]

    collection.update_many({}, {"$unset": {field: ""}})
