"""
Management command to create demo data for presentation.
Usage: python manage.py create_demo_data
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from users.models import CustomUser
from courses.models import Course
from outcomes.models import LearningOutcome, ProgramOutcome, ContributionRate
from grades.models import Grade


class Command(BaseCommand):
    help = 'Creates demo data for presentation (3 courses, 3 POs, LOs, 2 students, 1 instructor)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating demo data...'))
        
        # Create or get instructor
        instructor, created = CustomUser.objects.get_or_create(
            username='instructor1',
            defaults={
                'email': 'instructor1@example.com',
                'role': 'instructor',
                'first_name': 'Dr. Jane',
                'last_name': 'Smith',
            }
        )
        if created:
            instructor.set_password('instructor123')
            instructor.save()
            self.stdout.write(self.style.SUCCESS(f'Created instructor: {instructor.username}'))
        else:
            self.stdout.write(f'Instructor {instructor.username} already exists')
        
        # Create or get students
        student1, created = CustomUser.objects.get_or_create(
            username='student1',
            defaults={
                'email': 'student1@example.com',
                'role': 'student',
                'first_name': 'John',
                'last_name': 'Doe',
            }
        )
        if created:
            student1.set_password('student123')
            student1.save()
            self.stdout.write(self.style.SUCCESS(f'Created student: {student1.username}'))
        
        student2, created = CustomUser.objects.get_or_create(
            username='student2',
            defaults={
                'email': 'student2@example.com',
                'role': 'student',
                'first_name': 'Alice',
                'last_name': 'Johnson',
            }
        )
        if created:
            student2.set_password('student123')
            student2.save()
            self.stdout.write(self.style.SUCCESS(f'Created student: {student2.username}'))
        
        # Create courses
        course1, created = Course.objects.get_or_create(
            code='CS101',
            defaults={
                'name': 'Introduction to Computer Science',
                'instructor': instructor,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created course: {course1.code}'))
        
        course2, created = Course.objects.get_or_create(
            code='CS201',
            defaults={
                'name': 'Data Structures and Algorithms',
                'instructor': instructor,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created course: {course2.code}'))
        
        course3, created = Course.objects.get_or_create(
            code='CS301',
            defaults={
                'name': 'Database Systems',
                'instructor': instructor,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created course: {course3.code}'))
        
        # Create Learning Outcomes for Course 1
        lo1_1, created = LearningOutcome.objects.get_or_create(
            code='LO1',
            course=course1,
            defaults={
                'description': 'Understand basic programming concepts and syntax',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created LO: {lo1_1.code} for {course1.code}'))
        
        lo1_2, created = LearningOutcome.objects.get_or_create(
            code='LO2',
            course=course1,
            defaults={
                'description': 'Write simple programs using control structures',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created LO: {lo1_2.code} for {course1.code}'))
        
        # Create Learning Outcomes for Course 2
        lo2_1, created = LearningOutcome.objects.get_or_create(
            code='LO1',
            course=course2,
            defaults={
                'description': 'Implement common data structures (arrays, linked lists, stacks, queues)',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created LO: {lo2_1.code} for {course2.code}'))
        
        lo2_2, created = LearningOutcome.objects.get_or_create(
            code='LO2',
            course=course2,
            defaults={
                'description': 'Analyze algorithm complexity using Big-O notation',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created LO: {lo2_2.code} for {course2.code}'))
        
        # Create Learning Outcomes for Course 3
        lo3_1, created = LearningOutcome.objects.get_or_create(
            code='LO1',
            course=course3,
            defaults={
                'description': 'Design and normalize database schemas',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created LO: {lo3_1.code} for {course3.code}'))
        
        lo3_2, created = LearningOutcome.objects.get_or_create(
            code='LO2',
            course=course3,
            defaults={
                'description': 'Write complex SQL queries for data retrieval',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created LO: {lo3_2.code} for {course3.code}'))
        
        # Create Program Outcomes
        po1, created = ProgramOutcome.objects.get_or_create(
            code='PO1',
            defaults={
                'description': 'Apply engineering knowledge to solve complex problems',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created PO: {po1.code}'))
        
        po2, created = ProgramOutcome.objects.get_or_create(
            code='PO2',
            defaults={
                'description': 'Design and develop software solutions',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created PO: {po2.code}'))
        
        po3, created = ProgramOutcome.objects.get_or_create(
            code='PO3',
            defaults={
                'description': 'Analyze and evaluate system performance',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created PO: {po3.code}'))
        
        # Create Contribution Rates (LO → PO mappings)
        # Course 1 LO1 → PO1 (40%), PO2 (30%)
        ContributionRate.objects.get_or_create(
            learning_outcome=lo1_1,
            program_outcome=po1,
            defaults={'percentage': 40}
        )
        ContributionRate.objects.get_or_create(
            learning_outcome=lo1_1,
            program_outcome=po2,
            defaults={'percentage': 30}
        )
        
        # Course 1 LO2 → PO2 (50%)
        ContributionRate.objects.get_or_create(
            learning_outcome=lo1_2,
            program_outcome=po2,
            defaults={'percentage': 50}
        )
        
        # Course 2 LO1 → PO2 (40%), PO3 (30%)
        ContributionRate.objects.get_or_create(
            learning_outcome=lo2_1,
            program_outcome=po2,
            defaults={'percentage': 40}
        )
        ContributionRate.objects.get_or_create(
            learning_outcome=lo2_1,
            program_outcome=po3,
            defaults={'percentage': 30}
        )
        
        # Course 2 LO2 → PO3 (50%)
        ContributionRate.objects.get_or_create(
            learning_outcome=lo2_2,
            program_outcome=po3,
            defaults={'percentage': 50}
        )
        
        # Course 3 LO1 → PO1 (40%)
        ContributionRate.objects.get_or_create(
            learning_outcome=lo3_1,
            program_outcome=po1,
            defaults={'percentage': 40}
        )
        
        # Course 3 LO2 → PO2 (30%), PO3 (30%)
        ContributionRate.objects.get_or_create(
            learning_outcome=lo3_2,
            program_outcome=po2,
            defaults={'percentage': 30}
        )
        ContributionRate.objects.get_or_create(
            learning_outcome=lo3_2,
            program_outcome=po3,
            defaults={'percentage': 30}
        )
        
        self.stdout.write(self.style.SUCCESS('Created contribution rate mappings'))
        
        # Create sample grades
        # Student 1 grades
        Grade.objects.get_or_create(
            student=student1,
            course=course1,
            learning_outcome=lo1_1,
            defaults={'score': 85}
        )
        Grade.objects.get_or_create(
            student=student1,
            course=course1,
            learning_outcome=lo1_2,
            defaults={'score': 90}
        )
        Grade.objects.get_or_create(
            student=student1,
            course=course2,
            learning_outcome=lo2_1,
            defaults={'score': 88}
        )
        Grade.objects.get_or_create(
            student=student1,
            course=course2,
            learning_outcome=lo2_2,
            defaults={'score': 92}
        )
        
        # Student 2 grades
        Grade.objects.get_or_create(
            student=student2,
            course=course1,
            learning_outcome=lo1_1,
            defaults={'score': 75}
        )
        Grade.objects.get_or_create(
            student=student2,
            course=course1,
            learning_outcome=lo1_2,
            defaults={'score': 80}
        )
        Grade.objects.get_or_create(
            student=student2,
            course=course3,
            learning_outcome=lo3_1,
            defaults={'score': 85}
        )
        Grade.objects.get_or_create(
            student=student2,
            course=course3,
            learning_outcome=lo3_2,
            defaults={'score': 78}
        )
        
        self.stdout.write(self.style.SUCCESS('Created sample grades'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Demo data created successfully!'))
        self.stdout.write(self.style.SUCCESS('\nTest accounts:'))
        self.stdout.write(self.style.SUCCESS('  Instructor: instructor1 / instructor123'))
        self.stdout.write(self.style.SUCCESS('  Student 1: student1 / student123'))
        self.stdout.write(self.style.SUCCESS('  Student 2: student2 / student123'))

