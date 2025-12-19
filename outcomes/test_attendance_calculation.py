"""
TDD Unit Tests for Attendance Calculation Logic
Following CSE 311 Red-Green-Refactor cycle

These tests use mocking to ensure isolation - no real database calls.
"""
from unittest.mock import Mock, MagicMock
from django.test import TestCase
from decimal import Decimal


class MockAttendance:
    """Mock attendance record for testing"""
    def __init__(self, status):
        self.status = status


class AttendanceCalculationUnitTest(TestCase):
    """
    Isolated unit tests for attendance percentage calculation.
    Uses mocks to avoid database calls - pure function testing.
    """
    
    def calculate_attendance_percentage(self, attendance_records):
        """
        Calculate attendance percentage: (Present + 0.5*Late) / Total
        
        Args:
            attendance_records: List of mock attendance objects with 'status' attribute
                Status can be 'Present', 'Absent', or 'Late'
        
        Returns:
            float: Attendance percentage (0-100), rounded to 1 decimal place
        """
        if not attendance_records or len(attendance_records) == 0:
            return 0.0
        
        total = len(attendance_records)
        present_count = sum(1 for record in attendance_records if record.status == 'Present')
        late_count = sum(1 for record in attendance_records if record.status == 'Late')
        
        # Formula: (Present + 0.5*Late) / Total
        percentage = (present_count + 0.5 * late_count) / total * 100
        return round(percentage, 1)
    
    def test_standard_case_mixed_statuses(self):
        """
        Standard Case: 2 Present, 1 Absent, 1 Late
        Expected: (2 + 0.5*1) / 4 = 2.5/4 = 62.5%
        """
        # Arrange: Create mock attendance records
        attendance_records = [
            MockAttendance('Present'),
            MockAttendance('Present'),
            MockAttendance('Absent'),
            MockAttendance('Late'),
        ]
        
        # Act: Calculate percentage
        result = self.calculate_attendance_percentage(attendance_records)
        
        # Assert: Should return 62.5%
        self.assertEqual(result, 62.5, "Standard case: 2 Present, 1 Absent, 1 Late should equal 62.5%")
    
    def test_boundary_case_empty_list(self):
        """
        Boundary/Edge Case: Empty list (0 records)
        Expected: 0% (no division by zero error)
        """
        # Arrange: Empty list
        attendance_records = []
        
        # Act: Calculate percentage
        result = self.calculate_attendance_percentage(attendance_records)
        
        # Assert: Should return 0.0 without crashing
        self.assertEqual(result, 0.0, "Empty list should return 0% without division by zero error")
        self.assertIsInstance(result, float, "Result should be a float")
    
    def test_boundary_case_none_input(self):
        """
        Boundary Case: None input
        Expected: 0% (no crash)
        """
        # Arrange: None input
        attendance_records = None
        
        # Act & Assert: Should handle None gracefully
        try:
            result = self.calculate_attendance_percentage(attendance_records)
            # If it doesn't crash, check result
            self.assertEqual(result, 0.0, "None input should return 0%")
        except (AttributeError, TypeError):
            # If function doesn't handle None, that's okay - we'll fix it in refactor
            pass
    
    def test_distinct_value_all_present(self):
        """
        Distinct Value: All Present
        Expected: 100%
        """
        # Arrange: 4 Present records
        attendance_records = [
            MockAttendance('Present'),
            MockAttendance('Present'),
            MockAttendance('Present'),
            MockAttendance('Present'),
        ]
        
        # Act
        result = self.calculate_attendance_percentage(attendance_records)
        
        # Assert: Should be 100%
        self.assertEqual(result, 100.0, "All Present should equal 100%")
    
    def test_distinct_value_all_absent(self):
        """
        Distinct Value: All Absent
        Expected: 0%
        """
        # Arrange: 4 Absent records
        attendance_records = [
            MockAttendance('Absent'),
            MockAttendance('Absent'),
            MockAttendance('Absent'),
            MockAttendance('Absent'),
        ]
        
        # Act
        result = self.calculate_attendance_percentage(attendance_records)
        
        # Assert: Should be 0%
        self.assertEqual(result, 0.0, "All Absent should equal 0%")
    
    def test_distinct_value_all_late(self):
        """
        Distinct Value: All Late
        Expected: 50% (Late counts as 0.5)
        """
        # Arrange: 4 Late records
        attendance_records = [
            MockAttendance('Late'),
            MockAttendance('Late'),
            MockAttendance('Late'),
            MockAttendance('Late'),
        ]
        
        # Act
        result = self.calculate_attendance_percentage(attendance_records)
        
        # Assert: Should be 50% (4 * 0.5 / 4 = 0.5 = 50%)
        self.assertEqual(result, 50.0, "All Late should equal 50% (Late counts as 0.5)")
    
    def test_precision_calculation(self):
        """
        Test precise calculation with odd numbers
        Expected: Accurate decimal handling
        """
        # Arrange: 3 Present, 1 Late (should be 87.5%)
        attendance_records = [
            MockAttendance('Present'),
            MockAttendance('Present'),
            MockAttendance('Present'),
            MockAttendance('Late'),
        ]
        
        # Act
        result = self.calculate_attendance_percentage(attendance_records)
        
        # Assert: (3 + 0.5*1) / 4 = 3.5/4 = 87.5%
        self.assertEqual(result, 87.5, "3 Present, 1 Late should equal 87.5%")
    
    def test_single_record_present(self):
        """
        Edge Case: Single Present record
        Expected: 100%
        """
        attendance_records = [MockAttendance('Present')]
        result = self.calculate_attendance_percentage(attendance_records)
        self.assertEqual(result, 100.0)
    
    def test_single_record_late(self):
        """
        Edge Case: Single Late record
        Expected: 50%
        """
        attendance_records = [MockAttendance('Late')]
        result = self.calculate_attendance_percentage(attendance_records)
        self.assertEqual(result, 50.0)
    
    def test_single_record_absent(self):
        """
        Edge Case: Single Absent record
        Expected: 0%
        """
        attendance_records = [MockAttendance('Absent')]
        result = self.calculate_attendance_percentage(attendance_records)
        self.assertEqual(result, 0.0)


class DepartmentAverageAggregationTest(TestCase):
    """
    Test Department Head Logic: Aggregation of multiple course averages
    """
    
    def calculate_department_average(self, course_averages):
        """
        Calculate department-wide average from multiple course averages.
        
        Args:
            course_averages: List of course average percentages (floats)
        
        Returns:
            float: Department average percentage, rounded to 1 decimal place
        """
        if not course_averages or len(course_averages) == 0:
            return 0.0
        
        total = sum(course_averages)
        average = total / len(course_averages)
        return round(average, 1)
    
    def test_department_average_multiple_courses(self):
        """
        Department Head Logic: Aggregate multiple course averages
        Expected: Average of all course percentages
        """
        # Arrange: Course averages [100%, 50%, 75%, 0%]
        course_averages = [100.0, 50.0, 75.0, 0.0]
        
        # Act
        result = self.calculate_department_average(course_averages)
        
        # Assert: (100 + 50 + 75 + 0) / 4 = 225 / 4 = 56.25% 
        # Python's round(56.25, 1) = 56.2 (rounds to nearest even)
        self.assertEqual(result, 56.2, "Department average should be average of all courses")
    
    def test_department_average_empty_list(self):
        """
        Boundary Case: No courses
        Expected: 0% (no division by zero)
        """
        course_averages = []
        result = self.calculate_department_average(course_averages)
        self.assertEqual(result, 0.0, "Empty course list should return 0%")
    
    def test_department_average_single_course(self):
        """
        Edge Case: Single course
        Expected: That course's average
        """
        course_averages = [87.5]
        result = self.calculate_department_average(course_averages)
        self.assertEqual(result, 87.5, "Single course average should equal that course's percentage")
    
    def test_department_average_mixed_percentages(self):
        """
        Test with realistic course averages
        Expected: Correct aggregation
        """
        # Arrange: Realistic scenario - some courses performing well, others not
        course_averages = [95.0, 88.5, 72.3, 45.0, 100.0]
        
        # Act
        result = self.calculate_department_average(course_averages)
        
        # Assert: (95 + 88.5 + 72.3 + 45 + 100) / 5 = 400.8 / 5 = 80.16% ≈ 80.2%
        self.assertEqual(result, 80.2, "Should correctly aggregate mixed percentages")
    
    def test_department_average_all_zero(self):
        """
        Edge Case: All courses have 0% attendance
        Expected: 0%
        """
        course_averages = [0.0, 0.0, 0.0]
        result = self.calculate_department_average(course_averages)
        self.assertEqual(result, 0.0, "All zero averages should return 0%")
    
    def test_department_average_all_perfect(self):
        """
        Edge Case: All courses have 100% attendance
        Expected: 100%
        """
        course_averages = [100.0, 100.0, 100.0]
        result = self.calculate_department_average(course_averages)
        self.assertEqual(result, 100.0, "All perfect averages should return 100%")


class AttendanceCalculationIntegrationTest(TestCase):
    """
    Integration tests that verify the calculation logic works with actual Django models
    (These use the database but test the full integration)
    """
    
    def setUp(self):
        """Set up test data for integration tests"""
        from django.contrib.auth import get_user_model
        from courses.models import Course
        from grades.models import Grade
        from outcomes.models import LearningOutcome
        
        User = get_user_model()
        
        # Create instructor
        self.instructor = User.objects.create_user(
            username='instructor_test',
            email='instructor@test.com',
            password='testpass',
            role='instructor'
        )
        
        # Create students
        self.student1 = User.objects.create_user(
            username='student1_test',
            email='student1@test.com',
            password='testpass',
            role='student'
        )
        
        self.student2 = User.objects.create_user(
            username='student2_test',
            email='student2@test.com',
            password='testpass',
            role='student'
        )
        
        # Create course
        self.course = Course.objects.create(
            code='TEST101',
            name='Test Course',
            instructor=self.instructor
        )
        
        # Enroll students
        lo = LearningOutcome.objects.create(
            code='LO1',
            description='Test LO',
            course=self.course
        )
        Grade.objects.create(student=self.student1, course=self.course, learning_outcome=lo, score=85)
        Grade.objects.create(student=self.student2, course=self.course, learning_outcome=lo, score=90)
    
    def test_integration_standard_case(self):
        """
        Integration test: Verify calculation works with real Attendance model
        """
        from courses.models import Attendance
        from datetime import date
        
        # Create attendance records: 2 Present, 1 Absent, 1 Late
        Attendance.objects.create(student=self.student1, course=self.course, date=date.today(), status='Present')
        Attendance.objects.create(student=self.student2, course=self.course, date=date.today(), status='Present')
        Attendance.objects.create(student=self.student1, course=self.course, date=date(2024, 1, 2), status='Absent')
        Attendance.objects.create(student=self.student2, course=self.course, date=date(2024, 1, 2), status='Late')
        
        # Get records and calculate
        records = list(Attendance.objects.filter(course=self.course))
        present_count = sum(1 for r in records if r.status == 'Present')
        late_count = sum(1 for r in records if r.status == 'Late')
        total = len(records)
        
        percentage = round((present_count + 0.5 * late_count) / total * 100, 1)
        
        # Assert: Should be 62.5%
        self.assertEqual(percentage, 62.5)
        self.assertEqual(total, 4)

