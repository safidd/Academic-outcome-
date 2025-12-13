from django.db import models
from courses.models import Course


class LearningOutcome(models.Model):
    """Learning Outcome model"""
    code = models.CharField(max_length=20)
    description = models.TextField()
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='learning_outcomes'
    )
    
    class Meta:
        unique_together = ['code', 'course']
    
    def __str__(self):
        return f"{self.code} - {self.course.code}"


class ProgramOutcome(models.Model):
    """Program Outcome model"""
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    
    def __str__(self):
        return f"{self.code}"


class ContributionRate(models.Model):
    """Mapping between Learning Outcomes and Program Outcomes"""
    learning_outcome = models.ForeignKey(
        LearningOutcome,
        on_delete=models.CASCADE,
        related_name='contribution_rates'
    )
    program_outcome = models.ForeignKey(
        ProgramOutcome,
        on_delete=models.CASCADE,
        related_name='contribution_rates'
    )
    percentage = models.IntegerField(
        default=0,
        help_text="Percentage contribution (0-100)"
    )
    
    class Meta:
        unique_together = ['learning_outcome', 'program_outcome']
        constraints = [
            models.CheckConstraint(
                check=models.Q(percentage__gte=0) & models.Q(percentage__lte=100),
                name='valid_percentage_range'
            )
        ]
    
    def __str__(self):
        return f"{self.learning_outcome.code} -> {self.program_outcome.code}: {self.percentage}%"
