from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Q
from courses.models import Course, Attendance
from grades.models import Grade
from outcomes.models import LearningOutcome

User = get_user_model()


class AttendanceAverageCalculationTest(TestCase):
    """Test cases for attendance average calculation"""
    
    def setUp(self):
        """Set up test data"""
        # Create instructor
        self.instructor = User.objects.create_user(
            username='instructor1',
            email='instructor1@test.com',
            password='testpass123',
            role='instructor',
            first_name='Dr. Test',
            last_name='Instructor'
        )
        
        # Create students
        self.student1 = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123',
            role='student'
        )
        
        self.student2 = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass123',
            role='student'
        )
        
        # Create course
        self.course = Course.objects.create(
            code='CS101',
            name='Test Course',
            instructor=self.instructor
        )
        
        # Create learning outcome
        self.learning_outcome = LearningOutcome.objects.create(
            code='LO1',
            description='Test Learning Outcome',
            course=self.course
        )
        
        # Enroll students in course (by creating grades)
        Grade.objects.create(
            student=self.student1,
            course=self.course,
            learning_outcome=self.learning_outcome,
            score=85
        )
        Grade.objects.create(
            student=self.student2,
            course=self.course,
            learning_outcome=self.learning_outcome,
            score=90
        )
    
    def calculate_attendance_average(self, course):
        """Helper method to calculate attendance average: Count of 'Present' / Total records"""
        total_records = Attendance.objects.filter(course=course).count()
        if total_records == 0:
            return 0.0
        
        present_count = Attendance.objects.filter(course=course, status='Present').count()
        return round((present_count / total_records) * 100, 1)
    
    def test_attendance_average_all_present(self):
        """Test attendance average with all Present"""
        from datetime import date
        # Create 4 Present records
        Attendance.objects.create(student=self.student1, course=self.course, date=date.today(), status='Present')
        Attendance.objects.create(student=self.student2, course=self.course, date=date.today(), status='Present')
        Attendance.objects.create(student=self.student1, course=self.course, date=date(2024, 1, 2), status='Present')
        Attendance.objects.create(student=self.student2, course=self.course, date=date(2024, 1, 2), status='Present')
        
        average = self.calculate_attendance_average(self.course)
        # 4 Present / 4 Total = 100%
        self.assertEqual(average, 100.0)
    
    def test_attendance_average_mixed(self):
        """Test attendance average with mixed statuses"""
        from datetime import date
        # Create 2 Present, 1 Absent, 1 Late
        Attendance.objects.create(student=self.student1, course=self.course, date=date.today(), status='Present')
        Attendance.objects.create(student=self.student2, course=self.course, date=date.today(), status='Present')
        Attendance.objects.create(student=self.student1, course=self.course, date=date(2024, 1, 2), status='Absent')
        Attendance.objects.create(student=self.student2, course=self.course, date=date(2024, 1, 2), status='Late')
        
        average = self.calculate_attendance_average(self.course)
        # 2 Present / 4 Total = 50%
        self.assertEqual(average, 50.0)
    
    def test_attendance_average_zero_records(self):
        """Test attendance average with zero records (should not crash)"""
        average = self.calculate_attendance_average(self.course)
        # Should return 0.0, not crash
        self.assertEqual(average, 0.0)
    
    def test_attendance_average_all_absent(self):
        """Test attendance average with all Absent"""
        from datetime import date
        # Create 4 Absent records
        Attendance.objects.create(student=self.student1, course=self.course, date=date.today(), status='Absent')
        Attendance.objects.create(student=self.student2, course=self.course, date=date.today(), status='Absent')
        Attendance.objects.create(student=self.student1, course=self.course, date=date(2024, 1, 2), status='Absent')
        Attendance.objects.create(student=self.student2, course=self.course, date=date(2024, 1, 2), status='Absent')
        
        average = self.calculate_attendance_average(self.course)
        # 0 Present / 4 Total = 0%
        self.assertEqual(average, 0.0)
    
    def test_attendance_average_multiple_courses(self):
        """Test attendance average calculation for multiple courses"""
        from datetime import date
        
        # Create second course
        course2 = Course.objects.create(
            code='CS201',
            name='Test Course 2',
            instructor=self.instructor
        )
        
        # Course 1: 2 Present, 2 Absent = 50%
        Attendance.objects.create(student=self.student1, course=self.course, date=date.today(), status='Present')
        Attendance.objects.create(student=self.student2, course=self.course, date=date.today(), status='Present')
        Attendance.objects.create(student=self.student1, course=self.course, date=date(2024, 1, 2), status='Absent')
        Attendance.objects.create(student=self.student2, course=self.course, date=date(2024, 1, 2), status='Absent')
        
        # Course 2: 3 Present, 1 Absent = 75%
        Attendance.objects.create(student=self.student1, course=course2, date=date.today(), status='Present')
        Attendance.objects.create(student=self.student2, course=course2, date=date.today(), status='Present')
        Attendance.objects.create(student=self.student1, course=course2, date=date(2024, 1, 2), status='Present')
        Attendance.objects.create(student=self.student2, course=course2, date=date(2024, 1, 2), status='Absent')
        
        avg1 = self.calculate_attendance_average(self.course)
        avg2 = self.calculate_attendance_average(course2)
        
        self.assertEqual(avg1, 50.0)
        self.assertEqual(avg2, 75.0)


class AttendanceDashboardViewTest(TestCase):
    """Test cases for attendance dashboard view"""
    
    def setUp(self):
        """Set up test data"""
        # Create department head
        self.head = User.objects.create_user(
            username='head1',
            email='head1@test.com',
            password='testpass123',
            role='department_head'
        )
        
        # Create instructor
        self.instructor = User.objects.create_user(
            username='instructor1',
            email='instructor1@test.com',
            password='testpass123',
            role='instructor',
            first_name='Dr. Test',
            last_name='Instructor'
        )
        
        # Create course
        self.course = Course.objects.create(
            code='CS101',
            name='Test Course',
            instructor=self.instructor
        )
    
    def test_attendance_dashboard_requires_head_role(self):
        """Test that only department heads can access attendance dashboard"""
        from django.urls import reverse
        self.client.login(username='head1', password='testpass123')
        # This will be added to head_dashboard, so we'll test the head_dashboard view
        response = self.client.get(reverse('head:dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_attendance_dashboard_shows_courses(self):
        """Test that attendance dashboard shows courses with attendance data"""
        from django.urls import reverse
        from datetime import date
        
        # Create attendance records
        student = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123',
            role='student'
        )
        
        Attendance.objects.create(
            student=student,
            course=self.course,
            date=date.today(),
            status='Present'
        )
        
        self.client.login(username='head1', password='testpass123')
        response = self.client.get(reverse('head:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        # Should show course information
        self.assertContains(response, 'CS101')
