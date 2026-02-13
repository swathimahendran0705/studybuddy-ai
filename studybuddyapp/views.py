from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, FileResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import json
import io
import gridfs
from .models import save_pomodoro, get_today_minutes, get_streak, get_study_progress
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from .models import Note  
from pymongo import MongoClient
from bson.objectid import ObjectId
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from pdfminer.high_level import extract_text
import requests
import json, random, re
from django.core.mail import send_mail
from django.conf import settings
from studybuddypro.db import users_collection
import bcrypt
from django.shortcuts import redirect
from django.contrib.auth.hashers import make_password, check_password
from datetime import date
import random, string
from django.shortcuts import render, redirect
from pymongo import MongoClient
from django.contrib.auth.decorators import login_required   # <

# models.py
from pymongo import MongoClient
from django.conf import settings

client = MongoClient(settings.MONGO_URI)
db = client["studybuddydb"]
pomodoro_col = db["pomodoro"]  # or whatever your collection is

from studybuddyapp.models import (
    streak_col,
    get_study_progress
)


# MongoDB connection

client = MongoClient(settings.MONGO_URI)
db = client['studybuddy']
collection = db['users']


# --- MongoDB Setup ---
client = MongoClient(settings.MONGO_URI)
db = client["studybuddydb"]
fs = gridfs.GridFS(db)
notes_col = db["notes"]
hints_col = db["hints"]
quizzes_col = db["quizzes"]
hints_history_col = db["hints_history"]
quiz_history_col = db["quiz_history"]
gk_collection = db["gk_scores"]
# MongoDB collections
groups_col = db["groups"]
members_col = db["group_members"]
sessions_col = db["group_sessions"]
messages_col = db["group_messages"]




# --- AI Assistant ---
from groq import Groq
client_ai = Groq(api_key=settings.GROQ_API_KEY)

def ask_ai(request):
    reply = ""
    if request.method == "POST":
        user_input = request.POST.get("question", "").strip()
        if not user_input:
            return render(request, "AI.html", {"answer": "⚠️ Please enter a question."})
        try:
            response = client_ai.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": user_input}]
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"⚠️ Error connecting to AI: {e}"
    return render(request, "AI.html", {"answer": reply})


# views.py
from .models import save_pomodoro, get_today_minutes, get_streak
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def save_pomodoro(user_id, minutes):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    pomodoro_col.update_one(
        {"user_id": user_id, "date": today},
        {"$inc": {"minutes": minutes}},
        upsert=True
    )

def get_today_minutes(user_id):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    entry = pomodoro_col.find_one({"user_id": user_id, "date": today})
    return entry.get("minutes", 0) if entry else 0

def get_streak(user_id):
    streak = 0
    today = datetime.utcnow().date()
    for i in range(30):  # last 30 days
        day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        entry = pomodoro_col.find_one({"user_id": user_id, "date": day})
        if entry and entry.get("minutes", 0) >= 25:
            streak += 1
        else:
            break
    return streak

# ================= API endpoints =================

@csrf_exempt
def save_pomodoro_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            minutes = int(data.get("minutes", 0))
            if minutes <= 0:
                return JsonResponse({"success": False, "error": "Minutes missing"})
            save_pomodoro("guest", minutes)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"error": "Invalid method"}, status=405)


def today_minutes_api(request):
    try:
        minutes = get_today_minutes("guest")
        return JsonResponse({"today": minutes})
    except Exception as e:
        return JsonResponse({"today": 0, "error": str(e)})


def streak_api(request):
    try:
        streak = get_streak("guest")
        return JsonResponse({"streak": streak})
    except Exception as e:
        return JsonResponse({"streak": 0, "error": str(e)})


def study_progress_api(request):
    from studybuddyapp.models import get_study_progress
    try:
        data = get_study_progress("guest")
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)})



# ------------------------------------------
# PDF TEXT EXTRACTION
# ------------------------------------------
def extract_text_from_pdf(file_bytes):
    try:
        with open("tempfile.pdf", "wb") as temp:
            temp.write(file_bytes)

        text = extract_text("tempfile.pdf")
        return text
    except Exception:
        return ""


        # ------------------------------------------
        # UPLOAD NOTES
        # ------------------------------------------
@csrf_exempt
def upload_notes(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)

    files = request.FILES.getlist("notes")
    if not files:
        return JsonResponse({"error": "No files found"}, status=400)

    uploaded_files = []

    for file in files:
        content = file.read()
        # Save file in GridFS
        file_id = fs.put(content, filename=file.name)

        # Extract text
        if file.name.lower().endswith(".pdf"):
            text = extract_text_from_pdf(content)
        else:
            try:
                text = content.decode("utf-8", errors="ignore")
            except Exception:
                text = ""

        # Save metadata and text
        db.notes_text.insert_one({
            "file_id": str(file_id),
            "filename": file.name,
            "user": request.user.username if request.user.is_authenticated else "guest",
            "text": text,
            "uploaded_at": datetime.utcnow()
        })

        uploaded_files.append({"file_id": str(file_id), "filename": file.name})

    return JsonResponse({"status": "success", "notes": uploaded_files})

@csrf_exempt
def delete_note(request, file_id):
    if request.method == "POST":
        result = db.notes_text.delete_one({
            "file_id": file_id   # ✅ CORRECT
        })

        if result.deleted_count == 1:
            return JsonResponse({"status": "deleted"})
        else:
            return JsonResponse({"status": "not_found"})

    return JsonResponse({"status": "invalid_method"})

        # ------------------------------------------
        # GET NOTES LIST
        # ------------------------------------------
def get_notes(request):
    notes = []

    for n in db.notes_text.find().sort("_id", -1):
        notes.append({
            "file_id": n["file_id"],
            "filename": n["filename"]
        })

    return JsonResponse({"notes": notes})  # ✅ OUTSIDE LOOP



      

        # ------------------------------------------
        # PREVIEW NOTE
        # ------------------------------------------
def preview_note(request, file_id):
    doc = db.notes_text.find_one({"file_id": file_id})
    if not doc:
        return JsonResponse({"content": ""})
    return JsonResponse({"content": doc["text"]})

@csrf_exempt
def generate_hint(request):
    if request.method != "POST":
        return JsonResponse({"hints": []})

    data = json.loads(request.body.decode("utf-8"))
    file_id = data.get("file_id")

    doc = db.notes_text.find_one({"file_id": file_id})
    if not doc:
        return JsonResponse({"hints": []})

    text = doc.get("text", "").strip()
    if not text:
        return JsonResponse({"hints": []})

    # -------------------------------
    # CLEAN TEXT
    # -------------------------------
    text = re.sub(r"\s+", " ", text)   # extra spaces remove
    sentences = re.split(r"[.?!]", text)

    # meaningful sentences
    sentences = [
        s.strip() for s in sentences
        if len(s.split()) >= 6 and len(s.split()) <= 25
    ]

    # -------------------------------
    # CREATE HINTS
    # -------------------------------
    hints = []
    for s in sentences[:7]:
        hints.append("• " + s)

    return JsonResponse({"hints": hints})

        # ------------------------------------------
        # GENERATE MCQ via GROQ + Fallback
        # ------------------------------------------
@csrf_exempt
def generate_mcq_api(request):
            """
            Returns CLEAN MCQ text block:
            Q1: question
            A. opt
            B. opt
            C. opt
            D. opt
            Answer: B
            """
            if request.method != "POST":
                return JsonResponse({"error": "Invalid method"}, status=405)

            try:
                data = json.loads(request.body.decode("utf-8"))
                file_id = data.get("file_id")
            except:
                return JsonResponse({"error": "Invalid JSON"}, status=400)

            # Get notes text
            doc = db.notes_text.find_one({"file_id": file_id})

            if not doc:
                return JsonResponse({"quiz": ""})

            notes_text = doc.get("text", "")
            if not notes_text.strip():
                return JsonResponse({"quiz": ""})

            # ----------------------------------------
            # MCQ PROMPT
            # ----------------------------------------
            prompt = f"""
            You are an MCQ generator for the StudyBuddy app. Generate 10–15 exam-style MCQs.

            STRICT FORMAT:

            Q1: <question>
            A. <option>
            B. <option>
            C. <option>
            D. <option>
            Answer: <A/B/C/D>

            Rules:
            - Only output MCQs in this format.
            - NO markdown.
            - Options must be 2–6 words.
            - Simple short English.
            - Correct answer only one.
            - Do NOT repeat full sentences from notes.

            NOTES:
            {notes_text}
            """

            quiz_text = ""

            # ----------------------------------------
            # GROQ API CALL
            # ----------------------------------------
            try:
                response = client_ai.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}]
                )

                quiz_text = response.choices[0].message.content.strip()

            except Exception as e:
                print("Groq Error:", e)
                quiz_text = ""

            # ----------------------------------------
            # FALLBACK MCQ CREATOR
            # ----------------------------------------
            if not quiz_text:
                sentences = re.split(r"[.!?]\s+", notes_text)
                sentences = [s.strip() for s in sentences if len(s.split()) > 6][:10]

                fallback = []
                qnum = 1

                for s in sentences:
                    opts = [
                        "Key concept explanation",
                        "Important fact summary",
                        "Common misunderstanding",
                        "Main topic definition"
                    ]
                    random.shuffle(opts)

                    fallback.append(
                        f"Q{qnum}: What is the main idea of this statement?\n"
                        f"A. {opts[0]}\n"
                        f"B. {opts[1]}\n"
                        f"C. {opts[2]}\n"
                        f"D. {opts[3]}\n"
                        f"Answer: A"
                    )

                    qnum += 1

                quiz_text = "\n\n".join(fallback)

            return JsonResponse({"quiz": quiz_text})


        # ------------------------------------------
        # SAVE HINTS
        # ------------------------------------------
@csrf_exempt
def save_generated_hints(request):
    data = json.loads(request.body)
    hints = data.get("hints", [])
    file_id = data.get("file_id")
    db.hints.insert_one({
        "file_id": file_id,
        "hints": hints,
        "created_at": datetime.utcnow()
            })
    return JsonResponse({"message": "Hints saved"})


        # ------------------------------------------
        # GET SAVED HINTS
        # ------------------------------------------
def get_hints(request):
    out = []
    for h in db.hints.find().sort("created_at", -1):
        out.append({
            "file_id": h["file_id"],
            "hints": "\n".join(h["hints"]),
            "created_at": h["created_at"].isoformat()
                })
        return JsonResponse({"hints": out})


def mail(request):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        to_mail = request.POST.get("mail")      # 👈 DEFINE HERE
        message = request.POST.get("message")

        if not to_mail or not message:
            return JsonResponse({
                "status": "error",
                "message": "Email and message required"
            })

        try:
            send_mail(
                subject="Message from StudyBuddy",
                message=message,
                from_email="swathimahendran0705@gmail.com",  # FROM
                recipient_list=[to_mail],                   # TO
                fail_silently=False
            )
            return JsonResponse({
                "status": "success",
                "message": "Email sent successfully!"
            })

        except Exception as e:
            print("EMAIL ERROR:", e)
            return JsonResponse({
                "status": "error",
                "message": str(e)
            })

    return render(request, "Email.html")

def register(request):
    if request.method == 'POST':
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm-password")

        if password != confirm_password:
            return render(request, 'register.html', {"msg": "Passwords do not match"})

        if collection.find_one({"email": email}):
            return render(request, 'register.html', {"msg": "Email already registered"})

        # Hash password here ✅
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        data = {
            "name": name,
            "email": email,
            "password": hashed
        }
        collection.insert_one(data)

        return redirect('/login')

    return render(request, 'register.html')


import bcrypt

def login(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        password = request.POST.get('password')

        # Find user by name only
        user = collection.find_one({"name": name})
        if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]):
            # Login success
            return redirect('/home')
        else:
            # Invalid login
            return render(request, 'login.html', {"msg": "Invalid name/password"})

    return render(request, 'login.html')


def home(request):
		 return render(request,'index.html')

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@login_required
def create_group(request):
    if request.method=="POST":
        name = request.POST.get("name")
        subject = request.POST.get("subject")
        code = generate_code()
        creator_id = ObjectId(request.user.mongo_id)

        group = {
            "name": name,
            "subject": subject,
            "code": code,
            "creator": creator_id,
            "created_at": datetime.now()
        }
        result = groups_col.insert_one(group)
        members_col.insert_one({
            "group_id": result.inserted_id,
            "user_id": creator_id,
            "joined_at": datetime.now()
        })
        return JsonResponse({"status":"success","group_code":code})

@login_required
def join_group(request):
    if request.method=="POST":
        code = request.POST.get("code")
        user_id = ObjectId(request.user.mongo_id)

        group = groups_col.find_one({"code": code})
        if not group:
            return JsonResponse({"status":"invalid_code"})

        exists = members_col.find_one({"group_id": group["_id"], "user_id": user_id})
        if exists:
            return JsonResponse({"status":"already_joined"})

        members_col.insert_one({"group_id": group["_id"], "user_id": user_id, "joined_at": datetime.now()})
        return JsonResponse({"status":"joined"})

@login_required
def start_group_session(request):
    if request.method=="POST":
        group_id = ObjectId(request.POST.get("group_id"))
        user_id = ObjectId(request.user.mongo_id)
        group = groups_col.find_one({"_id": group_id})
        if group["creator"] != user_id:
            return JsonResponse({"status":"not_allowed"})
        sessions_col.insert_one({"group_id":group_id,"started_by":user_id,"start_time":datetime.now(),"end_time":None})
        return JsonResponse({"status":"session_started"})

@login_required
def end_group_session(request):
    if request.method=="POST":
        group_id = ObjectId(request.POST.get("group_id"))
        sessions_col.update_one({"group_id":group_id,"end_time":None},{"$set":{"end_time":datetime.now()}})
        return JsonResponse({"status":"session_ended"})

@login_required
def send_group_message(request):
    if request.method=="POST":
        group_id = ObjectId(request.POST.get("group_id"))
        user_id = ObjectId(request.user.mongo_id)
        text = request.POST.get("message")

        is_member = members_col.find_one({"group_id": group_id, "user_id": user_id})
        if not is_member:
            return JsonResponse({"status":"not_member"})

        messages_col.insert_one({"group_id":group_id,"user_id":user_id,"message":text,"time":datetime.now()})
        return JsonResponse({"status":"sent"})

@login_required
def get_group_messages(request, group_id):
    group_id = ObjectId(group_id)
    msgs = list(messages_col.find({"group_id": group_id}).sort("time",1))
    for m in msgs:
        m["_id"] = str(m["_id"])
        m["user_id"] = str(m["user_id"])
    return JsonResponse(msgs,safe=False)


@csrf_exempt
def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        if not name or not email or not message:
            return JsonResponse({"status":"error", "message":"All fields are required."})

        try:
            send_mail(
                subject=f"New message from {name}",
                message=f"Email: {email}\n\nMessage:\n{message}",
                from_email="swathimahendran0705@gmail.com",  # your Gmail
                recipient_list=["swathimahendran0705@gmail.com"],
                fail_silently=False,
            )
            return JsonResponse({"status":"success", "message":"Message sent successfully! 🎉"})
        except Exception as e:
            return JsonResponse({"status":"error", "message":"Failed to send message."})


def pomodoro(request):
    return render(request, 'pomodoro.html')

def index(request):
    return render(request, 'index.html')

def uploaded(request):
    return render(request, 'uploaded.html')
def time_table(request):
    return render(request, 'time_table.html')
def hints(request):
    return render(request, 'hints.html')
def quiz(request):
    return render(request, 'quiz.html')    
def AI(request):
    return render(request, 'AI.html') 
def Email(request):
    return render(request,'Email.html')
def study_pro(request):
    return render(request,'study_pro.html')                        