from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from collections import defaultdict
from .models import Grade
from courses.models import Attendance
from outcomes.utils import (
    calculate_po_scores,
    calculate_course_po_scores,
    build_course_po_distributions,
)


def calculate_attendance_percentage(attendance_records):
    """
    Calculate attendance percentage: (Present + 0.5*Late) / Total
    
    Args:
        attendance_records: QuerySet or list of Attendance objects
    
    Returns:
        float: Attendance percentage (0-100), rounded to 1 decimal place
    """
    if not attendance_records or len(attendance_records) == 0:
        return 0.0
    
    total = len(attendance_records)
    present_count = sum(1 for record in attendance_records if record.status == 'Present')
    late_count = sum(1 for record in attendance_records if record.status == 'Late')
    
    percentage = (present_count + 0.5 * late_count) / total * 100
    return round(percentage, 1)


@login_required
def student_dashboard(request):
    """Student dashboard - only accessible to students"""
    if request.user.role != 'student':
        raise PermissionDenied("Only students can access this page.")
    
    # Get all grades for this student
    grades = Grade.objects.filter(
        student=request.user
    ).select_related('course', 'learning_outcome').order_by('course__code', 'learning_outcome__code')
    
    # Group grades by course
    grades_by_course = defaultdict(list)
    for grade in grades:
        grades_by_course[grade.course].append(grade)
    
    # Convert to list of tuples (course, grades_list) for template
    courses_with_grades = [(course, grades_list) for course, grades_list in sorted(grades_by_course.items(), key=lambda x: x[0].code)]
    
    # Calculate PO scores for this student
    po_scores = calculate_po_scores(request.user)
    course_po_scores = calculate_course_po_scores(request.user)
    distribution_map = build_course_po_distributions([entry['course'].id for entry in course_po_scores])
    for entry in course_po_scores:
        entry['po_distribution'] = distribution_map.get(entry['course'].id, [])
    
    # Get PO details for display
    from outcomes.models import ProgramOutcome
    program_outcomes = ProgramOutcome.objects.all().order_by('code')
    
    # Calculate attendance by course
    attendance_by_course = {}
    overall_attendance_records = []
    
    for course in grades_by_course.keys():
        attendance_records = Attendance.objects.filter(
            student=request.user,
            course=course
        ).order_by('-date')
        
        if attendance_records.exists():
            overall_attendance_records.extend(list(attendance_records))
            attendance_by_course[course] = {
                'percentage': calculate_attendance_percentage(attendance_records),
                'total': attendance_records.count(),
                'present': attendance_records.filter(status='Present').count(),
                'late': attendance_records.filter(status='Late').count(),
                'absent': attendance_records.filter(status='Absent').count(),
                'records': attendance_records[:10],  # Latest 10 records
            }
    
    # Calculate overall attendance percentage
    overall_percentage = calculate_attendance_percentage(overall_attendance_records)
    
    return render(request, 'grades/student_dashboard.html', {
        'user': request.user,
        'grades': grades,
        'courses_with_grades': courses_with_grades,
        'po_scores': po_scores,
        'program_outcomes': program_outcomes,
        'course_po_scores': course_po_scores,
        'attendance_by_course': attendance_by_course,
        'overall_attendance_percentage': overall_percentage,
    })


@login_required
def my_attendance(request):
    """Student view for viewing detailed attendance"""
    if request.user.role != 'student':
        raise PermissionDenied("Only students can access this page.")
    
    # Get all attendance records for this student
    attendance_records = Attendance.objects.filter(
        student=request.user
    ).select_related('course').order_by('-date', 'course__code')
    
    # Group by course
    attendance_by_course = defaultdict(list)
    for record in attendance_records:
        attendance_by_course[record.course].append(record)
    
    # Calculate statistics per course
    course_stats = {}
    for course, records in attendance_by_course.items():
        course_stats[course] = {
            'percentage': calculate_attendance_percentage(records),
            'total': len(records),
            'present': sum(1 for r in records if r.status == 'Present'),
            'late': sum(1 for r in records if r.status == 'Late'),
            'absent': sum(1 for r in records if r.status == 'Absent'),
        }
    
    # Calculate overall attendance
    overall_percentage = calculate_attendance_percentage(attendance_records)
    
    return render(request, 'grades/my_attendance.html', {
        'attendance_records': attendance_records,
        'attendance_by_course': dict(attendance_by_course),
        'course_stats': course_stats,
        'overall_percentage': overall_percentage,
        'total_records': attendance_records.count(),
    })
