from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Custom User model with role field"""
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('department_head', 'Department Head'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student'
    )
    
    def __str__(self):
        if self.first_name or self.last_name:
            full_name = f"{self.first_name} {self.last_name}".strip()
            return f"{full_name} ({self.username}) - {self.get_role_display()}"
        return f"{self.username} ({self.get_role_display()})"
