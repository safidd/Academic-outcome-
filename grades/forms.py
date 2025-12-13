from django import forms
from .models import Grade
from courses.models import Course
from outcomes.models import LearningOutcome
from django.contrib.auth import get_user_model


class GradeEntryForm(forms.ModelForm):
    """Form for instructors to enter grades"""
    
    class Meta:
        model = Grade
        fields = ['course', 'student', 'learning_outcome', 'score']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'student': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'learning_outcome': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }
    
    def __init__(self, *args, instructor=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter courses to only those taught by this instructor
        if instructor:
            course_queryset = Course.objects.filter(instructor=instructor).order_by('code')
            self.fields['course'].queryset = course_queryset
            # Ensure there's a blank option
            self.fields['course'].empty_label = "Select a course..."
            
            # Filter students to only students (role='student') and order by name
            User = get_user_model()
            students = User.objects.filter(role='student').order_by('first_name', 'last_name', 'username')
            self.fields['student'].queryset = students
            self.fields['student'].label = 'Student'
            
            # Filter learning outcomes based on selected course (handled in template with JavaScript)
            # Start with empty queryset - will be populated via AJAX when course is selected
            self.fields['learning_outcome'].queryset = LearningOutcome.objects.none()
            self.fields['learning_outcome'].required = True
        
        self.fields['score'].label = 'Score (0-100)'
    
    def clean_score(self):
        """Validate score is between 0-100"""
        score = self.cleaned_data.get('score')
        if score is not None:
            if score < 0 or score > 100:
                raise forms.ValidationError("Score must be between 0 and 100.")
        return score
    
    def clean(self):
        """Validate that grade doesn't already exist for this student/course/LO combination"""
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        course = cleaned_data.get('course')
        learning_outcome = cleaned_data.get('learning_outcome')
        
        if student and course and learning_outcome:
            # Check if grade already exists (excluding current instance if editing)
            existing = Grade.objects.filter(
                student=student,
                course=course,
                learning_outcome=learning_outcome
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(
                    f"A grade already exists for {student.username} in {course.code} for {learning_outcome.code}."
                )
            
            # Ensure learning outcome belongs to the selected course
            if learning_outcome.course != course:
                raise forms.ValidationError(
                    f"Learning Outcome {learning_outcome.code} does not belong to course {course.code}."
                )
        
        return cleaned_data

