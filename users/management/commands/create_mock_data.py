"""
Management command to create comprehensive mock data.
Usage: python manage.py create_mock_data
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import CustomUser
from courses.models import Course
from outcomes.models import LearningOutcome, ProgramOutcome, ContributionRate
from grades.models import Grade
import random


class Command(BaseCommand):
    help = 'Creates comprehensive mock data: 15 students, 5 courses with learning outcomes, and grades'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating comprehensive mock data...'))
        
        with transaction.atomic():
            # Create 5 instructors (one per course)
            instructors = []
            instructor_names = [
                ('Dr. Sarah', 'Anderson', 'sarah.anderson'),
                ('Dr. Michael', 'Chen', 'michael.chen'),
                ('Dr. Emily', 'Rodriguez', 'emily.rodriguez'),
                ('Dr. James', 'Wilson', 'james.wilson'),
                ('Dr. Lisa', 'Thompson', 'lisa.thompson'),
            ]
            
            for first_name, last_name, username in instructor_names:
                instructor, created = CustomUser.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': f'{username}@university.edu',
                        'role': 'instructor',
                        'first_name': first_name,
                        'last_name': last_name,
                    }
                )
                if created:
                    instructor.set_password('instructor123')
                    instructor.save()
                    self.stdout.write(self.style.SUCCESS(f'Created instructor: {first_name} {last_name}'))
                else:
                    self.stdout.write(f'Instructor {username} already exists')
                instructors.append(instructor)
            
            # Create 15 students with full names
            students = []
            student_names = [
                ('Alex', 'Johnson', 'alex.johnson'),
                ('Maria', 'Garcia', 'maria.garcia'),
                ('David', 'Brown', 'david.brown'),
                ('Jennifer', 'Davis', 'jennifer.davis'),
                ('Robert', 'Miller', 'robert.miller'),
                ('Jessica', 'Martinez', 'jessica.martinez'),
                ('Christopher', 'Garcia', 'christopher.garcia'),
                ('Amanda', 'Rodriguez', 'amanda.rodriguez'),
                ('Daniel', 'Lewis', 'daniel.lewis'),
                ('Ashley', 'Lee', 'ashley.lee'),
                ('Matthew', 'Walker', 'matthew.walker'),
                ('Emily', 'Hall', 'emily.hall'),
                ('Andrew', 'Allen', 'andrew.allen'),
                ('Michelle', 'Young', 'michelle.young'),
                ('Joshua', 'King', 'joshua.king'),
            ]
            
            for first_name, last_name, username in student_names:
                student, created = CustomUser.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': f'{username}@student.university.edu',
                        'role': 'student',
                        'first_name': first_name,
                        'last_name': last_name,
                    }
                )
                if created:
                    student.set_password('student123')
                    student.save()
                    self.stdout.write(self.style.SUCCESS(f'Created student: {first_name} {last_name}'))
                else:
                    self.stdout.write(f'Student {username} already exists')
                students.append(student)
            
            # Create 5 courses with descriptive names
            courses_data = [
                {
                    'code': 'CS101',
                    'name': 'Introduction to Computer Programming',
                    'instructor': instructors[0],
                    'learning_outcomes': [
                        {
                            'code': 'LO1',
                            'description': 'Understand fundamental programming concepts including variables, data types, and basic syntax',
                        },
                        {
                            'code': 'LO2',
                            'description': 'Write and execute simple programs using control structures such as conditionals and loops',
                        },
                        {
                            'code': 'LO3',
                            'description': 'Design and implement functions to organize code and promote reusability',
                        },
                    ]
                },
                {
                    'code': 'CS201',
                    'name': 'Data Structures and Algorithms',
                    'instructor': instructors[1],
                    'learning_outcomes': [
                        {
                            'code': 'LO1',
                            'description': 'Implement and manipulate fundamental data structures including arrays, linked lists, stacks, and queues',
                        },
                        {
                            'code': 'LO2',
                            'description': 'Analyze and compare algorithm complexity using Big-O notation and performance metrics',
                        },
                        {
                            'code': 'LO3',
                            'description': 'Design and implement efficient algorithms for searching, sorting, and graph traversal',
                        },
                    ]
                },
                {
                    'code': 'CS301',
                    'name': 'Database Systems and Management',
                    'instructor': instructors[2],
                    'learning_outcomes': [
                        {
                            'code': 'LO1',
                            'description': 'Design normalized database schemas using Entity-Relationship modeling and relational database principles',
                        },
                        {
                            'code': 'LO2',
                            'description': 'Write complex SQL queries for data retrieval, manipulation, and transaction management',
                        },
                        {
                            'code': 'LO3',
                            'description': 'Implement database indexing, query optimization, and performance tuning techniques',
                        },
                    ]
                },
                {
                    'code': 'CS401',
                    'name': 'Web Development and Applications',
                    'instructor': instructors[3],
                    'learning_outcomes': [
                        {
                            'code': 'LO1',
                            'description': 'Build responsive web applications using HTML, CSS, and JavaScript with modern frameworks',
                        },
                        {
                            'code': 'LO2',
                            'description': 'Develop server-side applications using RESTful APIs and web server technologies',
                        },
                        {
                            'code': 'LO3',
                            'description': 'Implement authentication, authorization, and security best practices in web applications',
                        },
                    ]
                },
                {
                    'code': 'CS501',
                    'name': 'Software Engineering and Project Management',
                    'instructor': instructors[4],
                    'learning_outcomes': [
                        {
                            'code': 'LO1',
                            'description': 'Apply software development lifecycle methodologies including Agile, Scrum, and Waterfall',
                        },
                        {
                            'code': 'LO2',
                            'description': 'Design software architectures using design patterns and UML modeling techniques',
                        },
                        {
                            'code': 'LO3',
                            'description': 'Implement version control, continuous integration, and collaborative development workflows',
                        },
                    ]
                },
            ]
            
            courses = []
            all_learning_outcomes = []
            
            for course_data in courses_data:
                course, created = Course.objects.get_or_create(
                    code=course_data['code'],
                    defaults={
                        'name': course_data['name'],
                        'instructor': course_data['instructor'],
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created course: {course.name} ({course.code})'))
                else:
                    # Update course name if it exists
                    course.name = course_data['name']
                    course.instructor = course_data['instructor']
                    course.save()
                    self.stdout.write(f'Course {course.code} already exists, updated')
                
                courses.append(course)
                
                # Create learning outcomes for this course
                for lo_data in course_data['learning_outcomes']:
                    lo, created = LearningOutcome.objects.get_or_create(
                        code=lo_data['code'],
                        course=course,
                        defaults={
                            'description': lo_data['description'],
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'  Created LO: {lo.description[:50]}...'))
                    else:
                        # Update description if it exists
                        lo.description = lo_data['description']
                        lo.save()
                    all_learning_outcomes.append(lo)
            
            # Create or get Program Outcomes
            self.stdout.write(self.style.SUCCESS('\nCreating Program Outcomes...'))
            po1, created = ProgramOutcome.objects.get_or_create(
                code='PO1',
                defaults={'description': 'Apply engineering knowledge to solve complex problems'}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created PO: {po1.code}'))
            
            po2, created = ProgramOutcome.objects.get_or_create(
                code='PO2',
                defaults={'description': 'Design and develop software solutions'}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created PO: {po2.code}'))
            
            po3, created = ProgramOutcome.objects.get_or_create(
                code='PO3',
                defaults={'description': 'Analyze and evaluate system performance'}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created PO: {po3.code}'))
            
            program_outcomes = [po1, po2, po3]
            
            # Create Contribution Rates (LO → PO mappings)
            self.stdout.write(self.style.SUCCESS('\nCreating Contribution Rate mappings (LO → PO)...'))
            contribution_count = 0
            
            # Map learning outcomes to program outcomes based on course content
            for course_idx, course in enumerate(courses):
                course_los = [lo for lo in all_learning_outcomes if lo.course == course]
                
                for lo_idx, lo in enumerate(course_los):
                    # CS101: Programming basics → PO1 (40%), PO2 (35%)
                    # CS101: Control structures → PO2 (50%)
                    # CS101: Functions → PO2 (40%), PO3 (20%)
                    if course.code == 'CS101':
                        if lo_idx == 0:  # LO1
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po1,
                                defaults={'percentage': 40}
                            )
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po2,
                                defaults={'percentage': 35}
                            )
                            contribution_count += 2
                        elif lo_idx == 1:  # LO2
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po2,
                                defaults={'percentage': 50}
                            )
                            contribution_count += 1
                        elif lo_idx == 2:  # LO3
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po2,
                                defaults={'percentage': 40}
                            )
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po3,
                                defaults={'percentage': 20}
                            )
                            contribution_count += 2
                    
                    # CS201: Data structures → PO2 (45%), PO3 (30%)
                    # CS201: Algorithm analysis → PO3 (50%)
                    # CS201: Algorithm design → PO2 (35%), PO3 (35%)
                    elif course.code == 'CS201':
                        if lo_idx == 0:  # LO1
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po2,
                                defaults={'percentage': 45}
                            )
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po3,
                                defaults={'percentage': 30}
                            )
                            contribution_count += 2
                        elif lo_idx == 1:  # LO2
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po3,
                                defaults={'percentage': 50}
                            )
                            contribution_count += 1
                        elif lo_idx == 2:  # LO3
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po2,
                                defaults={'percentage': 35}
                            )
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po3,
                                defaults={'percentage': 35}
                            )
                            contribution_count += 2
                    
                    # CS301: Database design → PO1 (40%), PO2 (30%)
                    # CS301: SQL queries → PO2 (45%)
                    # CS301: Performance → PO3 (50%)
                    elif course.code == 'CS301':
                        if lo_idx == 0:  # LO1
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po1,
                                defaults={'percentage': 40}
                            )
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po2,
                                defaults={'percentage': 30}
                            )
                            contribution_count += 2
                        elif lo_idx == 1:  # LO2
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po2,
                                defaults={'percentage': 45}
                            )
                            contribution_count += 1
                        elif lo_idx == 2:  # LO3
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po3,
                                defaults={'percentage': 50}
                            )
                            contribution_count += 1
                    
                    # CS401: Web frontend → PO2 (40%)
                    # CS401: Web backend → PO2 (40%), PO3 (25%)
                    # CS401: Security → PO1 (35%), PO3 (30%)
                    elif course.code == 'CS401':
                        if lo_idx == 0:  # LO1
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po2,
                                defaults={'percentage': 40}
                            )
                            contribution_count += 1
                        elif lo_idx == 1:  # LO2
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po2,
                                defaults={'percentage': 40}
                            )
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po3,
                                defaults={'percentage': 25}
                            )
                            contribution_count += 2
                        elif lo_idx == 2:  # LO3
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po1,
                                defaults={'percentage': 35}
                            )
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po3,
                                defaults={'percentage': 30}
                            )
                            contribution_count += 2
                    
                    # CS501: SDLC → PO1 (40%), PO2 (30%)
                    # CS501: Architecture → PO2 (45%)
                    # CS501: DevOps → PO3 (50%)
                    elif course.code == 'CS501':
                        if lo_idx == 0:  # LO1
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po1,
                                defaults={'percentage': 40}
                            )
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po2,
                                defaults={'percentage': 30}
                            )
                            contribution_count += 2
                        elif lo_idx == 1:  # LO2
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po2,
                                defaults={'percentage': 45}
                            )
                            contribution_count += 1
                        elif lo_idx == 2:  # LO3
                            ContributionRate.objects.get_or_create(
                                learning_outcome=lo,
                                program_outcome=po3,
                                defaults={'percentage': 50}
                            )
                            contribution_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Created/updated {contribution_count} contribution rate mappings'))
            
            # Create grades for all students across all courses and learning outcomes
            self.stdout.write(self.style.SUCCESS('\nCreating grades for all students...'))
            
            grade_count = 0
            for student in students:
                for course in courses:
                    # Get learning outcomes for this course
                    course_los = [lo for lo in all_learning_outcomes if lo.course == course]
                    
                    for lo in course_los:
                        # Generate random grade between 60-100
                        score = random.randint(60, 100)
                        grade, created = Grade.objects.get_or_create(
                            student=student,
                            course=course,
                            learning_outcome=lo,
                            defaults={'score': score}
                        )
                        if created:
                            grade_count += 1
                        else:
                            # Update existing grade
                            grade.score = score
                            grade.save()
            
            self.stdout.write(self.style.SUCCESS(f'Created/updated {grade_count} grades'))
            
            # Summary
            self.stdout.write(self.style.SUCCESS('\n✅ Mock data created successfully!'))
            self.stdout.write(self.style.SUCCESS(f'\nSummary:'))
            self.stdout.write(self.style.SUCCESS(f'  - {len(instructors)} instructors created'))
            self.stdout.write(self.style.SUCCESS(f'  - {len(students)} students created'))
            self.stdout.write(self.style.SUCCESS(f'  - {len(courses)} courses created'))
            self.stdout.write(self.style.SUCCESS(f'  - {len(all_learning_outcomes)} learning outcomes created'))
            self.stdout.write(self.style.SUCCESS(f'  - {len(program_outcomes)} program outcomes created'))
            self.stdout.write(self.style.SUCCESS(f'  - {contribution_count} contribution rate mappings created'))
            self.stdout.write(self.style.SUCCESS(f'  - {grade_count} grades created'))
            self.stdout.write(self.style.SUCCESS(f'\nAll students can log in with password: student123'))
            self.stdout.write(self.style.SUCCESS(f'All instructors can log in with password: instructor123'))


