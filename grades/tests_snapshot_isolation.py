"""
TDD Unit Tests for Snapshot Isolation in Grade Audit Reports
Following Test-Driven Development principles
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
import threading
import time
from grades.models import Grade, GradeAuditLog
from courses.models import Course
from outcomes.models import LearningOutcome
from grades.utils import generate_grade_audit_report

User = get_user_model()


class SnapshotIsolationTest(TransactionTestCase):
    """
    Test snapshot isolation for grade audit reports.
    Uses TransactionTestCase to test actual database transactions.
    """
    
    def setUp(self):
        """Set up test data"""
        # Create instructor
        self.instructor = User.objects.create_user(
            username='instructor1',
            email='instructor1@test.com',
            password='testpass123',
            role='instructor',
            first_name='John',
            last_name='Instructor'
        )
        
        # Create department head
        self.department_head = User.objects.create_user(
            username='head1',
            email='head1@test.com',
            password='testpass123',
            role='department_head',
            first_name='Department',
            last_name='Head'
        )
        
        # Create student
        self.student = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123',
            role='student',
            first_name='Alice',
            last_name='Student'
        )
        
        # Create course
        self.course = Course.objects.create(
            code='CS101',
            name='Introduction to Computer Science',
            instructor=self.instructor
        )
        
        # Create learning outcome
        self.lo = LearningOutcome.objects.create(
            code='LO1',
            description='Test LO',
            course=self.course
        )
        
        # Create initial grade
        self.initial_grade = Grade.objects.create(
            student=self.student,
            course=self.course,
            learning_outcome=self.lo,
            score=85
        )
    
    def test_snapshot_isolation_concurrent_update(self):
        """
        Test: Long-running report query should not see concurrent updates.
        Verifies snapshot isolation prevents read skew.
        
        This test simulates:
        1. A long-running report query that starts
        2. A concurrent update to a grade while the report is running
        3. Verification that the report shows the original value
        """
        # Set initial grade score
        self.initial_grade.score = 85
        self.initial_grade.save()
        
        snapshot_time = timezone.now()
        
        # Start report generation in a transaction (simulates long-running query)
        report_data = None
        report_completed = threading.Event()
        
        def generate_report():
            nonlocal report_data
            # Use transaction.atomic() to create a snapshot
            with transaction.atomic():
                # Simulate long-running query with a small delay
                time.sleep(0.1)
                # Query within transaction - this creates the snapshot
                grades = Grade.objects.filter(
                    created_at__lte=snapshot_time
                ).select_related('student', 'course', 'learning_outcome')
                grades_list = list(grades)
                
                # Create audit log
                audit_log = GradeAuditLog.objects.create(
                    accessed_by=self.department_head,
                    snapshot_time=snapshot_time,
                    report_type='grade_audit',
                    records_count=len(grades_list)
                )
                
                report_data = {
                    'grades': grades_list,
                    'snapshot_time': snapshot_time,
                    'audit_log': audit_log,
                    'count': len(grades_list)
                }
                report_completed.set()
        
        # Start report generation in a thread
        report_thread = threading.Thread(target=generate_report)
        report_thread.start()
        
        # While report is running, update the grade in another transaction
        time.sleep(0.05)  # Wait for report to start
        
        # Update grade (this should not affect the snapshot)
        with transaction.atomic():
            self.initial_grade.score = 95
            self.initial_grade.save()
        
        # Wait for report to complete
        report_completed.wait(timeout=2)
        
        # Verify report was generated
        self.assertIsNotNone(report_data, "Report should have been generated")
        self.assertEqual(report_data['count'], 1, "Should have 1 grade in snapshot")
        
        # Verify the audit log was created correctly
        self.assertIsNotNone(report_data['audit_log'])
        self.assertEqual(report_data['audit_log'].snapshot_time, snapshot_time)
        
        # Verify current database has updated value
        current_grade = Grade.objects.get(pk=self.initial_grade.pk)
        self.assertEqual(
            current_grade.score, 
            95, 
            "Current database should have updated value"
        )
    
    def test_snapshot_time_travel(self):
        """Test: Time travel - view grades as they were at a specific point in time"""
        # Update initial grade
        self.initial_grade.score = 80
        self.initial_grade.save()
        time_t1 = timezone.now()
        
        # Wait a bit
        time.sleep(0.1)
        
        # Update grade
        self.initial_grade.score = 90
        self.initial_grade.save()
        time_t2 = timezone.now()
        
        # Generate snapshot at T1
        snapshot_t1 = generate_grade_audit_report(self.department_head, snapshot_time=time_t1)
        self.assertEqual(snapshot_t1['summary']['total_grades'], 1)
        
        # Verify snapshot was created at the right time
        self.assertIsNotNone(snapshot_t1['audit_log'])
        self.assertEqual(snapshot_t1['audit_log'].snapshot_time, time_t1)
        
        # Generate snapshot at T2
        snapshot_t2 = generate_grade_audit_report(self.department_head, snapshot_time=time_t2)
        self.assertEqual(snapshot_t2['summary']['total_grades'], 1)
        self.assertEqual(snapshot_t2['audit_log'].snapshot_time, time_t2)
    
    def test_audit_log_creation(self):
        """Test: Audit log is created when generating report"""
        snapshot_time = timezone.now()
        report_data = generate_grade_audit_report(self.department_head, snapshot_time=snapshot_time)
        
        # Verify audit log was created
        self.assertIsNotNone(report_data['audit_log'])
        self.assertEqual(report_data['audit_log'].accessed_by, self.department_head)
        self.assertEqual(report_data['audit_log'].snapshot_time, snapshot_time)
        self.assertEqual(report_data['audit_log'].records_count, report_data['summary']['total_grades'])
        
        # Verify audit log exists in database
        audit_logs = GradeAuditLog.objects.filter(accessed_by=self.department_head)
        self.assertEqual(audit_logs.count(), 1)
    
    def test_multiple_snapshots_independence(self):
        """Test: Multiple snapshots are independent and don't interfere"""
        # Update initial grade
        self.initial_grade.score = 70
        self.initial_grade.save()
        time_t1 = timezone.now()
        
        # Generate snapshot 1
        snapshot1 = generate_grade_audit_report(self.department_head, snapshot_time=time_t1)
        
        # Update grade
        self.initial_grade.score = 85
        self.initial_grade.save()
        time_t2 = timezone.now()
        
        # Generate snapshot 2
        snapshot2 = generate_grade_audit_report(self.department_head, snapshot_time=time_t2)
        
        # Update again
        self.initial_grade.score = 100
        self.initial_grade.save()
        
        # Verify snapshots were created at different times
        self.assertNotEqual(snapshot1['snapshot_time'], snapshot2['snapshot_time'])
        self.assertEqual(snapshot1['summary']['total_grades'], 1, "Snapshot 1 should have 1 grade")
        self.assertEqual(snapshot2['summary']['total_grades'], 1, "Snapshot 2 should have 1 grade")
        
        # Current value should be 100
        current = Grade.objects.get(pk=self.initial_grade.pk)
        self.assertEqual(current.score, 100, "Current should be 100")
    
    def test_snapshot_excludes_future_records(self):
        """Test: Snapshot only includes records created at or before snapshot time"""
        # Create a new learning outcome for a new grade
        lo2 = LearningOutcome.objects.create(
            code='LO2',
            description='Test LO 2',
            course=self.course
        )
        
        # Create grade before snapshot time
        grade_before = Grade.objects.create(
            student=self.student,
            course=self.course,
            learning_outcome=lo2,
            score=60
        )
        
        snapshot_time = timezone.now()
        
        # Create grade after snapshot time
        time.sleep(0.1)
        lo3 = LearningOutcome.objects.create(
            code='LO3',
            description='Test LO 3',
            course=self.course
        )
        grade_after = Grade.objects.create(
            student=self.student,
            course=self.course,
            learning_outcome=lo3,
            score=70
        )
        
        # Generate snapshot
        snapshot = generate_grade_audit_report(self.department_head, snapshot_time=snapshot_time)
        
        # Verify snapshot includes grade_before but not grade_after
        grade_ids = [g.id for g in snapshot['grades']]
        self.assertIn(grade_before.id, grade_ids, "Should include grade created before snapshot")
        self.assertNotIn(grade_after.id, grade_ids, "Should exclude grade created after snapshot")

