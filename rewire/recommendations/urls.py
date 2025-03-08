# tasks/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Addiction Profile endpoints
    path('profile/create/', views.create_addiction_profile, name='create_addiction_profile'),
    path('profile/', views.get_addiction_profile, name='get_addiction_profile'),
    
    # Task endpoints
    path('recommendations/', views.get_recommended_tasks, name='get_recommended_tasks'),
    path('list/', views.get_user_tasks, name='get_user_tasks'),
    path('<int:task_id>/', views.get_user_task_detail, name='get_user_task_detail'),
    path('<int:task_id>/complete/', views.complete_task, name='complete_task'),
    path('<int:task_id>/rate/', views.rate_task, name='rate_task'),
    
    # Stats endpoints
    path('stats/', views.get_user_stats, name='get_user_stats'),
]