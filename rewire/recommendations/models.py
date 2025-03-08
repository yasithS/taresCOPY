# tasks/models.py
from django.db import models
from core.models import User

class AddictionProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='addiction_profile')
    addiction_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=[
        ('MILD', 'Mild'),
        ('MODERATE', 'Moderate'),
        ('SEVERE', 'Severe')
    ])
    triggers = models.TextField(blank=True)
    recovery_goals = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.user_name}'s {self.addiction_type} profile"

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=20, choices=[
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard')
    ])
    marks = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} ({self.difficulty})"

class UserTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    user_rating = models.IntegerField(null=True, blank=True, choices=[
        (1, '1 - Not Helpful'),
        (2, '2 - Somewhat Helpful'),
        (3, '3 - Helpful'),
        (4, '4 - Very Helpful'),
        (5, '5 - Extremely Helpful')
    ])
    user_feedback = models.TextField(blank=True)
    marks_earned = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'task')
        
    def __str__(self):
        return f"{self.user.user_name} - {self.task.title}"