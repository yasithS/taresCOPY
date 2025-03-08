# tasks/views.py
import json
import logging
from django.utils import timezone
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AddictionProfile, Task, UserTask
from .serializers import (
    AddictionProfileSerializer, 
    TaskSerializer, 
    UserTaskSerializer,
    TaskRatingSerializer
)
from .services import TaskGenerationService

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_addiction_profile(request):
    """Create or update a user's addiction profile"""
    serializer = AddictionProfileSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        profile = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_addiction_profile(request):
    """Get the current user's addiction profile"""
    try:
        profile = AddictionProfile.objects.get(user=request.user)
        serializer = AddictionProfileSerializer(profile)
        return Response(serializer.data)
    except AddictionProfile.DoesNotExist:
        return Response(
            {"detail": "Addiction profile not found. Please create one first."}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommended_tasks(request):
    """Generate and return recommended tasks for the user"""
    try:
        # Get the user's addiction profile
        try:
            profile = AddictionProfile.objects.get(user=request.user)
        except AddictionProfile.DoesNotExist:
            return Response(
                {"detail": "Addiction profile not found. Please create one first."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get number of tasks requested (default to 9 - 3 of each difficulty)
        count = int(request.query_params.get('count', 9))
        
        # Generate tasks using OpenAI
        service = TaskGenerationService()
        task_data_list = service.generate_tasks(profile, count=count)
        
        # Save generated tasks and assign to user
        user_tasks = []
        for task_data in task_data_list:
            # Create the task
            task = Task.objects.create(
                title=task_data['title'],
                description=task_data['description'],
                difficulty=task_data['difficulty'],
                marks=task_data['marks']
            )
            
            # Assign to user
            user_task = UserTask.objects.create(
                user=request.user,
                task=task
            )
            user_tasks.append(user_task)
        
        # Serialize and return
        serializer = UserTaskSerializer(user_tasks, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error generating recommended tasks: {str(e)}")
        return Response(
            {"detail": "Error generating task recommendations. Please try again later."}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_tasks(request):
    """Get all tasks assigned to the current user"""
    # Filter options
    completed = request.query_params.get('completed')
    difficulty = request.query_params.get('difficulty')
    
    # Start with all user's tasks
    tasks = UserTask.objects.filter(user=request.user)
    
    # Apply filters if provided
    if completed is not None:
        completed_bool = completed.lower() == 'true'
        tasks = tasks.filter(completed=completed_bool)
        
    if difficulty:
        tasks = tasks.filter(task__difficulty=difficulty.upper())
        
    # Order by newest first
    tasks = tasks.order_by('-assigned_at')
    
    serializer = UserTaskSerializer(tasks, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_task_detail(request, task_id):
    """Get details of a specific user task"""
    user_task = get_object_or_404(UserTask, id=task_id, user=request.user)
    serializer = UserTaskSerializer(user_task)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_task(request, task_id):
    """Mark a task as completed and award marks"""
    try:
        user_task = get_object_or_404(UserTask, id=task_id, user=request.user)
        
        if user_task.completed:
            return Response({"detail": "Task is already marked as completed"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark as completed
        user_task.completed = True
        user_task.completed_at = timezone.now()
        user_task.marks_earned = user_task.task.marks
        user_task.save()
        
        # Get user's total score
        total_marks = UserTask.objects.filter(
            user=request.user, 
            completed=True
        ).aggregate(total=Sum('marks_earned'))['total'] or 0
        
        return Response({
            "message": "Task completed successfully",
            "marks_earned": user_task.marks_earned,
            "total_marks": total_marks
        })
        
    except Exception as e:
        logger.error(f"Error completing task: {str(e)}")
        return Response(
            {"detail": "Error completing task. Please try again."}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_task(request, task_id):
    """Rate a completed task"""
    try:
        user_task = get_object_or_404(UserTask, id=task_id, user=request.user)
        
        if not user_task.completed:
            return Response(
                {"detail": "Task must be completed before it can be rated"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TaskRatingSerializer(data=request.data)
        if serializer.is_valid():
            user_task.user_rating = serializer.validated_data['rating']
            user_task.user_feedback = serializer.validated_data.get('feedback', '')
            user_task.save()
            
            return Response({"message": "Task rated successfully"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error rating task: {str(e)}")
        return Response(
            {"detail": "Error rating task. Please try again."}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_stats(request):
    """Get user's task completion statistics"""
    try:
        # Get total tasks
        total_tasks = UserTask.objects.filter(user=request.user).count()
        completed_tasks = UserTask.objects.filter(user=request.user, completed=True).count()
        
        # Get tasks by difficulty
        easy_completed = UserTask.objects.filter(
            user=request.user, 
            completed=True,
            task__difficulty='EASY'
        ).count()
        
        medium_completed = UserTask.objects.filter(
            user=request.user, 
            completed=True,
            task__difficulty='MEDIUM'
        ).count()
        
        hard_completed = UserTask.objects.filter(
            user=request.user, 
            completed=True,
            task__difficulty='HARD'
        ).count()
        
        # Get total marks
        total_marks = UserTask.objects.filter(
            user=request.user, 
            completed=True
        ).aggregate(total=Sum('marks_earned'))['total'] or 0
        
        return Response({
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0,
            "difficulty_breakdown": {
                "easy": easy_completed,
                "medium": medium_completed,
                "hard": hard_completed
            },
            "total_marks": total_marks
        })
        
    except Exception as e:
        logger.error(f"Error retrieving user stats: {str(e)}")
        return Response(
            {"detail": "Error retrieving statistics. Please try again."}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )