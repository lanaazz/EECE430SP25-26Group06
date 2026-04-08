from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from scheduling.models import UserProfile
from .forms import RegisterForm, ProfileUpdateForm, ChangePasswordForm


def register_view(request):
    """New user registration with role & team selection."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Custom login view."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Create profile if missing (e.g. superuser)
            if not hasattr(user, 'profile'):
                UserProfile.objects.create(user=user, role='coach')
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            error = "Invalid username or password."

    return render(request, 'accounts/login.html', {'error': error, 'next': request.GET.get('next', '')})


def logout_view(request):
    """Logout and redirect to login."""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')


def role_select_view(request):
    """Role selection screen — shown after registration if needed."""
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        role = request.POST.get('role')
        valid_roles = [r[0] for r in UserProfile.ROLE_CHOICES]
        if role in valid_roles:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.role = role
            profile.save()
            messages.success(request, f"Role set to {profile.get_role_display()}.")
        return redirect('dashboard')

    return render(request, 'accounts/role_select.html')


@login_required
def profile_view(request):
    """View and edit own profile."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            # Update User fields
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name  = form.cleaned_data['last_name']
            request.user.email      = form.cleaned_data['email']
            request.user.save()
            # Update profile (handles avatar + team)
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile, user=request.user)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile,
        'active_page': 'profile',
    })


@login_required
def change_password_view(request):
    """Change password from profile page."""
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            user = request.user
            if not user.check_password(form.cleaned_data['current_password']):
                form.add_error('current_password', 'Current password is incorrect.')
            else:
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                update_session_auth_hash(request, user)  # keep logged in
                messages.success(request, "Password changed successfully.")
                return redirect('profile')
    else:
        form = ChangePasswordForm()

    return render(request, 'accounts/change_password.html', {
        'form': form,
        'active_page': 'profile',
    })
