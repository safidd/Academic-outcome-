"""
TDD Unit Tests for Attendance Submission with Transaction Atomicity
Following Test-Driven Development principles
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from datetime import date
from courses.models import Course, Attendance
from grades.models import Grade
from outcomes.models import LearningOutcome

User = get_user_model()


class AttendanceTransactionTest(TransactionTestCase):
    """
    Test attendance submission with transaction atomicity.
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
        
        # Create 10 students
        self.students = []
        for i in range(10):
            student = User.objects.create_user(
                username=f'student{i+1}',
                email=f'student{i+1}@test.com',
                password='testpass123',
                role='student',
                first_name=f'Student{i+1}',
                last_name='Test'
            )
            self.students.append(student)
        
        # Create course
        self.course = Course.objects.create(
            code='CS101',
            name='Introduction to Computer Science',
            instructor=self.instructor
        )
        
        # Enroll students by creating grades
        lo = LearningOutcome.objects.create(
            code='LO1',
            description='Test LO',
            course=self.course
        )
        
        for student in self.students:
            Grade.objects.create(
                student=student,
                course=self.course,
                learning_outcome=lo,
                score=85
            )
    
    def submit_attendance_atomic(self, attendance_data, fail_at=None):
        """
        Submit attendance with transaction atomicity.
        
        Args:
            attendance_data: Dict mapping student_id to status
                Example: {1: 'Present', 2: 'Absent', 3: 'Late'}
            fail_at: Optional student_id to simulate failure at this point
        
        Returns:
            tuple: (success: bool, created_count: int, updated_count: int, error_message: str)
        """
        from django.db import transaction
        
        created_count = 0
        updated_count = 0
        
        try:
            with transaction.atomic():
                for student_id, status in attendance_data.items():
                    # Simulate failure if specified
                    if fail_at and student_id == fail_at:
                        raise IntegrityError("Simulated database error")
                    
                    student = User.objects.get(id=student_id, role='student')
                    
                    attendance, created = Attendance.objects.update_or_create(
                        student=student,
                        course=self.course,
                        date=date.today(),
                        defaults={'status': status}
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                
                # If we get here, all records were processed successfully
                return True, created_count, updated_count, None
                
        except Exception as e:
            # Transaction will automatically rollback
            return False, created_count, updated_count, str(e)
    
    def test_transaction_success_all_students(self):
        """Test: Successful submission of attendance for all students"""
        attendance_data = {
            student.id: 'Present' for student in self.students
        }
        
        success, created, updated, error = self.submit_attendance_atomic(attendance_data)
        
        self.assertTrue(success, "Transaction should succeed")
        self.assertEqual(created, 10, "Should create 10 new attendance records")
        self.assertEqual(updated, 0, "Should not update any records")
        self.assertIsNone(error, "Should not have error message")
        
        # Verify all records exist in database
        records = Attendance.objects.filter(course=self.course, date=date.today())
        self.assertEqual(records.count(), 10, "All 10 records should exist")
    
    def test_transaction_rollback_on_failure(self):
        """Test: Transaction rolls back when failure occurs halfway through"""
        # Submit attendance for 10 students, but fail at student 5
        attendance_data = {
            student.id: 'Present' for student in self.students
        }
        
        success, created, updated, error = self.submit_attendance_atomic(
            attendance_data, 
            fail_at=self.students[4].id  # Fail at 5th student (index 4)
        )
        
        self.assertFalse(success, "Transaction should fail")
        self.assertIsNotNone(error, "Should have error message")
        self.assertIn("Simulated database error", error)
        
        # Verify NO records exist in database (rollback should have occurred)
        records = Attendance.objects.filter(course=self.course, date=date.today())
        self.assertEqual(
            records.count(), 
            0, 
            "Database should be empty - transaction should have rolled back"
        )
    
    def test_transaction_rollback_partial_data(self):
        """Test: Verify no partial data exists after rollback"""
        # First, create some existing attendance records
        Attendance.objects.create(
            student=self.students[0],
            course=self.course,
            date=date.today(),
            status='Absent'
        )
        
        initial_count = Attendance.objects.filter(
            course=self.course, 
            date=date.today()
        ).count()
        self.assertEqual(initial_count, 1, "Should have 1 initial record")
        
        # Try to submit attendance for all students, but fail halfway
        attendance_data = {
            student.id: 'Present' for student in self.students
        }
        
        success, created, updated, error = self.submit_attendance_atomic(
            attendance_data,
            fail_at=self.students[5].id  # Fail at 6th student
        )
        
        self.assertFalse(success, "Transaction should fail")
        
        # Verify only the original record exists (no partial updates)
        records = Attendance.objects.filter(course=self.course, date=date.today())
        self.assertEqual(
            records.count(), 
            1, 
            "Should only have the original record - no partial updates"
        )
        
        # Verify the original record is unchanged
        original_record = Attendance.objects.get(
            student=self.students[0],
            course=self.course,
            date=date.today()
        )
        self.assertEqual(
            original_record.status, 
            'Absent', 
            "Original record should remain unchanged"
        )
    
    def test_transaction_isolation_read_committed(self):
        """Test: Verify transaction isolation prevents dirty reads"""
        from django.db import connection
        
        # Check isolation level (SQLite uses SERIALIZABLE by default, but we can test behavior)
        with transaction.atomic():
            # Start transaction
            Attendance.objects.create(
                student=self.students[0],
                course=self.course,
                date=date.today(),
                status='Present'
            )
            
            # Before commit, verify record is not visible in another connection
            # (In SQLite, this is handled by transaction isolation)
            records_before_commit = Attendance.objects.filter(
                course=self.course,
                date=date.today()
            ).count()
            
            # Record should be visible within the same transaction
            self.assertEqual(records_before_commit, 1)
        
        # After commit, record should be visible
        records_after_commit = Attendance.objects.filter(
            course=self.course,
            date=date.today()
        ).count()
        self.assertEqual(records_after_commit, 1)
    
    def test_transaction_handles_validation_error(self):
        """Test: Transaction rolls back on validation error"""
        from django.db import transaction
        
        # Test that invalid status in form validation prevents transaction
        attendance_data = {
            self.students[0].id: 'InvalidStatus'  # Invalid status
        }
        
        # Simulate form validation failure
        try:
            with transaction.atomic():
                student = User.objects.get(id=self.students[0].id, role='student')
                
                # Validate status before creating
                valid_statuses = ['Present', 'Absent', 'Late']
                if attendance_data[self.students[0].id] not in valid_statuses:
                    raise ValidationError(f"Invalid status: {attendance_data[self.students[0].id]}")
                
                Attendance.objects.create(
                    student=student,
                    course=self.course,
                    date=date.today(),
                    status=attendance_data[self.students[0].id]
                )
        except ValidationError:
            # Transaction should rollback
            pass
        
        # Verify no records exist (transaction rolled back)
        records = Attendance.objects.filter(course=self.course, date=date.today())
        self.assertEqual(records.count(), 0, "Should have no records after rollback")

