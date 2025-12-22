from django import forms
from .models import Attendance, Course
from django.contrib.auth import get_user_model

User = get_user_model()


class AttendanceForm(forms.Form):
    """Form for bulk attendance submission"""
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': True})
    )
    
    def __init__(self, *args, instructor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if instructor:
            self.fields['course'].queryset = Course.objects.filter(
                instructor=instructor
            ).order_by('code')
            self.fields['course'].empty_label = "Select a course..."
    
    def save_attendance(self, attendance_data):
        """
        Bulk save/update attendance records
        
        Args:
            attendance_data: Dict mapping student_id to status
                Example: {1: 'Present', 2: 'Absent', 3: 'Late'}
        
        Returns:
            tuple: (created_count, updated_count)
        """
        course = self.cleaned_data['course']
        date = self.cleaned_data['date']
        
        created_count = 0
        updated_count = 0
        
        for student_id, status in attendance_data.items():
            student = User.objects.get(id=student_id, role='student')
            
            attendance, created = Attendance.objects.update_or_create(
                student=student,
                course=course,
                date=date,
                defaults={'status': status}
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        return created_count, updated_count

