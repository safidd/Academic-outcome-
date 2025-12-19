from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date, timedelta
from courses.models import Course, Attendance
from grades.models import Grade
from outcomes.models import LearningOutcome

User = get_user_model()


class AttendancePercentageCalculationTest(TestCase):
    """Test cases for attendance percentage calculation"""
    
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
        
        # Create student
        self.student = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123',
            role='student',
            first_name='Test',
            last_name='Student'
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
        
        # Enroll student in course (by creating a grade)
        Grade.objects.create(
            student=self.student,
            course=self.course,
            learning_outcome=self.learning_outcome,
            score=85
        )
    
    def calculate_attendance_percentage(self, attendances):
        """Helper method to calculate attendance percentage: (Present + 0.5*Late) / Total"""
        if not attendances:
            return 0.0
        
        total = len(attendances)
        present_count = sum(1 for att in attendances if att.status == 'Present')
        late_count = sum(1 for att in attendances if att.status == 'Late')
        
        # Formula: (Present + 0.5*Late) / Total
        percentage = (present_count + 0.5 * late_count) / total * 100
        return round(percentage, 1)
    
    def test_attendance_percentage_all_present(self):
        """Test attendance percentage with all Present"""
        # Create 4 Present records
        for i in range(4):
            Attendance.objects.create(
                student=self.student,
                course=self.course,
                date=date.today() - timedelta(days=i),
                status='Present'
            )
        
        attendances = Attendance.objects.filter(student=self.student, course=self.course)
        percentage = self.calculate_attendance_percentage(list(attendances))
        
        # (4 + 0.5*0) / 4 = 100%
        self.assertEqual(percentage, 100.0)
    
    def test_attendance_percentage_all_absent(self):
        """Test attendance percentage with all Absent"""
        # Create 4 Absent records
        for i in range(4):
            Attendance.objects.create(
                student=self.student,
                course=self.course,
                date=date.today() - timedelta(days=i),
                status='Absent'
            )
        
        attendances = Attendance.objects.filter(student=self.student, course=self.course)
        percentage = self.calculate_attendance_percentage(list(attendances))
        
        # (0 + 0.5*0) / 4 = 0%
        self.assertEqual(percentage, 0.0)
    
    def test_attendance_percentage_mixed(self):
        """Test attendance percentage with mixed statuses"""
        # Create 2 Present, 2 Late, 2 Absent
        Attendance.objects.create(student=self.student, course=self.course, date=date.today(), status='Present')
        Attendance.objects.create(student=self.student, course=self.course, date=date.today() - timedelta(days=1), status='Present')
        Attendance.objects.create(student=self.student, course=self.course, date=date.today() - timedelta(days=2), status='Late')
        Attendance.objects.create(student=self.student, course=self.course, date=date.today() - timedelta(days=3), status='Late')
        Attendance.objects.create(student=self.student, course=self.course, date=date.today() - timedelta(days=4), status='Absent')
        Attendance.objects.create(student=self.student, course=self.course, date=date.today() - timedelta(days=5), status='Absent')
        
        attendances = Attendance.objects.filter(student=self.student, course=self.course)
        percentage = self.calculate_attendance_percentage(list(attendances))
        
        # (2 + 0.5*2) / 6 = 3/6 = 50%
        self.assertEqual(percentage, 50.0)
    
    def test_attendance_percentage_all_late(self):
        """Test attendance percentage with all Late"""
        # Create 4 Late records
        for i in range(4):
            Attendance.objects.create(
                student=self.student,
                course=self.course,
                date=date.today() - timedelta(days=i),
                status='Late'
            )
        
        attendances = Attendance.objects.filter(student=self.student, course=self.course)
        percentage = self.calculate_attendance_percentage(list(attendances))
        
        # (0 + 0.5*4) / 4 = 2/4 = 50%
        self.assertEqual(percentage, 50.0)
    
    def test_attendance_percentage_zero_classes(self):
        """Test attendance percentage with zero classes (should not crash)"""
        attendances = Attendance.objects.filter(student=self.student, course=self.course)
        percentage = self.calculate_attendance_percentage(list(attendances))
        
        # Should return 0.0, not crash
        self.assertEqual(percentage, 0.0)
    
    def test_attendance_percentage_precise_calculation(self):
        """Test precise percentage calculation"""
        # Create 3 Present, 1 Late (should be 87.5%)
        Attendance.objects.create(student=self.student, course=self.course, date=date.today(), status='Present')
        Attendance.objects.create(student=self.student, course=self.course, date=date.today() - timedelta(days=1), status='Present')
        Attendance.objects.create(student=self.student, course=self.course, date=date.today() - timedelta(days=2), status='Present')
        Attendance.objects.create(student=self.student, course=self.course, date=date.today() - timedelta(days=3), status='Late')
        
        attendances = Attendance.objects.filter(student=self.student, course=self.course)
        percentage = self.calculate_attendance_percentage(list(attendances))
        
        # (3 + 0.5*1) / 4 = 3.5/4 = 87.5%
        self.assertEqual(percentage, 87.5)


class StudentAttendanceViewTest(TestCase):
    """Test cases for student attendance view"""
    
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
        
        # Create student
        self.student = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123',
            role='student',
            first_name='Test',
            last_name='Student'
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
        
        # Enroll student in course
        Grade.objects.create(
            student=self.student,
            course=self.course,
            learning_outcome=self.learning_outcome,
            score=85
        )
    
    def test_attendance_view_shows_course_summary(self):
        """Test that attendance view shows course summary cards"""
        # Create attendance records
        Attendance.objects.create(
            student=self.student,
            course=self.course,
            date=date.today(),
            status='Present'
        )
        Attendance.objects.create(
            student=self.student,
            course=self.course,
            date=date.today() - timedelta(days=1),
            status='Late'
        )
        
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('student:attendance'))
        
        self.assertEqual(response.status_code, 200)
        # Should show course name
        self.assertContains(response, 'CS101')
        self.assertContains(response, 'Test Course')
        # Should show instructor name
        self.assertContains(response, 'Dr. Test')
    
    def test_attendance_view_calculates_percentage_per_course(self):
        """Test that attendance percentage is calculated per course"""
        # Create attendance: 2 Present, 1 Late, 1 Absent
        Attendance.objects.create(student=self.student, course=self.course, date=date.today(), status='Present')
        Attendance.objects.create(student=self.student, course=self.course, date=date.today() - timedelta(days=1), status='Present')
        Attendance.objects.create(student=self.student, course=self.course, date=date.today() - timedelta(days=2), status='Late')
        Attendance.objects.create(student=self.student, course=self.course, date=date.today() - timedelta(days=3), status='Absent')
        
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('student:attendance'))
        
        self.assertEqual(response.status_code, 200)
        # Should show percentage: (2 + 0.5*1) / 4 = 62.5%
        self.assertContains(response, '62.5')
    
    def test_attendance_view_handles_zero_records(self):
        """Test that view handles zero attendance records without crashing"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('student:attendance'))
        
        self.assertEqual(response.status_code, 200)
        # Should show 0% or handle gracefully
        self.assertContains(response, '0')
