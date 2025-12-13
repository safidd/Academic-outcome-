from django.db import models
from django.conf import settings
from courses.models import Course
from outcomes.models import LearningOutcome


class Grade(models.Model):
    """Grade model"""
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
    
    class Meta:
        unique_together = ['student', 'course', 'learning_outcome']
        constraints = [
            models.CheckConstraint(
                check=models.Q(score__gte=0) & models.Q(score__lte=100),
                name='valid_score_range'
            )
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.course.code} - {self.learning_outcome.code}: {self.score}%"
