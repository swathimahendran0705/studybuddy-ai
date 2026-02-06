from django.conf import settings
from pymongo import MongoClient
import gridfs
from bson import ObjectId
from datetime import datetime




# MongoDB URI
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)











client = MongoClient(settings.MONGO_URI)
db = client.get_database("studybuddydb")

hints_col = db["hints"]   # NEW COLLECTION for hint maker


# --------------------------
# Connect to MongoDB
# --------------------------
client = MongoClient(settings.MONGO_URI)
db = client["studybuddydb"]   # ✔ Correct final DB name

# --------------------------
# Collections
# --------------------------

notes_col = db["notes_text"]           # metadata for uploaded files
timetable_col = db["timetable"]
streak_col = db["streak"]
mocktests_col = db["mocktests"]
gk_col = db["gkquestions"]
users_collection = db["users"]


             # Your database name
fs = gridfs.GridFS(db)                    # GridFS for storing files
notes_collection = db["notes"]  

# GridFS
fs = gridfs.GridFS(db)

# --------------------------
# Helper Functions
# --------------------------

def save_file_to_gridfs(user, uploaded_file):
    """
    Save a Django uploaded file to GridFS and store metadata
    """
    try:
        file_id = fs.put(
            uploaded_file.read(),
            filename=uploaded_file.name,
            content_type=getattr(uploaded_file, "content_type", "application/octet-stream")
        )
        # Save metadata in notes collection
        notes_col.insert_one({
            "user": user,
            "file_id": str(file_id),
            "file_name": uploaded_file.name,
            "uploaded_at": datetime.utcnow()
        })
        return str(file_id)
    except Exception as e:
        print("❌ Error saving file:", e)
        return None

def get_user_notes(user):
    """
    Fetch all notes uploaded by the user
    """
    try:
        notes = list(notes_collection.find({"user": user}).sort("uploaded_at", -1))
        return notes
    except Exception as e:
        print("❌ Error fetching notes:", e)
        return []

def get_file(file_id):
    """
    Retrieve a file from GridFS
    """
    try:
        grid_out = fs.get(file_id)
        return grid_out.read(), grid_out.filename, grid_out.content_type
    except Exception as e:
        print("❌ Error retrieving file:", e)
        return None, None, None

hints_history_col = db["hints_history"]
quiz_history_col = db["quiz_history"]


from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["studybuddy"]
notes_collection = db["notes"]

