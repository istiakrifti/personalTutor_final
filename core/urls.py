from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('register/', views.registration_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('auto-submit/', views.auto_submit_view, name='auto_submit'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('live-class/', views.live_class_view, name='live_class'),
    path('upload-hw/', views.upload_hw_view, name='upload_hw'),
    path('check-hw/<int:user_id>/', views.upload_checked_hw_view, name='check_hw'),
    path('check-script/<int:user_id>/', views.upload_checked_scripts_view, name='check_script'),
    path('show-unchecked-hw/<int:user_id>/', views.show_unchecked_hw_view, name='show_unchecked_hw'),
    path('show-unchecked-scripts/<int:user_id>/', views.show_unchecked_scripts_view, name='show_unchecked_scripts'),
    path('show-checked-hw/', views.show_checked_hw_view, name='show_checked_hw'),
    path('show-checked-script/', views.show_checked_scripts_view, name='show_checked_script'),
    path('add-files/<int:user_id>/', views.add_files_view, name='add_files'),
    path('show-files/', views.show_files_view, name='show_files'),
    path('show-files/<int:folder_id>/', views.show_files_view, name='show_files'),
    path('add-files/<int:user_id>/<int:folder_id>/', views.add_files_view, name='add_files'),
    path('create-folder/<int:user_id>/<int:folder_id>/', views.create_folder, name='create_folder'),
    path('upload-file/<int:user_id>/<int:folder_id>/', views.upload_file, name='upload_file'),
    path('edit_file/<int:user_id>/<int:file_id>/', views.edit_file, name='edit_file'),
    path('delete_file/<int:user_id>/<int:file_id>/', views.delete_file, name='delete_file'),
    path('delete-folder/<int:user_id>/<int:folder_id>/', views.delete_folder, name='delete_folder'),
    path('take-exam/', views.exam_form_view, name='take_exam'),
    path('attend-exam/', views.attend_exam_view, name='attend_exam'),
    path('exam-list/', views.exam_list_view, name='exam_list'),
    path('edit-exam/<int:exam_id>/', views.edit_exam_view, name='edit_exam'),
    path('check-title/', views.check_title_availability, name='check_title'),
    path('check-exam-title/', views.check_exam_title_availability, name='check_exam_title'),
    path('show-all-students/', views.show_all_students, name='show_all_students'),
    path('get-all-students/', views.get_all_students, name='get_all_students'),
    path('get-all-students-hw/', views.get_all_students_hw, name='get_all_students_hw'),
    path('get-all-students-history/', views.get_all_students_history, name='get_all_students_history'),
    path('edit-history/<int:user_id>/', views.edit_history_view, name='edit_history'),
    path('add-month-year/<int:user_id>/', views.add_month_year_view, name='add_month_year'),
    path('edit-month-year/<int:user_id>/', views.edit_month_year_view, name='edit_month_year'),
    path('month-year-suggestions/', views.month_year_suggestions, name='month_year_suggestions'),
    path('additional-info/', views.additional_info_view, name='additional_info_view'),
    path('show-history/', views.show_history_view, name='show_history'),
    path('expression-to-circuit/', views.expression_to_circuit_view, name='expression_to_circuit'),
    path('base-converter/', views.base_converter_view, name='base_converter'),
    path('all-tools/', views.all_tools_view, name='all_tools'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('verify-code/<int:user_id>/', views.verify_code_view, name='verify_code'),
    path('verify-code-reset-password/<int:user_id>/', views.verify_code_reset_password_view, name='verify_code_reset_password'),
    path('resend-code/<int:user_id>/', views.resend_code_view, name='resend_code'),
    path('resend-code-reset/<int:user_id>/', views.resend_code_reset_view, name='resend_code_reset'),
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)