from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Avg
from django.http import JsonResponse
from django.utils import timezone
import json
from datetime import datetime
from .models import ProgramOutcome
from courses.models import Course
from grades.models import Grade
from grades.utils import generate_grade_audit_report, get_historical_snapshots, get_weekly_snapshot_times
from .utils import (
    calculate_department_po_averages,
    calculate_department_course_po_scores,
    build_course_po_distributions,
    calculate_po_scores,
    get_po_radar_data_for_department,
    get_po_radar_data_for_course,
    calculate_course_attendance_averages,
)


@login_required
def head_dashboard(request):
    """Department Head dashboard - only accessible to department heads"""
    if request.user.role != 'department_head':
        raise PermissionDenied("Only department heads can access this page.")
    
    # Calculate department averages for all POs
    department_averages = calculate_department_po_averages()
    
    # Get all program outcomes for display
    program_outcomes = ProgramOutcome.objects.all().order_by('code')
    program_outcome_lookup = {po.code: po.description for po in program_outcomes}
    program_outcome_count = program_outcomes.count()
    
    # Get total number of students
    User = get_user_model()
    total_students = User.objects.filter(role='student').count()
    
    tracked_po_count = len(department_averages) if department_averages else 0
    average_score = 0
    top_po = None
    low_po = None
    
    if department_averages:
        values = list(department_averages.values())
        average_score = round(sum(values) / len(values), 1)
        sorted_pos = sorted(department_averages.items(), key=lambda item: item[1], reverse=True)
        top_code, top_value = sorted_pos[0]
        low_code, low_value = sorted_pos[-1]
        top_po = {
            'code': top_code,
            'value': top_value,
            'description': program_outcome_lookup.get(top_code, ''),
        }
        low_po = {
            'code': low_code,
            'value': low_value,
            'description': program_outcome_lookup.get(low_code, ''),
        }
    
    if average_score >= 85:
        health_status = {
            'label': 'On Track',
            'message': 'Program outcomes are performing well. Keep reinforcing successful strategies.',
            'badge_class': 'bg-success',
        }
    elif average_score >= 70:
        health_status = {
            'label': 'Needs Attention',
            'message': 'Some outcomes are trending down. Review curriculum alignment and assessments.',
            'badge_class': 'bg-warning text-dark',
        }
    else:
        health_status = {
            'label': 'At Risk',
            'message': 'Immediate intervention recommended. Identify low-performing outcomes first.',
            'badge_class': 'bg-danger',
        }
    
    insights = []
    if top_po:
        desc = top_po["description"]
        title = desc[:50] + "..." if len(desc) > 50 else desc
        insights.append({
            'title': f'Leading outcome: {title}',
            'detail': f'This outcome averages {top_po["value"]}%, indicating strong mastery.',
            'badge': 'Success pattern',
            'trend': '+4.2%',
        })
    if low_po:
        desc = low_po["description"]
        title = desc[:50] + "..." if len(desc) > 50 else desc
        insights.append({
            'title': f'Requires focus: {title}',
            'detail': f'This outcome averages {low_po["value"]}%. Consider targeted remediation.',
            'badge': 'Action needed',
            'trend': '-3.1%',
        })
    if not insights:
        insights.append({
            'title': 'Awaiting data',
            'detail': 'Enroll students and capture learning outcome grades to unlock insights.',
            'badge': 'Setup',
            'trend': '',
        })
    
    course_po_breakdown = calculate_department_course_po_scores()
    distribution_map = build_course_po_distributions([entry['course'].id for entry in course_po_breakdown])
    for entry in course_po_breakdown:
        entry['po_distribution'] = distribution_map.get(entry['course'].id, [])
    
    # Get all instructors with detailed information
    instructors = User.objects.filter(role='instructor').select_related().order_by('username')
    instructors_list = []
    for instructor in instructors:
        courses_taught = Course.objects.filter(instructor=instructor)
        total_grades = Grade.objects.filter(course__instructor=instructor).count()
        total_students_in_courses = Grade.objects.filter(course__instructor=instructor).values('student').distinct().count()
        
        instructors_list.append({
            'instructor': instructor,
            'courses': courses_taught,
            'courses_count': courses_taught.count(),
            'total_grades': total_grades,
            'total_students': total_students_in_courses,
        })
    
    # Get all students with detailed information
    students = User.objects.filter(role='student').select_related().order_by('username')
    students_list = []
    for student in students:
        student_grades = Grade.objects.filter(student=student).select_related('course', 'learning_outcome')
        courses_enrolled = student_grades.values('course').distinct().count()
        total_grades_count = student_grades.count()
        avg_grade = student_grades.aggregate(avg=Avg('score'))['avg'] or 0
        student_po_scores = calculate_po_scores(student)
        avg_po_score = sum(student_po_scores.values()) / len(student_po_scores) if student_po_scores else 0
        
        students_list.append({
            'student': student,
            'grades': student_grades,
            'courses_count': courses_enrolled,
            'total_grades': total_grades_count,
            'average_grade': round(avg_grade, 1),
            'po_scores': student_po_scores,
            'average_po_score': round(avg_po_score, 1),
        })
    
    # Get all courses with detailed information
    all_courses = Course.objects.select_related('instructor').order_by('code')
    courses_list = []
    for course in all_courses:
        course_grades = Grade.objects.filter(course=course)
        students_in_course = course_grades.values('student').distinct().count()
        total_grades_count = course_grades.count()
        avg_course_grade = course_grades.aggregate(avg=Avg('score'))['avg'] or 0
        
        courses_list.append({
            'course': course,
            'students_count': students_in_course,
            'total_grades': total_grades_count,
            'average_grade': round(avg_course_grade, 1),
        })
    
    # Get radar chart data for department
    radar_data = get_po_radar_data_for_department()
    
    return render(request, 'outcomes/head_dashboard.html', {
        'user': request.user,
        'department_averages': department_averages,
        'program_outcomes': program_outcomes,
        'total_students': total_students,
        'program_outcome_count': program_outcome_count,
        'tracked_po_count': tracked_po_count,
        'average_score': average_score,
        'top_po': top_po,
        'low_po': low_po,
        'health_status': health_status,
        'insights': insights,
        'course_po_breakdown': course_po_breakdown,
        'instructors_list': instructors_list,
        'students_list': students_list,
        'courses_list': courses_list,
        'radar_data': radar_data,
    })


@login_required
def get_radar_chart_data(request, target_type, target_id=None):
    """
    API endpoint to get radar chart data.
    
    Args:
        target_type: 'department' or 'course'
        target_id: Course ID (required if target_type is 'course')
    
    Returns:
        JSON response with radar chart data
    """
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    
    if request.user.role == 'department_head':
        # Department head can see department or any course
        if target_type == 'department':
            data = get_po_radar_data_for_department()
            return JsonResponse(data)
        elif target_type == 'course' and target_id:
            data = get_po_radar_data_for_course(target_id)
            if data:
                return JsonResponse(data)
            return JsonResponse({'error': 'Course not found'}, status=404)
    
    elif request.user.role == 'instructor':
        # Instructors can only see their own courses
        if target_type == 'course' and target_id:
            # Verify the course belongs to this instructor
            course = get_object_or_404(Course, pk=target_id, instructor=request.user)
            data = get_po_radar_data_for_course(target_id)
            if data:
                return JsonResponse(data)
            return JsonResponse({'error': 'Course not found'}, status=404)
        elif target_type == 'department':
            # Instructors can see department average for comparison
            data = get_po_radar_data_for_department()
            return JsonResponse(data)
    
    return JsonResponse({'error': 'Unauthorized'}, status=403)


@login_required
def grade_audit_report(request):
    """
    Department Head grade audit report with snapshot isolation.
    Prevents read skew by using MVCC and transaction isolation.
    """
    if request.user.role != 'department_head':
        raise PermissionDenied("Only department heads can access this page.")
    
    # Get snapshot time from request (for time travel)
    snapshot_time_str = request.GET.get('snapshot_time')
    snapshot_time = None
    
    if snapshot_time_str:
        try:
            snapshot_time = datetime.fromisoformat(snapshot_time_str.replace('Z', '+00:00'))
            if timezone.is_naive(snapshot_time):
                snapshot_time = timezone.make_aware(snapshot_time)
        except (ValueError, AttributeError):
            snapshot_time = None
    
    # Get filters
    course_filter = request.GET.get('course_id')
    if course_filter:
        try:
            course_filter = int(course_filter)
        except (ValueError, TypeError):
            course_filter = None
    
    date_range = None
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    if start_date_str or end_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
            end_date = datetime.fromisoformat(end_date_str) if end_date_str else None
            if start_date or end_date:
                if start_date and timezone.is_naive(start_date):
                    start_date = timezone.make_aware(start_date)
                if end_date and timezone.is_naive(end_date):
                    end_date = timezone.make_aware(end_date)
                date_range = (start_date, end_date)
        except (ValueError, AttributeError):
            date_range = None
    
    # Generate report with snapshot isolation
    try:
        report_data = generate_grade_audit_report(
            user=request.user,
            snapshot_time=snapshot_time,
            course_filter=course_filter,
            date_range=date_range
        )
    except PermissionError as e:
        raise PermissionDenied(str(e))
    
    # Get historical snapshots for time travel
    historical_snapshots = get_historical_snapshots(request.user, limit=20)
    weekly_snapshots = get_weekly_snapshot_times()
    
    # Get all courses for filter dropdown
    all_courses = Course.objects.all().order_by('code')
    
    return render(request, 'outcomes/grade_audit_report.html', {
        'report_data': report_data,
        'historical_snapshots': historical_snapshots,
        'weekly_snapshots': weekly_snapshots,
        'courses': all_courses,
        'selected_course': course_filter,
        'selected_snapshot_time': snapshot_time,
        'date_range': date_range,
    })


@login_required
def attendance_dashboard(request):
    """Department Head attendance dashboard showing course attendance averages"""
    if request.user.role != 'department_head':
        raise PermissionDenied("Only department heads can access this page.")
    
    # Get all course attendance data
    course_attendance = calculate_course_attendance_averages()
    
    # Handle search/filter
    search_query = request.GET.get('search', '').strip()
    filtered_attendance = course_attendance
    
    if search_query:
        search_lower = search_query.lower()
        filtered_attendance = [
            item for item in course_attendance
            if (search_lower in item['course'].code.lower() or
                search_lower in item['course'].name.lower() or
                (item['course'].instructor.first_name and search_lower in item['course'].instructor.first_name.lower()) or
                (item['course'].instructor.last_name and search_lower in item['course'].instructor.last_name.lower()) or
                search_lower in item['course'].instructor.username.lower())
        ]
    
    # Prepare data for bar chart
    chart_labels = [item['course'].code for item in filtered_attendance]
    chart_percentages = [item['attendance_percentage'] for item in filtered_attendance]
    chart_colors = [
        '#28a745' if item['attendance_percentage'] >= 85 else
        '#ffc107' if item['attendance_percentage'] >= 70 else
        '#dc3545'
        for item in filtered_attendance
    ]
    
    return render(request, 'outcomes/attendance_dashboard.html', {
        'course_attendance': filtered_attendance,
        'total_courses': len(course_attendance),
        'filtered_count': len(filtered_attendance),
        'search_query': search_query,
        'chart_labels': json.dumps(chart_labels),
        'chart_percentages': json.dumps(chart_percentages),
        'chart_colors': json.dumps(chart_colors),
    })
