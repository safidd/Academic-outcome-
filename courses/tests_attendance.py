"""
TDD Unit Tests for Attendance Submission Logic
Following Test-Driven Development principles
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from .models import Course, Attendance

User = get_user_model()


class AttendanceSubmissionTest(TestCase):
    """Test attendance submission logic"""
    
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
        
        # Create students
        self.student1 = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123',
            role='student',
            first_name='Alice',
            last_name='Student'
        )
        
        self.student2 = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass123',
            role='student',
            first_name='Bob',
            last_name='Student'
        )
        
        # Create course
        self.course = Course.objects.create(
            code='CS101',
            name='Introduction to Computer Science',
            instructor=self.instructor
        )
    
    def test_submit_attendance_single_student_present(self):
        """Test: Submit attendance for a single student with Present status"""
        attendance = Attendance.objects.create(
            student=self.student1,
            course=self.course,
            date=date.today(),
            status='Present'
        )
        
        self.assertEqual(attendance.student, self.student1)
        self.assertEqual(attendance.course, self.course)
        self.assertEqual(attendance.status, 'Present')
        self.assertEqual(attendance.date, date.today())
    
    def test_submit_attendance_multiple_students(self):
        """Test: Submit attendance for multiple students with different statuses"""
        today = date.today()
        
        # Create attendance records
        Attendance.objects.create(
            student=self.student1,
            course=self.course,
            date=today,
            status='Present'
        )
        
        Attendance.objects.create(
            student=self.student2,
            course=self.course,
            date=today,
            status='Late'
        )
        
        # Verify both records exist
        records = Attendance.objects.filter(course=self.course, date=today)
        self.assertEqual(records.count(), 2)
        
        # Verify statuses
        self.assertEqual(records.get(student=self.student1).status, 'Present')
        self.assertEqual(records.get(student=self.student2).status, 'Late')
    
    def test_submit_attendance_update_existing(self):
        """Test: Update existing attendance record (bulk INSERT/UPDATE)"""
        today = date.today()
        
        # Create initial attendance
        attendance = Attendance.objects.create(
            student=self.student1,
            course=self.course,
            date=today,
            status='Absent'
        )
        
        # Update to Present
        attendance.status = 'Present'
        attendance.save()
        
        # Verify update
        updated = Attendance.objects.get(student=self.student1, course=self.course, date=today)
        self.assertEqual(updated.status, 'Present')
    
    def test_submit_attendance_unique_constraint(self):
        """Test: Prevent duplicate attendance records for same student/course/date"""
        today = date.today()
        
        # Create first attendance
        Attendance.objects.create(
            student=self.student1,
            course=self.course,
            date=today,
            status='Present'
        )
        
        # Try to create duplicate - should raise IntegrityError
        with self.assertRaises(Exception):  # IntegrityError or ValidationError
            Attendance.objects.create(
                student=self.student1,
                course=self.course,
                date=today,
                status='Absent'
            )
    
    def test_submit_attendance_different_dates(self):
        """Test: Same student can have attendance on different dates"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        Attendance.objects.create(
            student=self.student1,
            course=self.course,
            date=yesterday,
            status='Present'
        )
        
        Attendance.objects.create(
            student=self.student1,
            course=self.course,
            date=today,
            status='Absent'
        )
        
        # Both records should exist
        records = Attendance.objects.filter(
            student=self.student1,
            course=self.course
        )
        self.assertEqual(records.count(), 2)
    
    def test_submit_attendance_invalid_status(self):
        """Test: Only valid status values are accepted"""
        # Django will raise ValidationError for invalid choice
        with self.assertRaises(Exception):
            Attendance.objects.create(
                student=self.student1,
                course=self.course,
                date=date.today(),
                status='InvalidStatus'
            )
    
    def test_get_enrolled_students(self):
        """Test: Get enrolled students for a course"""
        # Initially no enrolled students
        enrolled = self.course.get_enrolled_students()
        self.assertEqual(enrolled.count(), 0)
        
        # After creating grades, students are enrolled
        from grades.models import Grade
        from outcomes.models import LearningOutcome
        
        lo = LearningOutcome.objects.create(
            code='LO1',
            description='Test LO',
            course=self.course
        )
        
        Grade.objects.create(
            student=self.student1,
            course=self.course,
            learning_outcome=lo,
            score=85
        )
        
        Grade.objects.create(
            student=self.student2,
            course=self.course,
            learning_outcome=lo,
            score=90
        )
        
        # Now should have 2 enrolled students
        enrolled = self.course.get_enrolled_students()
        self.assertEqual(enrolled.count(), 2)
        self.assertIn(self.student1, enrolled)
        self.assertIn(self.student2, enrolled)

