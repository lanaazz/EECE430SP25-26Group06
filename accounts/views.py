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


@login_required
def manage_team_members(request):
    """Allow coaches and managers to add/remove players from team."""
    user_profile = request.user.profile if hasattr(request.user, 'profile') else None
    
    if not user_profile or user_profile.role not in ['coach', 'manager']:
        messages.error(request, "Only coaches and managers can manage team members.")
        return redirect('dashboard')
    
    user_team = user_profile.team
    if not user_team:
        messages.error(request, "You are not assigned to a team.")
        return redirect('dashboard')
    
    # Get all team members
    team_members = UserProfile.objects.filter(team=user_team).select_related('user')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            username = request.POST.get('username', '').strip()
            role = request.POST.get('role', 'player')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '').strip()
            
            # Check if user exists
            if User.objects.filter(username=username).exists():
                # Add existing user to team
                user = User.objects.get(username=username)
                profile = user.profile if hasattr(user, 'profile') else UserProfile.objects.create(user=user)
                profile.team = user_team
                profile.role = role
                profile.save()
                messages.success(request, f"User '{username}' added to team as {profile.get_role_display()}.")
            else:
                # Create new user and add to team
                try:
                    if not email or User.objects.filter(email=email).exists():
                        messages.error(request, "Email is required and must be unique.")
                    elif not password or len(password) < 8:
                        messages.error(request, "Password is required and must be at least 8 characters.")
                    else:
                        new_user = User.objects.create_user(
                            username=username,
                            email=email,
                            password=password,
                            first_name=first_name,
                            last_name=last_name,
                        )
                        UserProfile.objects.create(
                            user=new_user,
                            team=user_team,
                            role=role,
                        )
                        messages.success(request, f"New user '{username}' created and added to team as {role}.")
                except Exception as e:
                    messages.error(request, f"Error creating user: {str(e)}")
            
            return redirect('manage_team_members')
        
        elif action == 'remove':
            member_id = request.POST.get('member_id')
            try:
                member = UserProfile.objects.get(pk=member_id, team=user_team)
                username = member.user.username
                member.team = None
                member.save()
                messages.success(request, f"User '{username}' removed from team.")
            except UserProfile.DoesNotExist:
                messages.error(request, "Member not found.")
            
            return redirect('manage_team_members')
    
    context = {
        'team_members': team_members,
        'team': user_team,
        'active_page': 'manage_team',
        'role_choices': UserProfile.ROLE_CHOICES,
    }
    return render(request, 'accounts/manage_team_members.html', context)
