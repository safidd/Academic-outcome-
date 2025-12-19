from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from .models import Course, Attendance
from grades.models import Grade
from outcomes.models import LearningOutcome

User = get_user_model()


class AttendanceModelTest(TestCase):
    """Test cases for Attendance model"""
    
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
        
        # Create a grade to enroll student in course
        Grade.objects.create(
            student=self.student,
            course=self.course,
            learning_outcome=self.learning_outcome,
            score=85
        )
    
    def test_attendance_creation(self):
        """Test creating an attendance record"""
        attendance = Attendance.objects.create(
            student=self.student,
            course=self.course,
            date=date.today(),
            status='Present'
        )
        self.assertEqual(attendance.student, self.student)
        self.assertEqual(attendance.course, self.course)
        self.assertEqual(attendance.status, 'Present')
    
    def test_attendance_unique_constraint(self):
        """Test that duplicate attendance records are not allowed"""
        Attendance.objects.create(
            student=self.student,
            course=self.course,
            date=date.today(),
            status='Present'
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):  # IntegrityError
            Attendance.objects.create(
                student=self.student,
                course=self.course,
                date=date.today(),
                status='Absent'
            )
    
    def test_attendance_status_choices(self):
        """Test all status choices work"""
        for idx, status in enumerate(['Present', 'Absent', 'Late']):
            attendance = Attendance.objects.create(
                student=self.student,
                course=self.course,
                date=date.today() + timedelta(days=idx+1),
                status=status
            )
            self.assertEqual(attendance.status, status)
    
    def test_attendance_validation_unenrolled_student(self):
        """Test that attendance cannot be created for unenrolled student"""
        # Create another student not enrolled in course
        unenrolled_student = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass123',
            role='student'
        )
        
        attendance = Attendance(
            student=unenrolled_student,
            course=self.course,
            date=date.today(),
            status='Present'
        )
        
        with self.assertRaises(ValidationError):
            attendance.full_clean()


class AttendanceViewTest(TestCase):
    """Test cases for attendance views"""
    
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
            role='student',
            first_name='Test',
            last_name='Student1'
        )
        
        self.student2 = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass123',
            role='student',
            first_name='Test',
            last_name='Student2'
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
    
    def test_instructor_take_attendance_view_requires_login(self):
        """Test that attendance view requires login"""
        response = self.client.get(reverse('instructor:take_attendance', args=[self.course.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_instructor_take_attendance_view_requires_instructor_role(self):
        """Test that only instructors can access attendance view"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('instructor:take_attendance', args=[self.course.id]))
        self.assertEqual(response.status_code, 403)  # Permission denied
    
    def test_instructor_take_attendance_view_shows_students(self):
        """Test that attendance view shows enrolled students"""
        self.client.login(username='instructor1', password='testpass123')
        response = self.client.get(reverse('instructor:take_attendance', args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'student1')
        self.assertContains(response, 'student2')
    
    def test_instructor_submit_attendance(self):
        """Test submitting attendance for multiple students"""
        self.client.login(username='instructor1', password='testpass123')
        
        attendance_date = date.today()
        data = {
            'date': attendance_date.strftime('%Y-%m-%d'),
            f'attendance_{self.student1.id}': 'Present',
            f'attendance_{self.student2.id}': 'Late',
        }
        
        response = self.client.post(
            reverse('instructor:take_attendance', args=[self.course.id]),
            data,
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify attendance records were created
        self.assertEqual(Attendance.objects.count(), 2)
        self.assertEqual(
            Attendance.objects.get(student=self.student1, course=self.course, date=attendance_date).status,
            'Present'
        )
        self.assertEqual(
            Attendance.objects.get(student=self.student2, course=self.course, date=attendance_date).status,
            'Late'
        )
    
    def test_instructor_update_existing_attendance(self):
        """Test updating existing attendance records"""
        attendance_date = date.today()
        
        # Create initial attendance
        Attendance.objects.create(
            student=self.student1,
            course=self.course,
            date=attendance_date,
            status='Absent'
        )
        
        self.client.login(username='instructor1', password='testpass123')
        
        # Update attendance
        data = {
            'date': attendance_date.strftime('%Y-%m-%d'),
            f'attendance_{self.student1.id}': 'Present',
        }
        
        response = self.client.post(
            reverse('instructor:take_attendance', args=[self.course.id]),
            data,
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify attendance was updated
        self.assertEqual(Attendance.objects.count(), 1)
        self.assertEqual(
            Attendance.objects.get(student=self.student1, course=self.course, date=attendance_date).status,
            'Present'
        )
    
    def test_student_view_attendance_requires_login(self):
        """Test that student attendance view requires login"""
        response = self.client.get(reverse('student:attendance'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_student_view_attendance_requires_student_role(self):
        """Test that only students can access their attendance view"""
        self.client.login(username='instructor1', password='testpass123')
        response = self.client.get(reverse('student:attendance'))
        self.assertEqual(response.status_code, 403)  # Permission denied
    
    def test_student_view_attendance_shows_own_records(self):
        """Test that student can view their own attendance"""
        # Create some attendance records
        attendance_date = date.today()
        Attendance.objects.create(
            student=self.student1,
            course=self.course,
            date=attendance_date,
            status='Present'
        )
        Attendance.objects.create(
            student=self.student1,
            course=self.course,
            date=attendance_date - timedelta(days=1),
            status='Late'
        )
        # Create attendance for another student (should not appear)
        Attendance.objects.create(
            student=self.student2,
            course=self.course,
            date=attendance_date,
            status='Absent'
        )
        
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('student:attendance'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Present')
        self.assertContains(response, 'Late')
        # Should not contain other student's attendance
        self.assertNotContains(response, 'student2')
    
    def test_student_attendance_percentage_calculation(self):
        """Test attendance percentage calculation"""
        attendance_date = date.today()
        
        # Create attendance records: 2 Present, 1 Absent, 1 Late = 50% Present
        Attendance.objects.create(
            student=self.student1,
            course=self.course,
            date=attendance_date,
            status='Present'
        )
        Attendance.objects.create(
            student=self.student1,
            course=self.course,
            date=attendance_date - timedelta(days=1),
            status='Present'
        )
        Attendance.objects.create(
            student=self.student1,
            course=self.course,
            date=attendance_date - timedelta(days=2),
            status='Absent'
        )
        Attendance.objects.create(
            student=self.student1,
            course=self.course,
            date=attendance_date - timedelta(days=3),
            status='Late'
        )
        
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('student:attendance'))
        
        self.assertEqual(response.status_code, 200)
        # Should show 50% present (2 out of 4)
        # The template shows attendance_percentage which is (Present + Late) / total = 75%
        # But also shows present_percentage which is Present / total = 50%
        self.assertContains(response, '50')
