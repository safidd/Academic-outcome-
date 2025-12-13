"""
Script to create sample users for testing.
Run this with: python manage.py shell < create_sample_users.py
Or run: python manage.py shell, then copy-paste the commands below.
"""
from users.models import CustomUser

# Create a student user
student, created = CustomUser.objects.get_or_create(
    username='student1',
    defaults={
        'email': 'student1@example.com',
        'role': 'student',
    }
)
if created:
    student.set_password('student123')
    student.save()
    print(f"Created student user: {student.username}")
else:
    print(f"Student user {student.username} already exists")

# Create an instructor user
instructor, created = CustomUser.objects.get_or_create(
    username='instructor1',
    defaults={
        'email': 'instructor1@example.com',
        'role': 'instructor',
    }
)
if created:
    instructor.set_password('instructor123')
    instructor.save()
    print(f"Created instructor user: {instructor.username}")
else:
    print(f"Instructor user {instructor.username} already exists")

# Create a department head user
head, created = CustomUser.objects.get_or_create(
    username='head1',
    defaults={
        'email': 'head1@example.com',
        'role': 'department_head',
    }
)
if created:
    head.set_password('head123')
    head.save()
    print(f"Created department head user: {head.username}")
else:
    print(f"Department head user {head.username} already exists")

print("\nSample users created!")
print("You can now log in with:")
print("  Student: username=student1, password=student123")
print("  Instructor: username=instructor1, password=instructor123")
print("  Head: username=head1, password=head123")

