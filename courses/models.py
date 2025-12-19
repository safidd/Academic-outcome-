from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Course(models.Model):
    """Course model"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses_taught',
        limit_choices_to={'role': 'instructor'}
    )
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Attendance(models.Model):
    """Attendance tracking model"""
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
    ]
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendances',
        limit_choices_to={'role': 'student'}
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Absent'
    )
    
    class Meta:
        unique_together = ['student', 'course', 'date']
        ordering = ['-date', 'student__first_name', 'student__last_name']
        indexes = [
            models.Index(fields=['student', 'course', 'date']),
            models.Index(fields=['course', 'date']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.course.code} - {self.date} - {self.status}"
    
    def clean(self):
        """Validate that student is enrolled in the course"""
        if self.student and self.course:
            # Check if student has any grades for this course (indicating enrollment)
            from grades.models import Grade
            if not Grade.objects.filter(student=self.student, course=self.course).exists():
                raise ValidationError(
                    f"Student {self.student.username} is not enrolled in course {self.course.code}."
                )
    
    def save(self, *args, **kwargs):
        """Override save to call clean"""
        self.full_clean()
        super().save(*args, **kwargs)
