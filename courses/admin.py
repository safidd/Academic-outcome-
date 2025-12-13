from django.contrib import admin
from .models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'instructor')
    list_filter = ('instructor',)
    search_fields = ('code', 'name', 'instructor__username')
