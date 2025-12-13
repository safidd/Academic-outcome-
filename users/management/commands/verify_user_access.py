"""
Management command to verify all users can access their dashboards.
Usage: python manage.py verify_user_access
"""
from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from users.models import CustomUser

User = get_user_model()


class Command(BaseCommand):
    help = 'Verifies that all users can log in and access their dashboards'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Verifying user access...'))
        self.stdout.write('')
        
        client = Client()
        issues = []
        
        # Get all users
        all_users = CustomUser.objects.all()
        
        for user in all_users:
            username = user.username
            role = user.role
            
            # Determine password
            if user.is_superuser:
                password = 'admin123'
            elif role == 'student':
                password = 'student123'
            elif role == 'instructor':
                password = 'instructor123'
            elif role == 'department_head':
                password = 'head123'
            else:
                password = f'{username}123'
            
            # Try to log in
            login_success = client.login(username=username, password=password)
            
            if not login_success:
                issues.append(f"❌ {username} ({role}): Cannot log in")
                continue
            
            # Determine expected redirect URL
            if user.is_superuser:
                expected_url = reverse('admin_page')
            elif role == 'student':
                expected_url = reverse('student:dashboard')
            elif role == 'instructor':
                expected_url = reverse('instructor:dashboard')
            elif role == 'department_head':
                expected_url = reverse('head:dashboard')
            else:
                expected_url = reverse('home')
            
            # Try to access the dashboard
            response = client.get(expected_url)
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS(f'✓ {username} ({role}): Can log in and access dashboard'))
            elif response.status_code == 403:
                issues.append(f"❌ {username} ({role}): Permission denied (403)")
            elif response.status_code == 404:
                issues.append(f"❌ {username} ({role}): Dashboard not found (404)")
            else:
                issues.append(f"❌ {username} ({role}): Error {response.status_code}")
            
            client.logout()
        
        self.stdout.write('')
        if issues:
            self.stdout.write(self.style.ERROR('Issues found:'))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f'  {issue}'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ All users can log in and access their dashboards!'))

