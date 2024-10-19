from .models import UserProfile

class UserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                request.logged_in_user = UserProfile.objects.get(user=request.user)
            except UserProfile.DoesNotExist:
                request.logged_in_user = None

        else:
            request.logged_in_user = None

        response = self.get_response(request)
        return response