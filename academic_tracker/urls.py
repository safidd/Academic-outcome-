"""
URL configuration for academic_tracker project.
"""
from django.contrib import admin
from django.urls import path, include
from users.views import home, CustomLoginView, CustomLogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('student/', include('grades.urls', namespace='student')),
    path('instructor/', include('courses.urls', namespace='instructor')),
    path('head/', include('outcomes.urls', namespace='head')),
]
