# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient
from dotenv import load_dotenv
from scrapy import Spider
import os
from tqdm import tqdm
load_dotenv()
from typing import List, Callable, Mapping
import json
from urllib.parse import urljoin
from database.embbedings import encode_text, generate_bson_vector

class MongoDBProgramPipeline:
    collection_name_map = {
        "programs_meta": "programs",
        "programs": "programs"
    }
    mode_map = {
        "programs_meta": "create",
        "programs": "update"
    }
    id_field_map = {
        "programs_meta": "url",
        "programs": "url",
        "courses_meta": "id",
        "courses": "id"
    }

    def open_spider(self, spider: Spider):
        self.client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = self.client[os.getenv("MONGODB_DATABASE_NAME")]
        self.progress = tqdm(colour="green")
        self.collection_name = self.collection_name_map[spider.name] + "_" + os.getenv("YEAR").replace("-", "_")
        self.mode = self.mode_map[spider.name]
        self.id_field = self.id_field_map[spider.name]

        if self.mode == "create":
            try:
                self.db.drop_collection(self.collection_name)
                spider.log(f"Collection {self.collection_name} already exists")
            except Exception as e:
                spider.logger.error(f"Error dropping collection {self.collection_name}: {e}")
            self.collection = self.db.create_collection(self.collection_name)
        else:
            self.collection = self.db[self.collection_name]

    def close_spider(self, spider: Spider):
        self.client.close()
        self.progress.close()

    def process_item(self, item, spider: Spider):
        item_id = item[self.id_field]
        self.collection.update_one({self.id_field: item_id}, {"$set": ItemAdapter(item).asdict()}, upsert=True)
        self.progress.update(1)
        return item


class MongoDBFacultyPipeline:

    collection_name_map = {
        "programs_meta": "programs",
        "programs": "programs",
        "faculty": "faculty"

    }
    mode_map = {
        "programs_meta": "create",
        "programs": "update",
        "faculty": "update"
    }
    id_field_map = {
        "programs_meta": "url",
        "programs": "url",
        "courses_meta": "id",
        "courses": "id",
        "faculty": "url",
    }

    def open_spider(self, spider: Spider):
        self.client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = self.client[os.getenv("MONGODB_DATABASE_NAME")]
        self.collection_name = "general_" + os.getenv("YEAR").replace("-", "_")
        self.mode = "create"
        self.id_field = "url"
        self.domain = "www.cs.mcgill.ca"
        self.base_url = f"https://{self.domain}"

        if self.mode == "create":
            try:
                self.db.drop_collection(self.collection_name)
                spider.log(f"Collection {self.collection_name} already exists")
            except Exception as e:
                spider.logger.error(f"Error dropping collection {self.collection_name}: {e}")
            self.collection = self.db.create_collection(self.collection_name)
        else:
            self.collection = self.db[self.collection_name]

        self.encode: Callable[[str], List[float]] = lambda x: encode_text(x).squeeze().tolist()
        self.progress = tqdm(colour="green")

    def close_spider(self, spider: Spider):
        self.client.close()
        self.progress.close()

    def process_item(self, item, spider: Spider):
        if item is None: return


        url: str = item["url"]
        content: dict = item["content"]

        # print(url)
        # print(content.keys())

        common_tag: str = list(content.keys())[0] # usually the header of the content
        # department = "cs" # a metadata for the content
        # chunks, filter out empty strings 
        documents: List[str] = []
        tags: List[str] = []

        for _, (title, value) in enumerate(content.items()):
            if value == '':
                continue
            chunks = self.chunk_content(value)
            tags.extend([(common_tag + ',' if i != 0 else '') + title for i in range(len(chunks))])
            documents.extend([json.dumps({ "title": title + "-" + str(i), "content": chunk }) for i, chunk in enumerate(chunks)])
        
        # print(documents)
        
        docs: List[Mapping[str, str | int | float | bool]] = [
            {   
                "id": f"{idx}-{self.domain + url}",
                # "faculty": department,
                "tags": tag,
                "url": urljoin(self.base_url, url),
                "content": documents[idx],
                "embeddings": generate_bson_vector(self.encode(documents[idx]))
            }
            for idx, tag in enumerate(tags)
        ]

        # print(docs)

        for doc in docs:
            self.collection.update_one(
                {"id": doc["id"]}, 
                {"$set": doc}, 
                upsert=True
            )
            self.progress.update(1)
        
        return item

    def chunk_content(self, content: str, size: int=500, overlap: int=100) -> List[str]:
        words = content.split(" ")
        chunks = []
        for i in range(0, len(words), size - overlap):
            chunks.append(" ".join(words[i:i+size]))
        return chunks


class MongoDBCoursePipeline:
    
    def open_spider(self, spider: Spider):
        self.client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = self.client[os.getenv("MONGODB_DATABASE_NAME")]
        self.collection_name = "courses_" + os.getenv("YEAR").replace("-", "_")
        self.mode = "update"
        self.id_field = "id"
        self.domain = "www.cs.mcgill.ca"
        self.base_url = f"https://{self.domain}"

        self.collection = self.db[self.collection_name]

        self.progress = tqdm(colour="green", total=self.collection.count_documents({}))
        self.level_map = {
            "graduate, undergraduate": 0,
            "undergraduate": 1,
            "graduate": 2,
        }

    def process_item(self, item: dict, spider: Spider):
        # print(item)

        if not (id := item.get("id", None)) or not (level := item.get("level", None)):
            raise ValueError("Courses must have id")
        
        id = id.replace("-", "")
        level = self.level_map[level.lower()]

        # if (level == 0): print(id, level)

        result = self.collection.update_one(
            { "id": id },
            { "$set": { "level": level } }
        )

        if result.modified_count == 1: self.progress.update(1)
        else: print(id, level)

        return item