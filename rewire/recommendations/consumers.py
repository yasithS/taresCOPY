# tasks/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import UserTask

class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        # Anonymous users can't connect
        if self.user.is_anonymous:
            await self.close()
            return
            
        self.room_name = f"user_{self.user.id}_tasks"
        self.room_group_name = f"tasks_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Send initial stats when connecting
        stats = await self.get_user_stats()
        await self.send(text_data=json.dumps({
            'type': 'user_stats',
            'data': stats
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            action = text_data_json.get("action")
            
            if action == "get_stats":
                stats = await self.get_user_stats()
                await self.send(text_data=json.dumps({
                    'type': 'user_stats',
                    'data': stats
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

    # Send task update to WebSocket
    async def task_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'task_update',
            'data': event["data"]
        }))
        
    @database_sync_to_async
    def get_user_stats(self):
        """Get user's task statistics"""
        # Get total tasks
        total_tasks = UserTask.objects.filter(user=self.user).count()
        completed_tasks = UserTask.objects.filter(user=self.user, completed=True).count()
        
        # Calculate completion rate
        completion_rate = 0
        if total_tasks > 0:
            completion_rate = round(completed_tasks / total_tasks * 100, 2)
            
        # Get tasks by difficulty
        easy_completed = UserTask.objects.filter(
            user=self.user, 
            completed=True,
            task__difficulty='EASY'
        ).count()
        
        medium_completed = UserTask.objects.filter(
            user=self.user, 
            completed=True,
            task__difficulty='MEDIUM'
        ).count()
        
        hard_completed = UserTask.objects.filter(
            user=self.user, 
            completed=True,
            task__difficulty='HARD'
        ).count()
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": completion_rate,
            "difficulty_breakdown": {
                "easy": easy_completed,
                "medium": medium_completed,
                "hard": hard_completed
            }
        }