"""
Management command to create an admin superuser account.
Usage: python manage.py create_admin
"""
from django.core.management.base import BaseCommand
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Creates an admin superuser account for website creators'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating admin superuser account...'))
        
        # Create or update admin user
        admin, created = CustomUser.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@academictracker.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_superuser': True,
                'is_staff': True,
            }
        )
        
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Created admin superuser: {admin.username}'))
        else:
            # Update existing admin to be superuser
            admin.is_superuser = True
            admin.is_staff = True
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Updated admin user: {admin.username}'))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('ADMIN LOGIN CREDENTIALS'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Username: admin'))
        self.stdout.write(self.style.SUCCESS('Password: admin123'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('You can now log in at: /login/'))
        self.stdout.write(self.style.SUCCESS('After login, you\'ll be redirected to: /admin-page/'))
        self.stdout.write(self.style.SUCCESS('=' * 50))

