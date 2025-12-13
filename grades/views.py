from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Grade
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
        'po_scores': po_scores,
        'program_outcomes': program_outcomes,
        'course_po_scores': course_po_scores,
    })
