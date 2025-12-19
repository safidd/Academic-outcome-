from django.urls import path
from . import views

app_name = 'instructor'

urlpatterns = [
    path('dashboard/', views.instructor_dashboard, name='dashboard'),
    path('enter-grade/', views.enter_grade, name='enter_grade'),
    path('take-attendance/<int:course_id>/', views.take_attendance, name='take_attendance'),
    path('api/learning-outcomes/<int:course_id>/', views.get_learning_outcomes, name='get_learning_outcomes'),
]

