from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["studybuddy_db"]
users_collection = db["users"]
