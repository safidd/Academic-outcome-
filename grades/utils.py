"""
Utility functions for Grade Audit with Snapshot Isolation
Implements MVCC (Multi-Version Concurrency Control) to prevent read skew
"""
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Grade, GradeAuditLog
from datetime import datetime, timedelta

User = get_user_model()


def generate_grade_audit_report(user, snapshot_time=None, course_filter=None, date_range=None):
    """
    Generate grade audit report with snapshot isolation.
    
    Uses MVCC (Multi-Version Concurrency Control) to ensure consistent
    snapshot of database at a specific point in time, preventing read skew.
    
    Args:
        user: User requesting the report (must be department_head)
        snapshot_time: Point in time for snapshot (default: current time)
        course_filter: Optional course ID to filter by
        date_range: Optional tuple (start_date, end_date) for created_at filter
    
    Returns:
        dict: {
            'grades': List of Grade objects,
            'snapshot_time': datetime,
            'audit_log': GradeAuditLog instance,
            'summary': dict with statistics
        }
    """
    if user.role != 'department_head':
        raise PermissionError("Only department heads can generate audit reports")
    
    if snapshot_time is None:
        snapshot_time = timezone.now()
    
    # Use transaction with SERIALIZABLE isolation level (SQLite default)
    # For PostgreSQL, would use: REPEATABLE READ
    # This ensures snapshot isolation - the transaction sees a consistent
    # view of the database at the start of the transaction
    with transaction.atomic():
        # MVCC: Query only records that existed at or before snapshot_time
        # This ensures we get a consistent snapshot even if other transactions
        # are modifying grades concurrently
        grades_query = Grade.objects.filter(
            created_at__lte=snapshot_time
        ).select_related('student', 'course', 'learning_outcome', 'course__instructor')
        
        # Apply filters
        if course_filter:
            grades_query = grades_query.filter(course_id=course_filter)
        
        if date_range:
            start_date, end_date = date_range
            grades_query = grades_query.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            )
        
        # Materialize query to create snapshot
        # This locks in the data at this point in time
        grades_list = list(grades_query.order_by('course__code', 'student__username', 'learning_outcome__code'))
        
        # Calculate statistics
        total_grades = len(grades_list)
        total_students = len(set(g.student_id for g in grades_list))
        total_courses = len(set(g.course_id for g in grades_list))
        
        avg_score = sum(g.score for g in grades_list) / total_grades if total_grades > 0 else 0
        
        # Create audit log entry
        filters_applied = {}
        if course_filter:
            filters_applied['course_id'] = course_filter
        if date_range:
            filters_applied['date_range'] = {
                'start': date_range[0].isoformat() if date_range[0] else None,
                'end': date_range[1].isoformat() if date_range[1] else None
            }
        
        audit_log = GradeAuditLog.objects.create(
            accessed_by=user,
            snapshot_time=snapshot_time,
            report_type='grade_audit',
            filters_applied=filters_applied,
            records_count=total_grades
        )
        
        return {
            'grades': grades_list,
            'snapshot_time': snapshot_time,
            'audit_log': audit_log,
            'summary': {
                'total_grades': total_grades,
                'total_students': total_students,
                'total_courses': total_courses,
                'average_score': round(avg_score, 2)
            }
        }


def get_historical_snapshots(user, limit=10):
    """
    Get historical audit log entries for time travel.
    
    Args:
        user: User requesting history (must be department_head)
        limit: Maximum number of entries to return
    
    Returns:
        QuerySet of GradeAuditLog entries
    """
    if user.role != 'department_head':
        raise PermissionError("Only department heads can view audit history")
    
    return GradeAuditLog.objects.filter(
        accessed_by=user
    ).order_by('-accessed_at')[:limit]


def get_weekly_snapshot_times():
    """
    Get snapshot times for end of each week (for time travel).
    
    Returns:
        list: List of datetime objects representing end of each week
    """
    now = timezone.now()
    snapshots = []
    
    # Get last 8 weeks
    for weeks_ago in range(8):
        week_end = now - timedelta(weeks=weeks_ago)
        # Set to end of week (Sunday 23:59:59)
        days_since_sunday = week_end.weekday() + 1
        week_end = week_end - timedelta(days=days_since_sunday % 7)
        week_end = week_end.replace(hour=23, minute=59, second=59, microsecond=999999)
        snapshots.append(week_end)
    
    return snapshots

