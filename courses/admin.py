from django.contrib import admin
from .models import Course, Attendance


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'instructor')
    list_filter = ('instructor',)
    search_fields = ('code', 'name', 'instructor__username')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'date', 'status')
    list_filter = ('course', 'status', 'date')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'course__code', 'course__name')
    date_hierarchy = 'date'
    ordering = ('-date', 'course', 'student')
