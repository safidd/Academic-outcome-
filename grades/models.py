from django.db import models
from django.conf import settings
from django.utils import timezone
from courses.models import Course
from outcomes.models import LearningOutcome


class Grade(models.Model):
    """Grade model with MVCC support for snapshot isolation"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='grades',
        limit_choices_to={'role': 'student'}
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='grades'
    )
    learning_outcome = models.ForeignKey(
        LearningOutcome,
        on_delete=models.CASCADE,
        related_name='grades'
    )
    score = models.IntegerField(
        default=0,
        help_text="Score (0-100)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when grade was first created (for MVCC/snapshot isolation)"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when grade was last updated (for MVCC/snapshot isolation)"
    )
    
    class Meta:
        unique_together = ['student', 'course', 'learning_outcome']
        constraints = [
            models.CheckConstraint(
                check=models.Q(score__gte=0) & models.Q(score__lte=100),
                name='valid_score_range'
            )
        ]
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['course', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.course.code} - {self.learning_outcome.code}: {self.score}%"


class GradeAuditLog(models.Model):
    """Audit log for tracking grade report access with snapshot timestamps"""
    accessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='grade_audit_logs',
        limit_choices_to={'role': 'department_head'}
    )
    snapshot_time = models.DateTimeField(
        help_text="Point in time snapshot used for the report"
    )
    accessed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the report was accessed"
    )
    report_type = models.CharField(
        max_length=50,
        default='grade_audit',
        help_text="Type of report generated"
    )
    filters_applied = models.JSONField(
        default=dict,
        blank=True,
        help_text="Filters applied to the report (course, date range, etc.)"
    )
    records_count = models.IntegerField(
        default=0,
        help_text="Number of records in the snapshot"
    )
    
    class Meta:
        ordering = ['-accessed_at']
        indexes = [
            models.Index(fields=['accessed_by', 'accessed_at']),
            models.Index(fields=['snapshot_time']),
        ]
    
    def __str__(self):
        return f"Audit log: {self.accessed_by.username} - {self.snapshot_time}"
