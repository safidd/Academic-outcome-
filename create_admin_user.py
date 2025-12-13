"""
Script to create an admin superuser account for the website creators.
Run this with: python manage.py shell < create_admin_user.py
Or run: python manage.py shell, then copy-paste the commands below.
"""
from users.models import CustomUser

# Create admin superuser
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
    print(f"✓ Created admin superuser: {admin.username}")
    print(f"  Email: {admin.email}")
    print(f"  Password: admin123")
else:
    # Update existing admin to be superuser
    admin.is_superuser = True
    admin.is_staff = True
    admin.set_password('admin123')
    admin.save()
    print(f"✓ Updated admin user: {admin.username}")
    print(f"  Email: {admin.email}")
    print(f"  Password: admin123")

print("\n" + "="*50)
print("ADMIN LOGIN CREDENTIALS")
print("="*50)
print("Username: admin")
print("Password: admin123")
print("\nYou can now log in at: /login/")
print("After login, you'll be redirected to: /admin-page/")
print("="*50)

