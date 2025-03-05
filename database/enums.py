from enum import Enum

class ChromaCollection(Enum):
    Faculty = "faculty"
    Course = "course"
    Program = "program"


class MongoCollection(Enum):
    Course = "courses_2024_2025"
    Program = "programs_2024_2025"