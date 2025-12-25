from django.contrib import admin
from .models import Grade, GradeAuditLog


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'learning_outcome', 'score', 'created_at', 'updated_at')
    list_filter = ('course', 'learning_outcome', 'created_at')
    search_fields = ('student__username', 'course__code', 'learning_outcome__code')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(GradeAuditLog)
class GradeAuditLogAdmin(admin.ModelAdmin):
    list_display = ('accessed_by', 'snapshot_time', 'accessed_at', 'report_type', 'records_count')
    list_filter = ('report_type', 'accessed_at', 'snapshot_time')
    search_fields = ('accessed_by__username',)
    readonly_fields = ('accessed_at',)
    date_hierarchy = 'accessed_at'
