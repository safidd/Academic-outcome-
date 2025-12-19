from django import forms
from django.contrib.auth import get_user_model
from .models import Course, Attendance
from grades.models import Grade

User = get_user_model()


class AttendanceForm(forms.Form):
    """Form for instructors to take attendance"""
    
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': True
        }),
        label='Date'
    )
    
    def __init__(self, *args, instructor=None, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if instructor and course:
            # Get all students enrolled in this course (students with grades)
            enrolled_students = User.objects.filter(
                role='student',
                grades__course=course
            ).distinct().order_by('first_name', 'last_name', 'username')
            
            # Create a choice field for each student
            for student in enrolled_students:
                field_name = f'attendance_{student.id}'
                self.fields[field_name] = forms.ChoiceField(
                    choices=Attendance.STATUS_CHOICES,
                    initial='Present',
                    widget=forms.RadioSelect(attrs={
                        'class': 'form-check-input',
                    }),
                    label=f"{student.get_full_name() or student.username}",
                    required=False
                )
    
    def save(self, course, date):
        """Save attendance records for all students"""
        created_count = 0
        updated_count = 0
        
        for field_name, status in self.cleaned_data.items():
            if field_name.startswith('attendance_') and status:
                student_id = int(field_name.replace('attendance_', ''))
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

