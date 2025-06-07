from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload-video/', views.upload_video, name='upload_video'),
    path('report/', views.report_incident, name='report_incident'),
    path('rankings/', views.accident_rankings, name='accident_rankings'),
    path('contact/', views.contact_us, name='contact'),
]
