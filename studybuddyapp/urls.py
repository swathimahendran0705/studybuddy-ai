from django.urls import path
from . import views
from .views import save_study_time, get_study_time
from studybuddyapp import views

urlpatterns = [
    path('get_hints/<str:note_id>/', views.get_hints, name='get_hints'),

    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout, name="logout"),
    path("admin/", admin.site.urls),
]


