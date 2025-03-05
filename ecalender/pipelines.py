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

class MongoDBPipeline:
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