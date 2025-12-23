"""
TDD Unit Tests for Offline Attendance Synchronization
Following Test-Driven Development principles
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import json
from datetime import date
from courses.models import Course, Attendance
from grades.models import Grade
from outcomes.models import LearningOutcome

User = get_user_model()


class OfflineSyncTest(TestCase):
    """Test offline sync functionality"""
    
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
        
        # Enroll students
        lo = LearningOutcome.objects.create(
            code='LO1',
            description='Test LO',
            course=self.course
        )
        
        Grade.objects.create(student=self.student1, course=self.course, learning_outcome=lo, score=85)
        Grade.objects.create(student=self.student2, course=self.course, learning_outcome=lo, score=90)
    
    def test_sync_api_idempotent_duplicate_submission(self):
        """Test: API handles duplicate submissions gracefully (idempotency)"""
        client = Client()
        client.force_login(self.instructor)
        
        attendance_data = {
            str(self.student1.id): 'Present',
            str(self.student2.id): 'Late'
        }
        
        # First submission
        response1 = client.post(
            reverse('instructor:sync_attendance_api'),
            data=json.dumps({
                'course': self.course.id,
                'date': date.today().isoformat(),
                'attendance_data': attendance_data
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response1.status_code, 200)
        result1 = json.loads(response1.content)
        self.assertTrue(result1['success'])
        self.assertEqual(result1['created'], 2)
        
        # Verify records exist
        records = Attendance.objects.filter(course=self.course, date=date.today())
        self.assertEqual(records.count(), 2)
        
        # Second submission (duplicate) - should update, not create duplicates
        response2 = client.post(
            reverse('instructor:sync_attendance_api'),
            data=json.dumps({
                'course': self.course.id,
                'date': date.today().isoformat(),
                'attendance_data': {
                    str(self.student1.id): 'Absent',  # Changed status
                    str(self.student2.id): 'Late'  # Same status
                }
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response2.status_code, 200)
        result2 = json.loads(response2.content)
        self.assertTrue(result2['success'])
        self.assertEqual(result2['created'], 0)  # No new records
        self.assertEqual(result2['updated'], 2)  # Both updated
        
        # Verify no duplicates - should still be 2 records
        records = Attendance.objects.filter(course=self.course, date=date.today())
        self.assertEqual(records.count(), 2)
        
        # Verify student1 status was updated
        student1_record = Attendance.objects.get(
            student=self.student1,
            course=self.course,
            date=date.today()
        )
        self.assertEqual(student1_record.status, 'Absent')
    
    def test_sync_api_unauthorized_access(self):
        """Test: API rejects unauthorized access"""
        client = Client()
        
        # Not logged in - should return 401
        response = client.post(
            reverse('instructor:sync_attendance_api'),
            data=json.dumps({
                'course': self.course.id,
                'date': date.today().isoformat(),
                'attendance_data': {}
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('Authentication required', result['error'])
        
        # Logged in as student (wrong role) - should return 403
        student = User.objects.create_user(
            username='student_test',
            email='student_test@test.com',
            password='testpass123',
            role='student'
        )
        client.force_login(student)
        
        response2 = client.post(
            reverse('instructor:sync_attendance_api'),
            data=json.dumps({
                'course': self.course.id,
                'date': date.today().isoformat(),
                'attendance_data': {}
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response2.status_code, 403)
        result2 = json.loads(response2.content)
        self.assertFalse(result2['success'])
        self.assertIn('Unauthorized', result2['error'])
    
    def test_sync_api_invalid_data(self):
        """Test: API handles invalid data gracefully"""
        client = Client()
        client.force_login(self.instructor)
        
        # Missing required fields
        response = client.post(
            reverse('instructor:sync_attendance_api'),
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('Missing required fields', result['error'])
    
    def test_sync_api_invalid_status(self):
        """Test: API rejects invalid status values"""
        client = Client()
        client.force_login(self.instructor)
        
        response = client.post(
            reverse('instructor:sync_attendance_api'),
            data=json.dumps({
                'course': self.course.id,
                'date': date.today().isoformat(),
                'attendance_data': {
                    str(self.student1.id): 'InvalidStatus'
                }
            }),
            content_type='application/json'
        )
        
        # Should succeed but skip invalid status
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertEqual(result['created'], 0)  # Invalid status skipped
        
        # Verify no record created
        records = Attendance.objects.filter(course=self.course, date=date.today())
        self.assertEqual(records.count(), 0)
    
    def test_sync_api_transaction_atomicity(self):
        """Test: API maintains transaction atomicity"""
        client = Client()
        client.force_login(self.instructor)
        
        # Create a student that doesn't exist (will cause error)
        invalid_student_id = 99999
        
        attendance_data = {
            str(self.student1.id): 'Present',
            str(invalid_student_id): 'Present'  # Invalid student
        }
        
        response = client.post(
            reverse('instructor:sync_attendance_api'),
            data=json.dumps({
                'course': self.course.id,
                'date': date.today().isoformat(),
                'attendance_data': attendance_data
            }),
            content_type='application/json'
        )
        
        # Should succeed but skip invalid student
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertEqual(result['created'], 1)  # Only valid student
        
        # Verify only valid record exists
        records = Attendance.objects.filter(course=self.course, date=date.today())
        self.assertEqual(records.count(), 1)
        self.assertEqual(records.first().student, self.student1)

