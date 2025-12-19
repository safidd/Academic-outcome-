from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from collections import defaultdict
from .models import Grade
from courses.models import Attendance
from outcomes.utils import (
    calculate_po_scores,
    calculate_course_po_scores,
    build_course_po_distributions,
)


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
    
    return render(request, 'grades/student_dashboard.html', {
        'user': request.user,
        'grades': grades,
        'courses_with_grades': courses_with_grades,
        'po_scores': po_scores,
        'program_outcomes': program_outcomes,
        'course_po_scores': course_po_scores,
    })


def calculate_attendance_percentage(attendances):
    """Calculate attendance percentage: (Present + 0.5*Late) / Total"""
    if not attendances:
        return 0.0
    
    total = len(attendances)
    present_count = sum(1 for att in attendances if att.status == 'Present')
    late_count = sum(1 for att in attendances if att.status == 'Late')
    
    # Formula: (Present + 0.5*Late) / Total
    percentage = (present_count + 0.5 * late_count) / total * 100
    return round(percentage, 1)


@login_required
def student_attendance(request):
    """Student view to see their attendance records with course summaries"""
    if request.user.role != 'student':
        raise PermissionDenied("Only students can access this page.")
    
    # Get all attendance records for this student
    attendances = Attendance.objects.filter(
        student=request.user
    ).select_related('course', 'course__instructor').order_by('-date', 'course__code')
    
    # Calculate overall attendance statistics
    total_records = attendances.count()
    present_count = attendances.filter(status='Present').count()
    absent_count = attendances.filter(status='Absent').count()
    late_count = attendances.filter(status='Late').count()
    
    # Calculate overall percentage (Present + Late count as attended)
    if total_records > 0:
        attendance_percentage = round((present_count + late_count) / total_records * 100, 1)
        present_percentage = round(present_count / total_records * 100, 1)
    else:
        attendance_percentage = 0.0
        present_percentage = 0.0
    
    # Group attendance by course and calculate per-course statistics
    attendance_by_course = defaultdict(list)
    for attendance in attendances:
        attendance_by_course[attendance.course].append(attendance)
    
    # Build course summaries with attendance percentages
    course_summaries = []
    for course, att_list in sorted(attendance_by_course.items(), key=lambda x: x[0].code):
        # Sort attendance by date (newest first)
        sorted_attendance = sorted(att_list, key=lambda x: x.date, reverse=True)
        
        # Calculate statistics for this course
        course_total = len(sorted_attendance)
        course_present = sum(1 for att in sorted_attendance if att.status == 'Present')
        course_late = sum(1 for att in sorted_attendance if att.status == 'Late')
        course_absent = sum(1 for att in sorted_attendance if att.status == 'Absent')
        
        # Calculate percentage using formula: (Present + 0.5*Late) / Total
        course_percentage = calculate_attendance_percentage(sorted_attendance)
        
        # Calculate progress ring values (circumference = 2πr = 314.16 for r=50)
        circumference = 314.16
        progress_dash = circumference * course_percentage / 100
        
        course_summaries.append({
            'course': course,
            'attendance_list': sorted_attendance,
            'total_classes': course_total,
            'present_count': course_present,
            'late_count': course_late,
            'absent_count': course_absent,
            'attendance_percentage': course_percentage,
            'progress_dash': round(progress_dash, 1),
            'progress_circumference': circumference,
        })
    
    return render(request, 'grades/student_attendance.html', {
        'user': request.user,
        'attendances': attendances,
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'attendance_percentage': attendance_percentage,
        'present_percentage': present_percentage,
        'course_summaries': course_summaries,
    })
