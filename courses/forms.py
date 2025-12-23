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
        Bulk save/update attendance records with transaction atomicity.
        
        Uses database transactions to ensure all-or-nothing behavior.
        If any record fails, the entire transaction is rolled back.
        
        Args:
            attendance_data: Dict mapping student_id to status
                Example: {1: 'Present', 2: 'Absent', 3: 'Late'}
        
        Returns:
            tuple: (success: bool, created_count: int, updated_count: int, error_message: str)
        
        Raises:
            Exception: If transaction fails, raises the original exception
        """
        from django.db import transaction
        from django.core.exceptions import ValidationError
        
        course = self.cleaned_data['course']
        date = self.cleaned_data['date']
        
        created_count = 0
        updated_count = 0
        
        try:
            # Start transaction - ensures atomicity
            # Django uses 'READ COMMITTED' isolation level by default (or SERIALIZABLE for SQLite)
            with transaction.atomic():
                # Process each student's attendance
                for student_id, status in attendance_data.items():
                    try:
                        student = User.objects.select_for_update().get(
                            id=student_id, 
                            role='student'
                        )
                    except User.DoesNotExist:
                        raise ValueError(f"Student with ID {student_id} not found")
                    
                    # Validate status
                    valid_statuses = ['Present', 'Absent', 'Late']
                    if status not in valid_statuses:
                        raise ValidationError(f"Invalid status: {status}. Must be one of {valid_statuses}")
                    
                    # Use update_or_create with select_for_update for concurrency protection
                    attendance, created = Attendance.objects.select_for_update().update_or_create(
                        student=student,
                        course=course,
                        date=date,
                        defaults={'status': status}
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                
                # If we reach here, all records were processed successfully
                # Transaction will automatically commit
                return True, created_count, updated_count, None
                
        except Exception as e:
            # Transaction will automatically rollback on any exception
            # Return error information
            error_message = f"Failed to save attendance: {str(e)}"
            return False, created_count, updated_count, error_message

