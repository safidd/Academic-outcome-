"""
Management command to ensure all users have working passwords.
Usage: python manage.py setup_all_passwords
"""
from django.core.management.base import BaseCommand
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Sets passwords for all users based on common patterns to ensure they can log in'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up passwords for all users...'))
        
        def get_password_for_user(user):
            """Return password based on username and role"""
            username_lower = user.username.lower()
            
            # Check for role-specific patterns first
            if user.role == 'student':
                if 'student' in username_lower:
                    return 'student123'
                else:
                    return 'student123'  # Default for all students
            elif user.role == 'instructor':
                if 'instructor' in username_lower or 'teacher' in username_lower or 'prof' in username_lower:
                    return 'instructor123'
                else:
                    return 'instructor123'  # Default for all instructors
            elif user.role == 'department_head':
                if 'head' in username_lower or 'admin' in username_lower or 'dept' in username_lower:
                    return 'head123'
                else:
                    return 'head123'  # Default for all department heads
            # Default pattern: username + 123
            else:
                return f'{user.username}123'
        
        # Get all users
        all_users = CustomUser.objects.all()
        updated_count = 0
        
        for user in all_users:
            password = get_password_for_user(user)
            user.set_password(password)
            user.save()
            updated_count += 1
            self.stdout.write(f'✓ Set password for {user.username} ({user.get_role_display()}): {password}')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✅ Updated passwords for {updated_count} users'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('All users can now log in with their passwords!'))
        self.stdout.write(self.style.SUCCESS('Password patterns:'))
        self.stdout.write(self.style.SUCCESS('  - Students: student123'))
        self.stdout.write(self.style.SUCCESS('  - Instructors: instructor123'))
        self.stdout.write(self.style.SUCCESS('  - Department Heads: head123'))

