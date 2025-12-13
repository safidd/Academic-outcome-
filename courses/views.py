from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.http import JsonResponse
from django.db import models
from grades.forms import GradeEntryForm
from grades.models import Grade
from outcomes.models import LearningOutcome
from outcomes.utils import (
    calculate_instructor_course_po_scores,
    build_course_po_distributions,
)
from outcomes.models import ProgramOutcome
from courses.models import Course


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
