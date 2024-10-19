from .models import UserProfile

def user_context(request):
    if request.user.is_authenticated:
        try:
            student = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            student = None
    else:
        student = None

    return {'logged_in_user': student}
