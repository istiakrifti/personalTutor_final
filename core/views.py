from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import HWFiles, Folder, File, UserProfile, Exam, AnswerScript, History, TempProfile
from .forms import UploadHwForm, RegistrationForm, LoginForm, ChangePasswordForm, ExamForm, ExamEditForm, VerificationCodeForm, ResetPasswordForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from PIL import Image
from django.core.cache import cache
from cloudinary import uploader, api
from django.contrib import messages
from reportlab.pdfgen import canvas
from .decorators import admin_required, user_required
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from django.contrib.auth.decorators import login_required
import io, os, uuid
from django.core.files.base import ContentFile
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from twilio.rest import Client
from django.core.mail import send_mail
from PersonalTutor.settings import EMAIL_HOST_USER
from django.urls import reverse
from django.utils.html import format_html
import random
from django.contrib.auth.hashers import check_password
from cloudinary.utils import cloudinary_url
import cloudinary
from django.core.files.storage import default_storage
import shutil
from datetime import datetime

@login_required
def logout_view(request):
    logout(request)
    return redirect('/')

def month_year_suggestions(request):
    if 'term' in request.GET:
        term = request.GET['term']
        suggestions = History.objects.filter(month_year__icontains=term).values_list('month_year', flat=True)
        return JsonResponse(list(suggestions), safe=False)
    return JsonResponse([], safe=False)

def additional_info_view(request):
    if 'month_year' in request.GET:
        month_year = request.GET['month_year']
        
        # Retrieve the History object or related information
        history_entry = History.objects.filter(month_year=month_year).first()
        
        if history_entry:
            # Prepare the data to send back
            data = {
                'daycount': history_entry.daycount,
                'total_day_count': history_entry.total_day_count,
                'last_topic': history_entry.last_topic,
                'payment_status': history_entry.payment_status,
            }
            return JsonResponse(data)
    
    return JsonResponse({}, status=404)

def send_whatsapp_message(to, message_body):
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)

    # Make sure to format the number correctly
    formatted_number = f"+88{to}"  # Assuming `to` is passed in E.164 format

    try:
        message = client.messages.create(
            body=message_body,
            from_='whatsapp:+14155238886',
            to=f'whatsapp:{formatted_number}'
        )
        print(f"Message sent: {message.sid}")
    except Exception as e:
        print(f"An error occurred: {e}")

def index(request):
    return render(request, 'index.html')

def check_title_availability(request):
    title = request.GET.get('title')
    is_taken = HWFiles.objects.filter(hw_title=title, student=request.user).exists()

    return JsonResponse({'is_taken': is_taken})

def check_exam_title_availability(request):
    id = request.GET.get('student_id')
    title = request.GET.get('title')
    student = UserProfile.objects.filter(id=id).first()
    is_taken = Exam.objects.filter(title=title, student=student.user).exists()

    return JsonResponse({'is_taken': is_taken})
    
@login_required
@user_required
def live_class_view(request):
    return render(request, 'live_class.html')

@login_required
@user_required
def upload_hw_view(request):
    if request.method == 'POST':
        form = UploadHwForm(request.POST, request.FILES)
        
        if form.is_valid():
            title = form.cleaned_data['title']
            files = request.FILES.getlist('files[]')

            if HWFiles.objects.filter(hw_title=title, student=request.user).exists():
                form.add_error(None, 'A file with this title already exists.')
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors
                })

            images = []
            for file in files:
                if file.content_type == 'application/pdf':
                    new_filename = f"{title}"
                    file.name = new_filename

                    upload_result = uploader.upload(
                        file,
                        folder=f"hw/{request.user.username}/{title}",  # Folder structure
                        public_id=new_filename.replace(".pdf", ""),    # Custom public ID without extension
                        # resource_type="raw",
                        resource_type="auto",                          # Automatically determine resource type
                        access_mode="public"                           # Public access mode for easy download
                    )

                    HWFiles.objects.create(
                        hw_title=title,
                        file=upload_result['secure_url'],
                        student=request.user,
                        status='unchecked'
                    )
                elif file.content_type.startswith('image/'):
                    image = Image.open(file)
                    images.append(image)

            if images:
                buffer = io.BytesIO()
                pdf = canvas.Canvas(buffer, pagesize=letter)
                width, height = letter

                for image in images:
                    if image.mode != "RGB":
                        image = image.convert("RGB")

                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='JPEG')  # Save image as JPEG
                    img_byte_arr.seek(0)

                    aspect_ratio = image.height / float(image.width)
                    img_width = width
                    img_height = width * aspect_ratio

                    # Use ImageReader to pass the correct image format to ReportLab
                    img_reader = ImageReader(img_byte_arr)
                    pdf.drawImage(img_reader, 0, height - img_height, width=img_width, height=img_height)
                    pdf.showPage()

                pdf.save()

                # Save the generated PDF
                buffer.seek(0)
                file_name = f"{title}"
                content_file = ContentFile(buffer.getvalue(), name=file_name)

                upload_result = uploader.upload(
                    content_file,
                    folder=f"hw/{request.user.username}/{title}",  # Folder structure
                    public_id=file_name.replace(".pdf", ""),    # Custom public ID without extension
                    # resource_type="raw",
                    resource_type="auto",                          # Automatically determine resource type
                    access_mode="public"                           # Public access mode for easy download
                )

                HWFiles.objects.create(
                    hw_title=title,
                    file=upload_result['secure_url'],
                    student=request.user,
                    status='unchecked'
                )

            return JsonResponse({'status': 'success', 'redirect': '/'})
        
    else:
        form = UploadHwForm()

    return render(request, 'upload_hw.html', {'form': form})

@login_required
@admin_required
def show_unchecked_hw_view(request, user_id):
    user = UserProfile.objects.filter(id=user_id).first()
    unchecked_files = HWFiles.objects.filter(status='unchecked', student=user.user)
    return render(request, 'show_unchecked_files.html', {'unchecked_files': unchecked_files, 'user_id':user_id})

@login_required
@admin_required
def show_unchecked_scripts_view(request, user_id):
    user = UserProfile.objects.filter(id=user_id).first()
    unchecked_files = AnswerScript.objects.filter(status='unchecked', student=user.user)
    return render(request, 'show_unchecked_script.html', {'unchecked_files': unchecked_files, 'user_id':user_id})

@login_required
@user_required
def show_checked_hw_view(request):
    checked_files = HWFiles.objects.filter(status='checked', student=request.user)
    unchecked_files = HWFiles.objects.filter(status='unchecked', student=request.user)
    return render(request, 'show_checked_files.html', {'checked_files': checked_files, 'unchecked_files':unchecked_files})

@login_required
@user_required
def show_checked_scripts_view(request):
    checked_files = AnswerScript.objects.filter(status='checked', question__student=request.user)
    unchecked_files = AnswerScript.objects.filter(status='unchecked', question__student=request.user)
    return render(request, 'show_checked_script.html', {'checked_files': checked_files, 'unchecked_files':unchecked_files})

@login_required
@admin_required
def upload_checked_hw_view(request, user_id):
    if request.method == 'POST':
        form = UploadHwForm(request.POST, request.FILES)
        
        if form.is_valid():
            title = form.cleaned_data['title']
            files = request.FILES.getlist('files[]')
            for file in files:
                existing_files = HWFiles.objects.filter(hw_title=title)
                for existing_file in existing_files:
                    existing_file.status = 'okay'
                    existing_file.save()

                new_filename = f"{title}_checked"
                file.name = new_filename

                user = UserProfile.objects.filter(id=user_id).first()
                print(user.user.username, flush=True)
                upload_result = uploader.upload(
                    file,
                    folder=f"hw/{user.user.username}/{title}",  # Folder structure
                    public_id=new_filename.replace(".pdf", ""),    # Custom public ID without extension
                    # resource_type="raw",
                    resource_type="auto",                          # Automatically determine resource type
                    access_mode="public"                           # Public access mode for easy download
                )
                HWFiles.objects.create(
                    hw_title=f'{title}_checked',
                    file=upload_result['secure_url'],
                    status='checked',
                    student=user.user
                )

            return JsonResponse({'status': 'success', 'redirect': '/get-all-students-hw/'})
        
    else:
        form = UploadHwForm()

    return render(request, 'upload_script.html', {'form': form})

@login_required
@admin_required
def upload_checked_scripts_view(request, user_id):
    if request.method == 'POST':
        form = UploadHwForm(request.POST, request.FILES)
        
        if form.is_valid():
            title = form.cleaned_data['title']
            files = request.FILES.getlist('files[]')
            for file in files:
                question = Exam.objects.filter(title=title).first()
                new_filename = f"{title}_checked.pdf"
                file.name = new_filename

                
                existing_files = AnswerScript.objects.filter(question__title=title)
                for existing_file in existing_files:
                    existing_file.status = 'okay'
                    existing_file.save()

                    user = UserProfile.objects.filter(id=user_id).first()

                    upload_result = uploader.upload(
                        file,
                        folder=f"answer/{user.user.username}/{title}",  # Folder structure
                        public_id=new_filename.replace(".pdf", ""),    # Custom public ID without extension
                        # resource_type="raw",
                        resource_type="auto",                          # Automatically determine resource type
                        access_mode="public"                           # Public access mode for easy download
                    )

                    AnswerScript.objects.create(
                        answer=upload_result['secure_url'],
                        question=question,
                        status='checked',
                        student=user.user
                    )

            return JsonResponse({'status': 'success', 'redirect': '/get-all-students/'})
        
    else:
        form = UploadHwForm()

    return render(request, 'upload_script.html', {'form': form})

@login_required
@admin_required
def add_files_view(request, user_id, folder_id=None):
    folder = None
    # user_id = request.GET.get('student')
    # if user_id:
    #     request.session['student_id'] = user_id

    user_profile = UserProfile.objects.filter(id=user_id).first()
    if folder_id:
        folder = get_object_or_404(Folder, id=folder_id, user_profile=user_profile)
        subfolders = folder.subfolders.all()
        files = folder.files.all()
    else:
        subfolders = Folder.objects.filter(parent_folder__isnull=True, user_profile=user_profile)
        files = None
        folder_id = 0

    return render(request, 'add_files.html', {
        'subfolders': subfolders,
        'files': files,
        'current_folder': folder_id,
        'user_id': user_id
    })

@login_required
@user_required
def show_files_view(request, folder_id=None):
    folder = None
    if folder_id:
        folder = get_object_or_404(Folder, id=folder_id, user_profile__user=request.user)
        subfolders = folder.subfolders.all()
        files = folder.files.all()
    else:
        subfolders = Folder.objects.filter(parent_folder__isnull=True, user_profile__user=request.user)
        files = None
        folder_id = 0

    return render(request, 'show_files.html', {
        'subfolders': subfolders,
        'files': files,
        'current_folder': folder_id,
    })

@login_required
@admin_required
def create_folder(request, user_id, folder_id=None):
    if request.method == "POST":
        folder_name = request.POST.get("folder_name")
        if folder_name:
            parent_folder = get_object_or_404(Folder, id=folder_id) if folder_id else None
            
            user_profile = UserProfile.objects.filter(id=user_id).first()
            existing_folder = Folder.objects.filter(name=folder_name, parent_folder=parent_folder, user_profile=user_profile).first()
            if existing_folder:
                messages.error(request, 'A folder with this name already exists in the same parent folder.')
            else:
                try:
                    # user_id = request.session.get('student_id')
                    
                    Folder.objects.create(name=folder_name, parent_folder=parent_folder, user_profile=user_profile)
                    messages.success(request, 'Folder created successfully.')
                except Exception as e:
                    messages.error(request, f'Error creating folder: {str(e)}')
        else:
            messages.error(request, 'Folder name cannot be empty.')

    return redirect('add_files', user_id=user_id, folder_id=folder_id)

@login_required
@admin_required
def upload_file(request, user_id, folder_id):
    if request.method == 'POST':
        file_name = request.POST.get('file_name')
        uploaded_file = request.FILES.get('file')

        if uploaded_file:
            folder = get_object_or_404(Folder, id=folder_id)
            user_profile = UserProfile.objects.filter(id=user_id).first()
    
            existing_file = File.objects.filter(name=file_name, folder=folder).first()
            if existing_file:
                messages.error(request, 'A file with this name already exists in this folder.')
            else:
                try:
                    folder_path = folder.name
                    parent_folder = folder.parent_folder

                    # Traverse up the folder hierarchy to get the full path
                    while parent_folder:
                        folder_path = os.path.join(parent_folder.name, folder_path)
                        parent_folder = parent_folder.parent_folder

                    folder_path = folder_path.replace('\\', '/')
                    # Upload the file to the constructed folder path in Cloudinary
                    upload_result = uploader.upload(
                        uploaded_file,
                        folder=f"files/{user_profile.mobile_no}/{folder_path}",  # Use the constructed path
                        resource_type="auto",            # Automatically determine resource type
                        access_mode="public"             # Public access mode for easy download
                    )

                    File.objects.create(folder=folder, name=file_name, file=upload_result['secure_url'], public_id=upload_result['public_id'])
                    messages.success(request, 'File uploaded successfully.')
                except Exception as e:
                    messages.error(request, f'Error uploading file: {str(e)}')
        else:
            messages.error(request, 'No file uploaded.')

    return redirect('add_files', user_id=user_id, folder_id=folder_id)

@login_required
@admin_required
def edit_file(request, user_id, file_id):
    file_instance = get_object_or_404(File, id=file_id)
    
    if request.method == 'POST':
        new_file_name = request.POST.get('file_name')
        
        if new_file_name:
            existing_file = File.objects.filter(name=new_file_name, folder=file_instance.folder).first()
            if existing_file:
                messages.error(request, 'A file with this name already exists in this folder.')
            else:
                file_instance.name = new_file_name
                file_instance.save()
                messages.success(request, 'File name updated successfully.')
        else:
            messages.error(request, 'File name cannot be empty.')

    return redirect('add_files', user_id=user_id, folder_id=file_instance.folder.id)

@login_required
@admin_required
def delete_file(request, user_id, file_id):
    file_instance = get_object_or_404(File, id=file_id)
    folder_id = file_instance.folder.id

    if file_instance.file:
    
        public_id = file_instance.public_id

        # print(public_id, flush=True)

        uploader.destroy(public_id)
        
    file_instance.delete()
    messages.success(request, 'File deleted successfully.')

    return redirect('add_files', user_id=user_id, folder_id=folder_id)

@login_required
@admin_required
def delete_folder(request, user_id, folder_id):

    user_profile = UserProfile.objects.filter(id=user_id).first()
    folder = get_object_or_404(Folder, id=folder_id, user_profile=user_profile)

    # Function to delete all files and subfolders within a folder
    def delete_contents(folder):
        files_in_folder = folder.files.all()
        for file in files_in_folder:
            uploader.destroy(file.public_id)
            print(file.public_id, flush=True)
            file.delete()
        
        # Recursively delete all subfolders and their contents
        subfolders_in_folder = folder.subfolders.all()
        for subfolder in subfolders_in_folder:
            delete_contents(subfolder)  # Recursively delete subfolder contents
            subfolder.delete()  # Delete the subfolder itself

    # Delete all contents of the folder
    delete_contents(folder)

    # Now delete the folder
    folder.delete()
    messages.success(request, 'Folder and its contents deleted successfully.')

    return redirect('add_files', user_id=user_id, folder_id=folder.parent_folder.id if folder.parent_folder else 0)

def send_verification_code(email, user_id):
    # Generate a 6-digit random code
    verification_code = str(random.randint(100000, 999999))
    
    # Store the code in cache with a 2-minute expiration
    key = str(uuid.uuid4())
    cache_key = f'key_{user_id}'
    cache.set(cache_key, verification_code, timeout=120)  # 120 seconds = 2 minutes
    
    # Send the code via email
    send_mail(
        subject='Your Verification Code',
        message=f'Your verification code is: {verification_code}',
        from_email=EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )

def registration_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        
        # Check if the form is valid
        if form.is_valid():
            name = form.cleaned_data['name']
            mobile_no = form.cleaned_data['mobile_no']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            confirm_password = form.cleaned_data['confirm_password']
            files = request.FILES.getlist('files[]')

            picture = None
            for file in files:
                picture = file
            # Check if the mobile number already exists
            if UserProfile.objects.filter(mobile_no=mobile_no).exists():
                form.add_error(None, 'This phone number is already registered.')
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors
                })
            
            if UserProfile.objects.filter(email=email).exists():
                form.add_error('email', 'This email address is already registered.')
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors
                })

            if password != confirm_password:
                form.add_error(None, 'Passwords do not match.')
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors
                })
            
            if picture is not None:
                upload_result = uploader.upload(
                    picture,
                    folder=f"user/{mobile_no}",  # Folder structure
                    resource_type="auto",                          # Automatically determine resource type
                    access_mode="public"                           # Public access mode for easy download
                )
                pricture = upload_result['secure_url']

            # Store session data except the picture itself (store picture path instead)

            verification_code = str(random.randint(100000, 999999))
            token_created_at = timezone.now()

            temp_profile = TempProfile(
                name=name,
                mobile_no=mobile_no,
                email=email,
                password=password,
                picture=picture,
                verification_token=verification_code,
                token_created_at=token_created_at,
                role='user',
            )
            temp_profile.save()
            
            html_message = format_html(
                '''
                <div style="background-color:#f4f4f4; padding: 20px;">
                    <h1>Personal Tutor</h1>
                    <div style="text-align: center; padding: 20px; background-color: #2b6cb0; color: #fff; border-radius: 10px;">
                        <h2>Your Verification Code</h2>
                        <p style="font-size: 24px; font-weight: bold; color: #ffdd57;">{}</p>
                    </div>
                    <p style="text-align: center; font-size: 16px;">
                        Please use this verification code to proceed with your request. The code will expire shortly.
                    </p>
                </div>
                ''',
                verification_code
            )
            send_mail(
                subject='Your Verification Code',
                message=f'Your verification code is: {verification_code}',
                from_email=EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
                html_message=html_message
            )

            return JsonResponse({'status': 'success', 'redirect': f'/verify-code/{temp_profile.id}/'})

    else:
        form = RegistrationForm()

    return render(request, 'registration.html', {'form': form})

def verify_code_view(request, user_id):    
    if request.method == 'POST':
        form = VerificationCodeForm(request.POST)
        if form.is_valid():
            try:
                temporary_user = TempProfile.objects.get(id=user_id)
                # print(temporary_user.name)
            except TempProfile.DoesNotExist:
                form.add_error(None, 'Invalid User')
                return render(request, 'verify_code.html', {'form': form,'user_id': user_id})
            
            verification_code = form.cleaned_data['code']
            
            if temporary_user.verification_token == verification_code:
                time_since_creation = timezone.now() - temporary_user.token_created_at
                if time_since_creation > timedelta(minutes=3):
                    form.add_error(None, 'Verification Code expired')
                    return render(request, 'verify_code.html', {'form': form,'user_id': user_id})
                
                user_profile = UserProfile(
                    name=temporary_user.name,
                    mobile_no=temporary_user.mobile_no,
                    email=temporary_user.email,
                    password=temporary_user.password,
                    picture=temporary_user.picture,
                    role='user',
                )
                user_profile.save()
                user = authenticate(username=user_profile.mobile_no, password=temporary_user.password)
                if user is not None:
                    login(request, user)
                    print("GDSGS", flush=True)
                    messages.success(request, 'Your email has been verified successfully!')
                    return redirect('/')

            else:
                form.add_error(None, 'Invalid Verification Code')
                return render(request, 'verify_code.html', {'form': form,'user_id': user_id})
    else:
        form = VerificationCodeForm()

    return render(request, 'verify_code.html', {'form': form,'user_id': user_id})

def resend_code_view(request, user_id):
    temp_profile = TempProfile.objects.filter(id=user_id).first()

    verification_code = str(random.randint(100000, 999999))
    token_created_at = timezone.now()
    temp_profile.verification_token = verification_code
    temp_profile.token_created_at = token_created_at
    temp_profile.save()

    html_message = format_html(
        '''
        <div style="background-color:#f4f4f4; padding: 20px;">
            <div style="text-align: center; padding: 20px; background-color: #2b6cb0; color: #fff; border-radius: 10px;">
                <h1>Your Verification Code</h1>
                <p style="font-size: 24px; font-weight: bold; color: #ffdd57;">{}</p>
            </div>
            <p style="text-align: center; font-size: 16px;">
                Please use this verification code to proceed with your request. The code will expire shortly.
            </p>
        </div>
        ''',
        verification_code
    )

    send_mail(
        subject='Your Verification Code',
        message=f'Your verification code is: {verification_code}',
        from_email=EMAIL_HOST_USER,
        recipient_list=[temp_profile.email],
        fail_silently=False,
        html_message=html_message
    )

    return redirect(f'/verify-code/{user_id}/')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            mobile_no = form.cleaned_data['mobile_no']
            password = form.cleaned_data['password']

            try:
                student = UserProfile.objects.get(mobile_no=mobile_no)
                user = student.user

                authenticate_user = authenticate(username=user.username, password=password)

                if authenticate_user is not None:
                    login(request, authenticate_user)
                    return redirect('/')
                else:
                    form.add_error(None, 'Invalid Mobile No or Password')

            except UserProfile.DoesNotExist:
                form.add_error(None, 'Invalid Mobile No or Password')

    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def error(request):
    error_code = request.GET.get('error_code', '405')
    error_message = request.GET.get('error_message', 'Invalid Request')

    context = {
        'error_code': error_code,
        'error_message': error_message,
    }

    return render(request, 'error.html', context)

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            password = form.cleaned_data['password']
            confirm_password = form.cleaned_data['confirm_password']

            user_profile = UserProfile.objects.filter(user=request.user).first()

            if not check_password(old_password, user_profile.user.password):
                form.add_error(None, 'Wrong Old Password')
                return render(request, 'change_password.html', {'form': form})

            if password == confirm_password:
                user = request.user
                user.set_password(password)
                user.save()

                update_session_auth_hash(request, user)

                try:
                    student = UserProfile.objects.get(user=user)
                    student.password = password
                    
                except UserProfile.DoesNotExist:
                    student = None

                if student:
                    return redirect('/')
                else:
                    return render(request, 'error.html', {'error_code': "404", 'error_message': "User not found!"})
            else:
                form.add_error('confirm_password', 'Passwords not Matched')

    else:
        form = ChangePasswordForm()

    return render(request, 'change_password.html', {'form': form})

@login_required
@admin_required
def exam_form_view(request):
    if request.method == 'POST':
        form = ExamForm(request.POST, request.FILES)
        
        if form.is_valid():
            title = form.cleaned_data['title']
            files = request.FILES.getlist('files[]')
            start_time = form.cleaned_data['start_time']
            duration = form.cleaned_data['duration']
            student = form.cleaned_data['student']
            student = UserProfile.objects.filter(id=student).first()

            if Exam.objects.filter(title=title, student=student.user).exists():
                form.add_error(None, 'A file with this title already exists.')
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors
                })

            images = []
            for file in files:
                if file.content_type == 'application/pdf':
                    new_filename = f"{title}"
                    file.name = new_filename

                    upload_result = uploader.upload(
                        file,
                        folder=f"question/{student.user.username}/{title}",  # Folder structure
                        public_id=new_filename.replace(".pdf", ""),    # Custom public ID without extension
                        # resource_type="raw",
                        resource_type="auto",                          # Automatically determine resource type
                        access_mode="public"                           # Public access mode for easy download
                    )

                    Exam.objects.create(
                        title=title,
                        question=upload_result['secure_url'],
                        start_time=start_time,
                        duration=duration,
                        student=student.user
                    )
                elif file.content_type.startswith('image/'):
                    image = Image.open(file)
                    images.append(image)

            if images:
                buffer = io.BytesIO()
                pdf = canvas.Canvas(buffer, pagesize=letter)
                width, height = letter

                for image in images:
                    img_byte_arr = io.BytesIO()
                    format = 'PNG'
                    if hasattr(image, 'format'):
                        format = image.format 
                    image.save(img_byte_arr, format=format)
                    img_byte_arr.seek(0)

                    aspect_ratio = image.height / float(image.width)
                    img_width = width
                    img_height = width * aspect_ratio
                    pdf.drawImage(ImageReader(img_byte_arr), 0, height - img_height, width=img_width, height=img_height)
                    pdf.showPage()

                pdf.save()

                # Save the generated PDF
                buffer.seek(0)
                file_name = f"{title}"
                content_file = ContentFile(buffer.getvalue(), name=file_name)

                upload_result = uploader.upload(
                    content_file,
                    folder=f"question/{student.user.username}/{title}",  # Folder structure
                    public_id=file_name.replace(".pdf", ""),    # Custom public ID without extension
                    # resource_type="raw",
                    resource_type="auto",                          # Automatically determine resource type
                    access_mode="public"                           # Public access mode for easy download
                )

                Exam.objects.create(
                    title=title,
                    question=upload_result['secure_url'],
                    start_time=start_time,
                    duration=duration,
                    student=student.user
                )

            return JsonResponse({'status': 'success','redirect': '/'})
        
    else:
        form = ExamForm()

    return render(request, 'exam_form.html', {'form': form})

@login_required
@user_required
def attend_exam_view(request):
    if request.method == 'POST':
        id = request.POST.get('exam')
        exam = Exam.objects.filter(id=id).first()
        title = exam.title
        exam.status = 'done'
        exam.save()
        files = request.FILES.getlist('files[]')

        images = []
        for file in files:
            if file.content_type == 'application/pdf':
                new_filename = f"{title}"
                file.name = new_filename

                upload_result = uploader.upload(
                    file,
                    folder=f"answer/{request.user.username}/{title}",  # Folder structure
                    public_id=new_filename.replace(".pdf", ""),    # Custom public ID without extension
                    # resource_type="raw",
                    resource_type="auto",                          # Automatically determine resource type
                    access_mode="public"                           # Public access mode for easy download
                )

                AnswerScript.objects.create(
                    answer=upload_result['secure_url'],
                    question=exam,
                    status='unchecked',
                    student=request.user
                )
            elif file.content_type.startswith('image/'):
                image = Image.open(file)
                images.append(image)

        if images:
            buffer = io.BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            for image in images:
                img_byte_arr = io.BytesIO()
                format = 'PNG'
                if hasattr(image, 'format'):
                    format = image.format 
                image.save(img_byte_arr, format=format)
                img_byte_arr.seek(0)

                aspect_ratio = image.height / float(image.width)
                img_width = width
                img_height = width * aspect_ratio
                pdf.drawImage(ImageReader(img_byte_arr), 0, height - img_height, width=img_width, height=img_height)
                pdf.showPage()

            pdf.save()

            # Save the generated PDF
            buffer.seek(0)
            file_name = f"{title}"
            content_file = ContentFile(buffer.getvalue(), name=file_name)

            upload_result = uploader.upload(
                content_file,
                folder=f"answer/{request.user.username}/{title}",  # Folder structure
                public_id=file_name.replace(".pdf", ""),    # Custom public ID without extension
                # resource_type="raw",
                resource_type="auto",                          # Automatically determine resource type
                access_mode="public"                           # Public access mode for easy download
            )

            AnswerScript.objects.create(
                answer=upload_result['secure_url'], 
                question=exam,
                status='unchecked',
                student=request.user
            )
        return JsonResponse({'status': 'success','redirect': '/attend-exam/'})
    else:
        now = timezone.now()

        latest_exam = None
        for exam in Exam.objects.all():
            if exam.start_time > now:
                if latest_exam is None or exam.start_time > latest_exam.start_time:
                    latest_exam = exam

        
        end_time = None
        if latest_exam is not None:
            if latest_exam.student != request.user:
                latest_exam = None
            else:
                end_time = latest_exam.start_time + (latest_exam.duration*60)
        
        context = {
            'exam': latest_exam,
            'end_exam': end_time
        }

    return render(request, 'attend_exam.html', context)

@login_required
@user_required
def auto_submit_view(request):
    id = request.POST.get('exam')
    exam = Exam.objects.filter(id=id).first()
    title = exam.title
    exam.status = 'done'
    exam.save()
    files = request.FILES.getlist('files[]')

    images = []
    for file in files:
        if file.content_type == 'application/pdf':
            new_filename = f"{title}"
            file.name = new_filename

            upload_result = uploader.upload(
                file,
                folder=f"answer/{request.user.username}/{title}",  # Folder structure
                public_id=new_filename.replace(".pdf", ""),    # Custom public ID without extension
                # resource_type="raw",
                resource_type="auto",                          # Automatically determine resource type
                access_mode="public"                           # Public access mode for easy download
            )

            AnswerScript.objects.create(
                answer=file,
                question=exam,
                status='unchecked',
                student=request.user
            )
        elif file.content_type.startswith('image/'):
            image = Image.open(file)
            images.append(image)

    if images:
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        for image in images:
            img_byte_arr = io.BytesIO()
            format = 'PNG'
            if hasattr(image, 'format'):
                format = image.format 
            image.save(img_byte_arr, format=format)
            img_byte_arr.seek(0)

            aspect_ratio = image.height / float(image.width)
            img_width = width
            img_height = width * aspect_ratio
            pdf.drawImage(ImageReader(img_byte_arr), 0, height - img_height, width=img_width, height=img_height)
            pdf.showPage()

        pdf.save()

        # Save the generated PDF
        buffer.seek(0)
        file_name = f"{title}"
        content_file = ContentFile(buffer.getvalue(), name=file_name)

        upload_result = uploader.upload(
            content_file,
            folder=f"answer/{request.user.username}/{title}",  # Folder structure
            public_id=file_name.replace(".pdf", ""),    # Custom public ID without extension
            # resource_type="raw",
            resource_type="auto",                          # Automatically determine resource type
            access_mode="public"                           # Public access mode for easy download
        )

        AnswerScript.objects.create(
            answer=upload_result['secure_url'], 
            question=exam,
            status='unchecked',
            student=request.user
        )

    return JsonResponse({'status': 'success','redirect': '/attend-exam/'})

@login_required
@admin_required
def exam_list_view(request):
    exam_lists = Exam.objects.all().order_by('start_time')
    return render(request, 'exam_list.html', {'exam_lists':exam_lists})

@login_required
@admin_required
def edit_exam_view(request, exam_id):
    
    exam = Exam.objects.filter(id=exam_id).first()

    if request.method == 'POST':
        form = ExamEditForm(request.POST, request.FILES)
        if form.is_valid():
            exam.start_time = form.cleaned_data['start_time']
            exam.duration = form.cleaned_data['duration']
            id = form.cleaned_data['student']
            std = UserProfile.objects.filter(id=id).first()
            exam.student = std.user
            exam.status = form.cleaned_data['status']

            folder_path = f"question/{std.user.username}/{exam.title}"
            existing_files = api.resources(type="upload", prefix=folder_path)

            if existing_files['resources'] and form.cleaned_data['delete_existing_file']:
                for file in existing_files['resources']:
                    # Delete existing file from Cloudinary
                    uploader.destroy(file['public_id'])

            # Handle file upload if a new file is provided
            if 'file' in request.FILES:
                file = request.FILES['file']
                new_filename = f"{exam.title}"
                file.name = new_filename

                upload_result = uploader.upload(
                    file,
                    folder=f"question/{std.user.username}/{exam.title}",  # Folder structure
                    public_id=new_filename.replace(".pdf", ""),    # Custom public ID without extension
                    resource_type="auto",                          # Automatically determine resource type
                    access_mode="public"                           # Public access mode for easy download
                )

                exam.question = upload_result['secure_url']  # Store the new file URL

            exam.save()

            return redirect('exam_list')
    else:
        std = UserProfile.objects.filter(user=exam.student).first()
        form = ExamEditForm(initial={
            'start_time': exam.start_time,  
            'duration': int(exam.duration.total_seconds()),
            'student': std.id if std else '',
            'status': exam.status,
        })
    
    return render(request, 'edit_exam.html', {'form': form, 'exam':exam})

@login_required
@admin_required
def show_all_students(request):
    students = UserProfile.objects.filter(role='user').all()

    return render(request, 'show_all_students.html', {'students': students})

@login_required
@admin_required
def get_all_students(request):
    students = UserProfile.objects.filter(role='user').all()

    return render(request, 'get_all_students.html', {'students': students})

@login_required
@admin_required
def get_all_students_hw(request):
    students = UserProfile.objects.filter(role='user').all()

    return render(request, 'get_all_students_hw.html', {'students': students})

@login_required
@admin_required
def get_all_students_history(request):
    students = UserProfile.objects.filter(role='user').all()

    return render(request, 'get_all_students_history.html', {'students': students})

@login_required
@admin_required
def edit_history_view(request, user_id):
    return render(request, 'history_edit.html', {'user_id':user_id})

@login_required
@admin_required
def add_month_year_view(request, user_id):
    if request.method == "POST":
        month_year = request.POST.get("month_year")
        # print(month_year,flush=True)
        if month_year:
            user = UserProfile.objects.filter(id=user_id).first()
            # print(user.user,flush=True)
            existing_val = History.objects.filter(month_year=month_year, user=user.user).first()
            # print(existing_val,flush=True)
            if existing_val:
                messages.error(request, 'A month-year with this name already exists.')
            else:
                try:
                    user = UserProfile.objects.filter(id=user_id).first()
                    last_history = History.objects.filter(user=user.user).order_by('-created_at').first()
                    print(last_history)
                    total = 0
                    if last_history:
                        total = last_history.total_day_count
                    History.objects.create(
                        month_year=month_year,
                        daycount=0,
                        total_day_count=total,
                        payment_status = 'unpaid',
                        user=user.user,
                    )
                    messages.success(request, 'Field created successfully.')
                except Exception as e:
                    messages.error(request, "Can't create new field")
        else:
            messages.error(request, 'Month-Year cannot be empty.')

    return redirect('edit_history', user_id=user_id)

@login_required
@admin_required
def edit_month_year_view(request, user_id):
    user = UserProfile.objects.filter(id=user_id).first()
    if request.method == 'POST':
        month_year = request.POST.get('month_year')
        daycount = request.POST.get('daycount')
        total_day_count = request.POST.get('total_day_count')
        last_topic = request.POST.get('last_topic')
        status = request.POST.get('status')

        history_entry = History.objects.filter(user=user.user, month_year=month_year).first()
        if history_entry:
            history_entry.daycount = daycount
            history_entry.total_day_count = total_day_count
            history_entry.payment_status = status
            history_entry.last_topic = last_topic
            history_entry.save()

    return redirect('edit_history', user_id=user_id)

@login_required
@user_required
def show_history_view(request):
    history = History.objects.filter(user=request.user).order_by('-created_at').first()
    payment_info = History.objects.filter(user=request.user).order_by('created_at').all()
    return render(request, 'show_history.html', {'history': history, 'payment':payment_info})

@login_required
def all_tools_view(request):
    return render(request, 'all_tools.html')

@login_required
def expression_to_circuit_view(request):
    return render(request, 'expressionToCircuit.html')

@login_required
def base_converter_view(request):
    return render(request, 'numberSystemConversion.html')

def password_reset_view(request):
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            confirm_password = form.cleaned_data['confirm_password']

            try:
                user_profile = UserProfile.objects.get(email=email)
            except UserProfile.DoesNotExist:
                form.add_error(None, 'This email id is not registered')
                return render(request, 'reset_password.html', {'form': form})

            if password == confirm_password:
                profile = TempProfile.objects.filter(email=email).first()
                verification_code = str(random.randint(100000, 999999))
                token_created_at = timezone.now()

                profile.verification_token = verification_code
                profile.token_created_at = token_created_at
                profile.password = password

                profile.save()
                html_message = format_html(
                    '''
                    <div style="background-color:#f4f4f4; padding: 20px;">
                        <div style="text-align: center; padding: 20px; background-color: #2b6cb0; color: #fff; border-radius: 10px;">
                            <h1>Your Verification Code</h1>
                            <p style="font-size: 24px; font-weight: bold; color: #ffdd57;">{}</p>
                        </div>
                        <p style="text-align: center; font-size: 16px;">
                            Please use this verification code to proceed with your request. The code will expire shortly.
                        </p>
                    </div>
                    ''',
                    verification_code
                )
                send_mail(
                    subject='Your Verification Code',
                    message=f'Your verification code is: {verification_code}',
                    from_email=EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                    html_message=html_message
                )

                return redirect(f'/verify-code-reset-password/{profile.id}/')
                # user = request.user
                # user.set_password(password)
                # user.save()

                # update_session_auth_hash(request, user)

                # try:
                #     student = UserProfile.objects.get(user=user)
                #     student.password = password
                    
                # except UserProfile.DoesNotExist:
                #     student = None

                # if student:
                #     return redirect('/')
                # else:
                #     return render(request, 'error.html', {'error_code': "404", 'error_message': "User not found!"})
            else:
                form.add_error('confirm_password', 'Passwords not Matched')

    else:
        form = ResetPasswordForm()

    return render(request, 'reset_password.html', {'form': form})

def verify_code_reset_password_view(request, user_id):
    if request.method == 'POST':
        form = VerificationCodeForm(request.POST)
        if form.is_valid():
            user_profile = TempProfile.objects.get(id=user_id)
            
            verification_code = form.cleaned_data['code']
            
            if user_profile.verification_token == verification_code:
                time_since_creation = timezone.now() - user_profile.token_created_at
                if time_since_creation > timedelta(minutes=3):
                    form.add_error(None, 'Verification Code expired')
                    return render(request, 'verify_code_reset_password.html', {'form': form,'user_id': user_id})
                
                profile = UserProfile.objects.get(email=user_profile.email)
                user = profile.user
                user.set_password(user_profile.password)
                user.save()

                update_session_auth_hash(request, user)

                profile.password = user_profile.password
                profile.save()
                return redirect('login')

            else:
                form.add_error(None, 'Invalid Verification Code')
                return render(request, 'verify_code_reset_password.html', {'form': form,'user_id': user_id})
    else:
        form = VerificationCodeForm()

    return render(request, 'verify_code_reset_password.html', {'form': form,'user_id': user_id})

def resend_code_reset_view(request, user_id):
    temp_profile = TempProfile.objects.filter(id=user_id).first()

    verification_code = str(random.randint(100000, 999999))
    token_created_at = timezone.now()
    temp_profile.verification_token = verification_code
    temp_profile.token_created_at = token_created_at
    temp_profile.save()
    html_message = format_html(
        '''
        <div style="background-color:#f4f4f4; padding: 20px;">
            <div style="text-align: center; padding: 20px; background-color: #2b6cb0; color: #fff; border-radius: 10px;">
                <h1>Your Verification Code</h1>
                <p style="font-size: 24px; font-weight: bold; color: #ffdd57;">{}</p>
            </div>
            <p style="text-align: center; font-size: 16px;">
                Please use this verification code to proceed with your request. The code will expire shortly.
            </p>
        </div>
        ''',
        verification_code
    )
    send_mail(
        subject='Your Verification Code',
        message=f'Your verification code is: {verification_code}',
        from_email=EMAIL_HOST_USER,
        recipient_list=[temp_profile.email],
        fail_silently=False,
        html_message=html_message
    )

    return redirect(f'/verify-code-reset-password/{user_id}/')
