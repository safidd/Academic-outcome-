"""
TDD Unit Tests for Course Attendance Aggregation
Following Test-Driven Development principles
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from datetime import date
from courses.models import Course, Attendance
from grades.models import Grade
from outcomes.models import LearningOutcome

User = get_user_model()


class CourseAttendanceAggregationTest(TestCase):
    """Test attendance average calculation per course"""
    
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
        
        self.student3 = User.objects.create_user(
            username='student3',
            email='student3@test.com',
            password='testpass123',
            role='student',
            first_name='Charlie',
            last_name='Student'
        )
        
        # Create courses
        self.course1 = Course.objects.create(
            code='CS101',
            name='Introduction to Computer Science',
            instructor=self.instructor
        )
        
        self.course2 = Course.objects.create(
            code='CS102',
            name='Data Structures',
            instructor=self.instructor
        )
        
        # Create learning outcomes for enrollment
        self.lo1 = LearningOutcome.objects.create(
            code='LO1',
            description='Test LO',
            course=self.course1
        )
        
        self.lo2 = LearningOutcome.objects.create(
            code='LO1',
            description='Test LO',
            course=self.course2
        )
        
        # Enroll students by creating grades
        Grade.objects.create(student=self.student1, course=self.course1, learning_outcome=self.lo1, score=85)
        Grade.objects.create(student=self.student2, course=self.course1, learning_outcome=self.lo1, score=90)
        Grade.objects.create(student=self.student3, course=self.course1, learning_outcome=self.lo1, score=75)
        
        Grade.objects.create(student=self.student1, course=self.course2, learning_outcome=self.lo2, score=80)
        Grade.objects.create(student=self.student2, course=self.course2, learning_outcome=self.lo2, score=85)
    
    def calculate_course_attendance_average(self, course):
        """
        Calculate average attendance rate for a course.
        Formula: (Count of 'Present') / Total attendance records
        
        Args:
            course: Course instance
        
        Returns:
            float: Average attendance percentage (0-100), rounded to 1 decimal place
        """
        attendance_records = Attendance.objects.filter(course=course)
        
        if not attendance_records.exists():
            return 0.0
        
        total_records = attendance_records.count()
        present_count = attendance_records.filter(status='Present').count()
        
        # Calculate percentage: (Present / Total) * 100
        percentage = (present_count / total_records) * 100
        return round(percentage, 1)
    
    def test_course_with_all_present(self):
        """Test: Course with all students present should return 100%"""
        today = date.today()
        
        # Create attendance records - all Present
        Attendance.objects.create(student=self.student1, course=self.course1, date=today, status='Present')
        Attendance.objects.create(student=self.student2, course=self.course1, date=today, status='Present')
        Attendance.objects.create(student=self.student3, course=self.course1, date=today, status='Present')
        
        result = self.calculate_course_attendance_average(self.course1)
        self.assertEqual(result, 100.0, "All Present should equal 100%")
    
    def test_course_with_mixed_statuses(self):
        """Test: Course with mixed Present/Absent/Late should calculate correctly"""
        today = date.today()
        
        # Create attendance: 2 Present, 1 Absent
        Attendance.objects.create(student=self.student1, course=self.course1, date=today, status='Present')
        Attendance.objects.create(student=self.student2, course=self.course1, date=today, status='Present')
        Attendance.objects.create(student=self.student3, course=self.course1, date=today, status='Absent')
        
        result = self.calculate_course_attendance_average(self.course1)
        # (2 Present / 3 Total) * 100 = 66.7%
        self.assertEqual(result, 66.7, "2 Present out of 3 should equal 66.7%")
    
    def test_course_with_zero_attendance(self):
        """Test: Course with no attendance records should return 0% (handle divide-by-zero)"""
        result = self.calculate_course_attendance_average(self.course2)
        self.assertEqual(result, 0.0, "No attendance records should return 0% without error")
    
    def test_course_with_multiple_dates(self):
        """Test: Calculate average across multiple dates"""
        today = date.today()
        yesterday = today.replace(day=today.day - 1) if today.day > 1 else today.replace(month=today.month - 1, day=28)
        
        # Day 1: 2 Present, 1 Absent
        Attendance.objects.create(student=self.student1, course=self.course1, date=yesterday, status='Present')
        Attendance.objects.create(student=self.student2, course=self.course1, date=yesterday, status='Present')
        Attendance.objects.create(student=self.student3, course=self.course1, date=yesterday, status='Absent')
        
        # Day 2: All Present
        Attendance.objects.create(student=self.student1, course=self.course1, date=today, status='Present')
        Attendance.objects.create(student=self.student2, course=self.course1, date=today, status='Present')
        Attendance.objects.create(student=self.student3, course=self.course1, date=today, status='Present')
        
        # Total: 5 Present out of 6 records = 83.3%
        result = self.calculate_course_attendance_average(self.course1)
        self.assertEqual(result, 83.3, "5 Present out of 6 should equal 83.3%")
    
    def test_course_with_all_absent(self):
        """Test: Course with all Absent should return 0%"""
        today = date.today()
        
        Attendance.objects.create(student=self.student1, course=self.course1, date=today, status='Absent')
        Attendance.objects.create(student=self.student2, course=self.course1, date=today, status='Absent')
        Attendance.objects.create(student=self.student3, course=self.course1, date=today, status='Absent')
        
        result = self.calculate_course_attendance_average(self.course1)
        self.assertEqual(result, 0.0, "All Absent should equal 0%")
    
    def test_multiple_courses_aggregation(self):
        """Test: Calculate averages for multiple courses"""
        today = date.today()
        
        # Course 1: 2 Present, 1 Absent = 66.7%
        Attendance.objects.create(student=self.student1, course=self.course1, date=today, status='Present')
        Attendance.objects.create(student=self.student2, course=self.course1, date=today, status='Present')
        Attendance.objects.create(student=self.student3, course=self.course1, date=today, status='Absent')
        
        # Course 2: All Present = 100%
        Attendance.objects.create(student=self.student1, course=self.course2, date=today, status='Present')
        Attendance.objects.create(student=self.student2, course=self.course2, date=today, status='Present')
        
        result1 = self.calculate_course_attendance_average(self.course1)
        result2 = self.calculate_course_attendance_average(self.course2)
        
        self.assertEqual(result1, 66.7, "Course 1 should be 66.7%")
        self.assertEqual(result2, 100.0, "Course 2 should be 100%")
    
    def test_course_with_late_status(self):
        """Test: Late status is counted as Absent for average calculation"""
        today = date.today()
        
        # 1 Present, 1 Late, 1 Absent
        Attendance.objects.create(student=self.student1, course=self.course1, date=today, status='Present')
        Attendance.objects.create(student=self.student2, course=self.course1, date=today, status='Late')
        Attendance.objects.create(student=self.student3, course=self.course1, date=today, status='Absent')
        
        # Formula: Present / Total = 1/3 = 33.3%
        result = self.calculate_course_attendance_average(self.course1)
        self.assertEqual(result, 33.3, "1 Present out of 3 should equal 33.3%")

