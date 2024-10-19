from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from .models import UserProfile

def admin_required(view_func):
    @user_passes_test(lambda user: user.is_authenticated and user.userprofile.role == 'admin')
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return _wrapped_view

def user_required(view_func):
    @user_passes_test(lambda user: user.is_authenticated and user.userprofile.role == 'user')
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return _wrapped_view
