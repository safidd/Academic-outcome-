from django.urls import path
from . import views

app_name = 'head'

urlpatterns = [
    path('dashboard/', views.head_dashboard, name='dashboard'),
]

