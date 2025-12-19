from collections import defaultdict
from django.contrib.auth import get_user_model
from .models import ProgramOutcome, ContributionRate
from grades.models import Grade


def calculate_po_scores(student):
    """
    Calculate Program Outcome (PO) scores for a student based on their Learning Outcome (LO) grades.
    
    Formula:
    For each PO:
    PO_score = Σ(LO_score * contribution_percentage / 100) for all LOs that contribute to this PO
    
    Returns:
    dict: {po_code: score, ...} where scores are between 0-100
    """
    if student.role != 'student':
        return {}
    
    # Get all grades for this student
    grades = Grade.objects.filter(student=student).select_related('learning_outcome', 'course')
    
    # Initialize PO scores
    po_scores = {}
    
    # Get all program outcomes
    program_outcomes = ProgramOutcome.objects.all()
    
    for po in program_outcomes:
        po_score = 0.0
        total_weight = 0.0
        
        # Get all contribution rates for this PO
        contribution_rates = ContributionRate.objects.filter(
            program_outcome=po
        ).select_related('learning_outcome')
        
        for cr in contribution_rates:
            # Find the grade for this learning outcome
            grade = grades.filter(learning_outcome=cr.learning_outcome).first()
            
            if grade:
                # Convert percentage to weight (0-1)
                weight = cr.percentage / 100.0
                # Add weighted score
                po_score += grade.score * weight
                total_weight += weight
        
        # Calculate final PO score
        # According to requirement: LO1 = 80%, LO1 → PO2 weight = 0.4, PO2 = 80 * 0.4 = 32
        # So we sum the weighted contributions directly (not normalized)
        # Example: If LO1=80 and LO1→PO2=40%, then PO2 contribution = 80 * 0.4 = 32
        if total_weight > 0:
            # Sum of weighted scores (already calculated as po_score)
            # Cap at 100
            final_score = min(po_score, 100)
        else:
            final_score = 0
        
        po_scores[po.code] = round(final_score, 2)
    
    return po_scores


def calculate_department_po_averages():
    """
    Calculate average PO scores across all students in the department.
    
    Returns:
    dict: {po_code: average_score, ...}
    """
    # Get all students
    User = get_user_model()
    students = User.objects.filter(role='student')
    
    if not students.exists():
        return {}
    
    # Get all program outcomes
    program_outcomes = ProgramOutcome.objects.all()
    
    # Collect all PO scores for all students
    all_po_scores = {}
    
    for po in program_outcomes:
        all_po_scores[po.code] = []
    
    for student in students:
        student_po_scores = calculate_po_scores(student)
        for po_code, score in student_po_scores.items():
            all_po_scores[po_code].append(score)
    
    # Calculate averages
    department_averages = {}
    for po_code, scores in all_po_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            department_averages[po_code] = round(avg_score, 2)
        else:
            department_averages[po_code] = 0.0
    
    return department_averages


def _aggregate_course_po_scores(grades_queryset):
    """
    Helper to aggregate PO scores for any grade queryset (student, instructor, department)
    """
    course_map = {}
    
    for grade in grades_queryset:
        course = grade.course
        course_entry = course_map.setdefault(
            course.id,
            {
                'course': course,
                'student_scores': defaultdict(lambda: defaultdict(float)),
            }
        )
        
        contribution_rates = grade.learning_outcome.contribution_rates.all()
        student_scores = course_entry['student_scores'][grade.student_id]
        
        for cr in contribution_rates:
            weight = cr.percentage / 100.0
            student_scores[cr.program_outcome.code] += grade.score * weight
    
    results = []
    for entry in course_map.values():
        aggregated = defaultdict(list)
        for student_po_scores in entry['student_scores'].values():
            for code, score in student_po_scores.items():
                aggregated[code].append(min(score, 100))
        
        po_scores = {
            code: round(sum(values) / len(values), 2)
            for code, values in aggregated.items()
            if values
        }
        entry['po_scores'] = po_scores
        entry.pop('student_scores', None)
        results.append(entry)
    
    results.sort(key=lambda item: item['course'].code)
    return results


def calculate_course_po_scores(student):
    """
    Course-level PO scores for a single student
    """
    if student.role != 'student':
        return []
    
    grades = (
        Grade.objects.filter(student=student)
        .select_related('course', 'student', 'learning_outcome__course')
        .prefetch_related('learning_outcome__contribution_rates__program_outcome')
    )
    return _aggregate_course_po_scores(grades)


def calculate_instructor_course_po_scores(instructor):
    """
    Average PO performance per course for an instructor's sections
    """
    grades = (
        Grade.objects.filter(course__instructor=instructor)
        .select_related('course', 'student', 'learning_outcome__course')
        .prefetch_related('learning_outcome__contribution_rates__program_outcome')
    )
    return _aggregate_course_po_scores(grades)


def calculate_department_course_po_scores():
    """
    Department-wide course PO performance
    """
    grades = (
        Grade.objects.all()
        .select_related('course', 'course__instructor', 'student', 'learning_outcome__course')
        .prefetch_related('learning_outcome__contribution_rates__program_outcome')
    )
    return _aggregate_course_po_scores(grades)


def build_course_po_distributions(course_ids):
    """
    Return mapping of course_id -> list of PO distributions (LO percentages)
    """
    if not course_ids:
        return {}
    
    distributions = {}
    contribution_rates = (
        ContributionRate.objects
        .filter(learning_outcome__course_id__in=course_ids)
        .select_related('learning_outcome', 'learning_outcome__course', 'program_outcome')
        .order_by('program_outcome__code', 'learning_outcome__description')
    )
    
    for cr in contribution_rates:
        course_id = cr.learning_outcome.course_id
        course_entry = distributions.setdefault(course_id, {})
        po_entry = course_entry.setdefault(cr.program_outcome_id, {
            'program_outcome': {
                'code': cr.program_outcome.code,
                'description': cr.program_outcome.description,
            },
            'learning_outcomes': [],
        })
        po_entry['learning_outcomes'].append({
            'description': cr.learning_outcome.description,
            'percentage': cr.percentage,
        })
    
    # convert nested dicts to lists for easier template iteration
    for course_id, po_dict in distributions.items():
        distributions[course_id] = list(po_dict.values())
    
    return distributions


def get_po_radar_data_for_department():
    """
    Get Program Outcome data for Department Head radar chart.
    Returns average achievement for each PO across the entire department.
    
    Returns:
    dict: {
        'labels': [PO codes],
        'descriptions': [PO descriptions],
        'values': [average scores],
    }
    """
    from .models import ProgramOutcome
    
    # Get department averages
    department_averages = calculate_department_po_averages()
    
    # Get all program outcomes ordered by code
    program_outcomes = ProgramOutcome.objects.all().order_by('code')
    
    labels = []
    descriptions = []
    values = []
    
    for po in program_outcomes:
        labels.append(po.code)
        descriptions.append(po.description)
        values.append(department_averages.get(po.code, 0.0))
    
    return {
        'labels': labels,
        'descriptions': descriptions,
        'values': values,
    }


def get_po_radar_data_for_course(course_id):
    """
    Get Program Outcome data for a specific course.
    
    Args:
        course_id: ID of the course
    
    Returns:
    dict: {
        'labels': [PO codes],
        'descriptions': [PO descriptions],
        'course_values': [course average scores],
        'department_values': [department average scores],
    }
    """
    from .models import ProgramOutcome
    from courses.models import Course
    
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return None
    
    # Get department averages for comparison
    department_averages = calculate_department_po_averages()
    
    # Get course PO scores
    course_po_breakdown = calculate_department_course_po_scores()
    course_data = next((entry for entry in course_po_breakdown if entry['course'].id == course_id), None)
    
    # Get all program outcomes ordered by code
    program_outcomes = ProgramOutcome.objects.all().order_by('code')
    
    labels = []
    descriptions = []
    course_values = []
    department_values = []
    
    for po in program_outcomes:
        labels.append(po.code)
        descriptions.append(po.description)
        
        # Course value
        if course_data and 'po_scores' in course_data:
            course_values.append(course_data['po_scores'].get(po.code, 0.0))
        else:
            course_values.append(0.0)
        
        # Department value
        department_values.append(department_averages.get(po.code, 0.0))
    
    return {
        'labels': labels,
        'descriptions': descriptions,
        'course_values': course_values,
        'department_values': department_values,
        'course_name': f"{course.code} - {course.name}",
    }

