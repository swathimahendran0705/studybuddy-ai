from django.conf import settings
from pymongo import MongoClient
import gridfs
from datetime import datetime
from django.db import models
from django.utils import timezone

# --------------------------
# MongoDB Setup
# --------------------------
client = MongoClient(settings.MONGO_URI)
db = client.get_database("studybuddydb")  # Your MongoDB DB name

# Collections
notes_col = db["notes"]       # Metadata for uploaded files
streak_col = db["streak"]     # Pomodoro & streak data

# GridFS for storing files
fs = gridfs.GridFS(db)

# --------------------------
# Pomodoro / Study Functions
# --------------------------

def save_pomodoro(user, minutes):
    try:
        streak_col.insert_one({
            "user": user,
            "minutes": minutes,
            "date": timezone.now()
        })
        return True
    except Exception as e:
        print("❌ Error saving pomodoro:", e)
        return False



def get_today_minutes(user):
    try:
        today = timezone.now()
        today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        pipeline = [
            {"$match": {"user": user, "date": {"$gte": today_start, "$lte": today_end}}},
            {"$group": {"_id": "$user", "total_minutes": {"$sum": "$minutes"}}}
        ]
        result = list(streak_col.aggregate(pipeline))
        return result[0]["total_minutes"] if result else 0
    except Exception as e:
        print("❌ Error fetching today's minutes:", e)
        return 0



def get_streak(user):
    try:
        dates = streak_col.find({"user": user}).sort("date", -1)
        streak = 0
        last_date = None
        for doc in dates:
            date_only = doc["date"].date()
            if last_date is None:
                streak = 1
            elif (last_date - date_only).days == 1:
                streak += 1
            elif (last_date - date_only).days > 1:
                break
            last_date = date_only
        return streak
    except Exception as e:
        print("❌ Error calculating streak:", e)
        return 0


from datetime import timedelta

def get_study_progress(user="guest"):
    today_minutes = get_today_minutes(user)

    total_minutes = sum(
        doc.get("minutes", 0)
        for doc in streak_col.find({"user": user})
    )

    streak = get_streak(user)

    today = datetime.utcnow().date()
    daily_data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day, 0, 0, 0)
        day_end = datetime(day.year, day.month, day.day, 23, 59, 59)

        sessions = streak_col.find({
            "user": user,
            "date": {"$gte": day_start, "$lte": day_end}
        })

        minutes = sum(s.get("minutes", 0) for s in sessions)

        daily_data.append({
            "date": day.strftime("%Y-%m-%d"),
            "minutes": minutes
        })

    consistency = int(
        sum(1 for d in daily_data if d["minutes"] > 0) / 7 * 100
    )

    best_day = max(daily_data, key=lambda x: x["minutes"])
    weak_day = min(daily_data, key=lambda x: x["minutes"])

    return {
        "today_minutes": today_minutes,
        "total_minutes": total_minutes,
        "streak": streak,
        "daily_data": daily_data,
        "consistency": consistency,
        "best_day": best_day["date"] if best_day["minutes"] > 0 else "--",
        "weak_day": weak_day["date"] if weak_day["minutes"] > 0 else "--"
    }


from django.http import JsonResponse

def study_progress_api(request):
    user = "guest"
    data = get_study_progress(user)
    print("DEBUG data:", data)
    return JsonResponse(data)





    

    return JsonResponse(data)

# --------------------------
# File / Notes Functions
# --------------------------

def save_uploaded_file(user, uploaded_file):
    try:
        file_id = fs.put(
            uploaded_file,
            filename=uploaded_file.name,
            content_type=getattr(uploaded_file, "content_type", "application/octet-stream")
        )
        notes_col.insert_one({
            "user": user,
            "file_id": file_id,
            "file_name": uploaded_file.name,
            "uploaded_at": datetime.utcnow()
        })
        return file_id
    except Exception as e:
        print("❌ Error saving file:", e)
        return None


def get_user_notes(user):
    try:
        notes = list(notes_col.find({"user": user}).sort("uploaded_at", -1))
        for note in notes:
            note["_id"] = str(note["_id"])
            note["file_id"] = str(note["file_id"])
        return notes
    except Exception as e:
        print("❌ Error fetching user notes:", e)
        return []

# --------------------------
# Django Model Example
# --------------------------
class Student(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=100)
    confirm_password = models.CharField(max_length=100)
    
    def __str__(self):
        return self.username
from django.db import models
import uuid

class Note(models.Model):
    file_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='notes/')  # actual file

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename