from django.urls import path
from . import views

urlpatterns = [
    path('login/',           views.login_view,          name='login'),
    path('logout/',          views.logout_view,          name='logout'),
    path('register/',        views.register_view,        name='register'),
    path('role-select/',     views.role_select_view,     name='role_select'),
    path('profile/',         views.profile_view,         name='profile'),
    path('profile/password/',views.change_password_view, name='change_password'),
]
