from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import ProgramOutcome
from .utils import (
    calculate_department_po_averages,
    calculate_department_course_po_scores,
    build_course_po_distributions,
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
        insights.append({
            'title': f'{top_po["code"]} leading the cohort',
            'detail': f'{top_po["code"]} averages {top_po["value"]}%, indicating strong mastery.',
            'badge': 'Success pattern',
            'trend': '+4.2%',
        })
    if low_po:
        insights.append({
            'title': f'{low_po["code"]} requires focus',
            'detail': f'{low_po["code"]} averages {low_po["value"]}%. Consider targeted remediation.',
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
    })
