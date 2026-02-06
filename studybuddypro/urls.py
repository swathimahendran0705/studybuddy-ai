from django.contrib import admin
from django.urls import path, include
from studybuddyapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    
   

    # AI Assistant
    path('ask/', views.ask_ai, name='ask_ai'),
    path('AI/',views.AI,name='AI'),

    # Pomodoro Timer APIs
    path('home/', views.index, name='index'),
    path('pomodoro/', views.pomodoro, name='pomodoro'),
    path('api/pomodoro/save/', views.save_pomodoro_api, name='save_pomodoro_api'),
    path('api/today/', views.today_minutes_api, name='today_minutes_api'),
    path('api/streak/', views.streak_api, name='streak_api'),

    # Notes Upload
    path('uploaded/', views.uploaded, name='uploaded'),
    path("upload_notes/", views.upload_notes),
    path("get_notes/", views.get_notes),
    path("delete_note/<str:file_id>/", views.delete_note),
    path("preview_note/<str:file_id>/", views.preview_note),

    #time table
    path('time_table/', views.time_table, name='time_table'),

    # Hints & Quiz
    path('hints/',views.hints,name='hints'),
    path("generate_hint/", views.generate_hint),
    path("generate_mcq_api/", views.generate_mcq_api, name="generate_mcq_api"),
    path("save_generated_hints/", views.save_generated_hints),
    path('quiz/',views.quiz,name='quiz'),
    path("get_hints/<str:note_id>/", views.get_hints),


    path('mail/', views.mail, name='mail'),
    path('Email/',views.Email,name='Email'),
    
    # 🔹 AUTH ROUTES
   
    path('admin/', admin.site.urls),
    path('',views.register),
   
    path('login/',views.login),
    path('home/', views.home),
    
    # progress
    path('study_pro/',views.study_pro,name='study_pro'),
    path("api/progress/", views.study_progress_api),
    
    path('delete_note/<str:file_id>/', views.delete_note, name='delete_note'),

]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

