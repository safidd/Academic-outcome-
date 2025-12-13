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
        if user.role == 'student':
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
