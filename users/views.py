from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import PermissionDenied


class CustomLoginView(LoginView):
    """Custom login view with role-based redirect"""
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirect based on user role"""
        user = self.request.user
        if user.is_superuser:
            return reverse('admin_page')
        elif user.role == 'student':
            return reverse('student:dashboard')
        elif user.role == 'instructor':
            return reverse('instructor:dashboard')
        elif user.role == 'department_head':
            return reverse('head:dashboard')
        return reverse('home')


def home(request):
    """Home page"""
    return render(request, 'users/home.html')


class CustomLogoutView(LogoutView):
    """Custom logout view with Cyber Light Theme template"""
    template_name = 'registration/logged_out.html'
    next_page = 'home'


def permission_denied_view(request, exception):
    """Custom 403 permission denied page"""
    return render(request, 'users/403.html', status=403)


@login_required
def admin_page(request):
    """Admin page to view all users - only accessible to superusers"""
    if not request.user.is_superuser:
        raise PermissionDenied("Only administrators can access this page.")
    
    from users.models import CustomUser
    
    # Get all users categorized by role
    students = CustomUser.objects.filter(role='student').order_by('username')
    instructors = CustomUser.objects.filter(role='instructor').order_by('username')
    department_heads = CustomUser.objects.filter(role='department_head').order_by('username')
    
    # Common password patterns (for demo/test accounts)
    # In production, passwords should be reset through proper channels
    def get_default_password(username, role):
        """Return likely default password based on common patterns"""
        # Common patterns based on the codebase: student123, instructor123, head123, username123
        username_lower = username.lower()
        
        # Check for role-specific patterns first
        if 'student' in username_lower:
            return 'student123'
        elif 'instructor' in username_lower or 'teacher' in username_lower or 'prof' in username_lower:
            return 'instructor123'
        elif 'head' in username_lower or 'admin' in username_lower or 'dept' in username_lower:
            return 'head123'
        # Default pattern: username + 123
        else:
            return f'{username}123'
    
    # Add password hints to each user
    students_list = []
    for student in students:
        students_list.append({
            'user': student,
            'password_hint': get_default_password(student.username, 'student')
        })
    
    instructors_list = []
    for instructor in instructors:
        instructors_list.append({
            'user': instructor,
            'password_hint': get_default_password(instructor.username, 'instructor')
        })
    
    heads_list = []
    for head in department_heads:
        heads_list.append({
            'user': head,
            'password_hint': get_default_password(head.username, 'department_head')
        })
    
    return render(request, 'users/admin.html', {
        'students': students_list,
        'instructors': instructors_list,
        'department_heads': heads_list,
        'total_students': len(students_list),
        'total_instructors': len(instructors_list),
        'total_heads': len(heads_list),
    })
