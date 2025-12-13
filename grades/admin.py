from django.contrib import admin
from .models import Grade


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'learning_outcome', 'score')
    list_filter = ('course', 'learning_outcome', 'student')
    search_fields = ('student__username', 'course__code', 'learning_outcome__code')
