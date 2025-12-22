from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model


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
    
    def get_enrolled_students(self):
        """Get all students enrolled in this course (students who have grades)"""
        from grades.models import Grade
        User = get_user_model()
        return User.objects.filter(
            role='student',
            grades__course=self
        ).distinct().order_by('first_name', 'last_name', 'username')


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
        related_name='attendance_records',
        limit_choices_to={'role': 'student'}
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    
    class Meta:
        unique_together = ['student', 'course', 'date']
        ordering = ['-date', 'student']
        indexes = [
            models.Index(fields=['student', 'course']),
            models.Index(fields=['course', 'date']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.course.code} - {self.date} - {self.status}"