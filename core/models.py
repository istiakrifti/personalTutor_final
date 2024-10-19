from django.db import models
import os, uuid
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.dispatch import receiver
from django.db.models.signals import post_save
from django import forms
from cloudinary.models import CloudinaryField

def user_directory_path(instance, filename):
    return f'user/{instance.mobile_no}/{filename}'

class HWFiles(models.Model):
    hw_title = models.CharField(max_length=255)
    file = CloudinaryField('hw')
    student = models.ForeignKey(User, on_delete=models.CASCADE,  null=True, blank=True)
    
    STATUS_CHOICES = [
        ('checked', 'Checked'),
        ('unchecked', 'Unchecked'),
        ('okay', 'Okay'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unchecked')

    def downloadable_url(self):
        return self.file.url.replace("image/upload/", "image/upload/fl_attachment/")
    # def save(self, *args, **kwargs):
    #     if self.hw_title and self.student:
    #         try:
    #             user_profile = self.student.userprofile
    #             mobile_no = user_profile.mobile_no
    #             self.file.name = os.path.join('hw', mobile_no, self.hw_title, self.file.name)
    #         except UserProfile.DoesNotExist:
    #             raise ValueError("UserProfile not found for this student.")
    #     super().save(*args, **kwargs)

    def __str__(self):
        return self.hw_title
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=150, null=False, blank=False)
    mobile_no = models.CharField(max_length=11, unique=True, null=False, blank=False)
    password = models.CharField(max_length=255, null=False, blank=False)
    email = models.EmailField(max_length=255, unique=True, null=False, blank=False)
    picture = CloudinaryField('user', null=True, blank=True)
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]
    role = models.CharField(max_length=5, choices=ROLE_CHOICES)
    verification_token = models.CharField(default=uuid.uuid4, editable=False, null=True, blank=True)
    token_created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.password:
            self.password = make_password(self.password)
        
        # if self.picture:
        #     name = self.picture.name
        #     self.picture.name = os.path.join('user', self.mobile_no, name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.role}"

class TempProfile(models.Model):
    name = models.CharField(max_length=150, null=False, blank=False)
    mobile_no = models.CharField(max_length=11, null=False, blank=False)
    password = models.CharField(max_length=255, null=False, blank=False)
    email = models.EmailField(max_length=255, null=False, blank=False)
    picture = CloudinaryField('user', null=True, blank=True)
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]
    role = models.CharField(max_length=5, choices=ROLE_CHOICES)
    verification_token = models.CharField(default=uuid.uuid4, editable=False, null=True, blank=True)
    token_created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.role}"

@receiver(post_save, sender=UserProfile)
def create_user_for_users(sender, instance, created, **kwargs):
    if created:
        user = User.objects.create(username=instance.mobile_no)
        user.password = instance.password
        user.save()

        instance.user = user
        instance.save()

class Folder(models.Model):
    name = models.CharField(max_length=255)
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='folders')

    class Meta:
        unique_together = ('name', 'parent_folder', 'user_profile')

    def __str__(self):
        return self.name

class File(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True, related_name='files')
    name = models.CharField(max_length=255)
    file = CloudinaryField('')
    public_id = models.CharField(max_length=255, null=True,blank=True)

    # def save(self, *args, **kwargs):
    #     if self.folder:
    #         # Build the full folder path by traversing the folder hierarchy
    #         folder_path = self.folder.name
    #         parent_folder = self.folder.parent_folder

    #         # Traverse up the folder hierarchy to get the full path
    #         while parent_folder:
    #             folder_path = os.path.join(parent_folder.name, folder_path)
    #             parent_folder = parent_folder.parent_folder

    #         # Join the 'files' directory with the constructed folder path
    #         self.file.name = os.path.join('files', folder_path, self.file.name)
    #     super().save(*args, **kwargs)
    def downloadable_url(self):
        return self.file.url.replace("image/upload/", "image/upload/fl_attachment/")

    def __str__(self):
        return self.name

def question_upload_path(instance, filename):
    user_profile = instance.student.userprofile
    mobile_no = user_profile.mobile_no
    return f'questions/{mobile_no}/{instance.title}/{filename}'

class Exam(models.Model):
    title = models.CharField(max_length=255)
    question = CloudinaryField(question_upload_path)
    start_time = models.DateTimeField()
    duration = models.DurationField()
    student = models.ForeignKey(User, on_delete=models.CASCADE,  null=True, blank=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('okay', 'Okay'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    def downloadable_url(self):
        return self.question.url.replace("image/upload/", "image/upload/fl_attachment/")

    def __str__(self):
        return self.title

def answer_upload_path(instance, filename):
    user_profile = instance.student.userprofile
    mobile_no = user_profile.mobile_no
    return f'answers/{mobile_no}/{instance.question.title}/{filename}'

class AnswerScript(models.Model):
    answer = CloudinaryField(answer_upload_path)
    question = models.ForeignKey(Exam, on_delete=models.CASCADE,  null=True, blank=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE,  null=True, blank=True)

    STATUS_CHOICES = [
        ('checked', 'Checked'),
        ('unchecked', 'Unchecked'),
        ('okay', 'Okay'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unchecked')

    def downloadable_url(self):
        return self.answer.url.replace("image/upload/", "image/upload/fl_attachment/")

    def __str__(self):
        return self.question.title
    
class History(models.Model):
    month_year = models.CharField(max_length=20)
    daycount = models.IntegerField(null=True, blank=True)
    total_day_count = models.IntegerField(null=True, blank=True)
    last_topic = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
    ]
    payment_status = models.CharField(max_length=6, choices=PAYMENT_STATUS_CHOICES, default='unpaid', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.month_year} - {self.payment_status}"
