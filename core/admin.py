from django.contrib import admin
from .models import HWFiles, Folder, File, UserProfile, Exam, AnswerScript, History


class HWFilesAdmin(admin.ModelAdmin):
    list_display = ('hw_title', 'status')

class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_folder')
    search_fields = ('name',)
    list_filter = ('parent_folder',)

class FileAdmin(admin.ModelAdmin):
    list_display = ('name', 'folder')
    search_fields = ('name',)
    list_filter = ('folder',)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'mobile_no', 'role',)
    search_fields = ('name', 'mobile_no',)
    list_filter = ('role',)

class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'student',)
    search_fields = ('title', 'student',)
    list_filter = ('student',)

# Register models in admin
admin.site.register(HWFiles)
admin.site.register(Folder, FolderAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Exam, ExamAdmin)
admin.site.register(AnswerScript)
admin.site.register(History)