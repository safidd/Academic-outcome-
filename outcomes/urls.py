from django.urls import path
from . import views

app_name = 'head'

urlpatterns = [
    path('dashboard/', views.head_dashboard, name='dashboard'),
    path('attendance/', views.attendance_dashboard, name='attendance_dashboard'),
    path('grade-audit/', views.grade_audit_report, name='grade_audit_report'),
    path('api/radar-chart/<str:target_type>/', views.get_radar_chart_data, name='radar_chart_data'),
    path('api/radar-chart/<str:target_type>/<int:target_id>/', views.get_radar_chart_data, name='radar_chart_data_with_id'),
]

