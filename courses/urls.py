from django.urls import path
from . import views

app_name = 'instructor'

urlpatterns = [
    path('dashboard/', views.instructor_dashboard, name='dashboard'),
    path('enter-grade/', views.enter_grade, name='enter_grade'),
    path('take-attendance/', views.take_attendance, name='take_attendance'),
    path('api/learning-outcomes/<int:course_id>/', views.get_learning_outcomes, name='get_learning_outcomes'),
    path('api/sync-attendance/', views.sync_attendance_api, name='sync_attendance_api'),
    path('api/radar-chart/<str:target_type>/', views.get_radar_chart_data, name='radar_chart_data'),
    path('api/radar-chart/<str:target_type>/<int:target_id>/', views.get_radar_chart_data, name='radar_chart_data_with_id'),
]

