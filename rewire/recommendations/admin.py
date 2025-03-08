from django.contrib import admin
from .models import AddictionProfile, Task, UserTask

@admin.register(AddictionProfile)
class AddictionProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'addiction_type', 'severity', 'created_at')
    search_fields = ('user__email', 'user__user_name', 'addiction_type')
    list_filter = ('severity', 'addiction_type')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'difficulty', 'marks', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('difficulty', 'marks')

@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'assigned_at', 'completed', 'completed_at', 'user_rating', 'marks_earned')
    search_fields = ('user__email', 'user__user_name', 'task__title')
    list_filter = ('completed', 'user_rating', 'task__difficulty')
    readonly_fields = ('assigned_at',)
