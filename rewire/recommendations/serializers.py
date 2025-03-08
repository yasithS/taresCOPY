# tasks/serializers.py
from rest_framework import serializers
from .models import AddictionProfile, Task, UserTask

class AddictionProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddictionProfile
        fields = ['id', 'addiction_type', 'severity', 'triggers', 'recovery_goals']
        
    def create(self, validated_data):
        user = self.context['request'].user
        profile, created = AddictionProfile.objects.update_or_create(
            user=user,
            defaults=validated_data
        )
        return profile

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'difficulty', 'marks']

class UserTaskSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    
    class Meta:
        model = UserTask
        fields = ['id', 'task', 'assigned_at', 'completed', 'completed_at', 
                 'user_rating', 'user_feedback', 'marks_earned']

class TaskRatingSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    feedback = serializers.CharField(required=False, allow_blank=True)
    
    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value