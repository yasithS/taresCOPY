# tasks/services.py
import os
import json
import logging
import openai
from django.conf import settings
from .models import Task

logger = logging.getLogger(__name__)

class TaskGenerationService:
    def __init__(self):
        # Get API key from environment variables
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.error("OpenAI API key is not set in environment variables")
            raise ValueError("OpenAI API key is missing")
        
        openai.api_key = self.api_key
    
    def generate_tasks(self, addiction_profile, count=9):
        """
        Generate tasks based on addiction profile
        Returns tasks of varying difficulty (easy, medium, hard)
        
        Args:
            addiction_profile: The user's AddictionProfile instance
            count: Total number of tasks to generate (default=9, 3 of each difficulty)
            
        Returns:
            List of dictionaries representing tasks
        """
        try:
            # Calculate number of tasks per difficulty level
            easy_count = medium_count = hard_count = count // 3
            # Adjust if count is not divisible by 3
            if count % 3 == 1:
                easy_count += 1
            elif count % 3 == 2:
                easy_count += 1
                medium_count += 1
                
            # Construct prompt for OpenAI
            prompt = self._construct_prompt(
                addiction_profile, 
                easy_count=easy_count,
                medium_count=medium_count,
                hard_count=hard_count
            )
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4",  # You can adjust the model as needed
                messages=[
                    {"role": "system", "content": "You are a recovery coach specializing in addiction treatment. You create personalized tasks to help individuals overcome addiction, with careful attention to their specific triggers, goals, and severity level."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                top_p=1.0,
            )
            
            # Process the response
            return self._process_response(response)
            
        except Exception as e:
            logger.error(f"Error generating tasks: {str(e)}")
            # Return some default tasks in case of error
            return self._generate_fallback_tasks(count)
    
    def _construct_prompt(self, profile, easy_count=3, medium_count=3, hard_count=3):
        """Constructs a detailed prompt for the OpenAI API based on the user's profile"""
        
        return f"""
        Generate a personalized set of recovery tasks for someone dealing with {profile.addiction_type} addiction.
        
        INDIVIDUAL PROFILE:
        - Addiction Type: {profile.addiction_type}
        - Severity: {profile.severity}
        - Triggers: {profile.triggers}
        - Recovery Goals: {profile.recovery_goals}
        
        CREATE THE FOLLOWING TASKS:
        - {easy_count} EASY tasks (worth 5 marks each)
        - {medium_count} MEDIUM tasks (worth 10 marks each)
        - {hard_count} HARD tasks (worth 15 marks each)
        
        TASK REQUIREMENTS:
        1. Be specific and actionable
        2. Relate directly to the addiction type and recovery goals
        3. Consider the individual's triggers
        4. Match the appropriate difficulty level
        5. Each task should be achievable in a reasonable timeframe
        
        FORMAT:
        Return your response as a JSON array of objects, each with the following properties:
        - "title": A brief, descriptive title for the task
        - "description": Detailed instructions for completing the task
        - "difficulty": One of "EASY", "MEDIUM", or "HARD"
        - "marks": 5 for EASY, 10 for MEDIUM, 15 for HARD
        
        Example format (this is just an example, generate relevant tasks based on the profile):
        [
            {
                "title": "Morning Meditation",
                "description": "Complete a 5-minute guided meditation focusing on cravings.",
                "difficulty": "EASY",
                "marks": 5
            }
        ]
        
        YOUR RESPONSE MUST BE VALID JSON THAT CAN BE PARSED.
        """
    
    def _process_response(self, response):
        """Process and validate the OpenAI API response"""
        try:
            # Extract content from response
            content = response.choices[0].message.content.strip()
            
            # Find JSON array in the response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("Could not find JSON array in response")
                
            json_str = content[start_idx:end_idx]
            tasks = json.loads(json_str)
            
            # Validate each task
            validated_tasks = []
            for task in tasks:
                # Ensure required fields are present
                if all(key in task for key in ['title', 'description', 'difficulty', 'marks']):
                    # Normalize difficulty to uppercase
                    task['difficulty'] = task['difficulty'].upper()
                    
                    # Validate difficulty and marks
                    if task['difficulty'] not in ['EASY', 'MEDIUM', 'HARD']:
                        task['difficulty'] = 'MEDIUM'
                    
                    # Ensure marks match difficulty
                    if task['difficulty'] == 'EASY':
                        task['marks'] = 5
                    elif task['difficulty'] == 'MEDIUM':
                        task['marks'] = 10
                    elif task['difficulty'] == 'HARD':
                        task['marks'] = 15
                    
                    validated_tasks.append(task)
            
            return validated_tasks
            
        except Exception as e:
            logger.error(f"Error processing OpenAI response: {str(e)}")
            raise
    
    def _generate_fallback_tasks(self, count):
        """Generate fallback tasks in case of API failure"""
        fallback_tasks = [
            {
                "title": "Daily Reflection Journal",
                "description": "Spend 5 minutes writing about your feelings and progress today.",
                "difficulty": "EASY",
                "marks": 5
            },
            {
                "title": "Hydration Goal",
                "description": "Drink 8 glasses of water throughout the day to maintain hydration.",
                "difficulty": "EASY",
                "marks": 5
            },
            {
                "title": "Trigger Identification",
                "description": "Make a list of 3 situations that triggered cravings in the past week.",
                "difficulty": "EASY",
                "marks": 5
            },
            {
                "title": "30-Minute Exercise",
                "description": "Complete 30 minutes of moderate exercise like walking, jogging, or cycling.",
                "difficulty": "MEDIUM",
                "marks": 10
            },
            {
                "title": "Support Meeting",
                "description": "Attend a support group meeting online or in person.",
                "difficulty": "MEDIUM",
                "marks": 10
            },
            {
                "title": "Stress Management Practice",
                "description": "Learn and practice a new stress management technique for 15 minutes.",
                "difficulty": "MEDIUM",
                "marks": 10
            },
            {
                "title": "Difficult Conversation",
                "description": "Have an honest conversation with someone impacted by your addiction.",
                "difficulty": "HARD",
                "marks": 15
            },
            {
                "title": "Full Day Challenge",
                "description": "Complete a full day without engaging in your addictive behavior, using all your coping strategies.",
                "difficulty": "HARD",
                "marks": 15
            },
            {
                "title": "Temptation Navigation",
                "description": "Deliberately expose yourself to a moderate trigger and practice your coping skills to overcome it.",
                "difficulty": "HARD",
                "marks": 15
            }
        ]
        
        # Return the requested number of tasks
        return fallback_tasks[:count]