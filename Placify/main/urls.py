from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
     path('login/' , login_page , name="login"),
    path('register/' , register_page , name="register"),
    path('logout/' , logout_page , name="logout"),
    path('index/', index, name='index'),
    path('resume/', resume_builder, name='ai_resume'),
    path('result/', resume_result, name='res_result'),
    path('download/', download_resume, name='download_resume'),
    path('analyze-job/', analyze_job_description, name='analyze_job'),
]