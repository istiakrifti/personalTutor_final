from django import forms
from django.core.validators import RegexValidator, EmailValidator
from .models import UserProfile

class UploadHwForm(forms.Form):
    title = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'title',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        })
    )

class RegistrationForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder' : 'Your Name',
            'class': 'pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-indigo-500'
        })
    )
    
    mobile_no = forms.CharField(
        max_length=11,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^01\d{9}$',
                message="Invalid Mobile No"
            )
        ],
        widget=forms.TextInput(attrs={
            'placeholder': '01XXXXXXXXX',
            'class': 'pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-indigo-500'
        })
    )

    email = forms.EmailField(
        max_length=254,
        required=True,
        validators=[EmailValidator(message="Invalid Email Address")],
        widget=forms.EmailInput(attrs={
            'placeholder': 'you@example.com',
            'class': 'pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-indigo-500'
        })
    )
    
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-indigo-500'
        })
    )

    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-indigo-500'
        })
    )

class LoginForm(forms.Form):
    mobile_no = forms.CharField(
        max_length=11,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^01\d{9}$',
                message="Invalid Mobile No"
            )
        ],
        widget=forms.TextInput(attrs={
            'placeholder': '01XXXXXXXXX',
            'class': 'flex items-center border border-indigo-400 rounded-lg shadow-md transition duration-200 focus-within:ring-2 focus-within:ring-indigo-500 w-full px-3 py-2',
            'style': 'padding-left: 2.5rem;',  
        })
    )

    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'flex items-center border border-indigo-400 rounded-lg shadow-md transition duration-200 focus-within:ring-2 focus-within:ring-indigo-500 w-full px-3 py-2',
            'style': 'padding-left: 2.5rem;',  # Padding to accommodate the icon
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adding icons as HTML strings
        self.fields['mobile_no'].widget.attrs['icon'] = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-indigo-600 absolute left-3 top-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8a2 2 0 012-2h14a2 2 0 012 2v12a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" /></svg>'
        self.fields['password'].widget.attrs['icon'] = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-indigo-600 absolute left-3 top-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 7v1m0 4v5m0 0v1m0-1h0m0-1h0m0-1h0m1-1h2.5M12 10h2.5M6 7v4a2 2 0 002 2h8a2 2 0 002-2V7H6z" /></svg>'


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'shadow-sm rounded-md w-full px-3 py-2 border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
        })
    )

    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'shadow-sm rounded-md w-full px-3 py-2 border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
        })
    )

    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'shadow-sm rounded-md w-full px-3 py-2 border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
        })
    )

class ResetPasswordForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        required=True,
        validators=[EmailValidator(message="Invalid Email Address")],
        widget=forms.EmailInput(attrs={
            'placeholder': 'you@example.com',
            'class': 'shadow-sm rounded-md w-full px-3 py-2 border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
        })
    )

    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'shadow-sm rounded-md w-full px-3 py-2 border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
        })
    )

    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'shadow-sm rounded-md w-full px-3 py-2 border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
        })
    )

class ExamForm(forms.Form):
    title = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'title',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        })
    )

    start_time = forms.DateTimeField(
        required=True,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        }),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    duration = forms.DurationField(
        required=True,
        widget=forms.NumberInput(attrs={
            'placeholder': 'in minutes',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        })
    )

    student = forms.ChoiceField(
        choices=[('', 'Select')] + [(d.id, f'{d.name} {d.user}') for d in UserProfile.objects.filter(role='user').all()],
        required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md min-h-10 border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50',
            'id': 'division'
        })
    )

class ExamEditForm(forms.Form):
    start_time = forms.DateTimeField(
        required=True,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        }),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    duration = forms.DurationField(
        required=True,
        widget=forms.NumberInput(attrs={
            'placeholder': 'in minutes',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        })
    )

    student = forms.ChoiceField(
        choices=[('', 'Select')] + [(d.id, f'{d.name} {d.user}') for d in UserProfile.objects.filter(role='user').all()],
        required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md min-h-10 border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50',
            'id': 'division'
        })
    )

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('okay', 'Okay'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-opacity-50'
        })
    )

    delete_existing_file = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'mt-1 mr-2'
        }),
        label="Delete existing file?"
    )

    file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        })
    )

class VerificationCodeForm(forms.Form):
    code = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md min-h-10 border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        })
    )
