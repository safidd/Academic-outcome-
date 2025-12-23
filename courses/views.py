from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone
from datetime import date
from grades.forms import GradeEntryForm
from grades.models import Grade
from outcomes.models import LearningOutcome
from outcomes.utils import (
    calculate_instructor_course_po_scores,
    build_course_po_distributions,
    get_po_radar_data_for_course,
    get_po_radar_data_for_department,
)
from outcomes.models import ProgramOutcome
from courses.models import Course, Attendance
from courses.forms import AttendanceForm

User = get_user_model()


@login_required
def instructor_dashboard(request):
    """Instructor dashboard - only accessible to instructors"""
    if request.user.role != 'instructor':
        raise PermissionDenied("Only instructors can access this page.")
    
    # Get all courses taught by this instructor
    courses = request.user.courses_taught.all()
    
    # Calculate course averages for each course
    course_averages = []
    for course in courses:
        grades = Grade.objects.filter(course=course, course__instructor=request.user)
        if grades.exists():
            avg_score = grades.aggregate(avg=models.Avg('score'))['avg']
            student_count = grades.values('student').distinct().count()
            grade_count = grades.count()
            course_averages.append({
                'course': course,
                'average': round(avg_score, 2) if avg_score else 0,
                'student_count': student_count,
                'grade_count': grade_count,
            })
        else:
            course_averages.append({
                'course': course,
                'average': 0,
                'student_count': 0,
                'grade_count': 0,
            })
    
    # Sort by average score (highest first)
    course_averages.sort(key=lambda x: x['average'], reverse=True)
    
    # Calculate total grades
    total_grades = sum(entry['grade_count'] for entry in course_averages)
    
    course_po_summaries = calculate_instructor_course_po_scores(request.user)
    distribution_map = build_course_po_distributions([entry['course'].id for entry in course_po_summaries])
    for entry in course_po_summaries:
        entry['po_distribution'] = distribution_map.get(entry['course'].id, [])
    
    # Build distribution map for all courses (for course list display)
    all_course_distributions = build_course_po_distributions(list(courses.values_list('id', flat=True)))
    
    # Get all program outcomes for description lookup
    program_outcomes = ProgramOutcome.objects.all().order_by('code')
    
    return render(request, 'courses/instructor_dashboard.html', {
        'user': request.user,
        'courses': courses,
        'course_averages': course_averages,
        'total_grades': total_grades,
        'course_po_summaries': course_po_summaries,
        'course_distributions': {course.id: all_course_distributions.get(course.id, []) for course in courses},
        'program_outcomes': program_outcomes,
    })


@login_required
def enter_grade(request):
    """Instructor grade entry page"""
    if request.user.role != 'instructor':
        raise PermissionDenied("Only instructors can access this page.")
    
    if request.method == 'POST':
        form = GradeEntryForm(request.POST, instructor=request.user)
        if form.is_valid():
            grade = form.save()
            messages.success(request, f'Grade entered successfully: {grade.student.username} - {grade.course.code} - {grade.learning_outcome.code} = {grade.score}%')
            return redirect('instructor:enter_grade')
        else:
            # If form is invalid, re-populate learning outcomes for the selected course
            if 'course' in form.data and form.data['course']:
                try:
                    course_id = int(form.data['course'])
                    course = request.user.courses_taught.get(pk=course_id)
                    form.fields['learning_outcome'].queryset = LearningOutcome.objects.filter(course=course)
                except (ValueError, Course.DoesNotExist):
                    pass
    else:
        form = GradeEntryForm(instructor=request.user)
    
    # Get all courses taught by this instructor
    courses = request.user.courses_taught.all()
    
    distribution_map = build_course_po_distributions(list(courses.values_list('id', flat=True)))
    
    # Get all program outcomes for description lookup
    program_outcomes = ProgramOutcome.objects.all().order_by('code')
    
    return render(request, 'courses/enter_grade.html', {
        'form': form,
        'courses': courses,
        'user': request.user,
        'course_distributions': distribution_map,
        'program_outcomes': program_outcomes,
    })


@login_required
def get_learning_outcomes(request, course_id):
    """AJAX endpoint to get learning outcomes for a course"""
    if request.user.role != 'instructor':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Verify the course belongs to this instructor
    course = get_object_or_404(Course, pk=course_id, instructor=request.user)
    
    learning_outcomes = LearningOutcome.objects.filter(course=course).values('id', 'code', 'description')
    
    return JsonResponse({
        'learning_outcomes': list(learning_outcomes)
    })


@login_required
def get_radar_chart_data(request, target_type, target_id=None):
    """
    API endpoint to get radar chart data for instructors.
    
    Args:
        target_type: 'department' or 'course'
        target_id: Course ID (required if target_type is 'course')
    
    Returns:
        JSON response with radar chart data
    """
    if request.user.role != 'instructor':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
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
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def sync_attendance_api(request):
    """
    Idempotent API endpoint for syncing attendance records.
    Handles duplicate submissions gracefully using unique constraint.
    """
    # Check authentication
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
    
    # Check authorization
    if request.user.role != 'instructor':
        return JsonResponse({'success': False, 'error': 'Unauthorized - Instructor access required'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        
        course_id = data.get('course')
        date_str = data.get('date')
        attendance_data = data.get('attendance_data', {})
        
        if not course_id or not date_str or not attendance_data:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: course, date, attendance_data'
            }, status=400)
        
        # Verify course belongs to instructor
        course = get_object_or_404(Course, pk=course_id, instructor=request.user)
        
        # Parse date
        from datetime import datetime
        try:
            attendance_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        except (ValueError, AttributeError):
            try:
                attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid date format'
                }, status=400)
        
        # Use transaction for atomicity
        created_count = 0
        updated_count = 0
        
        try:
            with transaction.atomic():
                for student_id, status in attendance_data.items():
                    try:
                        student_id_int = int(student_id)
                    except (ValueError, TypeError):
                        continue
                    
                    # Validate status
                    valid_statuses = ['Present', 'Absent', 'Late']
                    if status not in valid_statuses:
                        continue
                    
                    try:
                        student = User.objects.get(id=student_id_int, role='student')
                    except User.DoesNotExist:
                        continue
                    
                    # Idempotent operation: update_or_create handles duplicates
                    # Uses unique constraint on (student, course, date) to prevent duplicates
                    attendance, created = Attendance.objects.update_or_create(
                        student=student,
                        course=course,
                        date=attendance_date,
                        defaults={'status': status}
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                
                return JsonResponse({
                    'success': True,
                    'message': f'Synced {created_count + updated_count} records',
                    'created': created_count,
                    'updated': updated_count
                })
                
        except Exception as e:
            import traceback
            return JsonResponse({
                'success': False,
                'error': f'Database error: {str(e)}'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def take_attendance(request):
    """Instructor view for taking attendance"""
    if request.user.role != 'instructor':
        raise PermissionDenied("Only instructors can access this page.")
    
    if request.method == 'POST':
        form = AttendanceForm(request.POST, instructor=request.user)
        
        if form.is_valid():
            # Extract attendance data from POST
            attendance_data = {}
            for key, value in request.POST.items():
                if key.startswith('student_'):
                    try:
                        student_id = int(key.replace('student_', ''))
                        attendance_data[student_id] = value
                    except ValueError:
                        messages.error(request, f'Invalid student ID: {key}')
                        return redirect('instructor:take_attendance')
            
            if attendance_data:
                # Save attendance with transaction atomicity
                success, created_count, updated_count, error_message = form.save_attendance(attendance_data)
                
                if success:
                    messages.success(
                        request,
                        f'Attendance saved successfully! Created: {created_count}, Updated: {updated_count}'
                    )
                    return redirect('instructor:take_attendance')
                else:
                    # Transaction was rolled back
                    messages.error(
                        request,
                        f'Failed to save attendance: {error_message}. No changes were made. Please try again.'
                    )
            else:
                messages.error(request, 'Please select attendance status for at least one student.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AttendanceForm(instructor=request.user)
    
    # Get selected course and date for displaying students
    selected_course = None
    selected_date = date.today()
    students = []
    existing_attendance = {}
    
    if 'course' in request.GET:
        try:
            course_id = int(request.GET['course'])
            selected_course = get_object_or_404(
                Course,
                pk=course_id,
                instructor=request.user
            )
            students = selected_course.get_enrolled_students()
            
            # Get existing attendance for selected date
            if 'date' in request.GET:
                try:
                    selected_date = date.fromisoformat(request.GET['date'])
                except (ValueError, TypeError):
                    selected_date = date.today()
            
            existing_attendance = {
                att.student.id: att.status
                for att in Attendance.objects.filter(
                    course=selected_course,
                    date=selected_date
                )
            }
        except (ValueError, Course.DoesNotExist):
            pass
    
    # Get all courses for dropdown
    courses = request.user.courses_taught.all()
    
    return render(request, 'courses/take_attendance.html', {
        'form': form,
        'courses': courses,
        'selected_course': selected_course,
        'selected_date': selected_date,
        'students': students,
        'existing_attendance': existing_attendance,
        'user': request.user,
    })
